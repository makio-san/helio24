"""Helio24 local historical replay dashboard. No live or synthetic predictions."""
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from helio24.data import MAGNETIC_COLUMNS, ROOT, read_observation, trusted_measurements
from helio24.modeling import metrics

st.set_page_config(
    page_title='Helio24 | Solar flare research console',
    page_icon='☀',
    layout='wide',
    initial_sidebar_state='collapsed',
)
st.markdown(
    '''
    <style>
    :root {
        --ink: #edf3f7;
        --muted: #8fa1b1;
        --line: rgba(148, 169, 187, .16);
        --panel: rgba(14, 27, 38, .88);
        --accent: #ffb45e;
        --accent-soft: rgba(255, 180, 94, .12);
    }
    .stApp {
        background:
            radial-gradient(circle at 78% -12%, rgba(39, 111, 139, .16), transparent 32rem),
            radial-gradient(circle at 8% 8%, rgba(255, 155, 68, .07), transparent 24rem),
            #071018;
        color: var(--ink);
    }
    header[data-testid="stHeader"] {background: transparent;}
    .block-container {max-width: 1180px; padding: 1.25rem 2rem 4rem;}
    h1, h2, h3, p {letter-spacing: -.018em;}
    h2 {font-size: 1.65rem !important; margin-bottom: .2rem !important;}
    h3 {font-size: 1.08rem !important;}
    [data-testid="stCaptionContainer"] {color: var(--muted);}
    [data-testid="stMetric"] {
        min-height: 118px;
        padding: 1.15rem 1.2rem;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: linear-gradient(145deg, rgba(17, 32, 44, .96), rgba(10, 22, 31, .92));
        box-shadow: 0 18px 40px rgba(0, 0, 0, .12);
    }
    [data-testid="stMetricLabel"] p {
        color: #9fb0bf;
        font-size: .78rem;
        letter-spacing: .045em;
        text-transform: uppercase;
        white-space: normal;
    }
    [data-testid="stMetricValue"] {font-size: 2rem;}
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line) !important;
        border-radius: 16px !important;
        background: rgba(10, 21, 30, .52);
    }
    [data-testid="stAlert"] {border-radius: 12px;}
    [data-testid="stDataFrame"] {border: 1px solid var(--line); border-radius: 12px; overflow: hidden;}
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.7rem;
        border-bottom: 1px solid var(--line);
    }
    .stTabs [data-baseweb="tab"] {
        height: 3.2rem;
        padding: 0;
        color: #8fa1b1;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {color: var(--ink) !important;}
    .stTabs [data-baseweb="tab-highlight"] {background-color: var(--accent);}
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 3.4rem;
        border-bottom: 1px solid var(--line);
    }
    .brand {display: flex; align-items: center; gap: .72rem; font-size: .82rem; font-weight: 750; letter-spacing: .16em;}
    .brand small {color: var(--muted); font-size: .68rem; font-weight: 600; letter-spacing: .12em;}
    .sun-mark {
        width: 19px;
        height: 19px;
        display: inline-block;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 30%, #fff3c4, #ffb45e 44%, #d65a32 82%);
        box-shadow: 0 0 22px rgba(255, 168, 81, .3);
    }
    .mode-pill {
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        padding: .42rem .7rem;
        border: 1px solid var(--line);
        border-radius: 999px;
        color: #a9b8c4;
        font-size: .67rem;
        font-weight: 700;
        letter-spacing: .1em;
    }
    .mode-pill i {width: 6px; height: 6px; border-radius: 50%; background: #71c6a3;}
    .hero {padding: 2.5rem 0 2rem; max-width: 980px;}
    .kicker {color: var(--accent); font-size: .7rem; font-weight: 750; letter-spacing: .18em; margin-bottom: 1rem;}
    .hero h1 {font-size: clamp(2.8rem, 5vw, 4.15rem); line-height: 1; margin: 0; letter-spacing: -.055em;}
    .hero h1 span {color: #91a4b3;}
    .hero p {max-width: 660px; margin: 1.35rem 0 0; color: #9eafbd; font-size: 1.02rem; line-height: 1.65;}
    .run-strip {
        display: grid;
        grid-template-columns: 1.35fr 1fr 1fr;
        gap: 1px;
        margin-bottom: 1.4rem;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 14px;
        background: var(--line);
    }
    .run-strip div {padding: .9rem 1rem; background: #0b1720;}
    .run-strip span {display: block; color: #718695; font-size: .64rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;}
    .run-strip strong {display: block; margin-top: .28rem; color: #dfe8ee; font-size: .88rem; font-weight: 600;}
    .window-context {
        margin: .7rem 0 1rem;
        color: #718695;
        font-size: .74rem;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .window-context b {color: #cbd6de; font-weight: 700;}
    .section-label {margin: 1.1rem 0 .15rem; color: #dfe8ee; font-size: 1rem; font-weight: 700;}
    .placeholder {
        min-height: 126px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.2rem;
        border: 1px dashed rgba(148, 169, 187, .25);
        border-radius: 12px;
        color: #718695;
        text-align: center;
        font-size: .86rem;
    }
    .method-card {min-height: 150px; padding: 1.15rem; border: 1px solid var(--line); border-radius: 14px; background: rgba(13, 25, 35, .62);}
    .method-card span {color: var(--accent); font-size: .65rem; font-weight: 750; letter-spacing: .12em;}
    .method-card h4 {margin: .55rem 0 .45rem; color: #e6edf2;}
    .method-card p {margin: 0; color: #8fa1b1; font-size: .84rem; line-height: 1.55;}
    .fine-print {margin-top: 2rem; color: #647987; font-size: .72rem; line-height: 1.6;}
    @media (max-width: 760px) {
        .block-container {padding: .8rem 1rem 3rem;}
        .brand small {display: none;}
        .hero {padding: 2.4rem 0 2rem;}
        .hero h1 {font-size: 3.2rem;}
        .run-strip {grid-template-columns: 1fr;}
    }
    </style>
    ''',
    unsafe_allow_html=True,
)

