# Precision research: magnetic features and training objectives

Date: 2026-10-27. No candidate met the promotion rule. Validation precision remains 0.079622; recall remains 0.950064. The objective of increasing precision was not achieved in this round.

## Scope and design

The same frozen V2 population was used: training has 484549 windows and 8698
positives; calibration has 50756 windows and 421 positives; validation has
60366 windows and 781 positives. Training ends before 2022; calibration is
2022; validation is 2023. The reserved 2024–2025 test remained unopened.
The threshold question remains M/X GOES peak in the next 24 hours from a
12-hour observation history. This is development evidence, not a final test.

Catalog event times do not establish when a flare report or retrospective HARP
association became available. That availability is unverified, so event-history
features were excluded. No target, label or future event is used as a feature.

Four sequential bounded searches were recorded before their respective runs:

- `features`: three logistic models append 78 products of 12 signed-log,
  train-standardized mean measurements, with C=0.01, 0.1, 1. One XGBoost
  model appends 72 relative-evolution features: std/(abs(mean)+std),
  delta/(abs(mean)+std), and (last-mean)/(abs(mean)+std) per measurement.
  Zero denominators become missing; ratios are clipped to [-100,100].
- `weighted`: four logistic models use either raw or signed-log features,
  with positive weight 10 or balanced training class weights, and C=1.
- `pool`: 57 probability pools use powers -1, 0, 2 (harmonic, geometric,
  quadratic mean), each with 19 logistic weights from 0.05 through 0.95.
  Each pool receives monotonic sigmoid calibration on calibration data.
- `splines`: three logistic models append training-quantile quadratic spline
  bases for all 24 mean measurements, with 4 knots, constant extrapolation,
  and C=0.01, 0.1, 1. Missing-value imputation, signed-log scales, spline knots
  and standardization fit on training data only.

The 11 newly trained models were each blended with the fixed incumbent using
new-model weights 0.25, 0.5, 0.75, 1.0: 44 candidates plus 57 pools, or 101
new probability combinations in total. All searches include the incumbent.
Candidate selection uses calibration precision at recall >=0.95, then AP,
then candidate ID. The selected candidate alone is compared on validation.
Validation promotion requires higher precision at recall >=0.95, AP no lower,
and Brier/log loss no higher than the incumbent. Thresholds are selected on
validation; the recall target is not relaxed to manufacture precision gains.

## Validation decisions

| experiment | selected_candidate | promote | recall | precision | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| features | incumbent | False | 0.950064 | 0.079622 | 8577 | 0.220619 | 0.011195 | 0.043996 |
| weighted | log_weightbalanced_w0.25 | False | 0.950064 | 0.074289 | 9246 | 0.225415 | 0.011144 | 0.043772 |
| pool | incumbent | False | 0.950064 | 0.079622 | 8577 | 0.220619 | 0.011195 | 0.043996 |
| splines | splines_C0.1_w0.25 | False | 0.950064 | 0.076385 | 8972 | 0.226132 | 0.011134 | 0.043646 |

The weighted candidate tied incumbent calibration precision and won the AP
tie-break, but validation precision fell to 0.074289 with 9246 false positives.
It was rejected despite slightly better AP and probability error. Improving
AP or calibration alone does not establish better precision at 95% recall.
The spline candidate improved calibration precision to 0.092764, but validation
precision was 0.076385 with 8972 false positives, so it was also rejected.

## Selected operating point

| metric | incumbent | selected |
| --- | --- | --- |
| precision | 0.079622 | 0.079622 |
| recall | 0.950064 | 0.950064 |
| tp | 742.000000 | 742.000000 |
| fp | 8577.000000 | 8577.000000 |
| fn | 39.000000 | 39.000000 |
| tn | 51008.000000 | 51008.000000 |
| accuracy | 0.857271 | 0.857271 |
| balanced_accuracy | 0.903059 | 0.903059 |
| f1 | 0.146931 | 0.146931 |
| false_positive_rate | 0.143946 | 0.143946 |
| false_alarm_ratio | 0.920378 | 0.920378 |
| tss | 0.806118 | 0.806118 |
| average_precision | 0.220619 | 0.220619 |
| brier | 0.011195 | 0.011195 |
| log_loss | 0.043996 | 0.043996 |
| threshold | 0.009311 | 0.009311 |

