"""Describe archive annotation evidence without repairing benchmark labels."""
import pandas as pd


def timing_evidence(stamp, peak):
    stamp, peak = pd.Timestamp(stamp), pd.Timestamp(peak)
    offset = (stamp-peak).total_seconds()/60
    return dict(offset_minutes=offset, nearest_12min_compatible=abs(offset) <= 6,
                containing_12min_compatible=stamp <= peak < stamp+pd.Timedelta(minutes=12))


def association_evidence(annotations):
    """Keep NOAA-based and location-based evidence separate by event and HARP."""
    rows = []
    for (flare_id, harp), group in annotations.groupby(['flare_id', 'harp'], sort=True):
        noaa = group.source.isin(['MFLARE_LABEL', 'XFLARE_LABEL']).any()
        location = group.source.isin(['MFLARE_LABEL_LOC', 'XFLARE_LABEL_LOC']).any()
        rows.append(dict(flare_id=int(flare_id), harp=int(harp), noaa_history=bool(noaa),
                         location_history=bool(location),
                         association_method='both' if noaa and location else 'noaa_only' if noaa else 'location_only'))
    return pd.DataFrame(rows)
