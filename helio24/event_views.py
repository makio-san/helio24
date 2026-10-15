"""Shared, gap-preserving retrospective timeline and optional dashboard tab."""
import json

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from helio24.events import HOUR
from helio24.full_data import sha256
from helio24.sensitivity import load_sensitivity


def load_investigation(root):
    directory = root / 'artifacts/event_provenance'
    report = json.loads((directory / 'report.json').read_text())
    for name, digest in report['source_hashes'].items():
        if sha256(root / name) != digest:
            raise ValueError(f'Investigation source changed: {name}')
    for name, digest in report['artifact_hashes'].items():
        if sha256(directory / name) != digest:
            raise ValueError(f'Investigation evidence changed: {name}')
    return report


def load_audit(directory):
    report = json.loads((directory / 'report.json').read_text())
    for name, digest in report['artifact_hashes'].items():
        if sha256(directory / name) != digest:
            raise ValueError(f'Event audit artifact changed: {name}')
    windows = pd.read_parquet(directory / 'windows.parquet')
    episodes = pd.read_csv(directory / 'episodes.csv', parse_dates=['start', 'end'])
    events = pd.read_csv(directory / 'events.csv', parse_dates=['start_time', 'peak_time', 'first_alarm'])
    regions = pd.read_csv(directory / 'regions.csv')
    return report, windows, episodes, events, regions


def timeline(windows, episodes, events, harp, threshold, measurement='USFLUX__last', reveal=False):
    group = windows[windows.harp.eq(harp)].sort_values('forecast_time')
    runs = episodes[episodes.harp.eq(harp)]
    local = events[(events.harp == harp) & (events.status != 'ambiguous')]
    fig, axes = plt.subplots(3, 1, figsize=(11, 6.5), sharex=True,
                             gridspec_kw={'height_ratios': [2, 1.5, 1]})
    # Each segment stops at a missing hourly forecast. NaNs in measurements
    # remain NaNs; single-point segments retain a visible marker.
    segments = group.forecast_time.diff().ne(HOUR).cumsum()
    for _, segment in group.groupby(segments):
        stamps = [*segment.forecast_time, segment.state_end.iloc[-1]]
        axes[0].step(stamps, np.r_[segment.probability.to_numpy(), segment.probability.iloc[-1]]*100,
                     where='post', color='#2379a5', linewidth=1.4)
        axes[1].plot(segment.forecast_time, segment[measurement], '.-', color='#2379a5', markersize=2)
        axes[2].step(stamps, np.r_[segment.missing_fraction.to_numpy(), segment.missing_fraction.iloc[-1]]*100,
                     where='post', color='#737373', linewidth=1)
    for run in runs.itertuples(index=False):
        axes[0].axvspan(run.start, run.end, color='#f6a54c', alpha=.24)
    axes[0].axhline(threshold*100, color='#a75b13', linestyle='--', linewidth=1,
                   label=f'Frozen threshold {threshold:.2%}')
    if reveal:
        for event in local.itertuples(index=False):
            for ax in axes:
                ax.axvline(event.peak_time, color='#ad1951', alpha=.6, linewidth=1)
            axes[0].annotate(event.goes_class, (event.peak_time, 1), xycoords=('data', 'axes fraction'),
                             rotation=90, fontsize=7, va='top', color='#ad1951')
    axes[0].set(ylabel='M/X probability (%)', ylim=(0, 100),
                title=f'HARP {int(harp)} · experiment-2 development timeline')
    axes[0].legend(loc='upper left', fontsize=8)
    axes[1].set_ylabel(measurement.replace('__last', '')+'\nlast measurement')
    axes[2].set_ylabel('Masked (%)')
    axes[2].set_xlabel('Forecast issue time · UTC (hourly state; gaps remain unobserved)')
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%d %b\n%H:%M'))
    for ax in axes:
        ax.grid(axis='y', alpha=.2)
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    return fig


