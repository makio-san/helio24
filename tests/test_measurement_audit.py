import numpy as np
import pytest
from helio24.measurement_audit import compare_values, force_hypotheses, safe_ratio


def test_missing_values_do_not_count_as_finite_agreement():
    result = compare_values([1, np.nan, np.inf, 0], [1, np.nan, 2, 0])
    assert result['finite_pairs'] == result['close_finite'] == 2
    assert result['both_missing'] == 1
    assert result['finite_mismatch'] == 1
    with pytest.raises(ValueError):
        compare_values([1, 2], [1])


def test_ratio_never_fills_missing_or_zero_denominators():
    result = safe_ratio([2, 1, np.inf, 1], [4, 0, 1, np.nan])
    assert result[0] == .5
    assert np.isnan(result[1:]).all()


def test_force_signs_are_explicit_and_inputs_unchanged():
    old = dict(TOTFX=np.array([4*np.pi]), TOTFY=np.array([4*np.pi]), TOTFZ=np.array([8*np.pi]))
    result = force_hypotheses(old)
    assert [result[k][0] for k in old] == pytest.approx([1, -1, 1])
    assert old['TOTFY'][0] == 4*np.pi
