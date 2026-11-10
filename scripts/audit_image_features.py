"""Audit whether a CNN score of daily SHARP Br maps raises precision at the v2 operating point."""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from helio24.full_data import sha256
from helio24.modeling import metrics
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, sha
from scripts.audit_region_context_features import fit_candidate

KEY = ['harp', 'forecast_time']
RULES = {'lag24': 24, 'same': 0}
FOLDS = 3
SHAPE = (128, 256)


def columns(rule, image):
    names = [f'map_available_{rule}', f'map_age_hours_{rule}']
    return [*names, f'cnn_logit_{rule}'] if image else names


CANDIDATES = {f'{kind}_{rule}': columns(rule, kind == 'image') for rule in RULES for kind in ['flag', 'image']}
CONTEXT = [name for rule in RULES for name in columns(rule, True)]


def load_maps(directory, expected_sha):
    """Return the map table (sorted by time) and the image stack; maps without a valid pixel are dropped."""
    log = directory/'records.jsonl'
    if sha256(log) != expected_sha:
        raise ValueError('Map records changed')
    latest = {}
    for line in log.read_text().splitlines():
        item = json.loads(line)
        latest[(item['harp'], item['date'])] = item
    table = pd.DataFrame([item for item in latest.values() if item['status'] == 'ok'])
    table['t_rec'] = pd.to_datetime(table.date, utc=True).astype('datetime64[ns, UTC]')
    if table.t_rec.ge(pd.Timestamp('2024-01-01', tz='UTC')).any():
        raise ValueError('Reserved period map present')
    table = table.sort_values(['t_rec', 'harp']).reset_index(drop=True)
    images = np.stack([np.load(directory/path) for path in table.map])
    keep = np.abs(images).reshape(len(images), -1).max(axis=1) > 0
    table = table[keep].reset_index(drop=True)
    extra = np.column_stack([np.log(table.width/500), np.log(table.height/250), table.nan_fraction]).astype(np.float32)
    return table[['harp', 't_rec']], images[keep], extra, int((~keep).sum())


def map_labels(maps, windows):
    """1 if a positive window of the HARP has forecast time in [T_REC, T_REC+48h); NaN without any such window."""
    day = windows.forecast_time.dt.floor('D').astype('datetime64[ns, UTC]')
    long = pd.concat([pd.DataFrame({'harp': windows.harp.to_numpy(), 't_rec': (day-pd.Timedelta(days=shift)).to_numpy(),
                                    'target': windows.target.to_numpy()}) for shift in [0, 1]])
    long['t_rec'] = pd.to_datetime(long.t_rec, utc=True).astype('datetime64[ns, UTC]')
    label = long.groupby(['harp', 't_rec']).target.max().rename('label').reset_index()
    return maps.merge(label, on=['harp', 't_rec'], how='left').label.to_numpy(dtype=float)


def attach_maps(frame, maps, score):
    """Availability, age and CNN logit of the latest admissible map under each rule, in frame order."""
    left = pd.DataFrame({'harp': frame.harp.to_numpy(),
                         'forecast_time': frame.forecast_time.dt.tz_convert(None).to_numpy().astype('datetime64[ns]')})
    left['row'] = np.arange(len(left))
    right = pd.DataFrame({'harp': maps.harp.to_numpy(), 'map_time': maps.t_rec.dt.tz_convert(None).to_numpy().astype('datetime64[ns]'),
                          'cnn_logit': score}).sort_values('map_time')
    out = pd.DataFrame(index=np.arange(len(left)))
    for rule, lag in RULES.items():
        probe = left.assign(cutoff=left.forecast_time-pd.Timedelta(hours=lag)).sort_values('cutoff')
        merged = pd.merge_asof(probe, right, left_on='cutoff', right_on='map_time', by='harp',
                               tolerance=pd.Timedelta(hours=24)).sort_values('row')
        found = merged.map_time.notna().to_numpy()
        age = (merged.forecast_time-merged.map_time).dt.total_seconds().to_numpy()/3600
        out[f'map_available_{rule}'] = found.astype(float)
        out[f'map_age_hours_{rule}'] = np.where(found, age, np.nan)
        out[f'cnn_logit_{rule}'] = np.where(found, merged.cnn_logit.to_numpy(), np.nan)
    return out[CONTEXT]


def build_net(dropout):
    import torch
    from torch import nn

    class MapNet(nn.Module):
        def __init__(self):
            super().__init__()
            layers, channels = [], 1
            for width in (16, 32, 64, 128):
                layers += [nn.Conv2d(channels, width, 3, padding=1), nn.BatchNorm2d(width), nn.ReLU(), nn.MaxPool2d(2)]
                channels = width
            self.features = nn.Sequential(*layers)
            self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(2*channels+3, 1))

        def forward(self, image, extra):
            maps = self.features(image)
            return self.head(torch.cat([maps.mean((2, 3)), maps.amax((2, 3)), extra], 1))[:, 0]
    return MapNet()