st.markdown(
    '''
    <div class="topbar">
        <div class="brand"><span class="sun-mark"></span> HELIO24 <small>RESEARCH CONSOLE</small></div>
        <div class="mode-pill"><i></i> HISTORICAL MODE</div>
    </div>
    <section class="hero">
        <div class="kicker">SWAN-SF · 24-HOUR FORECAST</div>
        <h1>Solar flare risk, <span>in context.</span></h1>
        <p>Replay a forecast from archived magnetic observations, inspect what the model knew,
        and reveal what happened during the following 24 hours.</p>
    </section>
    ''',
    unsafe_allow_html=True,
)

output = ROOT / 'artifacts'
required = ['report.json', 'predictions.parquet', 'calibration.csv']
if not all((output / name).exists() for name in required):
    st.info('No evaluated model artifacts were found. Run the real-data notebook first.')
    st.code('.venv/bin/python scripts/run_notebook.py', language='bash')
    st.caption('If the data is not available yet, run: python scripts/download.py')
    st.stop()


@st.cache_data
def load_results(version):
    report = json.loads((output / 'report.json').read_text())
    predictions = pd.read_parquet(output / 'predictions.parquet')
    calibration = pd.read_csv(output / 'calibration.csv')
    return report, predictions, calibration


report, predictions, calibration = load_results((output / 'report.json').stat().st_mtime_ns)
chosen = report['selection']['model']
threshold = report['selection']['threshold']
fractions = report.get('sample_fractions', {})
sample_description = (
    ', '.join(f'Partition {part}: {100*fraction:g}%' for part, fraction in fractions.items())
    or 'Sample fractions are not recorded in this report'
)
names = {'baseline': 'Constant baseline', 'logistic': 'Logistic regression', 'xgboost': 'XGBoost'}
test = predictions[(predictions.model == chosen) & (predictions.split == 'test')].copy()
model_name = names.get(chosen, chosen.replace('_', ' ').title())

