"""Fresh-process CNN fitting and scoring of SHARP Br maps; reads map labels of the training role only."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np

from helio24.map_model import pick_device, score_cnn, train_cnn


def run(work):
    if any(name in sys.modules for name in ['sklearn', 'xgboost']):
        raise RuntimeError('Worker must isolate the neural runtime')
    job = json.loads((work/'job.json').read_text())
    cache, settings, folds, year = Path(job['cache']), job['settings'], job['folds'], job['year']
    images, extra = np.load(cache/'images.npy', mmap_mode='r'), np.load(cache/'extra.npy')
    labels, usable = np.load(work/'labels.npy'), np.load(work/'usable.npy')
    harp, in_train = np.load(work/'harp.npy'), np.load(work/'in_train.npy')
    fold, device = harp % folds, pick_device()
    scores, log = np.full((folds, len(harp)), np.nan, dtype=np.float32), []
    for k in range(folds):
        fit = np.flatnonzero(np.isfinite(labels) & (fold != k))
        model, loss = train_cnn(np.asarray(images[fit]), extra[fit], labels[fit], settings, settings['seed']+year*10+k, device)
        scores[k, usable] = score_cnn(model, images, extra, usable, device)
        log.append({'year': year, 'fold': k, 'maps': len(fit), 'positive_maps': int(labels[fit].sum()), 'final_loss': loss})
        print(log[-1], flush=True)
        del model
    np.save(work/'scores.npy', np.where(in_train, scores[fold, np.arange(len(harp))], scores.mean(axis=0)))
    (work/'result.json').write_text(json.dumps({'log': log, 'device': device}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', type=Path, required=True)
    run(parser.parse_args().job)
