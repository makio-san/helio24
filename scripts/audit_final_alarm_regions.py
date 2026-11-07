"""Localize frozen TCN false alarms across all completed annual periods."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(frame, thresholds):
    if frame.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate forecast key')
    if not frame.target.isin([0, 1]).all():
        raise ValueError('Nonbinary target')
    a = frame.chronological.ge(thresholds['chronological'])
    b = frame.baseline.ge(thresholds['baseline'])
    neg = frame.target.eq(0)
    flags = frame[['harp', 'target']].assign(negative=neg, extra_fp=a & ~b & neg,
        removed_fp=b & ~a & neg, shared_fp=a & b & neg,
        extra_tp=a & ~b & ~neg, removed_tp=b & ~a & ~neg,
        candidate_fp=a & neg, baseline_fp=b & neg)
    regions = flags.groupby('harp', sort=True).sum().reset_index()
    top = regions.sort_values(['extra_fp', 'harp'], ascending=[False, True]).head(10)
    total = int(regions.extra_fp.sum())
    negatives = int(neg.sum())
    summary = {key:int(regions[key].sum()) for key in ['extra_fp', 'removed_fp', 'shared_fp',
        'extra_tp', 'removed_tp', 'candidate_fp', 'baseline_fp']}
    summary.update(positives=int(frame.target.sum()), negatives=negatives,
        top10_extra_fp=int(top.extra_fp.sum()),
        top10_extra_fp_share=float(top.extra_fp.sum()/total) if total else None,
        top10_negative_share=float(top.negative.sum()/negatives) if negatives else None,
        zero_positive_region_extra_fp=int(regions.loc[regions.target.eq(0), 'extra_fp'].sum()))
    if summary['extra_fp']-summary['removed_fp'] != summary['candidate_fp']-summary['baseline_fp']:
        raise ValueError('Paired alarm accounting failed')
    return summary, regions


def run(source, expected, output):
    if output.exists():
        raise FileExistsError(output)
    if sha(source/'report.json') != expected:
        raise ValueError('Final experiment manifest changed')
    report = json.loads((source/'report.json').read_text())
    years = [year for year in report['protocol']['evaluation_years'] if f'{year}/finished.json' in report['artifact_hashes']]
    rows, region_tables = [], []
    for year in years:
        for name in ['predictions.parquet', 'thresholds.json', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        frame = pd.read_parquet(source/str(year)/'predictions.parquet')
        thresholds = json.loads((source/str(year)/'thresholds.json').read_text())
        summary, regions = summarize(frame, thresholds)
        rows.append({'year':year, **summary})
        region_tables.append(regions.assign(year=year))
    output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(output/'summary.csv', index=False)
    pd.concat(region_tables, ignore_index=True).to_csv(output/'regions.csv', index=False)
    result = {'source_report_sha256':expected, 'years':years, 'summary':rows,
        'scope':'Post-hoc localization of overlapping forecast windows; not event counts or causal predictors.',
        'reserved_test_accessed':False, 'model_promoted':False,
        'artifact_hashes':{p.name:sha(p) for p in output.iterdir()}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.source, args.source_sha256, args.output)
    print(pd.DataFrame(result['summary']).to_string(index=False))