## Every calibration candidate

| experiment | candidate | recall | precision | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| features | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| features | interactions_C0.01_w0.25 | 0.950119 | 0.087203 | 4187 | 0.295043 | 0.006923 | 0.027491 |
| features | interactions_C0.01_w0.5 | 0.950119 | 0.082610 | 4442 | 0.296392 | 0.006881 | 0.027313 |
| features | interactions_C0.01_w0.75 | 0.950119 | 0.082491 | 4449 | 0.296129 | 0.006858 | 0.027222 |
| features | interactions_C0.01_w1 | 0.950119 | 0.076409 | 4835 | 0.294546 | 0.006856 | 0.027215 |
| features | interactions_C0.1_w0.25 | 0.950119 | 0.087758 | 4158 | 0.296315 | 0.006917 | 0.027500 |
| features | interactions_C0.1_w0.5 | 0.950119 | 0.082169 | 4468 | 0.297144 | 0.006872 | 0.027352 |
| features | interactions_C0.1_w0.75 | 0.950119 | 0.077760 | 4744 | 0.296653 | 0.006850 | 0.027313 |
| features | interactions_C0.1_w1 | 0.950119 | 0.071531 | 5192 | 0.293992 | 0.006851 | 0.027390 |
| features | interactions_C1_w0.25 | 0.950119 | 0.088378 | 4126 | 0.292832 | 0.006936 | 0.027608 |
| features | interactions_C1_w0.5 | 0.950119 | 0.081202 | 4526 | 0.290065 | 0.006913 | 0.027573 |
| features | interactions_C1_w0.75 | 0.950119 | 0.073719 | 5026 | 0.284757 | 0.006916 | 0.027667 |
| features | interactions_C1_w1 | 0.950119 | 0.065617 | 5696 | 0.278303 | 0.006945 | 0.027923 |
| features | relative_xgb_w0.25 | 0.950119 | 0.084728 | 4321 | 0.281584 | 0.007004 | 0.027766 |
| features | relative_xgb_w0.5 | 0.950119 | 0.082833 | 4429 | 0.272262 | 0.007035 | 0.027831 |
| features | relative_xgb_w0.75 | 0.950119 | 0.072926 | 5085 | 0.258229 | 0.007078 | 0.027984 |
| features | relative_xgb_w1 | 0.950119 | 0.067317 | 5542 | 0.240254 | 0.007132 | 0.028266 |
| weighted | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| weighted | raw_weight10_w0.25 | 0.950119 | 0.088086 | 4141 | 0.276892 | 0.007035 | 0.028045 |
| weighted | raw_weight10_w0.5 | 0.950119 | 0.089546 | 4067 | 0.261508 | 0.007123 | 0.028458 |
| weighted | raw_weight10_w0.75 | 0.950119 | 0.089087 | 4090 | 0.239397 | 0.007249 | 0.029050 |
| weighted | raw_weight10_w1 | 0.950119 | 0.078709 | 4682 | 0.220968 | 0.007413 | 0.029896 |
| weighted | raw_weightbalanced_w0.25 | 0.950119 | 0.089465 | 4071 | 0.269442 | 0.007062 | 0.028131 |
| weighted | raw_weightbalanced_w0.5 | 0.950119 | 0.088203 | 4135 | 0.234322 | 0.007197 | 0.028690 |
| weighted | raw_weightbalanced_w0.75 | 0.950119 | 0.086730 | 4212 | 0.207230 | 0.007388 | 0.029516 |
| weighted | raw_weightbalanced_w1 | 0.950119 | 0.079239 | 4648 | 0.187431 | 0.007636 | 0.030787 |
| weighted | log_weight10_w0.25 | 0.950119 | 0.088437 | 4123 | 0.299929 | 0.006923 | 0.027333 |
| weighted | log_weight10_w0.5 | 0.950119 | 0.089047 | 4092 | 0.306264 | 0.006888 | 0.027061 |
| weighted | log_weight10_w0.75 | 0.950119 | 0.084477 | 4335 | 0.300137 | 0.006879 | 0.026945 |
| weighted | log_weight10_w1 | 0.950119 | 0.079888 | 4607 | 0.289394 | 0.006895 | 0.027019 |
| weighted | log_weightbalanced_w0.25 | 0.950119 | 0.090662 | 4012 | 0.301798 | 0.006914 | 0.027192 |
| weighted | log_weightbalanced_w0.5 | 0.950119 | 0.087873 | 4152 | 0.303870 | 0.006883 | 0.026879 |
| weighted | log_weightbalanced_w0.75 | 0.950119 | 0.084567 | 4330 | 0.293634 | 0.006891 | 0.026797 |
| weighted | log_weightbalanced_w1 | 0.950119 | 0.076614 | 4821 | 0.275800 | 0.006940 | 0.027022 |
| pool | power-1_w0.05 | 0.950119 | 0.063776 | 5872 | 0.254117 | 0.007084 | 0.028159 |
| pool | power-1_w0.1 | 0.950119 | 0.064714 | 5781 | 0.262645 | 0.007061 | 0.028070 |
| pool | power-1_w0.15 | 0.950119 | 0.065136 | 5741 | 0.269507 | 0.007047 | 0.028018 |
| pool | power-1_w0.2 | 0.950119 | 0.066192 | 5643 | 0.274377 | 0.007037 | 0.027987 |
| pool | power-1_w0.25 | 0.950119 | 0.066878 | 5581 | 0.277806 | 0.007030 | 0.027972 |
| pool | power-1_w0.3 | 0.950119 | 0.067602 | 5517 | 0.280055 | 0.007026 | 0.027968 |
| pool | power-1_w0.35 | 0.950119 | 0.069979 | 5316 | 0.282147 | 0.007023 | 0.027973 |
| pool | power-1_w0.4 | 0.950119 | 0.070922 | 5240 | 0.283289 | 0.007022 | 0.027986 |
| pool | power-1_w0.45 | 0.950119 | 0.074060 | 5001 | 0.284024 | 0.007022 | 0.028005 |
| pool | power-1_w0.5 | 0.950119 | 0.076176 | 4851 | 0.284296 | 0.007023 | 0.028031 |
| pool | power-1_w0.55 | 0.950119 | 0.078232 | 4713 | 0.284155 | 0.007025 | 0.028063 |
| pool | power-1_w0.6 | 0.950119 | 0.079554 | 4628 | 0.284846 | 0.007028 | 0.028101 |
| pool | power-1_w0.65 | 0.950119 | 0.083005 | 4419 | 0.284032 | 0.007032 | 0.028146 |
| pool | power-1_w0.7 | 0.950119 | 0.083963 | 4364 | 0.283854 | 0.007037 | 0.028199 |
| pool | power-1_w0.75 | 0.950119 | 0.083752 | 4376 | 0.283091 | 0.007043 | 0.028260 |
| pool | power-1_w0.8 | 0.950119 | 0.082389 | 4455 | 0.281971 | 0.007051 | 0.028333 |
| pool | power-1_w0.85 | 0.950119 | 0.079554 | 4628 | 0.280275 | 0.007060 | 0.028421 |
| pool | power-1_w0.9 | 0.950119 | 0.076775 | 4810 | 0.279571 | 0.007071 | 0.028532 |
| pool | power-1_w0.95 | 0.950119 | 0.076438 | 4833 | 0.278703 | 0.007086 | 0.028685 |
| pool | power0_w0.05 | 0.950119 | 0.063462 | 5903 | 0.247614 | 0.007099 | 0.028208 |
| pool | power0_w0.1 | 0.950119 | 0.064000 | 5850 | 0.256876 | 0.007077 | 0.028101 |
| pool | power0_w0.15 | 0.950119 | 0.065125 | 5742 | 0.264783 | 0.007058 | 0.028009 |
| pool | power0_w0.2 | 0.950119 | 0.067465 | 5529 | 0.270619 | 0.007043 | 0.027934 |
| pool | power0_w0.25 | 0.950119 | 0.071212 | 5217 | 0.276758 | 0.007032 | 0.027875 |
| pool | power0_w0.3 | 0.950119 | 0.072820 | 5093 | 0.280900 | 0.007024 | 0.027832 |
| pool | power0_w0.35 | 0.950119 | 0.076555 | 4825 | 0.283624 | 0.007019 | 0.027806 |
| pool | power0_w0.4 | 0.950119 | 0.082884 | 4426 | 0.285649 | 0.007016 | 0.027796 |
| pool | power0_w0.45 | 0.950119 | 0.086843 | 4206 | 0.286572 | 0.007016 | 0.027802 |
| pool | power0_w0.5 | 0.950119 | 0.087070 | 4194 | 0.287466 | 0.007018 | 0.027824 |
| pool | power0_w0.55 | 0.950119 | 0.085324 | 4288 | 0.287449 | 0.007022 | 0.027863 |
| pool | power0_w0.6 | 0.950119 | 0.087051 | 4195 | 0.286879 | 0.007028 | 0.027918 |
| pool | power0_w0.65 | 0.950119 | 0.087758 | 4158 | 0.286741 | 0.007035 | 0.027990 |
| pool | power0_w0.7 | 0.950119 | 0.087298 | 4182 | 0.285859 | 0.007043 | 0.028077 |
| pool | power0_w0.75 | 0.950119 | 0.087260 | 4184 | 0.283985 | 0.007052 | 0.028182 |
| pool | power0_w0.8 | 0.950119 | 0.083875 | 4369 | 0.282889 | 0.007062 | 0.028304 |
| pool | power0_w0.85 | 0.950119 | 0.080080 | 4595 | 0.281592 | 0.007073 | 0.028443 |
| pool | power0_w0.9 | 0.950119 | 0.077071 | 4790 | 0.280898 | 0.007084 | 0.028600 |
| pool | power0_w0.95 | 0.950119 | 0.075572 | 4893 | 0.278692 | 0.007096 | 0.028776 |
| pool | power2_w0.05 | 0.950119 | 0.076731 | 4813 | 0.245892 | 0.007105 | 0.028064 |
| pool | power2_w0.1 | 0.950119 | 0.081766 | 4492 | 0.254424 | 0.007086 | 0.027924 |
| pool | power2_w0.15 | 0.950119 | 0.084818 | 4316 | 0.263052 | 0.007070 | 0.027830 |
| pool | power2_w0.2 | 0.950119 | 0.086730 | 4212 | 0.270676 | 0.007057 | 0.027766 |
| pool | power2_w0.25 | 0.950119 | 0.086151 | 4243 | 0.275745 | 0.007047 | 0.027722 |
| pool | power2_w0.3 | 0.950119 | 0.087912 | 4150 | 0.278719 | 0.007039 | 0.027695 |
| pool | power2_w0.35 | 0.950119 | 0.089008 | 4094 | 0.280964 | 0.007034 | 0.027682 |
| pool | power2_w0.4 | 0.950119 | 0.088692 | 4110 | 0.283429 | 0.007031 | 0.027682 |
| pool | power2_w0.45 | 0.950119 | 0.088281 | 4131 | 0.285209 | 0.007029 | 0.027693 |
| pool | power2_w0.5 | 0.950119 | 0.087893 | 4151 | 0.286716 | 0.007030 | 0.027715 |
| pool | power2_w0.55 | 0.950119 | 0.087241 | 4185 | 0.287643 | 0.007032 | 0.027748 |
| pool | power2_w0.6 | 0.950119 | 0.087203 | 4187 | 0.287272 | 0.007035 | 0.027792 |
| pool | power2_w0.65 | 0.950119 | 0.085985 | 4252 | 0.287152 | 0.007040 | 0.027848 |
| pool | power2_w0.7 | 0.950119 | 0.086412 | 4229 | 0.286878 | 0.007046 | 0.027918 |
| pool | power2_w0.75 | 0.950119 | 0.086505 | 4224 | 0.286339 | 0.007054 | 0.028004 |
| pool | power2_w0.8 | 0.950119 | 0.085892 | 4257 | 0.285605 | 0.007062 | 0.028109 |
| pool | power2_w0.85 | 0.950119 | 0.083595 | 4385 | 0.283981 | 0.007073 | 0.028239 |
| pool | power2_w0.9 | 0.950119 | 0.082321 | 4459 | 0.282385 | 0.007084 | 0.028404 |
| pool | power2_w0.95 | 0.950119 | 0.080499 | 4569 | 0.280232 | 0.007096 | 0.028626 |
| pool | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| splines | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| splines | splines_C0.01_w0.25 | 0.950119 | 0.091659 | 3964 | 0.286524 | 0.006982 | 0.027530 |
| splines | splines_C0.01_w0.5 | 0.950119 | 0.090539 | 4018 | 0.278403 | 0.007003 | 0.027471 |
| splines | splines_C0.01_w0.75 | 0.950119 | 0.090868 | 4002 | 0.267763 | 0.007047 | 0.027561 |
| splines | splines_C0.01_w1 | 0.950119 | 0.084656 | 4325 | 0.256863 | 0.007115 | 0.027811 |
| splines | splines_C0.1_w0.25 | 0.950119 | 0.092764 | 3912 | 0.287122 | 0.006968 | 0.027489 |
| splines | splines_C0.1_w0.5 | 0.950119 | 0.089827 | 4053 | 0.278454 | 0.006981 | 0.027395 |
| splines | splines_C0.1_w0.75 | 0.950119 | 0.088968 | 4096 | 0.268132 | 0.007023 | 0.027459 |
| splines | splines_C0.1_w1 | 0.950119 | 0.082867 | 4427 | 0.258141 | 0.007093 | 0.027698 |
| splines | splines_C1_w0.25 | 0.950119 | 0.092700 | 3915 | 0.286699 | 0.006969 | 0.027506 |
| splines | splines_C1_w0.5 | 0.950119 | 0.089626 | 4063 | 0.276757 | 0.006984 | 0.027426 |
| splines | splines_C1_w0.75 | 0.950119 | 0.088849 | 4102 | 0.266313 | 0.007030 | 0.027507 |
| splines | splines_C1_w1 | 0.950119 | 0.082355 | 4457 | 0.256705 | 0.007107 | 0.027768 |

