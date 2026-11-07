"""Audit NOAA report creation times without treating them as publication proof."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def inspect_header(text):
    created = re.search(r'^:Created:\s*(\d{4}) ([A-Za-z]{3}) (\d{2}) (\d{4}) UT\s*$', text, re.M)
    day = re.search(r'^:Date:\s*(\d{4} \d{2} \d{2})\s*$', text, re.M)
    if not created or not day:
        raise ValueError('Missing or unsupported NOAA creation/date header')
    months = {m:i+1 for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
    year, month, date, clock = created.groups()
    stamp = datetime(int(year), months[month], int(date), int(clock[:2]), int(clock[2:]), tzinfo=timezone.utc)
    report_day = datetime.strptime(day[1], '%Y %m %d').replace(tzinfo=timezone.utc)
    if stamp < report_day:
        raise ValueError('Creation time precedes report day')
    return {'report_date':report_day.date().isoformat(), 'created_utc':stamp.isoformat(),
            'hours_after_report_day_start':(stamp-report_day).total_seconds()/3600,
            'availability_verified':False}


def run(source, output):
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((source/'manifest.json').read_text())
    rows = []
    for item in manifest['sources']:
        if item['status'] != 'downloaded':
            rows.append({'year':item['year'], 'status':'unavailable'})
            continue
        path = (source/item['file']).resolve()
        if not path.is_relative_to(source.resolve()):
            raise ValueError('Invalid source path')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Source hash mismatch')
        rows.append({'year':item['year'], 'status':'inspected', 'url':item['url'],
                     'sha256':item['sha256'], **inspect_header(raw.decode())})
    output.mkdir(parents=True)
    report = {'scope':manifest['scope'], 'sources':rows, 'training_ready':False,
              'reserved_test_accessed':False,
              'limitation':'Created is a document-generation timestamp, not verified first publication or immutable as-of availability. Region association provenance and full date coverage remain unverified.'}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.output), indent=2))
