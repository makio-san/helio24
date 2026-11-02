import numpy as np
import pytest
from helio24.probability_review import paired_probability_intervals,reliability


def test_paired_probability_scores_preserve_region_pairing():
    y=[0,0,1,1];p=[.1,.2,.8,.9];h=[1,1,2,2]
    result=paired_probability_intervals(y,p,p,h,draws=100,seed=24)
    for row in result.values():assert row['estimate']==row['lower']==row['upper']==0
    worse=paired_probability_intervals(y,[.8,.9,.2,.1],p,h,draws=100)
    assert worse['brier']['lower']>0 and worse['log_loss']['lower']>0
    extreme=paired_probability_intervals(y,[0,0,1,1],p,h,draws=100)
    assert np.isfinite(extreme['log_loss']['estimate'])


def test_reliability_preserves_empty_bins_and_cluster_undefined_draws():
    rows=reliability([0,0,1,1],[0,.1,.9,1],[1,1,2,2],[0,.1,.5,1],draws=100)
    assert [r['n'] for r in rows]==[2,0,2]
    assert rows[1]['observed_rate'] is None and rows[1]['valid_draws']==0
    assert 0<rows[2]['undefined_draws']<100
    assert rows[2]['regions']==1 and rows[2]['positive_regions']==1
    assert rows[2]['observed_rate']==1 and rows[2]['mean_probability']==.95
    with pytest.raises(ValueError):reliability([0],[.2],[1],[0,1])
    with pytest.raises(ValueError):reliability([0,1],[.1,1.2],[1,2],[0,1])


def test_interim_gate_cannot_pass_when_both_arms_lack_required_years():
    from helio24.probability_review import coverage_contrast
    base={'year':2014,'n':100,'positives':10,'precision':.2,'recall':.96,'fp':40,'average_precision':.3,'brier':.1,'log_loss':.3}
    candidate={**base,'arm':'new','precision':.3,'fp':25,'average_precision':.4,'brier':.09,'log_loss':.2}
    control={**base,'arm':'old'}
    r=coverage_contrast([candidate,control],'new','old',[2014,2015])
    assert r['full_met_count']==1 and r['required_positive_years']==2
    assert r['missing_years']=='2015' and not r['all_year_full']


def test_missing_zero_event_year_still_prevents_complete_coverage():
    from helio24.probability_review import coverage_contrast
    base={'year':2014,'n':100,'positives':10,'precision':.2,'recall':.96,'fp':40,'average_precision':.3,'brier':.1,'log_loss':.3}
    rows=[{**base,'arm':'old'},{**base,'arm':'new','precision':.3,'fp':25,'average_precision':.4,'brier':.09,'log_loss':.2}]
    r=coverage_contrast(rows,'new','old',[2014],[2014,2018])
    assert r['missing_years']=='none' and r['missing_eligible_years']=='2018'
    assert not r['all_year_full']


def test_final_report_refuses_an_incomplete_experiment(tmp_path,monkeypatch):
    import json
    from helio24.full_data import sha256
    from scripts import evaluate_temporal_snapshot as script
    monkeypatch.setattr(script,'ROOT',tmp_path)
    (tmp_path/'config').mkdir();protocol=tmp_path/'config/temporal-sequence-v2.json';protocol.write_text('{}')
    source=tmp_path/'source';source.mkdir()
    (source/'prepared.json').write_text(json.dumps({'protocol_sha256':sha256(protocol),'folds':[{'year':2014,'status':'complete'}]}))
    plan=tmp_path/'plan.json';plan.write_text('{}');output=tmp_path/'output'
    with pytest.raises(ValueError,match='not complete'):script.run(source,output,plan,require_complete=True)
    assert not output.exists()
