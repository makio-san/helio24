import numpy as np
import pandas as pd
import pytest
from helio24.sequence_training import fit_scaler,transform,key_permutation,align_indices


def test_scaling_uses_training_only_and_retains_missing_mask():
    x=np.ones((3,60,24),dtype='float32');x[1]=3;x[2]=1e30;x[0,2,3]=np.nan
    scaler=fit_scaler(x,np.array([0,1]))
    x[2]=-1e30
    assert scaler==fit_scaler(x,np.array([0,1]))
    z=transform(x,scaler)
    assert z.shape==(3,60,48) and np.isfinite(z).all()
    assert z[0,2,3]==0 and z[0,2,27]==1
    assert np.max(np.abs(z[:,:,:24]))<=8
    x[:2,:,0]=np.nan
    with pytest.raises(ValueError):fit_scaler(x,np.array([0,1]))


def test_shuffle_key_is_stable_across_batch_order_and_timezone():
    first=key_permutation(24,7,'2022-01-01T00:00Z')
    np.testing.assert_equal(first,key_permutation(24,7,'2022-01-01T03:00+03:00'))
    assert first[0]==0 and first[-1]==59 and sorted(first.tolist())==list(range(60))
    assert not np.array_equal(first,key_permutation(24,8,'2022-01-01T00:00Z'))
    keys=pd.DataFrame({'harp':[7,8],'forecast_time':pd.to_datetime(['2022-01-01','2022-01-02'],utc=True)})
    np.testing.assert_equal(align_indices(keys,keys.iloc[::-1]),[1,0])
    with pytest.raises(ValueError):align_indices(keys,keys.assign(harp=99))


def test_cache_preserves_keys_and_detects_corruption(tmp_path):
    import json
    from helio24.full_data import sha256
    from helio24.sequence_training import prepare_cache
    source=tmp_path/'source';(source/'shards').mkdir(parents=True)
    keys=pd.DataFrame({'harp':[7,7],'forecast_time':pd.to_datetime(['2022-01-01','2022-01-02'],utc=True),'role':['train','train']})
    x=np.ones((2,60,24),dtype='float32');x[0,1,2]=np.nan
    np.savez_compressed(source/'shards'/'sample.npz',values=x,missing=~np.isfinite(x))
    keys.to_parquet(source/'shards'/'sample.parquet',index=False)
    shard={'file':'sample.npz','sha256':sha256(source/'shards'/'sample.npz'),'keys':'sample.parquet','keys_sha256':sha256(source/'shards'/'sample.parquet')}
    (source/'report.json').write_text(json.dumps({'rows':2,'shards':[shard]}));expected=sha256(source/'report.json');cache=tmp_path/'cache'
    prepare_cache(source,expected,cache,[24])
    np.testing.assert_equal(np.load(cache/'values.npy'),x)
    pd.testing.assert_frame_equal(pd.read_parquet(cache/'keys.parquet'),keys)
    mapped=np.load(cache/'values.npy',mmap_mode='r+');mapped[0,0,0]=99;mapped.flush();del mapped
    with pytest.raises(ValueError,match='Changed file'):prepare_cache(source,expected,cache,[24])