## Uncertainty and limits

| experiment | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- |
| features | recall | 0.877975 | 0.997118 | 1000 | 0 |
| features | precision | 0.051430 | 0.111802 | 1000 | 0 |
| features | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| features | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| features | brier | 0.007289 | 0.015279 | 1000 | 0 |
| weighted | recall | 0.877975 | 0.997118 | 1000 | 0 |
| weighted | precision | 0.048201 | 0.103818 | 1000 | 0 |
| weighted | false_positive_rate | 0.124852 | 0.185657 | 1000 | 0 |
| weighted | false_alarm_ratio | 0.896182 | 0.951799 | 1000 | 0 |
| weighted | brier | 0.007238 | 0.015226 | 1000 | 0 |
| pool | recall | 0.877975 | 0.997118 | 1000 | 0 |
| pool | precision | 0.051430 | 0.111802 | 1000 | 0 |
| pool | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| pool | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| pool | brier | 0.007289 | 0.015279 | 1000 | 0 |
| splines | recall | 0.877975 | 0.997118 | 1000 | 0 |
| splines | precision | 0.049479 | 0.107089 | 1000 | 0 |
| splines | false_positive_rate | 0.120559 | 0.180430 | 1000 | 0 |
| splines | false_alarm_ratio | 0.892911 | 0.950521 | 1000 | 0 |
| splines | brier | 0.007248 | 0.015181 | 1000 | 0 |