st.markdown(
    f'''
    <div class="run-strip">
        <div><span>Selected model</span><strong>{model_name}</strong></div>
        <div><span>Fixed alarm threshold</span><strong>{100*threshold:.2f}%</strong></div>
        <div><span>Evaluation mode</span><strong>Held-out historical data</strong></div>
    </div>
    ''',
    unsafe_allow_html=True,
)

replay_tab, performance_tab, data_tab = st.tabs(
    ['Historical replay', 'Model evaluation', 'Data & method']
)

with replay_tab:
    st.subheader('Replay a forecast window')
    st.caption(
        'Choose a region and time from the held-out test partition. '
        'Every timestamp is shown in UTC.'
    )
    with st.container(border=True):
        region_col, date_col, time_col = st.columns([1, 1.35, 1.35], gap='large')
        with region_col:
            region = st.selectbox(
                'Active region',
                sorted(test.harp.unique()),
                format_func=lambda value: f'HARP {value}',
            )
        available = test[test.harp.eq(region)].sort_values('forecast_time')
        with date_col:
            day = st.selectbox(
                'Forecast date · UTC',
                sorted(available.forecast_time.dt.date.unique()),
            )
        windows = available[available.forecast_time.dt.date.eq(day)]
        with time_col:
            stamp = st.select_slider(
                'Forecast time · UTC',
                options=windows.forecast_time.tolist(),
                format_func=lambda value: value.strftime('%H:%M'),
            )
    row = windows[windows.forecast_time.eq(stamp)].iloc[0]
    st.markdown(
        f'<div class="window-context"><b>HARP {int(row.harp)}</b> &nbsp;·&nbsp; '
        f'{row.forecast_time:%d %b %Y, %H:%M} UTC &nbsp;·&nbsp; '
        f'Observation completeness {100*(1-row.missing_fraction):.1f}%</div>',
        unsafe_allow_html=True,
    )

    probability_text = '<0.1%' if row.probability < 0.001 else f'{100*row.probability:.1f}%'
    c1, c2, c3 = st.columns([1.3, 1, 1], gap='medium')
    c1.metric('M/X probability', probability_text)
    c2.metric('Alarm threshold', f'{100*threshold:.2f}%')
    c3.metric('Forecast horizon', '24 hours')
    if row.probability >= threshold:
        st.warning(
            'Above threshold — the model raises an M/X-class flare alarm for this window.'
        )
    else:
        st.info(
            'Below threshold — the model does not raise an alarm. '
            'This is not a guarantee that no flare occurred.'
        )

    chart_col, outcome_col = st.columns([1.75, 1], gap='large')
    with chart_col:
        st.markdown('<div class="section-label">Previous 12 hours</div>', unsafe_allow_html=True)
        measurement = st.selectbox(
            'SHARP magnetic parameter',
            MAGNETIC_COLUMNS,
            index=MAGNETIC_COLUMNS.index('USFLUX'),
        )
        path = ROOT / row.file
        if path.exists():
            observation = read_observation(path)
            series = trusted_measurements(observation)[measurement]
            with plt.style.context('dark_background'):
                fig, ax = plt.subplots(figsize=(8.4, 3.15))
                fig.patch.set_alpha(0)
                ax.set_facecolor('#0a151e')
                ax.plot(
                    observation['Timestamp'],
                    series,
                    color='#ffb45e',
                    linewidth=2,
                )
                ax.fill_between(
                    observation['Timestamp'],
                    series.to_numpy(),
                    color='#ffb45e',
                    alpha=.08,
                )
                ax.grid(axis='y', color='#304251', alpha=.34, linewidth=.7)
                ax.tick_params(colors='#8093a2', labelsize=8)
                for spine in ax.spines.values():
                    spine.set_visible(False)
                ax.margins(x=.01)
                ax.set_xlabel('Observation time · UTC', color='#8093a2', fontsize=8)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            st.caption(
                f'Observation window: {row.observation_start:%d %b %Y, %H:%M}–'
                f'{row.forecast_time:%d %b %Y, %H:%M} UTC (end exclusive). '
                f'Last sample: {row.observation_last:%H:%M}. '
                'Gaps indicate missing or untrusted measurements.'
            )
        else:
            st.warning(
                'The raw observation file is not available locally. '
                'Run the data download step again.'
            )

    with outcome_col:
        st.markdown('<div class="section-label">Recorded outcome</div>', unsafe_allow_html=True)
        st.caption(
            f'Outcome window: {row.forecast_time:%d %b %Y, %H:%M}–'
            f'{row.prediction_end:%d %b %Y, %H:%M} UTC (end exclusive).'
        )
        if st.toggle('Reveal recorded outcome', value=False, key=f'outcome_{region}_{stamp.isoformat()}'):
            if row.target:
                st.error(f'M/X-class flare recorded · {row.label.split("@")[0]}')
            else:
                detail = (
                    'quiet window in the dataset'
                    if row.label == 'FQ'
                    else f'strongest record: {row.label.split("@")[0]}'
                )
                st.success(f'No M/X-class flare recorded · {detail}')
            if pd.notna(row.peak_time):
                st.caption(f'Catalog peak time: {row.peak_time:%d %b %Y, %H:%M} UTC')
            alarm = row.probability >= threshold
            outcome = (
                ('Hit' if row.target else 'False alarm')
                if alarm
                else ('Miss' if row.target else 'Correct quiet forecast')
            )
            st.markdown(f'**Window outcome:** {outcome}')
            st.caption('Outcome labels remain separate from every model feature.')
        else:
            st.markdown(
                '<div class="placeholder">Outcome hidden to preserve the replay.<br>'
                'Reveal it when you are ready to compare forecast and reality.</div>',
                unsafe_allow_html=True,
            )

