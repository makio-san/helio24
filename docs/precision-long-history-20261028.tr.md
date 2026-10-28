# Uzun geçmişli precision deneyi

Kalibrasyonda `incumbent` seçildi. Seçilen aday, geliştirme amaçlı tanısal model değiştirme kontrollerinin tamamını geçmedi. Aynı recall düzeyindeki doğrulama
incelemesinde precision değişimi 0.000000 yüzde puan oldu. Dashboard modeli
değiştirilmedi. Bu değerleri uygulama performansı olarak yorumlamadan önce ayrı
sunulan aktarılmış eşik sonuçlarına bakılmalıdır.

## Veri ve özellikler

Tamamlanan özellik hazırlığı, özgün 595671 tahmin anahtarının birebir eşleştiğini doğruladı.
Eğitimde 484549 pencere/8698 pozitif, kalibrasyonda 50756/421, doğrulamada 60366/781 vardır.
Eğitim, 2022 kalibrasyonundan ve 2023 doğrulamasından öncedir. Ayrılmış 2024–2025
gözlemleri ve etiketleri mantıksal okuyucu sınırında dışlandı; bu yılları içeren arşiv
baytları yalnızca bütünlük doğrulaması için indirildi. Etiketler ve korunan tahminler
değiştirilmedi. Özellikler, sonuçlara bağlı satır dışlamalarından bağımsız olarak ham
gözlemleri kullanır. Önceki disk alanı engeli giderildi.

Her 24/48 saatlik geçmiş, 24 manyetik ölçümün ortalamasını, popülasyon standart sapmasını,
uç noktalar arasındaki değişimini ve normalize edilmiş değişimini; ayrıca kapsam/eksiklik
göstergelerini ekler: 196 yeni özellik, toplam 292 özellik. Tam gözlem sıklığı, tahminden
kesinlikle önceki 120/240 gözlemi gerektirir. Veri bölümü sınırını, gözlem boşluğunu veya
artık saniye geçişini aşan geçmişler kullanılamaz; satırlar korunur. Her ölçüm için %80
sonlu değer gerekir. Normalize edilmiş değişim, uç noktalar arasındaki farkı mutlak
ortalama ile standart sapmanın toplamına böler ve [-100, 100] aralığına kırpar; sıfır
payda eksik değer üretir. Kullanılabilirlik zamansal kapsamdır, cihaz kalitesi garantisi değildir.

| role | available_24h | available_48h |
| --- | --- | --- |
| train | 446081 | 378074 |
| calibration | 46861 | 39785 |
| validation | 55856 | 47776 |

## Dondurulmuş arama

Üç aday, işaret koruyan logaritmik lojistik regresyon (C=1), XGBoost (200 ağaç, derinlik 3)
ve histogram tabanlı gradient boosting (200 iterasyon, 15 yaprak) kullanır. Tüm parametreler
ve kaynak özetleri `config/precision-long-history-v2.json` içinde sabitlenmiştir. Ön işleme yalnızca
eğitimde, sigmoid kalibrasyonu kalibrasyon verisinde öğrenilir. 0.25, 0.5, 0.75 ve 1.0
yeni model karışım ağırlıkları, mevcut modele ek 12 aday üretir. Seçim, recall >=0.95
koşulunda kalibrasyon precision değerini, ardından AP değerini ve aday kimliğini kullanır.
Doğrulamada yalnızca seçilen aday değerlendirilir. Mevcut model, 0.45 lojistik/0.55 XGBoost
birleşimi olarak kalır.

| candidate | precision | recall | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| incumbent | 0.090662 | 0.950119 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| history_logistic_w0.25 | 0.087032 | 0.950119 | 4196 | 0.310089 | 0.006871 | 0.027349 |
| history_logistic_w0.5 | 0.087432 | 0.950119 | 4175 | 0.320887 | 0.006799 | 0.027140 |
| history_logistic_w0.75 | 0.085561 | 0.950119 | 4275 | 0.315636 | 0.006768 | 0.027160 |
| history_logistic_w1 | 0.060341 | 0.950119 | 6229 | 0.308453 | 0.006779 | 0.027556 |
| history_xgboost_w0.25 | 0.086040 | 0.950119 | 4249 | 0.296323 | 0.006952 | 0.027592 |
| history_xgboost_w0.5 | 0.082389 | 0.950119 | 4455 | 0.296497 | 0.006940 | 0.027540 |
| history_xgboost_w0.75 | 0.073046 | 0.950119 | 5076 | 0.289074 | 0.006949 | 0.027618 |
| history_xgboost_w1 | 0.064683 | 0.950119 | 5784 | 0.278489 | 0.006978 | 0.027875 |
| history_hist_w0.25 | 0.082372 | 0.950119 | 4456 | 0.291551 | 0.006968 | 0.027668 |
| history_hist_w0.5 | 0.084104 | 0.950119 | 4356 | 0.281037 | 0.006998 | 0.027838 |
| history_hist_w0.75 | 0.080354 | 0.950119 | 4578 | 0.257176 | 0.007072 | 0.028249 |
| history_hist_w1 | 0.065349 | 0.950119 | 5721 | 0.232070 | 0.007192 | 0.028970 |

