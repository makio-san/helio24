import numpy as np
import pytest
from helio24.signed_log import SignedLogScaler


def test_transform_keeps_training_scale_and_sign():
    model = SignedLogScaler().fit([[2, 0], [-4, 0], [6, 0]])
    np.testing.assert_allclose(model.scale_, [4, 1])
    np.testing.assert_allclose(model.transform([[8, -3], [0, 0]]),
                               [[np.log(3), -np.log(4)], [0, 0]])
    np.testing.assert_allclose(model.scale_, [4, 1])
    with pytest.raises(ValueError, match='Feature count'):
        model.transform([[1]])
