# Proje çalışma noktasında tam metrikler (2026-11-09)

## Amaç ve kapsam

Bu rapor, donmuş yıllık V2 baseline için her proje metriğini
[operating-point-decision-20261109.tr.md](operating-point-decision-20261109.tr.md) belgesinde tanımlanan çalışma
noktasında listeler: önceki kalibrasyon yılında pencere recall 0,90'da seçilen ve sonraki yıla değiştirilmeden
uygulanan eşik. Betimleyicidir. Hiçbir model, eşik, etiket veya özellik değişmedi ve ayrılmış 2024–2025 testine
erişilmedi. Donmuş tanım [`config/full-metrics-v1.json`](../config/full-metrics-v1.json) dosyasındadır.

Baseline, özgün 96 özellikli topluluktur (0,45 lojistik + 0,55 XGBoost, sigmoid kalibrasyonlu) ve 2014, 2015, 2016,
2017, 2022 ve 2023 geliştirme yıllarında değerlendirilmiştir. 2018'de sıfır pozitif vardır ve raporlanmaz.

## Sayımlar

| year | pencere | pozitif pencere | TP | FP | FN | TN |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 75228 | 2310 | 2007 | 7634 | 303 | 65284 |
| 2015 | 69138 | 1355 | 1308 | 6294 | 47 | 61489 |
| 2016 | 42987 | 181 | 162 | 1303 | 19 | 41503 |
| 2017 | 19529 | 253 | 235 | 1035 | 18 | 18241 |
| 2022 | 50756 | 421 | 414 | 8949 | 7 | 41386 |
| 2023 | 60366 | 781 | 653 | 4852 | 128 | 54733 |

## Eşik metrikleri

| year | eşik | accuracy | hep-negatif accuracy | recall | precision | F1 | balanced accuracy | FPR | FAR | TSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.0324 | 0.8945 | 0.9693 | 0.8688 | 0.2082 | 0.3359 | 0.8821 | 0.1047 | 0.7918 | 0.7641 |
| 2015 | 0.0407 | 0.9083 | 0.9804 | 0.9653 | 0.1721 | 0.2921 | 0.9362 | 0.0929 | 0.8279 | 0.8725 |
| 2016 | 0.0539 | 0.9692 | 0.9958 | 0.8950 | 0.1106 | 0.1968 | 0.9323 | 0.0304 | 0.8894 | 0.8646 |
| 2017 | 0.0219 | 0.9461 | 0.9870 | 0.9289 | 0.1850 | 0.3086 | 0.9376 | 0.0537 | 0.8150 | 0.8752 |
| 2022 | 0.0110 | 0.8235 | 0.9917 | 0.9834 | 0.0442 | 0.0846 | 0.9028 | 0.1778 | 0.9558 | 0.8056 |
| 2023 | 0.0242 | 0.9175 | 0.9871 | 0.8361 | 0.1186 | 0.2078 | 0.8773 | 0.0814 | 0.8814 | 0.7547 |

## Olasılık ve sıralama metrikleri

| year | yaygınlık | AP | ROC AUC | Brier | log loss |
| --- | --- | --- | --- | --- | --- |
| 2014 | 0.0307 | 0.5079 | 0.9498 | 0.0207 | 0.0765 |
| 2015 | 0.0196 | 0.4924 | 0.9781 | 0.0136 | 0.0478 |
| 2016 | 0.0042 | 0.3664 | 0.9899 | 0.0033 | 0.0145 |
| 2017 | 0.0130 | 0.8117 | 0.9891 | 0.0049 | 0.0205 |
| 2022 | 0.0083 | 0.2800 | 0.9698 | 0.0071 | 0.0292 |
| 2023 | 0.0129 | 0.2206 | 0.9509 | 0.0112 | 0.0440 |

## %95 aralıkları

Tüm-HARP bootstrap, 1000 çekiliş, tohum 24, eşik sabit. Aralıklar model yeniden uydurma belirsizliğini ve tüm
güneş döngüsü kaymalarını içermez.