These are conditional 95% HARP-cluster bootstrap intervals from 1000 draws,
seed 24. They hold model and threshold fixed, excluding training, calibration,
model-selection and threshold-selection uncertainty. FP/TP/FN count overlapping
windows rather than independent flares or operational alerts. Precision still
measures the fraction of alarm windows that are truly positive.

Calibration was reused for probability fitting and candidate selection, and
previous development results influenced these new designs. Thus the process
is adaptive; neither calibration nor validation results are independent final
tests. More searches can overfit development data. Lack of improvement does
not prove a theoretical ceiling, nor does the current point estimate guarantee
future recall. The historical V1 precision 0.164840 uses a different population
and cannot serve as a matched before/after comparison.

## Reproduction and provenance

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py --protocol config/precision-features-v1.json --output artifacts/precision_features_20261027_r1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py --protocol config/precision-weighted-v1.json --output artifacts/precision_weighted_20261027_r1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_pool.py --output artifacts/precision_pool_20261027_r1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py --protocol config/precision-splines-v1.json --output artifacts/precision_splines_20261027_r1
.venv/bin/python scripts/report_precision_features.py --output artifacts/precision_features_summary_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_precision_features_20261027
```

Existing outputs are protected. Repeat with fresh output paths and corresponding
report input paths; this reporting script uses the dated inputs shown above.
Review both Markdown editions and register their source hash before publishing
changed content. The frozen model selection remains development-only; dashboard
models are not automatically replaced. Dataset/model/generated artifacts remain
outside Git, and local Streamlit branding changes remain uncommitted.

| source | SHA-256 |
| --- | --- |
| artifacts/precision_features_20261027_r1/report.json | 1bbce1f2326cf89295c386d51c118c5115eb059aa05286bce0ed934091cffbab |
| artifacts/precision_features_20261027_r1/calibration_candidates.csv | 68549b611fe28a42053be57d27ad256620c23678856cd412974f665b59736a64 |
| artifacts/precision_features_20261027_r1/validation_predictions.parquet | 615de72ac7bf51ab9436d7b790755c222635a2b893caa785b9ddd9e60757a445 |
| artifacts/precision_weighted_20261027_r1/report.json | 2303cfac286319fc0ed32e7c2319ec36d2b585870726353fdc97353477745599 |
| artifacts/precision_weighted_20261027_r1/calibration_candidates.csv | 7cafc40dd94c1812cd9f9d0e6514a82e1bc01b9415781fb8ae28fc73c7873046 |
| artifacts/precision_weighted_20261027_r1/validation_predictions.parquet | 2c53baf189ae28c917b92e7feb2bfabfcbaf50d6b9464ae696883080894e4835 |
| artifacts/precision_pool_20261027_r1/report.json | f32a27b4acb519b4466c765ff284f0deaeb64d85fa3556b8f176c32dc20b685f |
| artifacts/precision_pool_20261027_r1/calibration_candidates.csv | 0937f4d3b96be3310b3cdb4bf8d5f281cff71bfc71ea9f232b9009e6e045cb3f |
| artifacts/precision_pool_20261027_r1/validation_predictions.parquet | 615de72ac7bf51ab9436d7b790755c222635a2b893caa785b9ddd9e60757a445 |
| artifacts/precision_splines_20261027_r1/report.json | 0e42f80efa8deaa2a3559c7c3ad5d2f9c85db1aadc002a8e5c205f6d8fb5e892 |
| artifacts/precision_splines_20261027_r1/calibration_candidates.csv | c3f94390148a5f775a1f95d8b6eea6be863fc17bbb16e36be6c1a12db7072fc6 |
| artifacts/precision_splines_20261027_r1/validation_predictions.parquet | 1bc30449a55c77ca9f621ec78a07ede68a49a85764700cf356e2b27ef48b6eb2 |

