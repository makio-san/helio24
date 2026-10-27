"""Snapshot bounded historical SHARP metadata for three development events."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from helio24.data import ROOT
from helio24.full_data import sha256


def run():
    output=ROOT/'data/region_headers_20261027'
    output.mkdir(parents=True,exist_ok=False)
    tasks=[(9152,'2023.03.02_12:00:00_UTC/60h@12m'),
           (9584,'2023.05.23_00:00:00_UTC/48h@12m'),
           (9584,'2023.05.29_00:00:00_UTC/48h@12m')]
    keys='HARPNUM,T_REC,T_OBS,NOAA_AR,NOAA_ARS,QUALITY,CRLN_OBS,CRVAL1,LON_FWT,LAT_FWT,USFLUX,MEANPOT,TOTPOT'
    def fetch(task):
        harp,window=task;name=f'harp_{harp}_{window[:10]}.json';path=output/name
        attempts=[]
        for scheme in ['https','http']:
            url=f'{scheme}://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info?'+urlencode(
                {'op':'rs_list','ds':f'hmi.sharp_cea_720s[{harp}][{window}]','key':keys})
            r=subprocess.run(['curl','--fail','--silent','--show-error','--location','--max-time','40',
                '--max-filesize','2000000','--proto','=http,https','--output',str(path),url],capture_output=True,text=True)
            attempts.append({'url':url,'returncode':r.returncode,'error':r.stderr,
                             'retrieved_utc':datetime.now(timezone.utc).isoformat()})
            if r.returncode==0:
                payload=json.loads(path.read_text())
                return {'harp':harp,'window':window,'file':name,'sha256':sha256(path),
                        'transport':scheme,'status':payload.get('status'),'count':payload.get('count'),
                        'attempts':attempts}
        return {'harp':harp,'window':window,'status':'unavailable','attempts':attempts}
    with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(fetch,tasks))
    (output/'manifest.json').write_text(json.dumps({'records':records,'code_sha256':sha256(Path(__file__)),
        'limitation':'HTTP fallback is unauthenticated; TLS verification is not disabled.'},indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='attempts'} for r in records],indent=2))


if __name__=='__main__':run()
