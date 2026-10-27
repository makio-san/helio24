import numpy as np
from helio24.data import FEATURE_COLUMNS
from helio24.magnetic_interactions import MagneticInteractions, RelativeEvolution


def test_relative_features_depend_only_on_current_row():
    X = np.tile([2., 1., 4., 3.], (2, 24))
    transformer = RelativeEvolution().fit(X)
    first = transformer.transform(X[:1])
    np.testing.assert_allclose(first[:, 96:120], 1/3)
    np.testing.assert_allclose(first[:, 120:144], 1)
    np.testing.assert_allclose(first[:, 144:], 2/3)
    X[1] = 1e6
    np.testing.assert_allclose(transformer.transform(X)[0], first[0])
    assert np.isnan(transformer.transform(np.zeros((1, 96)))[:, 96:]).all()


def test_interactions_use_expected_magnetic_fields():
    X = np.zeros((1, 96))
    X[0, FEATURE_COLUMNS.index('USFLUX__mean')] = 2
    X[0, FEATURE_COLUMNS.index('TOTUSJH__mean')] = -3
    result = MagneticInteractions().fit_transform(X)
    assert result.shape == (1, 174)
    assert result[0, 96] == 4
    assert result[0, 97] == -6
    np.testing.assert_array_equal(result[:, :96], X)


def test_splines_keep_fitted_knots_when_future_extremes_change():
    from helio24.magnetic_interactions import MagneticSplines
    rng = np.random.default_rng(24)
    X = rng.normal(size=(100, 96))
    model = MagneticSplines().fit(X)
    knots = [spline.t.copy() for spline in model.spline_.bsplines_]
    result = model.transform(np.full((2, 96), 1e6))
    assert np.isfinite(result).all()
    assert result.shape[1] > 96
    for before, after in zip(knots, model.spline_.bsplines_):
        np.testing.assert_array_equal(before, after.t)
