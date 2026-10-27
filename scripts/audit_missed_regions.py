"""Audit two development HARPs against raw V2 records, HEK and JSOC metadata."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from helio24.data import ROOT,FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.v2_contract import V2_MEASUREMENTS,EVENT_COLUMNS,audit_event_rows,tai_to_utc,label_windows
from helio24.v2_features import extract_harp_windows


def run(output,raw):
    output.mkdir(parents=True,exist_ok=False)
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    sources={}
    def verified(path,digest=None):
        value=sha256(path)
        if digest is not None and value!=digest:raise ValueError(f'Changed source: {path}')
        sources[str(path.relative_to(ROOT))]=value
        return path
    base=ROOT/'artifacts/experiment5_v2_development_20261026_r2'
    original=json.loads(verified(base/'report.json','b57ce8e12de3d18740872b1504f97ff6a9dee22b272143836bb1a739d155ef03').read_text())
    predictions=pd.read_parquet(verified(base/'validation_predictions.parquet',original['artifact_hashes']['validation_predictions.parquet']))
    predictions=predictions[predictions.model.eq('ensemble') & predictions.harp.isin([9152,9584])].copy()
    raw_report=json.loads(verified(raw/'report.json').read_text())
    verified(ROOT/'config/swan_sf_v2_sources.verified.json',raw_report['manifest_sha256'])
    material=ROOT/'artifacts/v2_development_features_20261025_r2'
    mat=json.loads(verified(material/'report.json','62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82').read_text())
    retained=[]
    for shard in mat['shards']:
        if shard['file'] in ['partition-1-d917a8a4fd4a.parquet','partition-2-05b11f13de93.parquet']:
            frame=pd.read_parquet(verified(material/'shards'/shard['file'],shard['sha256']))
            retained.append(frame[frame.harp.isin([9152,9584])])
    frozen=pd.concat(retained,ignore_index=True)
    inventory=ROOT/'artifacts/hek_major_inventory_20261025_r2'
    inv=json.loads(verified(inventory/'report.json').read_text())
    verified(inventory/'events.csv',inv['events_sha256'])
    external=[]
    for month in ['2023-03','2023-05']:
        item=next(q for q in inv['queries'] if q['start'].startswith(month))
        payload=json.loads(verified(inventory/'raw'/f'{month}.json',item['response_sha256']).read_text())
        external.extend(payload['result'])
    header_dir=ROOT/'data/region_headers_20261027'
    hm=json.loads(verified(header_dir/'manifest.json').read_text())
    headers=[]
    for record in hm['records']:
        if record['status']!=0:raise ValueError('JSOC metadata unavailable')
        payload=json.loads(verified(header_dir/record['file'],record['sha256']).read_text())
        d=pd.DataFrame({k['name']:k['values'] for k in payload['keywords']})
        d['utc']=[tai_to_utc(pd.to_datetime(s.replace('_TAI',''),format='%Y.%m.%d_%H:%M:%S')) for s in d.T_REC]
        d['harp']=d.HARPNUM.astype(int)
        d['quality_bits']=[int(s,16) if s.startswith('0x') else int(s) for s in d.QUALITY]
        d['transport']=record['transport'];headers.append(d)
    headers=pd.concat(headers,ignore_index=True)
    config=json.loads((ROOT/'config/experiment5-v7.json').read_text())
    roles={k:tuple(map(pd.Timestamp,v)) for k,v in config['roles'].items() if k!='test'}
    unknown=pd.read_csv(verified(ROOT/'artifacts/v2_label_inventory_20261025_r1/unassigned_major_events.csv'))
    summaries,events,source_checks=[],[],[]
    for record in raw_report['records']:
        harp=record['harp']
        joined=pd.read_parquet(verified(raw/record['file'],record['artifact_sha256']))
        observation=joined[['harp_number','obs_start',*V2_MEASUREMENTS.values()]].drop_duplicates().sort_values('obs_start')
        if observation.obs_start.duplicated().any():raise ValueError('Conflicting raw observations')
        observation['utc']=[tai_to_utc(pd.Timestamp(t)) for t in observation.obs_start]
        attached,errors=audit_event_rows(joined[EVENT_COLUMNS])
        generated,extraction=extract_harp_windows(observation,roles)
        generated=label_windows(generated,attached,unknown,inventory_complete=True)
        stored=frozen[frozen.harp.eq(harp)]
        match=stored.merge(generated,on=['harp','forecast_time'],suffixes=('_stored','_raw'),validate='one_to_one')
        if len(match)!=len(stored):raise ValueError('Missing reconstructed forecasts')
        equal=np.isclose(match[[c+'_stored' for c in FEATURE_COLUMNS]].to_numpy(float),
                         match[[c+'_raw' for c in FEATURE_COLUMNS]].to_numpy(float),rtol=1e-9,atol=1e-12,equal_nan=True)
        if not equal.all():raise ValueError('Reconstructed features differ')
        if not match.target_stored.eq(match.target_raw).all():raise ValueError('Reconstructed labels differ')
        p=predictions[predictions.harp.eq(harp)].sort_values('forecast_time')
        numeric=observation[list(V2_MEASUREMENTS.values())].apply(pd.to_numeric,errors='coerce')
        finite=np.isfinite(numeric.to_numpy(float))
        h=headers[headers.harp.eq(harp)]
        raw_flux=observation[['utc','usflux']].merge(h[['utc','USFLUX','quality_bits']],on='utc')
        jsoc_flux=pd.to_numeric(raw_flux.USFLUX,errors='coerce')
        v2_flux=pd.to_numeric(raw_flux.usflux,errors='coerce')
        valid=np.isfinite(jsoc_flux)&np.isfinite(v2_flux)
        source_checks.append({'harp':harp,'matched_header_times':len(raw_flux),'finite_flux_pairs':int(valid.sum()),
            'flux_matches_rtol_1e5':int(np.isclose(jsoc_flux[valid],v2_flux[valid],rtol=1e-5,atol=0).sum()),
            'header_rows':len(h),'nonzero_quality':int(h.quality_bits.ne(0).sum()),
            'noaa_ars':','.join(sorted(h.NOAA_ARS.unique())),'transport':','.join(sorted(h.transport.unique()))})
        missed=p[p.target.eq(1)&~p.alarm]
        summary={'harp':harp,'raw_rows':len(observation),'retained_windows':len(p),
            'positive_windows':int(p.target.sum()),'tp':int((p.target.eq(1)&p.alarm).sum()),'fn':len(missed),
            'fp':int((p.target.eq(0)&p.alarm).sum()),
            'cadence_gaps':int(observation.obs_start.diff().dropna().ne(pd.Timedelta(minutes=12)).sum()),
            'raw_rows_nonfinite':int((~finite).any(axis=1).sum()),
            'zero_flux_rows':int(numeric.usflux.eq(0).sum()),
            'missed_windows_without_missing_values':int(missed.missing_fraction.eq(0).sum()),
            'reproduced_windows':len(match),'reproduced_feature_values':int(equal.sum()),
            'attached_event_errors':errors,'extraction':extraction}
        summaries.append(summary)
        major=attached[attached.has_goes & attached.goes_class.str.startswith(('M','X'))]
        major=major.drop_duplicates(['peak_time_utc','goes_class'])
        for event in major.itertuples():
            if event.peak_time_utc.year!=2023:continue
            matches=[v for v in external if pd.Timestamp(v['event_peaktime'],tz='UTC')==event.peak_time_utc and v['fl_goescls']==event.goes_class]
            if len(matches)!=1:raise ValueError('Independent event match not unique')
            e=matches[0]
            q=p[(p.forecast_time<=event.peak_time_utc)&(p.prediction_end>event.peak_time_utc)]
            alarms=q[q.alarm];first=alarms.forecast_time.min()
            nearest=h.iloc[(h.utc-event.peak_time_utc).abs().argmin()]
            events.append({'harp':harp,'peak_utc':event.peak_time_utc.isoformat(),'start_utc':event.start_time_utc.isoformat(),
                'goes_class':event.goes_class,'confidence':event.confidence,
                'harp_vote':str(event.harp_vote),'max_pair_distance_deg':float(event.max_pair_distance_deg),
                'hek_noaa':int(e['ar_noaanum']),'jsoc_noaa':nearest.NOAA_ARS,
                'noaa_matches':str(e['ar_noaanum']) in nearest.NOAA_ARS.split(','),
                'header_offset_seconds':abs((nearest.utc-event.peak_time_utc).total_seconds()),
                'eligible_windows':len(q),'alarm_windows':len(alarms),
                'first_alarm_utc':first.isoformat() if len(alarms) else None,
                'lead_to_peak_hours':(event.peak_time_utc-first).total_seconds()/3600 if len(alarms) else None,
                'lead_to_start_hours':(event.start_time_utc-first).total_seconds()/3600 if len(alarms) else None})
        observation.to_csv(output/f'harp_{harp}_observations.csv',index=False)
        p.to_csv(output/f'harp_{harp}_windows.csv',index=False)
        attached.to_csv(output/f'harp_{harp}_events.csv',index=False)
        for lang in ['en','tr']:
            fig,axes=plt.subplots(4,1,figsize=(12,10),sharex=True,layout='constrained')
            axes[0].scatter(p.forecast_time,p.probability,s=12,c=np.where(p.target.eq(1),'tab:red','tab:blue'))
            axes[0].axhline(.00931081050648097,color='black',linestyle='--')
            axes[0].set_ylabel('Probability / threshold' if lang=='en' else 'Olasılık / eşik')
            for ax,col in zip(axes[1:3],['usflux','totusjh']):
                ax.plot(observation.utc,pd.to_numeric(observation[col],errors='coerce'),lw=.8)
                ax.set_ylabel(col.upper());ax.set_yscale('symlog',linthresh=1e18 if col=='usflux' else 1)
            axes[3].scatter(p.forecast_time,p.missing_fraction*100,s=10,label='Window missing %' if lang=='en' else 'Pencere eksik %')
            bad=h[h.quality_bits.ne(0)]
            axes[3].scatter(bad.utc,np.full(len(bad),-2),marker='x',s=14,label='JSOC QUALITY != 0')
            axes[3].legend(loc='upper right');axes[3].set_ylabel('%');axes[3].set_xlabel('UTC')
            for e in major.itertuples():
                for ax in axes:ax.axvline(e.peak_time_utc,color='tab:red',alpha=.4,lw=.8)
            for ax in axes:ax.grid(alpha=.2)
            fig.suptitle(f'HARP {harp} — '+('Retrospective audit; red = positive windows / flare peaks' if lang=='en' else 'Geçmiş veri denetimi; kırmızı = pozitif pencereler / patlama tepeleri'))
            fig.savefig(output/f'harp_{harp}.{lang}.png',dpi=150);plt.close(fig)
    pd.DataFrame(events).to_csv(output/'event_checks.csv',index=False)
    pd.DataFrame(source_checks).to_csv(output/'header_checks.csv',index=False)
    report={'scope':'Retrospective audit of two development regions; no relabeling, retraining or test access',
        'regions':summaries,'events':events,'headers':source_checks,'source_hashes':sources,
        'code_sha256':sha256(Path(__file__)),
        'artifact_hashes':{p.name:sha256(p) for p in output.iterdir() if p.is_file()}}
    (output/'report.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
    print(json.dumps({k:report[k] for k in ['regions','events','headers']},indent=2,default=str))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.output.resolve(),args.raw.resolve())
