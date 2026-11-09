import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.fetch_sharp_maps import month_index, resize

ROOT = Path(__file__).resolve().parents[1]


def test_resize_averages_valid_pixels_only():
    image = np.full((40, 100), 7.0)
    image[:, :50] = np.nan
    small = resize(image, (4, 10))
    assert small.shape == (4, 10) and small.dtype == np.float16
    assert np.all(small[:, :5] == 0) and np.allclose(small[:, 5:], 7.0)
    mixed = np.array([[np.nan, 4.0], [2.0, np.nan]])
    assert np.allclose(resize(mixed, (1, 1)), 3.0)


def test_resize_handles_maps_smaller_than_the_output():
    assert np.allclose(resize(np.full((10, 30), -5.0), (128, 256)), -5.0)


def test_reserved_period_is_never_indexed(tmp_path):
    config = json.loads((ROOT/'config/sharp-maps-v1.json').read_text())
    with pytest.raises(ValueError):
        month_index(pd.Timestamp('2024-01-01'), tmp_path, config)
    assert config['scope']['index_period'][1] < '2024-01-01'
    assert config['reserved_test_accessed'] is False
    assert config['status'] == 'frozen_before_any_map_download'
