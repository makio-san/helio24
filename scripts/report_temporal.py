"""Render a standalone local report for experiment 3."""
import base64
from io import BytesIO
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from helio24.data import ROOT


def figure_data(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight')
    memory = BytesIO()
    fig.savefig(memory, format='png', dpi=160, bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(memory.getvalue()).decode()


def render():
    output = ROOT / 'artifacts/experiment3'
    report = json.loads((output / 'report.json').read_text())
    metrics = pd.read_csv(output / 'development_metrics.csv')
    retrospective = pd.read_csv(output / 'retrospective_metrics.csv')
    quarter = pd.read_csv(output / 'error_by_quarter.csv')
    missingness = pd.read_csv(output / 'error_by_missingness.csv')
    at_90 = metrics[np.isclose(metrics.recall_target, .9)].copy()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    x = np.arange(3)
    width = .36
    for offset, model, color in [(-width/2, 'control', '#74a9cf'), (width/2, 'temporal', '#fdae6b')]:
        group = at_90[at_90.model.eq(model)].set_index('fold').loc[['A', 'B', 'C']]
        axes[0].bar(x+offset, group.fp, width, label=model.title(), color=color)
        axes[1].bar(x+offset, group.average_precision, width, label=model.title(), color=color)
    axes[0].set(title='False alarms at 90% empirical recall', ylabel='False-alarm windows', xticks=x, xticklabels=['A', 'B', 'C'])
    axes[1].set(title='Average precision', ylabel='Average precision', xticks=x, xticklabels=['A', 'B', 'C'], ylim=(0, .6))
    for axis in axes:
        axis.spines[['top', 'right']].set_visible(False)
        axis.legend(frameon=False)
    comparison_image = figure_data(fig, output / 'development_comparison.png')

    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(quarter))
    ax.plot(x, quarter.miss_rate*100, marker='o', label='Miss rate among positives', color='#d95f0e')
    ax.plot(x, quarter.false_alarm_rate*100, marker='o', label='False-positive rate among negatives', color='#3182bd')
    ax.set(title='Experiment-2 validation errors by calendar quarter', ylabel='Rate (%)',
           xticks=x, xticklabels=quarter.quarter)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False)
    error_image = figure_data(fig, output / 'error_by_quarter.png')

    columns = ['fold', 'model', 'recall', 'precision', 'fp', 'fn', 'average_precision', 'brier']
    display = at_90[columns].copy()
    for column in ['recall', 'precision', 'average_precision', 'brier']:
        display[column] = display[column].map(lambda value: f'{value:.4f}')
    retro_display = retrospective[['model', 'threshold', 'recall', 'precision', 'fp', 'fn', 'average_precision', 'brier']].copy()
    for column in ['threshold', 'recall', 'precision', 'average_precision', 'brier']:
        retro_display[column] = retro_display[column].map(lambda value: f'{value:.4f}')
    missing_display = missingness.copy()
    missing_display['miss_rate'] = missing_display.miss_rate.map(lambda value: f'{value:.2%}')
    missing_display['false_alarm_rate'] = missing_display.false_alarm_rate.map(lambda value: f'{value:.2%}')
    decision = report['decision']
    error = report['error_audit']
    verdict = 'Candidate rejected by the fixed development rule' if not decision['promising'] else 'Candidate passed the fixed development rule'
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Helio24 experiment 3</title>
<style>
body{{font:15px/1.5 system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;color:#17202a;background:#fbfcfd}}
h1,h2{{color:#102a43}} .verdict{{padding:16px;border-left:5px solid #d95f0e;background:#fff3e8;font-weight:700}}
table{{border-collapse:collapse;width:100%;margin:12px 0 28px;background:white}} th,td{{border:1px solid #d9e2ec;padding:7px;text-align:right}} th:first-child,td:first-child{{text-align:left}}
img{{max-width:100%;background:white;border:1px solid #d9e2ec}} code{{background:#eef2f6;padding:2px 5px}} .note{{color:#52616b}}
</style></head><body>
<h1>Helio24 experiment 3: temporal discrimination</h1>
<p class="verdict">{verdict}.</p>
<p>The temporal model reduced pooled false alarms from {decision['pooled_control_false_alarms']:,} to {decision['pooled_temporal_false_alarms']:,} at the 90% development recall target, and won on false alarms in {decision['fewer_false_alarm_folds']} of 3 folds. Its average precision was no lower in {decision['nonlower_average_precision_folds']} of 3 folds, so it failed the preregistered rule.</p>
<img alt="Development model comparison" src="data:image/png;base64,{comparison_image}">
<h2>Walk-forward development results</h2>{display.to_html(index=False, border=0)}
<p class="note">Thresholds were selected within each development fold to compare ranking at matched empirical recall. They are not deployable operating thresholds.</p>
<h2>Existing-model error audit</h2>
<p>At the frozen experiment-2 validation threshold, {error['outcome_counts']['hit']:,} windows were hits, {error['outcome_counts']['miss']:,} were misses and {error['outcome_counts']['false_alarm']:,} were false alarms. The ten regions with the most errors contained {error['top_10_region_error_share']:.1%} of all misses and false alarms.</p>
<img alt="Errors by quarter" src="data:image/png;base64,{error_image}">
{missing_display.to_html(index=False, border=0)}
<h2>Previously inspected stability period</h2>{retro_display.to_html(index=False, border=0)}
<p class="note">Partition 5 was inspected in earlier experiments. These values are descriptive and did not select the features, models, thresholds or verdict. Because the fixed thresholds produce different recall, their false-alarm counts are not a matched-recall comparison.</p>
<h2>Scope</h2>
<p>Metrics count overlapping forecast windows, not unique flare events. The result evaluates a fixed concatenation of recent slopes, changes and change volatility; it does not rule out every temporal model. Generated models and data remain local and are excluded from Git.</p>
</body></html>'''
    (output / 'report.html').write_text(html)
    print(output / 'report.html')


if __name__ == '__main__':
    render()
