"""Descriptive alarm episodes, coverage-aware event matches and region summaries."""
import numpy as np
import pandas as pd

HOUR = pd.Timedelta(hours=1)
DAY = pd.Timedelta(hours=24)


def alarm_episodes(frame, threshold):
    if not 0 <= threshold <= 1:
        raise ValueError('Threshold must be a probability')
    frame = frame.sort_values(['harp', 'forecast_time']).reset_index(drop=True).copy()
    if frame.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate HARP/forecast record')
    if not np.isfinite(frame.probability).all() or not frame.probability.between(0, 1).all():
        raise ValueError('Invalid forecast probabilities')
    if not frame.target.isin([0, 1]).all():
        raise ValueError('Targets must be binary')
    frame['alarm'] = frame.probability.ge(threshold)
    following = frame.groupby('harp').forecast_time.shift(-1)
    frame['state_end'] = pd.concat([frame.forecast_time+HOUR, following], axis=1).min(axis=1)
    frame['state_hours'] = (frame.state_end-frame.forecast_time).dt.total_seconds()/3600
    frame['episode_id'] = -1
    episodes = []
    for harp, group in frame.groupby('harp', sort=True):
        previous = group.forecast_time.shift()
        next_time = group.forecast_time.shift(-1)
        adjacent_previous = group.forecast_time.sub(previous).eq(HOUR)
        adjacent_next = next_time.sub(group.forecast_time).eq(HOUR)
        starts = ~(group.alarm & group.alarm.shift(fill_value=False) & adjacent_previous)
        for _, run in group[group.alarm].groupby(starts.cumsum()):
            episode_id = len(episodes)
            frame.loc[run.index, 'episode_id'] = episode_id
            false = run.target.eq(0)
            episodes.append(dict(
                episode_id=episode_id, harp=int(harp), start=run.forecast_time.iloc[0],
                end=run.state_end.iloc[-1], windows=len(run), state_hours=float(run.state_hours.sum()),
                false_windows=int(false.sum()), false_hours=float(run.loc[false, 'state_hours'].sum()),
                all_negative=bool(false.all()), left_censored=not bool(adjacent_previous.loc[run.index[0]]),
                right_censored=not bool(adjacent_next.loc[run.index[-1]]),
                mean_probability=float(run.probability.mean()),
                mean_missing_fraction=float(run.missing_fraction.mean()),
            ))
    columns = ['episode_id', 'harp', 'start', 'end', 'windows', 'state_hours', 'false_windows',
               'false_hours', 'all_negative', 'left_censored', 'right_censored',
               'mean_probability', 'mean_missing_fraction']
    return frame, pd.DataFrame(episodes, columns=columns)


def coverage_hours(windows, start, end):
    """Union of modeled issue-state slots, clipped to the requested interval."""
    covered, last = 0.0, start
    for left, right in windows[['forecast_time', 'state_end']].itertuples(index=False, name=None):
        left, right = max(left, start, last), min(right, end)
        if right > left:
            covered += (right-left).total_seconds()/3600
            last = right
    return covered


