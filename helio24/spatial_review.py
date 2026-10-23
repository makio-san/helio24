"""Validate browse-image evidence without turning visual candidates into labels."""
import pandas as pd


def validate_frame(frame, metadata, observed_watermark):
    if frame.get('rejection') or frame['metadata']['status'] != 'downloaded' or frame.get('image', {}).get('status') != 'downloaded':
        raise ValueError('Incomplete or rejected image evidence')
    if metadata.get('name') != 'AIA 131' or str(metadata['id']) != str(frame['image_id']):
        raise ValueError('Unexpected image identity or channel')
    actual = pd.Timestamp(metadata['date'], tz='UTC')
    requested = pd.Timestamp(frame['requested_utc'])
    if requested.tzinfo is None or abs((actual-requested).total_seconds()) > 60:
        raise ValueError('Image outside the requested UTC time tolerance')
    if actual != pd.Timestamp(frame['actual_utc']) or actual != pd.Timestamp(observed_watermark, tz='UTC'):
        raise ValueError('Rendered watermark and metadata time disagree')
    return actual.isoformat()


def disposition(flare_id):
    candidates = {8765: (12149, 4466), 8864: (12155, 4502)}
    noaa, disputed_harp = candidates[flare_id]
    return dict(flare_id=flare_id, favored_noaa_candidate=noaa, disputed_harp=disputed_harp,
                status='limb_source_favored_harp_unresolved', label_change_allowed=False,
                evidence_type='assistant_visual_review_of_three_AIA131_browse_frames',
                definitive_spatial_adjudication=False)
