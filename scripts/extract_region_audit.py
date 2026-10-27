"""Extract two pre-2024 HARPs from hash-verified V2 archives for error auditing."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.v2_archive import stream_verified_archive_with_retries
from helio24.v2_contract import EVENT_COLUMNS,V2_MEASUREMENTS,utc_to_tai


def run(output):
    manifest_path=ROOT/'config/swan_sf_v2_sources.verified.json'
    manifest=json.loads(manifest_path.read_text())
    output.mkdir(parents=True,exist_ok=False)
    targets={1:9152,2:9584}
    def scan(item):
        harp=targets[item['partition']]
        frames=[]
        def member(path,name,size):
            columns=['obs_start',*V2_MEASUREMENTS.values(),*EVENT_COLUMNS]
            frame=pd.read_parquet(path,columns=columns,filters=[('harp_number','==',harp),
                ('obs_start','<',utc_to_tai(pd.Timestamp('2024-01-01T00:00:00Z')))])
            if len(frame):frames.append(frame)
            return {'member':name,'selected_rows':len(frame)}
        record=stream_verified_archive_with_retries(item,member,temporary_root=ROOT/'data/cache')
        if not frames:raise ValueError('Target HARP absent')
        path=output/f'harp_{harp}.parquet'
        pd.concat(frames,ignore_index=True).drop_duplicates().to_parquet(path,index=False)
        record.update(harp=harp,file=path.name,artifact_sha256=sha256(path))
        print(f'HARP {harp}: verified and extracted',flush=True)
        return record
    items=[item for item in manifest['archives'] if item['partition'] in targets]
    with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(scan,items))
    report={'scope':'HARP 9152 and 9584, pre-2024 logical reads only; no training',
            'manifest_sha256':sha256(manifest_path),'code_sha256':sha256(Path(__file__)),
            'records':records,'reserved_test_accessed':False}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
