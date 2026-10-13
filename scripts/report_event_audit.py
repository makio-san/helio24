"""Render self-contained event audit tables and representative region timelines."""
import base64
from html import escape
from io import BytesIO
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from helio24.data import ROOT
from helio24.event_views import load_audit, timeline
from helio24.full_data import sha256


def render(root=ROOT):
    output = root / 'artifacts/event_audit'
    report, windows, episodes, events, regions = load_audit(output)
    rejected_path = root / 'data/event_mapping/rejected.csv'
    if sha256(rejected_path) != report['mapping_audit']['files']['rejected.csv']:
        raise ValueError('Mapping rejection source changed')
    rejected_counts = pd.read_csv(rejected_path).reason.value_counts().to_dict()
    picks = dict.fromkeys([int(regions.harp.iloc[0]),
                          int(regions.sort_values('longest_all_negative_hours', ascending=False).harp.iloc[0]),
                          int(regions.sort_values('mapped_covered_events', ascending=False).harp.iloc[0])])
    charts = []
    for harp in picks:
        fig = timeline(windows, episodes, events, harp, report['threshold'], reveal=True)
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=140, bbox_inches='tight')
        fig.savefig(output / f'harp_{harp}.png', dpi=140, bbox_inches='tight')
        plt.close(fig)
        encoded = base64.b64encode(buffer.getvalue()).decode()
        charts.append(f'<img alt="HARP {harp} retrospective timeline" src="data:image/png;base64,{encoded}">')
    rows = {key: value for key, value in report.items() if not isinstance(value, dict)}
    summary_table = pd.DataFrame(list(rows.items()), columns=['Measure', 'Value']).to_html(index=False, escape=True)
    counts = pd.DataFrame(list(report['catalog_status_counts'].items()), columns=['Catalog status', 'Events'])
    eligible = events[events.status == 'evaluated']
    conflicts = pd.read_csv(output / 'label_conflicts.csv')
    conflicts = conflicts.merge(events[['flare_id', 'goes_class', 'peak_time', 'evidence']], on='flare_id', how='left')
    features = pd.read_csv(output / 'outcome_features.csv')
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Helio24 alarm and event audit</title><style>
body{{font:15px/1.5 system-ui;max-width:1150px;margin:32px auto;padding:0 20px;color:#183040}}
img{{width:100%;margin:20px 0}}table{{border-collapse:collapse;font-size:13px;width:100%}}
td,th{{padding:6px;border:1px solid #d7e0e7;text-align:left}}.scroll{{overflow:auto;margin:20px 0}}
.notice{{background:#fff3df;padding:15px;border-left:4px solid #bb700c}}
</style></head><body><h1>Alarm periods and covered flare events</h1>
<p>Experiment 2, full-calibrated model, partition-4 development predictions.
Frozen threshold {report['threshold']:.4%}. No refitting or new held-out test.</p>
<p>{report['episodes']} alarm periods; {report['all_negative_episodes']} all-negative periods;
{report['false_alarm_region_hours']:,.0f} benchmark false-alarm region-hours out of
{report['monitored_region_hours']:,.0f} monitored region-hours ({report['false_alarm_hour_fraction']:.2%}).</p>
<p>Detected {report['detected_events']}/{report['covered_mapped_events']} covered mapped events;
{report['before_start_events']} received an alarm strictly before catalog start.
The fully covered prior-24-hour subset is {report['fully_covered_detected']}/{report['fully_covered_events']}.
This conditional event recall is compatible with long, repeated false alarms and incomplete mapping.</p>
<p class="notice">{report['mapped_event_negative_label_conflicts']} event/window associations conflict with
negative benchmark labels. Alarm burden keeps the original labels. Event matching uses catalog peaks
and recovered associations. These two definitions do not completely agree; no relabeling was performed.</p>
<h2>Counting and coverage</h2><p>Each forecast contributes up to one hour of state, including the last
record. Gaps break episodes; 24-hour forecast horizons are not counted as 24 hours of alarm state.
Hours sum across regions and are not wall-clock hours for one observer. {report['boundary_or_gap_censored_episodes']}
episodes touch a gap or region boundary, so complete duration is unknown.</p>
<p>Only unique, unambiguous catalog IDs with an available forecast are evaluated. Unmapped whole-Sun
catalog entries are not automatic misses. History annotations recover events hidden by strongest-window
labels; timestamp mismatches and unverified annotations are excluded. The source contains
{rejected_counts.get('peak_not_near_annotation', 0)} rejected time associations and
{rejected_counts.get('unverified', 0)} unverified associations. First-warning lead is measured from the earliest
qualifying issue within the 24-hour horizon, not necessarily the beginning of a longer alarm episode.</p>
{counts.to_html(index=False)}<h2>Representative regions</h2>
<p>Selected deterministically: most false hours, longest all-negative episode, most covered mapped events.
Orange bands are alarm state, magenta lines are catalog peaks. Magnetic measurements are the final
masked sample from each observation window, plotted at issue time (12 minutes after the sample).
Neither forecast nor measurement curves connect across unavailable forecasts.</p>
{''.join(charts)}<h2>Region ranking by false hours</h2>
<div class="scroll">{regions.head(15).to_html(index=False, float_format=lambda x: f'{x:.4g}')}</div>
<h2>Measurement summaries by window outcome</h2>{features.to_html(index=False, float_format=lambda x: f'{x:.4g}')}
<p>These overlapping-window summaries are descriptive associations, not causal explanations or
independent significance tests. High event recall alone does not establish a useful operating policy.</p>
<h2>Mapped event/label conflicts</h2>{conflicts.to_html(index=False)}
<h2>Evaluated unique events</h2><div class="scroll">{eligible.to_html(index=False)}</div>
<h2>Complete summary</h2>{summary_table}
<h2>Protocol</h2><pre style="white-space:pre-wrap">{escape((output / 'protocol.md').read_text())}</pre>
</body></html>'''
    (output / 'report.html').write_text(html)
    print(output / 'report.html')


if __name__ == '__main__':
    render()