## Aynı recall düzeyinde geliştirme incelemesi

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

Bu eşikler, recall >=0.95 düzeyinde precision karşılaştırmak için doğrulama etiketleriyle
yeniden seçilir. Kalibrasyondan aktarılmış eşikler değildir. Tanısal model değiştirme
kontrolü, recall >=0.95 koşulunda daha yüksek precision, daha düşük olmayan AP ve daha
yüksek olmayan Brier/log loss gerektirir. Yalnızca bu karşılaştırmayı geçmek, uygulamada
%95 recall sağlayan bir alarm eşiğini kanıtlamaz.

## Yorum ve sonraki geliştirme adımı

Kalibrasyondaki en güçlü yeni aday `history_logistic_w0.5` oldu: precision değeri
0.087432, mevcut modelinki 0.090662; yanlış
pozitif pencere sayıları sırasıyla 4175 ve 4012.
AP değerleri 0.320887 ve 0.286706 oldu.
Dolayısıyla genel sıralamadaki iyileşme, kalibrasyonda hedeflenen yüksek recall çalışma
noktasında daha iyi precision sağlamadı. Bu, uzun geçmişin özünde yararsız olduğunu
kanıtlamaz; denenen belirli adayları ve özetleri eler.

Sonraki araştırma adımı, ek kronolojik geliştirme bölümleridir: alarm eşikleri her erken
kalibrasyon döneminde belirlenip sonraki döneme değiştirilmeden aktarılmalıdır. Yeni ve
geniş bir parametre aramasından önce hem precision hem recall kararlılığı ölçülmelidir.
Her yeni aramanın bütçesi önceden sabitlenmeli ve ayrılmış test korunmalıdır. Bu adım,
bu deney kapsamında yürütülmedi.

## Sabit kalibrasyon eşiklerinin doğrulama sonuçları

| metric | incumbent | selected |
| --- | --- | --- |
| precision | 0.103397 | 0.103397 |
| recall | 0.884763 | 0.884763 |
| tp | 691.000000 | 691.000000 |
| fp | 5992.000000 | 5992.000000 |
| fn | 90.000000 | 90.000000 |
| tn | 53593.000000 | 53593.000000 |
| accuracy | 0.899248 | 0.899248 |
| balanced_accuracy | 0.892100 | 0.892100 |
| f1 | 0.185155 | 0.185155 |
| false_positive_rate | 0.100562 | 0.100562 |
| false_alarm_ratio | 0.896603 | 0.896603 |
| tss | 0.784201 | 0.784201 |
| average_precision | 0.220619 | 0.220619 |
| brier | 0.011195 | 0.011195 |
| log_loss | 0.043996 | 0.043996 |
| threshold | 0.018203 | 0.018203 |

Bu eşikler doğrulama değerlendirmesinden önce kaydedildi ve doğrulama etiketlerine göre
ayarlanmadı. Tablo, seçilen alarm kuralının daha sonraki döneme aktarımını ölçer; recall
0.95 altına düşebilir. Yukarıdaki aynı recall düzeyinde karşılaştırmadan ayrıdır.

## Belirsizlik ve sınırlamalar