def render_event_tab(root):
    import streamlit as st

    directory = root / 'artifacts/event_audit'
    st.subheader('Alarm periods and mapped flare events')
    st.caption('Experiment 2 · full calibrated model · partition-4 development data. '
               'This audit uses a different model and period from the historical replay tab.')
    if not (directory / 'report.json').exists():
        st.info('No event audit is available. Prepare event associations and run the audit first.')
        st.code('python scripts/prepare_event_mapping.py\npython scripts/run_event_audit.py')
        return
    @st.cache_data
    def cached_load(path, revision):
        return load_audit(path)
    try:
        revision = tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size)
                         for p in sorted(directory.iterdir()) if p.is_file())
        report, windows, episodes, events, regions = cached_load(directory, revision)
    except (ValueError, FileNotFoundError) as error:
        st.error(f'Event audit cannot be loaded: {error}')
        return
    st.write(f"{report['episodes']:,} alarm periods · {report['all_negative_episodes']:,} all-negative periods · "
             f"{report['false_alarm_region_hours']:,.0f} benchmark false-alarm region-hours "
             f"({report['false_alarm_hour_fraction']:.2%} of monitored region-hours).")
    st.caption('Durations assign up to one hour to each available forecast, including the last one. '
               'Missing forecasts break alarm periods. Region-hours add across regions, not wall-clock time. '
               'All-negative and false-alarm hours use the benchmark window labels.')
    st.write(f"Covered mapped events: {report['detected_events']}/{report['covered_mapped_events']} detected; "
             f"{report['before_start_events']} warned before catalog start. "
             f"Fully covered prior 24h: {report['fully_covered_detected']}/{report['fully_covered_events']} detected.")
    st.caption('Event recall is conditional on verified mapping and available forecasts. '
               'A long alarm can cover several events; this is not independent final-test performance.')
    if report['mapped_event_negative_label_conflicts']:
        st.warning(f"{report['mapped_event_negative_label_conflicts']} event/window associations conflict with "
                   'negative benchmark labels. Inspect the mapping conflicts below before interpreting event recall.')
    if (root / 'artifacts/event_provenance/report.json').exists():
        with st.expander('Label provenance investigation'):
            try:
                investigation = load_investigation(root)
            except (ValueError, FileNotFoundError) as error:
                st.error(f'Provenance evidence cannot be verified: {error}')
            else:
                st.write(f"Catalog event {investigation['case_event']}: archive history associations")
                st.dataframe(pd.DataFrame(investigation['case_associations']), hide_index=True)
                st.write('HARPs in positive filename labels for this event: '
                         + (', '.join(map(str, investigation['case_filename_harps'])) or 'None in partition 4'))
                st.caption('NOAA-number and location-based histories are distinct association methods. '
                           'Agreement with a filename does not establish the physically correct location. '
                           'The existing event audit retains its original conservative mapping rules.')
                st.dataframe(pd.DataFrame(investigation['timing']), hide_index=True)
                st.caption('Nearest-compatible: within six minutes of catalog peak. '
                           'Containing-compatible: peak falls in [annotation time, annotation time + 12 minutes). '
                           'These conventions differ; no automatic relabeling has been applied.')
    if (root / 'artifacts/label_sensitivity/report.json').exists():
        with st.expander('Label association sensitivity'):
            try:
                sensitivity, metrics, transitions = load_sensitivity(root)
            except (ValueError, FileNotFoundError) as error:
                st.error(f'Sensitivity evidence cannot be verified: {error}')
            else:
                st.caption('Six development comparisons with fixed probabilities, threshold and benchmark labels. '
                           'Every variant retains filename evidence; ambiguous mappings are excluded. '
                           'Conditional event recall is not independent test performance.')
                shown = metrics.copy()
                for column in ['recall', 'fully_covered_recall', 'common_recall']:
                    shown[column] = shown[column].map(lambda x: f'{x:.2%}' if pd.notna(x) else 'Not evaluated')
                st.dataframe(shown, hide_index=True)
                st.caption('Nearest: within six minutes of catalog peak. Containing: peak falls in the '
                           '12-minute interval starting at the annotation. Common events are evaluated on '
                           'the same HARP in all six variants. Conflicts count event/window pairs.')
                st.write(f"Benchmark false-alarm region-hours remain {sensitivity['false_alarm_region_hours']:,.0f}.")
                st.dataframe(transitions[transitions.changed], hide_index=True)
                sensitivity_dir = root / 'artifacts/label_sensitivity'
                st.download_button('Download sensitivity comparison', (sensitivity_dir / 'metrics.csv').read_bytes(),
                                   file_name='label_sensitivity.csv', mime='text/csv', key='sensitivity_csv')
                st.download_button('Download sensitivity report', (sensitivity_dir / 'report.html').read_bytes(),
                                   file_name='label_sensitivity.html', mime='text/html', key='sensitivity_html')
    ordering = st.selectbox('Rank regions by', ['False-alarm hours', 'Longest all-negative period'], key='event_rank')
    key = 'false_hours' if ordering == 'False-alarm hours' else 'longest_all_negative_hours'
    ordered = regions.sort_values([key, 'harp'], ascending=[False, True])
    harp = st.selectbox('Audit region', ordered.harp.tolist(), key=f'event_region_{key}',
                        format_func=lambda value: f'HARP {value}')
    measurement = st.selectbox('Timeline magnetic measurement', ['USFLUX__last', 'R_VALUE__last', 'TOTUSJH__last'],
                              key='event_measurement', format_func=lambda x: x.replace('__last', ''))
    reveal = st.checkbox('Reveal mapped flare peaks', value=False, key=f'event_reveal_{harp}')
    fig = timeline(windows, episodes, events, harp, report['threshold'], measurement, reveal)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption('Orange spans: alarm periods. Measurement points: final masked measurement from each '
               '12-hour observation window (sampled 12 minutes before issue), shown at forecast issue time. '
               'When revealed, magenta lines mark catalog peak times. Mapping may be incomplete.')
    st.dataframe(episodes[episodes.harp.eq(harp)], hide_index=True, width='stretch')
    if reveal:
        st.dataframe(events[events.harp.eq(harp)], hide_index=True, width='stretch')
    with st.expander('Region comparisons and mapping coverage'):
        st.dataframe(ordered, hide_index=True, width='stretch')
        st.dataframe(pd.DataFrame(list(report['catalog_status_counts'].items()), columns=['Catalog status', 'Events']), hide_index=True)
        st.caption('Unmapped whole-Sun catalog events are not automatically regional misses. '
                   'Uncovered and ambiguous events are excluded from recall.')
        st.dataframe(pd.read_csv(directory / 'label_conflicts.csv'), hide_index=True)
    for filename, label in [('episodes.csv', 'Download alarm periods'), ('events.csv', 'Download catalog event audit'),
                            ('regions.csv', 'Download region comparisons')]:
        st.download_button(label, (directory / filename).read_bytes(), file_name=filename, mime='text/csv', key='event_'+filename)