def match_events(windows, mapping, catalog):
    """Unique catalog IDs; ambiguous or uncovered associations are not misses."""
    if catalog.flare_id.duplicated().any():
        raise ValueError('Catalog IDs must be unique')
    mapping = mapping.drop_duplicates(['harp', 'flare_id']).copy()
    catalog = catalog.copy()
    for column in ['start_time', 'peak_time']:
        catalog[column] = pd.to_datetime(catalog[column])
    strong = catalog[catalog.goes_class.str.startswith(('M', 'X'))]
    # Whole-Sun catalog is a coverage context, not the regional recall denominator.
    strong = strong[(strong.peak_time >= windows.forecast_time.min()) &
                    (strong.peak_time < windows.prediction_end.max())]
    by_region = {int(harp): group for harp, group in windows.groupby('harp')}
    rows = []
    for event in strong.itertuples(index=False):
        evidence = mapping[mapping.flare_id.eq(event.flare_id)]
        row = dict(flare_id=int(event.flare_id), goes_class=event.goes_class,
                   start_time=event.start_time, peak_time=event.peak_time,
                   harp=None, evidence=';'.join(sorted(set(evidence.evidence))), status='unmapped',
                   available_forecasts=0, coverage_hours=0., fully_covered=False,
                   detected=False, before_start=False, alarm_windows=0, alarm_episodes=0,
                   first_alarm=pd.NaT, peak_lead_hours=np.nan, start_lead_hours=np.nan)
        if evidence.harp.nunique() > 1:
            row['status'] = 'ambiguous'
        elif len(evidence):
            harp = int(evidence.harp.iloc[0])
            row['harp'] = harp
            row['status'] = 'no_forecast_coverage'
            group = by_region.get(harp)
            if group is not None:
                eligible = group[(group.forecast_time <= event.peak_time) &
                                 (group.prediction_end > event.peak_time)]
                hours = coverage_hours(group, event.peak_time-DAY, event.peak_time)
                row.update(coverage_hours=hours, fully_covered=bool(np.isclose(hours, 24)))
                if len(eligible):
                    alarms = eligible[eligible.alarm]
                    row.update(status='evaluated', available_forecasts=len(eligible),
                               detected=bool(len(alarms)), before_start=bool((alarms.forecast_time < event.start_time).any()),
                               alarm_windows=len(alarms), alarm_episodes=int(alarms.episode_id.nunique()))
                    if len(alarms):
                        first = alarms.forecast_time.min()
                        row.update(first_alarm=first, peak_lead_hours=(event.peak_time-first).total_seconds()/3600)
                        if first < event.start_time:
                            row['start_lead_hours'] = (event.start_time-first).total_seconds()/3600
        rows.append(row)
    return pd.DataFrame(rows)


def regional_summary(windows, episodes, events):
    rows = []
    episodes = episodes.copy()
    episodes['previous_peak_hours'] = np.nan
    episodes['next_peak_hours'] = np.nan
    for harp, group in windows.groupby('harp'):
        runs = episodes[episodes.harp.eq(harp)]
        local_events = events[(events.harp == harp) & (events.status == 'evaluated')]
        peaks = events[(events.harp == harp) & (events.status != 'ambiguous')].peak_time
        for index, run in runs.iterrows():
            before, after = peaks[peaks <= run.start], peaks[peaks >= run.end]
            if len(before):
                episodes.loc[index, 'previous_peak_hours'] = (run.start-before.max()).total_seconds()/3600
            if len(after):
                episodes.loc[index, 'next_peak_hours'] = (after.min()-run.end).total_seconds()/3600
        false = group.alarm & group.target.eq(0)
        positive = group.target.eq(1)
        negative = group.target.eq(0)
        quiet_runs = runs[runs.all_negative.astype(bool)]
        row = dict(harp=int(harp), windows=len(group), monitored_hours=float(group.state_hours.sum()),
                   alarm_hours=float(group.loc[group.alarm, 'state_hours'].sum()),
                   false_hours=float(group.loc[false, 'state_hours'].sum()), false_windows=int(false.sum()),
                   negative_windows=int(negative.sum()), positive_windows=int(positive.sum()),
                   missed_windows=int((~group.alarm & positive).sum()), episodes=len(runs),
                   all_negative_episodes=len(quiet_runs),
                   longest_all_negative_hours=float(quiet_runs.state_hours.max()) if len(quiet_runs) else 0.,
                   mapped_covered_events=len(local_events), detected_events=int(local_events.detected.sum()),
                   mean_missing_fraction=float(group.missing_fraction.mean()),
                   false_alarm_missing_fraction=float(group.loc[false, 'missing_fraction'].mean()) if false.any() else np.nan)
        row['false_hour_fraction'] = row['false_hours']/row['monitored_hours']
        for name in ['USFLUX', 'R_VALUE', 'TOTUSJH']:
            column = name+'__last'
            row[column+'_median'] = float(group[column].median()) if column in group else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values(['false_hours', 'harp'], ascending=[False, True]), episodes
