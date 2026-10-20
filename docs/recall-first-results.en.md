# Helio24: recall-first fourth experiment

User objective: recall ≥95%, while reducing false alarms at that level.
The development objectives were not all met. Candidate for analysis: **control**.
Development recall is 95.07%, with 5,183 false-positive windows, a 0.00%
reduction relative to control. Applying the previous period's threshold
unchanged gives 95.63% recall and 5,345 false positives.
These two thresholds answer different questions.

## Experiment scope and limitations

Eight preregistered XGBoost candidates were actually retrained. Training:
partitions 1–2 (159,247 windows); sigmoid calibration and transfer threshold:
partition 3 (41,470 windows); comparison: partition 4 (50,631 windows,
1,076 positives, 470 HARPs). Windows whose target horizon crossed a temporal
boundary and shared regions across roles were excluded.
The control exactly reproduced TP=1023, FP=5183, FN=53, TN=44372.

Partition 4 was previously inspected and used for threshold/model selection.
Achieving 95% recall here is not independent test success. Partition-5 features
and predictions and the reserved 2024–2025 data were not opened. The transfer
threshold was selected on the same partition-3 samples as calibration and
was not adjusted on partition 4. However, candidates were compared on
partition 4, so transfer performance is not a final independent test either.
The dashboard model was not automatically replaced. V2 compatibility remains unresolved.

FP and FN count **overlapping forecast windows**, not independent flares or
alerts. A 95% window recall does not guarantee detection of 95% of flares.

## Targets and results

There is no universal “correct metric range.” Recall 95% is the user target;
10% fewer FP is a project improvement target. Higher AP and lower Brier/log
loss are preferred and compared against control. No accuracy cutoff was set:
always predicting quiet achieves 97.87% accuracy here while missing every positive.
Table rates use a 0–1 scale. Precision is the proportion of correct alarms;
FPR=FP/(FP+TN), FAR=FP/(TP+FP). AP measures threshold-independent ranking;
Brier and log loss measure probability error. Reliability bins are saved separately.

## Target comparison

| Metric | Target | Control | Candidate |
| --- | --- | --- | --- |
| Recall | >= 0.95 | 0.950743 | 0.950743 |
| False-positive windows | < 5183; stretch target <= 4664 | 5183.000000 | 5183.000000 |
| Average precision (AP) | >= 0.471980 | 0.471980 | 0.471980 |
| Brier score | <= 0.014832 | 0.014832 | 0.014832 |
| Log loss | <= 0.052204 | 0.052204 | 0.052204 |

## All candidates: 95% recall threshold selected on validation

| model | recall | precision | fp | fn | accuracy | balanced_accuracy | f1 | false_positive_rate | false_alarm_ratio | tss | average_precision | brier | log_loss | threshold | tp | tn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control | 0.950743 | 0.164840 | 5183 | 53 | 0.896585 | 0.923076 | 0.280967 | 0.104591 | 0.835160 | 0.846153 | 0.471980 | 0.014832 | 0.052204 | 0.034028 | 1023 | 44372 |
| shallow | 0.950743 | 0.160269 | 5360 | 53 | 0.893089 | 0.921290 | 0.274300 | 0.108163 | 0.839731 | 0.842581 | 0.438157 | 0.015196 | 0.053278 | 0.034028 | 1023 | 44195 |
| region_weight | 0.950743 | 0.152687 | 5677 | 53 | 0.886828 | 0.918092 | 0.263117 | 0.114560 | 0.847313 | 0.836184 | 0.413685 | 0.015604 | 0.054672 | 0.031723 | 1023 | 43878 |
| regularized | 0.950743 | 0.150198 | 5788 | 53 | 0.884636 | 0.916972 | 0.259414 | 0.116800 | 0.849802 | 0.833944 | 0.410609 | 0.015544 | 0.055120 | 0.028132 | 1023 | 43767 |
| depth4 | 0.950743 | 0.146018 | 5983 | 53 | 0.880784 | 0.915004 | 0.253155 | 0.120735 | 0.853982 | 0.830009 | 0.396946 | 0.015700 | 0.055452 | 0.028384 | 1023 | 43572 |
| positive_weight | 0.950743 | 0.142638 | 6149 | 53 | 0.877506 | 0.913330 | 0.248060 | 0.124084 | 0.857362 | 0.826659 | 0.399509 | 0.015655 | 0.055300 | 0.026154 | 1023 | 43406 |
| depth5 | 0.950743 | 0.133099 | 6663 | 53 | 0.867354 | 0.908143 | 0.233508 | 0.134457 | 0.866901 | 0.816287 | 0.399161 | 0.015878 | 0.057103 | 0.021411 | 1023 | 42892 |
| depth6 | 0.950743 | 0.128728 | 6924 | 53 | 0.862199 | 0.905510 | 0.226754 | 0.139724 | 0.871272 | 0.811020 | 0.410709 | 0.015753 | 0.057661 | 0.021067 | 1023 | 42631 |

## Transfer of the previous period's 95% threshold