def _batch(images, extra, index, device):
    import torch
    image = torch.from_numpy(np.clip(images[index].astype(np.float32)/500, -6, 6))[:, None].to(device)
    return image, torch.from_numpy(extra[index]).to(device)


def train_cnn(images, extra, labels, settings, seed, device):
    import torch
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = build_net(settings['dropout']).to(device)
    optimiser = torch.optim.Adam(model.parameters(), lr=settings['learning_rate'], weight_decay=settings['weight_decay'])
    loss_fn = torch.nn.BCEWithLogitsLoss()
    target = torch.from_numpy(labels.astype(np.float32))
    last = float('nan')
    for _ in range(settings['epochs']):
        model.train()
        order, total = rng.permutation(len(labels)), 0.0
        for start in range(0, len(order), settings['batch']):
            index = np.sort(order[start:start+settings['batch']])
            image, scalars = _batch(images, extra, index, device)
            flip = torch.from_numpy(rng.random(len(index)) < 0.5).to(device)
            image = torch.where(flip[:, None, None, None], image.flip(3), image)
            sign = torch.from_numpy(np.where(rng.random(len(index)) < 0.5, -1.0, 1.0).astype(np.float32)).to(device)
            loss = loss_fn(model(image*sign[:, None, None, None], scalars), target[index].to(device))
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            total += loss.item()*len(index)
        last = total/len(order)
    return model, last


def score_cnn(model, images, extra, index, device, batch=256):
    import torch
    model.eval()
    out = np.empty(len(index), dtype=np.float32)
    with torch.no_grad():
        for start in range(0, len(index), batch):
            part = index[start:start+batch]
            out[start:start+len(part)] = model(*_batch(images, extra, part, device)).cpu().numpy()
    return out


def stacked_scores(maps, images, extra, train, year, settings, device):
    """Out-of-fold logits for training-role HARPs, mean fold logit for every other HARP; maps before year+1 only."""
    labels = map_labels(maps, train)
    usable = np.flatnonzero(maps.t_rec.lt(pd.Timestamp(f'{year+1}-01-01', tz='UTC')).to_numpy())
    fold = maps.harp.to_numpy() % FOLDS
    scores, log = np.full((FOLDS, len(maps)), np.nan, dtype=np.float32), []
    for k in range(FOLDS):
        fit = np.flatnonzero(np.isfinite(labels) & (fold != k))
        model, loss = train_cnn(images[fit], extra[fit], labels[fit], settings, settings['seed']+year*10+k, device)
        scores[k, usable] = score_cnn(model, images, extra, usable, device)
        log.append({'year': year, 'fold': k, 'maps': len(fit), 'positive_maps': int(labels[fit].sum()), 'final_loss': loss})
        del model
    in_train = maps.harp.isin(set(train.harp)).to_numpy()
    final = np.where(in_train, scores[fold, np.arange(len(maps))], scores.mean(axis=0))
    return final, log