with performance_tab:
    st.subheader('Held-out model performance')
    st.caption(
        f'{model_name} and its alarm threshold were selected on validation data '
        'before the test split was evaluated.'
    )
    results = pd.DataFrame(report['metrics'])
    selected = results[(results.model == chosen) & (results.split == 'test')].iloc[0]
    a, b, c, d = st.columns(4, gap='medium')
    a.metric('Recall', f'{100*selected.recall:.1f}%')
    b.metric('Precision', f'{100*selected.precision:.1f}%')
    c.metric('False alarms', str(int(selected.fp)))
    d.metric('Missed positive windows', str(int(selected.fn)))
    st.caption(
        f'{int(selected.n):,} test windows · {int(selected.positives)} positive windows. '
        'These are forecast windows, not counts of unique flare events.'
    )

    st.markdown(
        '<div class="section-label">Same test split, three models</div>',
        unsafe_allow_html=True,
    )
    summary = results[results.split.eq('test')][
        [
            'model',
            'recall',
            'precision',
            'fp',
            'fn',
            'average_precision',
            'brier',
            'tss',
        ]
    ].copy()
    summary['model'] = summary.model.map(names)
    summary = summary.rename(
        columns={
            'model': 'Model',
            'recall': 'Recall',
            'precision': 'Precision',
            'fp': 'False alarms',
            'fn': 'Misses',
            'average_precision': 'Avg precision',
            'brier': 'Brier',
            'tss': 'TSS',
        }
    )
    for column in ['Recall', 'Precision', 'Avg precision', 'Brier', 'TSS']:
        summary[column] = summary[column].map(lambda value: f'{value:.3f}')
    st.dataframe(summary, hide_index=True, width='stretch')
    st.caption(
        'Brier is better when lower. Average precision measures ranking quality under '
        'class imbalance. Model selection used validation average precision.'
    )

    st.markdown(
        '<div class="section-label">Probability calibration</div>',
        unsafe_allow_html=True,
    )
    selected_calibration = calibration[(calibration.model == chosen) & (calibration.split == 'test')]
    with plt.style.context('dark_background'):
        fig, ax = plt.subplots(figsize=(8.6, 3.35))
        fig.patch.set_alpha(0)
        ax.set_facecolor('#0a151e')
        ax.plot([0, 1], [0, 1], '--', color='#657b8b', linewidth=1, label='Ideal')
        ax.plot(
            selected_calibration.mean_probability,
            selected_calibration.observed_rate,
            'o-',
            color='#ffb45e',
            linewidth=2,
            markersize=5,
            label=model_name,
        )
        ax.set(
            xlabel='Mean predicted probability',
            ylabel='Observed event rate',
            xlim=(0, 1),
            ylim=(0, 1),
        )
        ax.grid(color='#304251', alpha=.28, linewidth=.7)
        ax.tick_params(colors='#8093a2', labelsize=8)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.legend(frameon=False, fontsize=8)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with st.expander('Calibration bins and sample counts'):
        st.dataframe(
            selected_calibration[
                ['bin', 'count', 'mean_probability', 'observed_rate']
            ],
            hide_index=True,
            width='stretch',
        )

    st.markdown(
        '<div class="section-label">Explore the operating threshold</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.caption(
            'Validation data only. This control never changes the saved model, '
            'the fixed threshold, or the test metrics above.'
        )
        experimental = st.slider(
            'Experimental alarm threshold (%)',
            0.0,
            100.0,
            float(threshold*100),
            step=0.01,
        )
        validation = predictions[
            (predictions.model == chosen) & predictions.split.eq('validation')
        ]
        tradeoff = metrics(validation.target, validation.probability, experimental/100)
        a, b, c = st.columns(3, gap='medium')
        a.metric('Validation recall', f'{100*tradeoff["recall"]:.1f}%')
        b.metric('Validation precision', f'{100*tradeoff["precision"]:.1f}%')
        c.metric('Validation false alarms', tradeoff['fp'])
        st.caption(
            'False-positive rate is FP/(FP+TN); false-alarm ratio is FP/(TP+FP).'
        )

