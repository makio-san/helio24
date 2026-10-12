"""Render an exportable, standalone scientific report from experiment 2 outputs."""
import base64
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def render():
    directory = ROOT / 'artifacts/experiment2'
    report = json.loads((directory / 'report.json').read_text())
    metrics = pd.read_csv(directory / 'metrics.csv')
    intervals = pd.read_csv(directory / 'cluster_intervals.csv')
    calibration = pd.read_csv(directory / 'calibration.csv')
    colors = {'original_sample': '#848c96', 'full_raw': '#e57c31', 'full_calibrated': '#246e9e', 'baseline': '#589376'}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for split, ax in zip(['validation', 'audit'], axes):
        ax.plot([0, 1], [0, 1], '--', color='gray', linewidth=1)
        for name in ['full_raw', 'full_calibrated']:
            group = calibration[(calibration.model == name) & (calibration.split == split)]
            ax.plot(group.mean_probability, group.observed_rate, 'o-', label=name, color=colors[name])
        ax.set(title=split.title(), xlabel='Mean predicted probability', ylabel='Observed event rate', xlim=(0, 1), ylim=(0, 1))
        ax.legend(); ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(directory / 'reliability.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for split, ax in zip(['validation', 'audit'], axes):
        for name in ['original_sample', 'full_raw', 'full_calibrated']:
            group = metrics[(metrics.model == name) & (metrics.split == split)].sort_values('recall_target')
            ax.plot(group.fp, group.recall, 'o-', label=name, color=colors[name])
            for _, row in group.iterrows():
                if name != 'full_calibrated':
                    ax.annotate(f'{row.recall_target:.0%}', (row.fp, row.recall),
                                xytext=(0, -14 if name == 'original_sample' else 7),
                                textcoords='offset points', fontsize=7, ha='center')
        ax.set(title=split.title(), xlabel='False-alarm windows', ylabel='Achieved recall', ylim=(0, 1))
        ax.legend(); ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(directory / 'alarm_tradeoffs.png', dpi=160)
    plt.close(fig)
    def image(name):
        encoded = base64.b64encode((directory / name).read_bytes()).decode()
        return f'<img alt="{name}" src="data:image/png;base64,{encoded}">'
    def table(frame):
        return frame.to_html(index=False, float_format=lambda x: f'{x:.5f}', escape=True)
    roles = pd.DataFrame(report['roles']).T.reset_index(names='role')
    columns = ['model', 'split', 'recall_target', 'threshold', 'recall', 'precision', 'fp', 'fn', 'false_positive_rate', 'brier', 'log_loss']
    counts = []
    for audit in report['archive_sources']:
        counts.append(dict(partition=audit['partition'], inspected=audit['inspected'], retained=audit['accepted'], excluded=audit['excluded'],
                           positive_before=sum(audit['full_class_counts'].get(c, 0) for c in ['M', 'X']),
                           positive_after=sum(audit['retained_class_counts'].get(c, 0) for c in ['M', 'X'])))
    paired = report['paired_brier_difference']
    content = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Helio24 — Experiment 2</title>
    <style>body{{font:16px/1.6 system-ui;margin:48px auto;max-width:1180px;padding:0 24px;color:#162431}}h1,h2{{line-height:1.2}}img{{max-width:100%}}table{{border-collapse:collapse;font-size:12px;width:100%;margin:20px 0}}td,th{{padding:7px;border-bottom:1px solid #dce3e9;text-align:left}}.note{{padding:20px;background:#fff1dc;border-left:4px solid #d78828}}.table{{overflow:auto}}@media print{{body{{margin:12px}}}}</style>
    <h1>Helio24 · Full-data calibration audit</h1>
    <p class="note">Retrospective audit, not an untouched final test. Partition 5 was inspected in experiment 1.
    Models and thresholds were frozen before this audit; the original dashboard model remains unchanged.</p>
    <h2>Coverage and chronological roles</h2>{table(pd.DataFrame(counts))}{table(roles)}
    <h2>Probability quality</h2><p>Validation preference: <b>{html.escape(report['protocol']['selected_probability'])}</b>.
    This choice uses partition 4 Brier only. Brier also depends on discrimination and prevalence; inspect the reliability bins below.</p>
    {image('reliability.png')}
    <p>Paired calibrated-minus-raw audit Brier difference: <b>{paired['estimate']:.6f}</b>;
    95% HARP-cluster interval [{paired['lower']:.6f}, {paired['upper']:.6f}]. Negative favors calibration.</p>
    <h2>Recall and false alarms</h2><p>Targets are selected on validation. Audit recall may miss its target.
    Monotonic calibration preserves rankings, so raw and calibrated operating curves may overlap.</p>
    {image('alarm_tradeoffs.png')}<div class="table">{table(metrics[columns])}</div>
    <h2>Cluster uncertainty</h2><p>1,000 draws, seed 24; whole HARP regions are resampled with all their windows.
    These conditional intervals exclude model-fitting and calibration-fitting uncertainty, cross-region dependence, and future-cycle shift.</p>
    <div class="table">{table(intervals)}</div>
    <h2>Reliability bins and counts</h2><div class="table">{table(calibration)}</div>
    <h2>Limits</h2><p>Counts represent forecast windows, not unique flare events. Full-data training changes both sample size
    and training-period coverage relative to experiment 1; this comparison cannot isolate the effect of sample size alone.
    No satellite-damage, Earth-impact, or live-availability prediction is made. The audit is not used to retune thresholds.</p>
    <p>Protocol SHA-256: {report['protocol']['protocol_sha256']}</p></html>'''
    (directory / 'report.html').write_text(content)
    print(directory / 'report.html')


if __name__ == '__main__':
    render()