def pick_device():
    import torch
    return 'mps' if torch.backends.mps.is_available() else 'cpu'


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    walk_report = json.loads((Path(evidence['baseline_artifact'])/'report.json').read_text())
    control_thresholds = json.loads(Path(evidence['control_thresholds']).read_text())
    if sha(Path(evidence['control_thresholds'])) != evidence['control_thresholds_sha256']:
        raise ValueError('Control thresholds changed')
    target = config['recall_target']
    base = {**json.loads(Path(evidence['base_protocol']).read_text()), 'required_recall': target}
    maps, images, extra, empty_maps = load_maps(Path(evidence['maps_directory']), evidence['maps_records_sha256'])
    original, _ = load_development(Path(base['source']), evidence['frozen_shards_report_sha256'])
    development = pd.concat(original.values(), ignore_index=True)
    del original
    device = pick_device()
    output.mkdir(parents=True)
    thresholds, prepared, coverage, cnn_log = {}, {}, [], []
    for year in config['years']:
        groups, audit = annual_fold(development, year)
        if audit != next(f for f in walk_report['folds'] if f['year'] == year)['audit']:
            raise ValueError(f'Annual populations changed: {year}')
        groups['evaluation'] = groups['evaluation'].drop(columns=['target', 'label_status'])
        score, log = stacked_scores(maps, images, extra, groups['train'], year, config['cnn'], device)
        cnn_log += log
        pd.DataFrame({'harp': maps.harp, 't_rec': maps.t_rec, 'cnn_logit': score}).dropna().to_parquet(
            output/f'cnn_scores_{year}.parquet', index=False)
        contexts = {role: attach_maps(group, maps, score) for role, group in groups.items()}
        for role, context in contexts.items():
            row = {'year': year, 'role': role, 'rows': len(context)}
            for rule in RULES:
                row[f'map_available_share_{rule}'] = float(context[f'map_available_{rule}'].mean())
            coverage.append(row)
        chosen, probabilities = {'control': float(control_thresholds[str(year)][str(target)])}, {}
        for candidate, names in CANDIDATES.items():
            chosen[candidate], probabilities[candidate] = fit_candidate(base, groups, contexts, names)
            gc.collect()
        thresholds[str(year)] = chosen
        logits = {f'cnn_logit_{rule}': contexts['evaluation'][f'cnn_logit_{rule}'].to_numpy() for rule in RULES}
        prepared[year] = groups['evaluation'][KEY].reset_index(drop=True).assign(**probabilities, **logits)
        print(f'{year}: thresholds {chosen}', flush=True)
        del groups, contexts
        gc.collect()
    del images
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    pd.DataFrame(coverage).to_csv(output/'map_coverage.csv', index=False)
    pd.DataFrame(cnn_log).to_csv(output/'cnn_training.csv', index=False)
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels are read only now.
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    candidates = ['control', *CANDIDATES]
    rows_out, intervals, diagnostics = [], [], []
    for year in config['years']:
        labels = pd.read_parquet(source/str(year)/'predictions.parquet',
                                 columns=[*KEY, 'target', 'missing_fraction', 'baseline'])
        frame = labels.merge(prepared[year], on=KEY, how='inner').rename(columns={'baseline': 'control'})
        if len(frame) != len(labels) or len(frame) != len(prepared[year]):
            raise ValueError(f'Evaluation keys do not match: {year}')
        y = frame.target.to_numpy()
        for rule in RULES:
            covered = frame[f'cnn_logit_{rule}'].notna().to_numpy()
            both = covered.any() and 0 < y[covered].sum() < covered.sum()
            diagnostics.append({'year': year, 'rule': rule, 'covered_share': float(covered.mean()),
                                'positives_covered_share': float(y[covered].sum()/max(y.sum(), 1)),
                                'cnn_only_ap': float(average_precision_score(
                                    y[covered], frame.loc[covered, f'cnn_logit_{rule}'])) if both else np.nan,
                                'control_ap_same_windows': float(average_precision_score(
                                    y[covered], frame.loc[covered, 'control'])) if both else np.nan})
        results = {c: evaluate(frame, c, thresholds[str(year)][c], 1) for c in candidates}
        control, control_harp = results['control']
        for candidate in candidates:
            values, per_harp = results[candidate]
            scores = metrics(y, frame[candidate].to_numpy(), thresholds[str(year)][candidate])
            tn = len(y)-values['tp']-values['fp']-values['fn']
            row = dict(year=year, candidate=candidate, **values, accuracy=(values['tp']+tn)/len(y),
                       always_negative_accuracy=float((y == 0).mean()),
                       average_precision=scores['average_precision'], brier=scores['brier'],
                       log_loss=scores['log_loss'], tss=scores['tss'])
            if candidate != 'control':
                flags = acceptance(values, control, tolerance)
                row.update(flags)
                row['primary_met'] = bool(all(flags.values()))
                for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                    intervals.append(dict(year=year, candidate=candidate, metric=metric, **interval))
            rows_out.append(row)
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table_out = pd.DataFrame(rows_out)
    summary = []
    for candidate in CANDIDATES:
        gated = table_out[table_out.candidate == candidate]
        summary.append(dict(candidate=candidate, years_met=int(gated.primary_met.sum()), required_years=len(gated),
                            met_years=[int(v) for v in gated.loc[gated.primary_met.astype(bool), 'year']]))
    table_out.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(diagnostics).to_csv(output/'cnn_diagnostics.csv', index=False)
    result = {'config_sha256': sha(config_path), 'thresholds_sha256': thresholds_sha, 'years': config['years'],
              'maps_used': len(maps), 'maps_without_valid_pixel': empty_maps, 'device': device,
              'acceptance': summary, 'cnn_fits': len(cnn_log),
              'constituent_fits': len(config['years'])*len(CANDIDATES)*2,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table_out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/image-features-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tp', 'fp', 'fn', 'recall', 'precision', 'accuracy', 'average_precision',
                 'brier', 'primary_met']].round(4).to_string(index=False))
    print(json.dumps(result['acceptance']))
