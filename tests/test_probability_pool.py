import numpy as np
import pytest
from helio24.probability_pool import probability_pool


def test_pool_recovers_known_means_and_bounds():
    a,b=np.array([.2,.8]),np.array([.8,.2])
    np.testing.assert_allclose(probability_pool(a,b,.5,1),.5)
    np.testing.assert_allclose(probability_pool(a,b,.5,0),.4)
    np.testing.assert_allclose(probability_pool(a,b,.5,-1),.32)
    for power in [-1,0,1,2]:
        np.testing.assert_allclose(probability_pool(a,b,1,power),a)
        np.testing.assert_allclose(probability_pool(a,b,0,power),b)
    with pytest.raises(ValueError):
        probability_pool([2],[.2],.5,0)
