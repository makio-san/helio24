# Alarm episodes: does grouping windows raise precision?

## Scope and decision

Precision is low when alarms are counted as overlapping hourly forecast windows. This
audit asks whether counting consecutive-hour alarms as one alarm episode changes that
picture. It re-reads the frozen annual predictions and thresholds of the completed seven-year
comparison (source report SHA256 `e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`).
No training, threshold change, relabeling, model acceptance or access to the reserved
2024–2025 test took place. The analysis is post-hoc and descriptive.

The hypothesis that episode counting would raise precision is not supported. Episode precision is
lower than window precision in every year with positive windows, for both reported arms. The
operational burden is a large number of short, all-negative alarm episodes, not a few long ones.

## Definitions

An alarm episode is a run of consecutive hourly windows of one HARP whose probability is at or
above the frozen threshold. A hit episode contains at least one positive-labelled window; an
all-negative episode contains none. Episode precision is hit episodes divided by episodes. A positive
run is a run of consecutive positive-labelled windows of one HARP; it counts as alarmed when any
of its windows is in an alarm. These are groupings of overlapping windows, not physical flares,
not independent events and not a catalog match. Gaps in the hourly record split an episode;
the CSV counts episodes touching a record boundary.

## Results

Baseline and chronological arms at their unchanged calibration thresholds. All four arms and
more fields are in the local `episodes.csv`.

| year | arm | positive_runs | positive_runs_alarmed | window_precision | episodes | hit_episodes | episode_precision | all_negative_episodes | median_all_negative_hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline | 83 | 80 | 0.135905 | 686 | 67 | 0.097668 | 619 | 5 |
| 2014 | chronological | 83 | 79 | 0.100078 | 801 | 65 | 0.081149 | 736 | 7 |
| 2015 | baseline | 51 | 51 | 0.105164 | 568 | 38 | 0.066901 | 530 | 3 |
| 2015 | chronological | 51 | 50 | 0.105677 | 578 | 38 | 0.065744 | 540 | 4 |
| 2016 | baseline | 7 | 7 | 0.071400 | 204 | 4 | 0.019608 | 200 | 3 |
| 2016 | chronological | 7 | 7 | 0.026380 | 385 | 5 | 0.012987 | 380 | 6 |
| 2017 | baseline | 6 | 5 | 0.155512 | 85 | 5 | 0.058824 | 80 | 3.5 |
| 2017 | chronological | 6 | 5 | 0.133521 | 140 | 5 | 0.035714 | 135 | 3 |
| 2018 | baseline | 0 | 0 | 0.000000 | 30 | 0 | 0.000000 | 30 | 2 |
| 2018 | chronological | 0 | 0 | 0.000000 | 49 | 0 | 0.000000 | 49 | 3 |
| 2022 | baseline | 16 | 16 | 0.039573 | 622 | 16 | 0.025723 | 606 | 5 |
| 2022 | chronological | 16 | 16 | 0.030061 | 809 | 16 | 0.019778 | 793 | 4 |
| 2023 | baseline | 38 | 36 | 0.103397 | 475 | 40 | 0.084211 | 435 | 5 |
| 2023 | chronological | 38 | 37 | 0.054318 | 796 | 37 | 0.046482 | 759 | 5 |

Window precision equals the existing annual evaluation. Recall is not equalized between
arms or years. Hit episodes can exceed alarmed positive runs because one positive run can
overlap several alarm episodes.

## Interpretation

- Episode precision is below window precision. For the baseline in 2014 it is 0.097668
  against 0.135905; in 2023 it is 0.084211 against 0.103397. Positive windows cluster in
  few runs, while false alarms arrive as many separate short episodes.
- Almost all alarm episodes are all-negative: in 2022 the baseline has 606 of 622, and in 2014
  619 of 686. The median all-negative episode lasts 2 to 7 hours, so the burden is the
  number of alarm starts rather than prolonged alarms.
- Positive runs are almost always alarmed (for example 80 of 83 in 2014 and 51 of 51 in 2015
  for the baseline), but 2017 and 2023 show misses (5 of 6 and 36 of 38). Small positive-run
  counts, such as 7 in 2016, give very uncertain proportions; no intervals were computed.
- The chronological arm creates more episodes than the baseline in every year, so the earlier
  TCN comparison also holds at episode level.
- 2018 has no positive windows. Only the 30 and 49 all-negative episodes are measurable there.

## Limitations

Episode definitions depend on the consecutive-hour rule and on record gaps. The
positive-run recall describes labelled windows, not physical flare detection. The numbers are
adaptive historical evidence after repeated inspection, not an independent test, and the
analysis cannot show that a different grouping or suppression rule would help. Adding an alarm
cooldown or merging episodes would be a new protocol with a frozen rule before any look at results.

## Reproduction

```sh
export PYTHONPATH=. PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_alarm_episodes.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/alarm_episodes_20261107_r2
"$PY" -m pytest tests/test_alarm_episodes_audit.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r4
```

Source hash of the produced `report.json`: `9d6b5c02d370f0b08ecc0dc3083d2df88d65a39469907077192666b143306788`. Use new output names for reruns.
Generated artifacts stay outside Git. The paired Turkish edition covers the same findings
and limits.
