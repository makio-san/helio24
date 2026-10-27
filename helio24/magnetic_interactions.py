"""Causal nonlinear features computed from one observation window."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_array, check_is_fitted
from helio24.data import FEATURE_COLUMNS


class MagneticInteractions(TransformerMixin, BaseEstimator):
    """Append selected mean-feature products after train-fitted scaling."""
    def fit(self, X, y=None):
        values = check_array(X)
        self.n_features_in_ = values.shape[1]
        names = ['USFLUX', 'TOTUSJH', 'TOTUSJZ', 'TOTPOT', 'ABSNJZH', 'SAVNCPP',
                 'R_VALUE', 'MEANSHR', 'SHRGT45', 'MEANPOT', 'MEANJZH', 'MEANALP']
        self.indices_ = [FEATURE_COLUMNS.index(f'{name}__mean') for name in names]
        return self

    def transform(self, X):
        check_is_fitted(self, 'indices_')
        values = check_array(X)
        if values.shape[1] != self.n_features_in_:
            raise ValueError('Feature count changed')
        selected = values[:, self.indices_]
        products = [selected[:, i]*selected[:, j] for i in range(len(self.indices_))
                    for j in range(i, len(self.indices_))]
        return np.column_stack([values, *products])


class RelativeEvolution(TransformerMixin, BaseEstimator):
    """Append bounded within-window ratios; no labels, dates or other windows."""
    def fit(self, X, y=None):
        values = check_array(X, ensure_all_finite='allow-nan')
        self.n_features_in_ = values.shape[1]
        if values.shape[1] != len(FEATURE_COLUMNS):
            raise ValueError('Expected the frozen 96-feature observation schema')
        return self

    def transform(self, X):
        check_is_fitted(self, 'n_features_in_')
        values = check_array(X, ensure_all_finite='allow-nan')
        if values.shape[1] != self.n_features_in_:
            raise ValueError('Feature count changed')
        means, std, last, delta = (values[:, i::4] for i in range(4))
        denominator = np.abs(means)+std
        denominator = np.where(denominator > 0, denominator, np.nan)
        derived = [std/denominator, delta/denominator, (last-means)/denominator]
        return np.column_stack([values, *[np.clip(v, -100, 100) for v in derived]])
