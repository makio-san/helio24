"""Read the pinned final development comparison without training or tuning."""
import hashlib
import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st


def verified_bytes(path, expected):
    if path.stat().st_flags & 0x40000000:
        raise ValueError('Comparison file is not downloaded locally')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Comparison evidence failed its hash check')
    return data


def load_comparison(root):
    root = Path(root)
    config = json.loads((root/'config/dashboard-comparison-v1.json').read_text())
    folder = (root/config['source']).resolve()
    if not folder.is_relative_to(root.resolve()):
        raise ValueError('Invalid comparison source')
    report = json.loads(verified_bytes(folder/'report.json', config['report_sha256']))
    if report['status'] != 'final_complete' or report['missing_eligible_years']:
        raise ValueError('Final annual comparison is incomplete')
    tables = {name:pd.read_csv(io.BytesIO(verified_bytes(folder/name, report['artifact_hashes'][name])))
              for name in ['metrics.csv', 'comparisons.csv']}
    return report, tables


def render_final_comparison(root):
    st.subheader('Final annual comparison')
    try:
        report, tables = load_comparison(root)
    except (OSError, ValueError, KeyError) as error:
        st.info(f'Verified final comparison unavailable: {error}')
        return
    gate = tables['comparisons.csv'].query("candidate == 'chronological' and control == 'baseline'").iloc[0]
    cols = st.columns(3)
    cols[0].metric('Evaluated years', str(len(report['selected_years'])))
    cols[1].metric('Years with higher precision', f"{int(gate.precision_win_count)} / {int(gate.required_positive_years)}")
    cols[2].metric('Years passing all criteria', f"{int(gate.full_met_count)} / {int(gate.required_positive_years)}")
    st.warning('The TCN did not meet the multi-year acceptance criteria. No model was promoted.')
    st.caption('Retrospective development results; 2024–2025 reserved test remains closed. '
               'Thresholds came from the preceding calibration year. Counts are forecast windows, not distinct flares.')
    metrics = tables['metrics.csv']
    year = st.selectbox('Comparison year', report['selected_years'], key='final_comparison_year')
    arms = ['baseline', 'short_training', 'chronological', 'shuffled_interior']
    selected = metrics[metrics.year.eq(year) & metrics.arm.isin(arms)]
    st.dataframe(selected[['arm', 'precision', 'recall', 'fp', 'tp', 'fn', 'accuracy',
                           'average_precision', 'brier', 'log_loss']], hide_index=True, width='stretch')
    if selected.positives.eq(0).all():
        st.info('This year contains no positive windows. Recall and average precision are undefined; false alarms remain measurable.')
    st.caption('Precision: correct alarms / all alarms. Recall: detected positive windows / all positive windows. '
               'FP: false alarms. Accuracy: correct predictions / all windows. '
               'Average precision measures ranking; Brier and log loss measure probability error (lower is better).')
    chart = metrics[metrics.arm.isin(['baseline', 'chronological'])].pivot(index='year', columns='arm', values='precision')
    st.line_chart(chart, y_label='Precision (0–1)')
    with st.expander('Acceptance criteria and full comparison'):
        st.write('Each positive year requires higher precision, recall ≥ 0.95 and fewer false alarms. '
                 'Full acceptance also requires no worse average precision, Brier or log loss. '
                 'These are project criteria, not universal metric ranges.')
        st.dataframe(tables['comparisons.csv'], hide_index=True, width='stretch')
        st.download_button('Download all annual metrics', tables['metrics.csv'].to_csv(index=False),
                           'helio24-final-annual-metrics.csv', 'text/csv')
    for language, suffix in [('English', ''), ('Türkçe', '.tr')]:
        path = Path(root)/f'docs/temporal-evaluation-final-20261106{suffix}.md'
        if path.exists():
            st.download_button(f'{language} report', path.read_text(), path.name, 'text/markdown')