with data_tab:
    st.subheader('Data provenance and evaluation design')
    st.caption(
        'The dashboard exposes the experiment as it was run, including its boundaries.'
    )

    source_col, feature_col, target_col = st.columns(3, gap='medium')
    with source_col:
        st.markdown(
            '''
            <div class="method-card"><span>01 / SOURCE</span>
            <h4>SWAN-SF archive</h4>
            <p>Historical active-region windows from Harvard Dataverse.
            No live feed or synthetic forecast records.</p></div>
            ''',
            unsafe_allow_html=True,
        )
    with feature_col:
        st.markdown(
            '''
            <div class="method-card"><span>02 / INPUT</span>
            <h4>12 hours of magnetics</h4>
            <p>Twenty-four SHARP parameters become 96 observation-only summary features.
            Outcome fields are excluded.</p></div>
            ''',
            unsafe_allow_html=True,
        )
    with target_col:
        st.markdown(
            '''
            <div class="method-card"><span>03 / TARGET</span>
            <h4>M/X within 24 hours</h4>
            <p>M- and X-class windows are positive. C, B, and flare-quiet windows
            remain in the negative class.</p></div>
            ''',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">Experiment splits</div>', unsafe_allow_html=True)
    splits = pd.DataFrame(report['splits']).T.reset_index(names='Split')
    splits = splits.rename(
        columns={
            'n': 'Windows',
            'positives': 'Positive windows',
            'harps': 'HARPs',
            'start': 'Start',
            'end': 'End',
        }
    )
    splits['Split'] = splits['Split'].str.title()
    st.dataframe(splits, hide_index=True, width='stretch')

    st.markdown(
        '''
        - **Separation:** partition 1 for training, 3 for validation, and 5 for test;
          overlapping boundaries and shared HARP identities are removed.
        - **Sampling:** records are selected without using the target label.
        - **Probabilities:** displayed values are raw model outputs; no additional
          probability-calibration model is fitted.
        - **Availability:** the replay does not claim that finalized archive SHARP
          measurements were available in real time.
        '''
    )
    st.caption(sample_description)
    st.info(
        'A HARP may contain more than one NOAA active region. Windows within a '
        'partition can overlap, so recall is not a unique-event detection rate.'
    )
    st.markdown(
        f'<div class="fine-print">RUN DIGEST {report["input_sha256"][:16]} &nbsp;·&nbsp; '
        f'SCIKIT-LEARN {report["versions"]["sklearn"]} &nbsp;·&nbsp; '
        'Flare probability is not a satellite-damage or Earth-impact probability.</div>',
        unsafe_allow_html=True,
    )