| evaluation | model | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| validation_reselected | incumbent | recall | 0.877975 | 0.997118 | 1000 | 0 |
| validation_reselected | incumbent | precision | 0.051430 | 0.111802 | 1000 | 0 |
| validation_reselected | incumbent | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| validation_reselected | incumbent | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| validation_reselected | incumbent | brier | 0.007289 | 0.015279 | 1000 | 0 |
| validation_reselected | selected | recall | 0.877975 | 0.997118 | 1000 | 0 |
| validation_reselected | selected | precision | 0.051430 | 0.111802 | 1000 | 0 |
| validation_reselected | selected | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| validation_reselected | selected | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| validation_reselected | selected | brier | 0.007289 | 0.015279 | 1000 | 0 |
| calibration_transferred | incumbent | recall | 0.792142 | 0.959200 | 1000 | 0 |
| calibration_transferred | incumbent | precision | 0.067199 | 0.143637 | 1000 | 0 |
| calibration_transferred | incumbent | false_positive_rate | 0.076680 | 0.124274 | 1000 | 0 |
| calibration_transferred | incumbent | false_alarm_ratio | 0.856363 | 0.932801 | 1000 | 0 |
| calibration_transferred | incumbent | brier | 0.007289 | 0.015279 | 1000 | 0 |
| calibration_transferred | selected | recall | 0.792142 | 0.959200 | 1000 | 0 |
| calibration_transferred | selected | precision | 0.067199 | 0.143637 | 1000 | 0 |
| calibration_transferred | selected | false_positive_rate | 0.076680 | 0.124274 | 1000 | 0 |
| calibration_transferred | selected | false_alarm_ratio | 0.856363 | 0.932801 | 1000 | 0 |
| calibration_transferred | selected | brier | 0.007289 | 0.015279 | 1000 | 0 |

Aralıklar, eğitilmiş modeller ve eşikler sabitken 24 tohumla bütün HARP'ları örnekleyen
1000 bootstrap tekrarı kullanır. Eğitim, kalibrasyon ve model seçimi belirsizliğini içermez.
Kalibrasyon hem olasılık öğrenimi hem aday seçimi için tekrar kullanılır; önceki doğrulama
bulguları bu deneyi yönlendirdi. Bu uyarlamalı geliştirmedir, bağımsız test değildir.
Sayılar bağımsız patlamaları veya alarm dönemlerini değil, örtüşen tahmin pencerelerini
anlatır. Daha uzun geçmişler belirsiz olay-bölge ilişkilerini çözmez. Gelecekte herhangi
bir precision veya recall düzeyi garanti edilmez. Accuracy tüm tahminler içindeki doğru
tahmin oranıdır; precision alarmlar içindeki pozitiflerin, recall pozitif pencereler
içindeki yakalananların oranıdır. AP eşikler boyunca sıralama başarısını ölçer; daha düşük
Brier/log loss daha iyi olasılıksal puanlama gösterir. Olay sıklığından ve yanlış alarm
maliyetinden bağımsız, evrensel bir kabul edilebilir precision değeri yoktur.

## Yeniden üretim ve kanıt

```sh
.venv/bin/python scripts/materialize_long_history.py --output artifacts/long_history_20261028_r2 --workers 1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-long-history-v2.json --output artifacts/precision_long_history_20261028_r1
.venv/bin/python scripts/report_long_history_precision.py \
  --source artifacts/precision_long_history_20261028_r1 --report-name precision-long-history-20261028
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_precision-long-history-20261028
```

Mevcut çıktılar dondurulmuş olarak korunmalıdır. Yeni çalıştırmada yeni artifact dizinleri
ve belge adları seçilmeli; eğitimden önce yeni hazırlık özeti yeni protokol sürümünde
sabitlenmelidir. İki belge sürümü gözden geçirilmeli, ardından kaynak özeti ve bağlantılar
`docs/reports.json` ve `docs/reports.md` dosyalarına kaydedilmeli, yeni HTML dizinine
yayımlanmalıdır. Ham veri, modeller, tahminler ve üretilen HTML Git dışında kalır.

| source | SHA-256 |
| --- | --- |
| artifacts/precision_long_history_20261028_r1/report.json | 2fb929cda4dc9e39d198d3b3af5b9457f2f1fe3b8ac3d8d47f8d68f4c2cd77db |
| artifacts/precision_long_history_20261028_r1/calibration_candidates.csv | 8d5e44d793e96b742fbf6cff9cc71fcfd3459f9bc276934e82fb7ced090c6ab2 |
| artifacts/precision_long_history_20261028_r1/operating_thresholds.json | 46a82ab336b9934b63d4e0372fd72a9d1c615b9b38de5bd637ad65419f562ce5 |
| artifacts/precision_long_history_20261028_r1/validation_predictions.parquet | 615de72ac7bf51ab9436d7b790755c222635a2b893caa785b9ddd9e60757a445 |
| artifacts/long_history_20261028_r2/report.json | 5764eabdc9463a507b27759481982622fc406b6cabcadd64baf10d4236e51fee |

