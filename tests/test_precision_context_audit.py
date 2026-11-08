import numpy as np
import pandas as pd
from scipy.special import logit

from scripts.audit_precision_context import context_features, cross_fit, fp_allowed, harp_folds, CONTEXT


def frame(hours, harp=1):
    time = pd.Timestamp('2020-01-01', tz='UTC')+pd.to_timedelta(hours, unit='h')
    return pd.DataFrame({'harp': harp, 'forecast_time': time, 'missing_fraction': 0.0})


def test_context_uses_only_strictly_earlier_windows_of_the_same_harp():
    data = pd.concat([frame([0, 1, 2, 30]), frame([0, 1], harp=2)], ignore_index=True)
    p = np.array([.1, .5, .2, .3, .9, .9])
    out = context_features(data, p, control_threshold=.4)
    l = logit(p)
    assert list(out.columns) == CONTEXT
    assert out.coverage24.tolist() == [0, 1, 2, 0, 0, 1]
    assert np.isclose(out.past24_max_logit[2], max(l[0], l[1]))
    assert np.isclose(out.past24_max_logit[0], l[0])  # no history: equals the current logit
    assert np.isclose(out.past72_mean_logit[3], l[[0, 1, 2]].mean())  # 30h back sees all three
    assert out.past72_hours_above_control.tolist() == [0, 0, 1, 1, 0, 1]
    assert np.isclose(out.age_log_hours[3], np.log1p(30))
    # HARP 2 never sees HARP 1 history
    assert np.isclose(out.past24_max_logit[4], l[4]) and out.coverage72[4] == 0


def test_later_rows_do_not_change_earlier_features():
    data, p = frame([0, 1, 2]), np.array([.2, .3, .4])
    short = context_features(data.iloc[:2], p[:2], .5)
    full = context_features(data, p, .5)
    pd.testing.assert_frame_equal(short, full.iloc[:2])


def test_harp_folds_are_deterministic_rank_modulo_five():
    harps = np.array([50, 10, 30, 10, 20, 40, 60])
    assert harp_folds(harps).tolist() == [4, 0, 2, 0, 1, 3, 0]


def test_cross_fit_holds_out_each_harp_group_and_returns_full_model():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(200, 2))
    y = (x[:, 0]+rng.normal(scale=.5, size=200) > 0).astype(int)
    harps = np.repeat(np.arange(20), 10)
    cross, full = cross_fit(x, y, harps)
    assert cross.shape == (200,) and 0 < cross.min() and cross.max() < 1
    assert full.predict_proba(x).shape == (200, 2)


def test_fp_allowed_for_target_precision():
    assert fp_allowed(300) == 700
    assert fp_allowed(0) == 0
    assert fp_allowed(10) == 23