| year | recall | precision | F1 | balanced accuracy | FPR | FAR | TSS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.7722–0.9283 | 0.1327–0.2868 | 0.2278–0.4372 | 0.8352–0.9154 | 0.0803–0.1303 | 0.7132–0.8673 | 0.6705–0.8308 |
| 2015 | 0.9107–0.9930 | 0.1069–0.2401 | 0.1917–0.3856 | 0.9085–0.9552 | 0.0676–0.1201 | 0.7599–0.8931 | 0.8170–0.9103 |
| 2016 | 0.3182–1.0000 | 0.0122–0.2039 | 0.0235–0.3357 | 0.6497–0.9886 | 0.0163–0.0493 | 0.7961–0.9878 | 0.2995–0.9771 |
| 2017 | 0.7692–1.0000 | 0.0397–0.4693 | 0.0763–0.6227 | 0.8601–0.9800 | 0.0204–0.0946 | 0.5307–0.9603 | 0.7201–0.9601 |
| 2022 | 0.9357–1.0000 | 0.0222–0.0724 | 0.0434–0.1350 | 0.8764–0.9243 | 0.1420–0.2158 | 0.9276–0.9778 | 0.7528–0.8486 |
| 2023 | 0.7245–0.9257 | 0.0765–0.1630 | 0.1367–0.2735 | 0.8209–0.9227 | 0.0605–0.1030 | 0.8370–0.9235 | 0.6418–0.8454 |

## Altı yılın ağırlıksız ortalaması

| metrik | ortalama |
| --- | --- |
| accuracy | 0.9099 |
| recall | 0.9129 |
| precision | 0.1398 |
| f1 | 0.2376 |
| balanced_accuracy | 0.9114 |
| fpr | 0.0902 |
| far | 0.8602 |
| tss | 0.8228 |
| ap | 0.4465 |
| roc_auc | 0.9713 |
| brier | 0.0101 |
| log_loss | 0.0388 |

Ortalama, yaygınlığı farklı altı uyarlanabilir geliştirme yılının özetidir; birleştirilmiş bir tahmin değildir.

## Hedeflere göre durum

- Recall: sunulan 0,8361–0,9834, hedef 0,90; 2014, 2016 ve 2023 hedefin altında kalır.
- Precision: 0,0442–0,2082; önceki 0,30 hedefine hiçbir yılda ulaşılmaz.
- FAR, 1 − precision değeridir (0,7918–0,9558).
- Accuracy her yıl hep-negatif accuracy değerinin altındadır; bu yüzden yararlı bir hedef değildir.
- TSS 0,7547–0,8752, balanced accuracy 0,8773–0,9376 ve ROC AUC 0,9498–0,9899 yüksektir; bunlar precision gibi yaygınlıkla sınırlanmaz.
- AP 0,2206–0,8117 olup yıla çok bağlıdır (2017 en yüksek, 2023 en düşük).
- F1, balanced accuracy, TSS, AP, Brier ve log loss için donmuş kabul eşiği yoktur; yalnızca raporlanırlar.

## Sınırlar

Bunlar zaten incelenmiş uyarlanabilir geliştirme yıllarıdır, bağımsız bir test değildir. Sayılar örtüşen tahmin
pencereleridir, fiziksel patlamalar değildir. Brier ve log loss kalibrasyonu, ayrım gücünü ve veri belirsizliğini
birlikte yansıtır.

## Yeniden üretim

```sh
python -m scripts.audit_full_metrics --output artifacts/full_metrics_20261109_r1
```

Girdiler: `artifacts/temporal_years_20261101_r1` (`predictions.parquet` içindeki baseline sütunu) ve
`artifacts/operating_point_review_20261109_r1/deployable_thresholds.json` (recall hedefi 0.9). Çıktı özetleri
`artifacts/full_metrics_20261109_r1/report.json` içindedir (config sha256 `82366e0b8630a83709be6e9e67317e30a4824f704dcfeb3139244548a82e5f76`, eşik sha256
`bd4594e2ab0e5ebcdc58cc438b59f7a213828fa3dfdd5b5dfb9c7fcb0df3d6c0`). Var olan çıktının üzerine yazılmaz.
