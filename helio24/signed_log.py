"""Train-fitted magnitude compression for signed magnetic features."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_array, check_is_fitted


class SignedLogScaler(TransformerMixin, BaseEstimator):
    """Compress tails relative to each training column's median magnitude."""

    def fit(self, X, y=None):
        values = check_array(X, dtype=np.float64)
        self.n_features_in_ = values.shape[1]
        scale = np.median(np.abs(values), axis=0)
        self.scale_ = np.where(scale > 0, scale, 1.0)
        return self

    def transform(self, X):
        check_is_fitted(self, 'scale_')
        values = check_array(X, dtype=np.float64)
        if values.shape[1] != self.n_features_in_:
            raise ValueError('Feature count changed')
        return np.sign(values)*np.log1p(np.abs(values)/self.scale_)
