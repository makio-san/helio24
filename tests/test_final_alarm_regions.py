import pandas as pd
import pytest
from scripts.audit_final_alarm_regions import summarize


def test_paired_alarm_accounting_preserves_gains_losses_and_zero_positive_regions():
    frame = pd.DataFrame({'harp':[1, 1, 2, 2], 'forecast_time':[1, 2, 1, 2],
        'target':[0, 0, 1, 0], 'chronological':[.8, .2, .2, .8], 'baseline':[.2, .8, .8, .8]})
    summary, _ = summarize(frame, {'chronological':.5, 'baseline':.5})
    assert [summary[k] for k in ['extra_fp','removed_fp','shared_fp','removed_tp']] == [1,1,1,1]
    assert summary['zero_positive_region_extra_fp'] == 1


def test_duplicate_forecasts_fail():
    frame = pd.DataFrame({'harp':[1,1], 'forecast_time':[1,1]})
    with pytest.raises(ValueError, match='Duplicate'):
        summarize(frame, {})
