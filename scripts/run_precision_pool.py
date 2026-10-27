"""Select a bounded probability pool on calibration; assess one validation candidate."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import pandas as pd
from helio24.calibration import SigmoidCalibration, recall_threshold, cluster_intervals
from helio24.data import ROOT, FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.metric_summary import enrich
from helio24.modeling import metrics
from helio24.probability_pool import probability_pool
from helio24.v2_training import load_development, METADATA


def run(output):
    protocol_path = ROOT / 'config/precision-pool-v1.json'
    protocol = json.loads(protocol_path.read_text())
    if output.exists():
        raise ValueError('Preserve frozen output')
    base = ROOT / 'artifacts/experiment5_v2_development_20261026_r2'
    if sha256(base / 'report.json') != protocol['incumbent_report_sha256']:
        raise ValueError('Incumbent changed')
    original = json.loads((base / 'report.json').read_text())
    models = {}
    for name in ['logistic', 'xgboost']:
        if sha256(base / f'{name}.joblib') != original['artifact_hashes'][f'{name}.joblib']:
            raise ValueError('Model changed')
        models[name] = joblib.load(base / f'{name}.joblib')
    groups, _ = load_development(ROOT / 'artifacts/v2_development_features_20261025_r2',
                                 protocol['materialization_report_sha256'])
    output.mkdir(parents=True)
    def base_predictions(role):
        X = groups[role][FEATURE_COLUMNS].to_numpy(dtype='float32')
        return [models[name]['calibrator'].transform(models[name]['model'].predict_proba(X)[:, 1])
                for name in ['logistic', 'xgboost']]
    def score(role, p):
        y = groups[role].target
        return enrich(metrics(y, p, recall_threshold(y, p, .95)))
    left, right = base_predictions('calibration')
    candidates, calibration = [], {}
    for power in protocol['powers']:
        for weight in protocol['weights']:
            p = probability_pool(left, right, weight, power)
            # Calibrate each pool monotonically on calibration before comparing probability errors.
            calibrator = SigmoidCalibration().fit(p, groups['calibration'].target)
            calibrated = calibrator.transform(p)
            key = f'power{power}_w{weight:g}'
            candidates.append({'candidate': key, 'power': power, 'weight': weight,
                               **score('calibration', calibrated)})
            calibration[key] = calibrator
    candidates.append({'candidate': 'incumbent', 'power': 1, 'weight': .45,
                       **score('calibration', .45*left+.55*right)})
    winner = sorted(candidates,key=lambda row: (-row['precision'], -row['average_precision'],row['candidate']))[0]
    pd.DataFrame(candidates).to_csv(output / 'calibration_candidates.csv', index=False)
    (output / 'calibration_selection.json').write_text(json.dumps(winner,indent=2)+'\n')
    left,right = base_predictions('validation')
    incumbent = .45*left+.55*right
    selected = incumbent if winner['candidate']=='incumbent' else calibration[winner['candidate']].transform(
        probability_pool(left,right,winner['weight'],winner['power']))
    results = {name:score('validation',p) for name,p in [('incumbent',incumbent),('selected',selected)]}
    old,new = results['incumbent'],results['selected']
    promote = (new['precision']>old['precision'] and new['recall']>=.95 and new['average_precision']>=old['average_precision']
               and new['brier']<=old['brier'] and new['log_loss']<=old['log_loss'])
    frame = groups['validation'][METADATA].copy()
    frame['incumbent'],frame['selected'] = incumbent,selected
    frame.to_parquet(output / 'validation_predictions.parquet',index=False)
    intervals={name:cluster_intervals(groups['validation'].target,p,groups['validation'].harp,results[name]['threshold'])
               for name,p in [('incumbent',incumbent),('selected',selected)]}
    report={'winner':winner,'metrics':results,'promote':bool(promote),'conditional_cluster_intervals':intervals,
            'reserved_test_accessed':False,'protocol':protocol,'protocol_sha256':sha256(protocol_path),
            'code_hashes':{name:sha256(ROOT/name) for name in ['helio24/probability_pool.py','scripts/run_precision_pool.py']}}
    joblib.dump({'models':models,'winner':winner,'calibrator':calibration.get(winner['candidate']),
                 'threshold':new['threshold']},output/'candidate.joblib')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
