import numpy as np
import pandas as pd
from helio24.threshold_audit import summarize_scores


def test_region_influence_and_undefined_after_only_positive_region_removed():
    d=pd.DataFrame({'harp':[1,1,2,3],'target':[1,1,0,0]})
    s,rows=summarize_scores(d,np.array([.1,.9,.05,.2]))
    assert s['positive_regions']==1 and s['top1_positive_share']==1
    assert s['concentration_equivalent_regions']==1 and s['negative_alarm_rate']==.5
    assert rows[0]['threshold_without_region'] is None and s['loro_undefined']==1


def test_leave_region_removes_its_negative_windows_too():
    d=pd.DataFrame({'harp':[1,1,2,3],'target':[1,0,1,0]})
    s,rows=summarize_scores(d,[.1,.8,.9,.2])
    first=next(r for r in rows if r['harp']==1)
    assert first['removed_rows']==2 and first['threshold_without_region']==.9
    assert s['positive_regions']==2 and s['top1_positive_share']==.5
