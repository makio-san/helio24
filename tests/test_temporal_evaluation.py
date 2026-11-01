import json
import numpy as np
import pandas as pd
import pytest
from scripts import run_temporal_years as runner


@pytest.mark.parametrize('has_events',[True,False])
def test_annual_evaluation_freezes_calibration_thresholds_and_handles_zero_events(tmp_path,monkeypatch,has_events):
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    directory=tmp_path/'run';directory.mkdir();year=2018
    cal=pd.DataFrame({'harp':[1,1,2,2,3,3],'target':[0,0,0,0,1,1]})
    evaluation=pd.DataFrame({'harp':[4,4,5,5],'target':[0,1,0,1] if has_events else [0,0,0,0]})
    cal.to_parquet(directory/'calibration-metadata.parquet',index=False)
    evaluation.to_parquet(directory/'evaluation-metadata.parquet',index=False)
    protocol={'arms':['chronological','shuffled_interior'],'seeds':[24,42,97],'baseline_artifact':'baseline','short_control':'short','uncertainty':{'draws':10,'seed':24}}
    for arm in protocol['arms']:
        for seed in protocol['seeds']:
            job=directory/f'{arm}_seed{seed}';job.mkdir()
            np.save(job/'calibration.npy',np.array([.1,.3,.6,.4,.5,.8]))
            np.save(job/'evaluation.npy',np.array([.7,.8,.2,.4]))
    for name,column in [('baseline','ensemble'),('short','shared_train_one_year')]:
        p=tmp_path/name/str(year);p.mkdir(parents=True)
        (p/'thresholds.json').write_text(json.dumps({column:.5}))
        pd.DataFrame({column:[.6,.7,.2,.4]}).to_parquet(p/'predictions.parquet',index=False)
    result=runner.evaluate_fold(protocol,directory,year)
    thresholds=json.loads((directory/'thresholds.json').read_text())
    assert len(result['metrics'])==10
    assert thresholds['chronological']==thresholds['shuffled_interior']
    assert (directory/'finished.json').exists()
    if not has_events:
        assert all(r['recall'] is None for r in result['metrics'])
    # Changing only evaluation labels cannot change fitted calibration or thresholds.
    evaluation.target=1-evaluation.target
    evaluation.to_parquet(directory/'evaluation-metadata.parquet',index=False)
    # This helper is exercised in a disposable test directory, never a frozen run.
    (directory/'finished.json').unlink()
    runner.evaluate_fold(protocol,directory,year)
    assert thresholds==json.loads((directory/'thresholds.json').read_text())
