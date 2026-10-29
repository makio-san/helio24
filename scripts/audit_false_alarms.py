"""Compare frozen annual false alarms with exposure-aware regional diagnostics."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256


def summarize(frame, year):
    d = frame.sort_values(['harp','forecast_time']).copy()
    d['negative'] = d.target.eq(0)
    d['fp'] = d.negative & d.ensemble_alarm
    d['tp'] = ~d.negative & d.ensemble_alarm
    regions = d.groupby('harp').agg(rows=('target','size'), positives=('target','sum'),
        negatives=('negative','sum'), fp=('fp','sum'), tp=('tp','sum'),
        mean_missing=('missing_fraction','mean')).reset_index()
    regions['fpr'] = regions.fp/regions.negatives.replace(0,np.nan)
    regions['year'] = year
    regions = regions.sort_values(['fp','harp'],ascending=[False,True])
    nneg, nfp = int(d.negative.sum()), int(d.fp.sum())
    top = regions.head(10)
    # Exact one-hour adjacency; excluded/missing windows always break a run.
    contiguous = d.harp.eq(d.harp.shift()) & d.forecast_time.diff().eq(pd.Timedelta(hours=1))
    run = (~(contiguous & d.fp & d.fp.shift(fill_value=False))).cumsum()
    runs = d[d.fp].groupby(run[d.fp]).agg(harp=('harp','first'),
        start=('forecast_time','min'), end=('forecast_time','max'), windows=('fp','size'))
    runs['year'] = year
    summary = {'year':year,'rows':len(d),'negatives':nneg,'fp':nfp,
        'fpr':nfp/nneg if nneg else None,'top10_fp':int(top.fp.sum()),
        'top10_fp_share':float(top.fp.sum()/nfp) if nfp else None,
        'top10_negative_share':float(top.negatives.sum()/nneg) if nneg else None,
        'zero_positive_region_fp':int(regions.loc[regions.positives.eq(0),'fp'].sum()),
        'complete_measurement_fp':int(d.loc[d.missing_fraction.eq(0),'fp'].sum()),
        'both_models_alarm_fp':int((d.fp & d.logistic_alarm & d.xgboost_alarm).sum()),
        'fp_windows_in_runs_ge6':int(runs.loc[runs.windows.ge(6),'windows'].sum()),
        'max_fp_run_windows':int(runs.windows.max()) if len(runs) else 0}
    bins = pd.cut(d.missing_fraction,[-1e-12,0,.01,.05,1],
                  labels=['zero','(0,0.01]','(0.01,0.05]','(0.05,1]'])
    d['missing_bin'] = bins
    missing = d.groupby('missing_bin',observed=False).agg(rows=('target','size'),
        negatives=('negative','sum'),fp=('fp','sum'),positives=('target','sum')).reset_index()
    missing['fpr'] = missing.fp/missing.negatives.replace(0,np.nan)
    missing['year'] = year
    return summary, regions, missing, runs.reset_index(drop=True)


def run(source, output):
    if output.exists():
        raise ValueError('Preserve existing audit')
    report = json.loads((source/'report.json').read_text())
    for relative,digest in report['artifact_hashes'].items():
        if sha256(source/relative) != digest:
            raise ValueError(f'Frozen evidence changed: {relative}')
    output.mkdir(parents=True)
    summaries, regions, missing, runs = [], [], [], []
    for fold in report['folds']:
        if fold['status'] != 'complete':
            continue
        year=fold['year'];d=pd.read_parquet(source/str(year)/'predictions.parquet')
        thresholds=json.loads((source/str(year)/'thresholds.json').read_text())
        for model in ['ensemble','logistic','xgboost']:
            if not d[f'{model}_alarm'].eq(d[model].ge(thresholds[model])).all():
                raise ValueError('Alarm policy differs from frozen threshold')
        summary, region, quality, streak = summarize(d,year)
        expected=next(m for m in report['metrics'] if m['year']==year and m['model']=='ensemble')
        if summary['fp']!=expected['fp'] or summary['rows']!=expected['n']:
            raise ValueError('Confusion counts do not reproduce')
        summaries.append(summary);regions.append(region);missing.append(quality);runs.append(streak)
    for name,df in [('summary',pd.DataFrame(summaries)),('regions',pd.concat(regions)),
                    ('missing_bins',pd.concat(missing)),('fp_runs',pd.concat(runs))]:
        df.to_csv(output/f'{name}.csv',index=False)
    result={'source':str(source.relative_to(ROOT)),'source_sha256':sha256(source/'report.json'),
        'code_sha256':sha256(Path(__file__)), 'summaries':summaries,
        'reserved_test_accessed':False,
        'scope':'Post-hoc development error audit; no new training, relabeling or exclusions',
        'artifact_hashes':{p.name:sha256(p) for p in sorted(output.glob('*.csv'))}}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'artifacts/walk_forward_20261028_r1')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.source.resolve(),args.output.resolve())
