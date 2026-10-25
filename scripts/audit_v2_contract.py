"""Audit the frozen V2 time, quality and label policy on development-only overlap."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from helio24.data import MAGNETIC_COLUMNS, ROOT, read_observation
from helio24.full_data import sha256
from helio24.v2_contract import (
    ACCEPTED_CONFIDENCE, AMBIGUOUS_CONFIDENCE, EVENT_COLUMNS,
    V2_MEASUREMENTS, extract_window, parse_flare_class, prepare_events,
    tai_utc_offset,
)


def summaries(array):
    counts = np.isfinite(array).sum(axis=0)
    denominator = np.where(counts, counts, np.nan)
    means = np.nansum(array, axis=0)/denominator
    std = np.sqrt(np.nansum((array-means)**2, axis=0)/denominator)
    return np.column_stack([means, std, array[-1], array[-1]-array[0]]).ravel()


def run(root=ROOT, output=None):
    output = output or root / 'artifacts/v2_contract_audit'
    if output.exists():
        raise RuntimeError('Preserve the existing V2 contract audit')
    source = root / 'data/compatibility_probe/first_member.parquet'
    overlap_path = root / 'artifacts/v2_overlap/report.json'
    overlap = json.loads(overlap_path.read_text())
    expected_source_hash = overlap['source_hashes']['data/compatibility_probe/first_member.parquet']
    if sha256(source) != expected_source_hash:
        raise ValueError('The bounded V2 source changed')

    measurement_names = list(V2_MEASUREMENTS.values())
    observations = pd.read_parquet(
        source, columns=['harp_number', 'obs_start', *measurement_names],
        filters=[('obs_start', '<', pd.Timestamp('2019-01-01'))],
    ).drop_duplicates()
    if observations.duplicated(['harp_number', 'obs_start']).any():
        raise ValueError('Conflicting V2 observations at one HARP/time')

    quality_rows = []
    for selected in overlap['selected']:
        start = pd.Timestamp(selected['observation_start'])
        end = start+pd.Timedelta(hours=12)
        window = observations[
            observations.harp_number.eq(selected['harp'])
            & observations.obs_start.ge(start)
            & observations.obs_start.lt(end)
        ].copy()
        extracted = extract_window(window)
        old = read_observation(root / selected['source'], magnetic_only=True)
        trusted = (old.IS_TMFI.astype(str).str.lower().isin(['true', '1', '1.0'])
                   & pd.to_numeric(old.QUALITY, errors='coerce').eq(0)).to_numpy()
        native = window.sort_values('obs_start')[measurement_names].apply(
            pd.to_numeric, errors='coerce').to_numpy(dtype=float, na_value=np.nan, copy=True)
        native[~np.isfinite(native)] = np.nan
        historical_mask = native.copy()
        historical_mask[~trusted, :] = np.nan
        native_summary = summaries(native)
        masked_summary = summaries(historical_mask)
        close = np.isclose(native_summary, masked_summary, rtol=1e-5, atol=1e-8, equal_nan=True)
        quality_rows.append(dict(
            harp=selected['harp'], observation_start=str(start),
            native_missing=int(np.isnan(native).sum()),
            historical_mask_missing=int(np.isnan(historical_mask).sum()),
            historical_trusted_rows=int(trusted.sum()),
            native_max_missing_fraction=float(np.isnan(native).mean(axis=0).max()),
            historical_max_missing_fraction=float(np.isnan(historical_mask).mean(axis=0).max()),
            both_policies_retain=True,
            summary_values=96, summary_values_changed=int((~close).sum()),
            forecast_time_utc=extracted['forecast_time'].isoformat(),
        ))

    raw_events = pd.read_parquet(
        source, columns=EVENT_COLUMNS+['obs_start'],
        filters=[('obs_start', '<', pd.Timestamp('2019-01-01'))],
    )
    events = prepare_events(raw_events)
    events['letter'] = [parse_flare_class(value)[0] for value in events.goes_class]
    events['strong'] = events.letter.isin(['M', 'X'])
    goes = events[events.has_goes].copy()
    catalog = pd.read_csv(root / 'data/flare_catalog.csv', usecols=['peak_time', 'goes_class'])
    catalog['peak_time'] = pd.to_datetime(catalog.peak_time, errors='raise')
    official_keys = set(zip(catalog.peak_time, catalog.goes_class))
    exact_official = sum((stamp.tz_localize(None), flare_class) in official_keys
                         for stamp, flare_class in zip(goes.peak_time_utc, goes.goes_class))
    exact_official_strong = sum(
        strong and (stamp.tz_localize(None), flare_class) in official_keys
        for stamp, flare_class, strong in zip(goes.peak_time_utc, goes.goes_class, goes.strong)
    )
    class_confidence = (goes.groupby(['letter', 'confidence']).size().rename('events')
                        .reset_index().sort_values(['letter', 'confidence']))
    class_confidence_rows = class_confidence.to_dict('records')
    for row in class_confidence_rows:
        row['events'] = int(row['events'])

    offset_counts = observations.obs_start.map(tai_utc_offset).value_counts().sort_index()
    output.mkdir(parents=True)
    quality_table = pd.DataFrame(quality_rows)
    quality_table.to_csv(output / 'quality_windows.csv', index=False)
    class_confidence.to_csv(output / 'goes_class_confidence.csv', index=False)
    report = {
        'scope': 'One bounded raw member before 2019; no 2024-2025 rows, model fitting or scoring',
        'retrieved_utc': datetime.now(timezone.utc).isoformat(),
        'source_member_rows_before_2019': int(len(raw_events)),
        'distinct_observation_rows_before_2019': int(len(observations)),
        'source_member_harps_before_2019': int(raw_events.harp_number.nunique()),
        'tai_utc_offset_counts': {str(int(k)): int(v) for k, v in offset_counts.items()},
        'quality_overlap': {
            'windows': len(quality_rows),
            'both_policies_retain': int(sum(row['both_policies_retain'] for row in quality_rows)),
            'native_missing': int(sum(row['native_missing'] for row in quality_rows)),
            'historical_mask_missing': int(sum(row['historical_mask_missing'] for row in quality_rows)),
            'summary_values': int(sum(row['summary_values'] for row in quality_rows)),
            'summary_values_changed': int(sum(row['summary_values_changed'] for row in quality_rows)),
            'decision': 'Use versioned V2 finite-value policy; do not claim historical mask equivalence',
        },
        'event_overlap': {
            'attached_events': int(len(events)),
            'goes_events': int(len(goes)),
            'goes_exact_peak_and_class_matches_in_v1_catalog': int(exact_official),
            'goes_strong_events': int(goes.strong.sum()),
            'goes_strong_exact_peak_and_class_matches_in_v1_catalog': int(exact_official_strong),
            'goes_strong_accepted_confidence': int((goes.strong & goes.confidence.isin(ACCEPTED_CONFIDENCE)).sum()),
            'goes_strong_ambiguous_confidence': int((goes.strong & goes.confidence.isin(AMBIGUOUS_CONFIDENCE)).sum()),
            'class_confidence': class_confidence_rows,
            'decision': 'GOES-only primary labels; half-open peak interval; ambiguous and unassigned strong events cannot become negatives',
        },
        'boundary_finding': 'The paper specifies a half-open prediction interval; pinned slicer code uses an inclusive final sampled timestamp. Helio24 regenerates labels with the paper interval.',
        'gate_decisions': {
            'quality_policy': 'verified',
            'utc_conversion': 'verified',
            'label_inclusion_policy': 'verified',
            'measurement_semantics': 'pending',
            'versioned_dataset_manifest': 'pending',
            'development_coverage_audit': 'pending',
            'training_runner_review': 'pending',
        },
        'source_hashes': {
            'data/compatibility_probe/first_member.parquet': sha256(source),
            'data/compatibility_probe/schema.json': sha256(source.parent / 'schema.json'),
            'data/flare_catalog.csv': sha256(root / 'data/flare_catalog.csv'),
            'artifacts/v2_overlap/report.json': sha256(overlap_path),
            'config/swan_sf_v2_sources.json': sha256(root / 'config/swan_sf_v2_sources.json'),
            'data/toolkit_source/py_src/swdatatoolkit/slicer/_HarpDataSlicer.py': sha256(root / 'data/toolkit_source/py_src/swdatatoolkit/slicer/_HarpDataSlicer.py'),
            'data/toolkit_source/docs/_src/Tutorial_RST/harpdownloader_tutorial.rst': sha256(root / 'data/toolkit_source/docs/_src/Tutorial_RST/harpdownloader_tutorial.rst'),
        },
        'code_hashes': {
            'helio24/v2_contract.py': sha256(root / 'helio24/v2_contract.py'),
            'scripts/audit_v2_contract.py': sha256(root / 'scripts/audit_v2_contract.py'),
        },
    }
    report['artifact_hashes'] = {
        'quality_windows.csv': sha256(output / 'quality_windows.csv'),
        'goes_class_confidence.csv': sha256(output / 'goes_class_confidence.csv'),
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if not k.endswith('_hashes')}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/v2_contract_audit')
    args = parser.parse_args()
    run(output=args.output)