| model | recall | precision | fp | fn | accuracy | balanced_accuracy | f1 | false_positive_rate | false_alarm_ratio | tss | average_precision | brier | log_loss | threshold | tp | tn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control | 0.956320 | 0.161437 | 5345 | 47 | 0.893504 | 0.924230 | 0.276242 | 0.107860 | 0.838563 | 0.848460 | 0.471980 | 0.014832 | 0.052204 | 0.031960 | 1029 | 44210 |
| shallow | 0.961896 | 0.153174 | 5722 | 41 | 0.886176 | 0.923214 | 0.264267 | 0.115468 | 0.846826 | 0.846428 | 0.438157 | 0.015196 | 0.053278 | 0.030047 | 1035 | 43833 |
| depth4 | 0.955390 | 0.143415 | 6140 | 48 | 0.877782 | 0.915744 | 0.249393 | 0.123903 | 0.856585 | 0.831488 | 0.396946 | 0.015700 | 0.055452 | 0.026855 | 1028 | 43415 |
| depth5 | 0.932156 | 0.140772 | 6122 | 73 | 0.877644 | 0.904308 | 0.244604 | 0.123540 | 0.859228 | 0.808617 | 0.399161 | 0.015878 | 0.057103 | 0.025696 | 1003 | 43433 |
| depth6 | 0.964684 | 0.123088 | 7395 | 38 | 0.853193 | 0.907728 | 0.218319 | 0.149228 | 0.876912 | 0.815456 | 0.410709 | 0.015753 | 0.057661 | 0.018753 | 1038 | 42160 |
| regularized | 0.964684 | 0.145358 | 6103 | 38 | 0.878711 | 0.920764 | 0.252647 | 0.123156 | 0.854642 | 0.841528 | 0.410609 | 0.015544 | 0.055120 | 0.025214 | 1038 | 43452 |
| positive_weight | 0.953532 | 0.142362 | 6181 | 50 | 0.876933 | 0.914401 | 0.247736 | 0.124730 | 0.857638 | 0.828802 | 0.399509 | 0.015655 | 0.055300 | 0.025892 | 1026 | 43374 |
| region_weight | 0.950743 | 0.152687 | 5677 | 53 | 0.886828 | 0.918092 | 0.263117 | 0.114560 | 0.847313 | 0.836184 | 0.413685 | 0.015604 | 0.054672 | 0.031712 | 1023 | 43878 |

## Preregistered acceptance checks

| model | promising | stretch_target | false_alarm_reduction | failed_checks |
| --- | --- | --- | --- | --- |
| control | False | False | 0.000000 | fewer_false_alarms |
| shallow | False | False | -0.034150 | fewer_false_alarms, ap_noninferior, brier_noninferior, log_loss_noninferior |
| region_weight | False | False | -0.095312 | fewer_false_alarms, ap_noninferior, brier_noninferior, log_loss_noninferior |
| regularized | False | False | -0.116728 | fewer_false_alarms, ap_noninferior, brier_noninferior, log_loss_noninferior |
| depth4 | False | False | -0.154351 | fewer_false_alarms, ap_noninferior, brier_noninferior, log_loss_noninferior |
| positive_weight | False | False | -0.186379 | fewer_false_alarms, ap_noninferior, brier_noninferior, log_loss_noninferior |
| depth5 | False | False | -0.285549 | fewer_false_alarms, ap_noninferior, brier_noninferior, log_loss_noninferior |
| depth6 | False | False | -0.335906 | fewer_false_alarms, ap_noninferior, brier_noninferior, log_loss_noninferior |

## HARP-cluster bootstrap: conditional 95% intervals

| model | threshold_role | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| control | development | recall | 0.890093 | 0.987532 | 1000 | 0 |
| control | development | precision | 0.094194 | 0.237715 | 1000 | 0 |
| control | development | false_positive_rate | 0.076441 | 0.132258 | 1000 | 0 |
| control | development | false_alarm_ratio | 0.762285 | 0.905806 | 1000 | 0 |
| control | development | brier | 0.009232 | 0.021252 | 1000 | 0 |
| control | calibration_transfer | recall | 0.898343 | 0.989275 | 1000 | 0 |
| control | calibration_transfer | precision | 0.092405 | 0.233067 | 1000 | 0 |
| control | calibration_transfer | false_positive_rate | 0.079075 | 0.136038 | 1000 | 0 |
| control | calibration_transfer | false_alarm_ratio | 0.766933 | 0.907595 | 1000 | 0 |
| control | calibration_transfer | brier | 0.009232 | 0.021252 | 1000 | 0 |

## Uncertainty and next step

Bootstrap resamples whole HARP regions 1,000 times. Thresholds are fixed;
intervals exclude training, model-selection and threshold-selection
uncertainty. Differences between candidates' intervals must not be read
as a statistical significance test.

The preregistered eight-candidate budget is complete. Failed candidates were
retained; the same validation period was not searched indefinitely until a
target was reached. The next evaluation should use the reserved later period,
after compatibility is verified and all choices are frozen. Development
results alone do not support live deployment or a claim of 95% future recall.

## Reproduction and outputs

Protocol: `docs/fourth-experiment-protocol.md`.
Training: `.venv/bin/python scripts/run_recall_experiment.py` (refuses to overwrite).
Reporting: `.venv/bin/python scripts/report_recall_experiment.py`.
Local `artifacts/experiment4/` holds eight models, raw/calibrated probabilities,
all 90%/95%/99% operating points, reliability bins, split audit, bootstrap
and source SHA-256 hashes. Data, models and large outputs are not committed;
the traceable report and code are version controlled.
