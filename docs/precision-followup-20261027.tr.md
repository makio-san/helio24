# Precision takibi: karşılaştırma, deneyler ve belirsizlik

Tarih: 2026-10-27. **Precision, 0.950064 recall düzeyinde 0.079622 olarak kaldı.**
Altı yeni model ve 24 olasılık karışımı kalibrasyonda mevcut modeli geçemedi.
İki deneyde de yeni model seçilmedi. Ayrılmış 2024–2025 testi kapalı kaldı.

## Güncel sayı neden tarihsel sayıdan düşük?

| population | windows | positives | prevalence | recall | FPR | precision |
| --- | --- | --- | --- | --- | --- | --- |
| V1 historical | 50631 | 1076 | 0.021252 | 0.950743 | 0.104591 | 0.164840 |
| V2 incumbent | 60366 | 781 | 0.012938 | 0.950064 | 0.143946 | 0.079622 |

Önceki 0.164840, V1 geliştirme verisinden; güncel 0.079622, 2023 V2 doğrulama
verisinden geliyor. Bunların popülasyonları, özellik hesapları, etiket kapsamı
ve dışlama kuralları farklı. Daha önce bildirilen 0.061597 → 0.079622 artışı,
aynı V2 satırlarında XGBoost ile ensemble karşılaştırmasıydı. Tarihsel V1
sayısını aşmadı. Önceki açıklamalar bu ayrımı yeterince açık yapmadı.

Precision şu eşitliği sağlar:
`recall * prevalence / (recall * prevalence + FPR * (1 - prevalence))`.
V2 pozitif pencere sıklığı daha düşük ve ölçülen FPR daha yüksek. Bu iki terim
sayısal farkı açıklar; gözlemler hangi arşiv, etiket veya modelleme değişikliğinin
buna neden olduğunu kanıtlamaz. Cebirsel bir örnekte, V2 recall ve FPR sabit
tutulup V1 olay sıklığı yerleştirildiğinde precision 0.125347 olur. Bu varsayımsal
bir hesaplamadır, ölçülmüş model sonucu değildir. Gözlenen farkı yalnızca sınıf
dengesizliğiyle açıklamak yeterli değildir.

## Hataların yoğunlaştığı bölgeler

8577 yanlış pozitif pencerenin 2180 tanesi, bu sayıya göre ilk 10 HARP'tadır.
Başka bir gruplama, 6815 tanesinin tutulan doğrulama örnekleminde pozitif
penceresi olmayan HARP'larda bulunduğunu gösterir. Bu, o bölgelerin hiç
patlamadığı anlamına gelmez; dışlanan pencereler ve örneklem dışı olaylar bu
ifadenin kapsamı dışındadır. Bunlar geçmişe dönük hata incelemeleridir; tahmin
girdisi veya zor negatifleri eleme kuralı olarak kullanılamaz. Sayılar bağımsız
patlamaları veya alarm olaylarını değil, örtüşen tahmin pencerelerini sayar.

## Sınırlı deneyler

İşaret koruyan logaritma deneyi; medyanla eksik değer doldurma, eğitim
sütunlarının medyan mutlak büyüklük ölçekleri, işaret koruyan `log1p`,
standartlaştırma ve lojistik regresyonu eğitim verisinde öğrendi. C değerleri
0.1, 1 ve 10 idi. Histogram deneyi HistGradientBoostingClassifier ile 15 veya
31 yaprak, 200 iterasyon, 0.05 öğrenme oranı, 100 minimum yaprak örneği ve
10 L2 düzenlileştirmesi kullandı. Üçüncü histogram adayı 15 yaprakla yalnızca
2018 ve sonrasındaki eğitim tarihlerini kullandı. Rastgele iç doğrulama
bölünmesini önlemek için erken durdurma kapatıldı.

Bu altı modelin her birinde sigmoid kalibrasyonu 2022 verisini kullandı.
Yeni modelin olasılık ağırlığı 0.25, 0.5, 0.75 veya 1.0 idi; kalan ağırlık
sabit mevcut modele verildi. Her sınırlı arama, çalıştırılmadan önce JSON
protokolüne kaydedildi. Seçim recall >= 0.95 düzeyindeki kalibrasyon
precision'ı, ardından AP ve aday kimliğini kullandı. Yalnızca seçilen aday
doğrulamaya geçti; her iki arama da mevcut modeli seçti. Reddedilen adaylar
doğrulama üzerinde aranmadı. Tüm kalibrasyon adayları aşağıda korunuyor.

| experiment | candidate | recall | precision | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| log | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| log | signed_log_C0.1_w0.25 | 0.950119 | 0.088731 | 4108 | 0.299169 | 0.006920 | 0.027359 |
| log | signed_log_C0.1_w0.5 | 0.950119 | 0.089686 | 4060 | 0.309379 | 0.006873 | 0.027081 |
| log | signed_log_C0.1_w0.75 | 0.950119 | 0.087989 | 4146 | 0.314496 | 0.006845 | 0.026924 |
| log | signed_log_C0.1_w1 | 0.950119 | 0.086356 | 4232 | 0.317257 | 0.006835 | 0.026905 |
| log | signed_log_C1_w0.25 | 0.950119 | 0.088613 | 4114 | 0.299178 | 0.006919 | 0.027345 |
| log | signed_log_C1_w0.5 | 0.950119 | 0.089606 | 4064 | 0.309647 | 0.006873 | 0.027066 |
| log | signed_log_C1_w0.75 | 0.950119 | 0.087970 | 4147 | 0.315106 | 0.006844 | 0.026918 |
| log | signed_log_C1_w1 | 0.950119 | 0.086599 | 4219 | 0.317389 | 0.006835 | 0.026919 |
| log | signed_log_C10_w0.25 | 0.950119 | 0.088378 | 4126 | 0.298702 | 0.006919 | 0.027361 |
| log | signed_log_C10_w0.5 | 0.950119 | 0.089226 | 4083 | 0.308675 | 0.006872 | 0.027091 |
| log | signed_log_C10_w0.75 | 0.950119 | 0.087508 | 4171 | 0.314680 | 0.006844 | 0.026950 |
| log | signed_log_C10_w1 | 0.950119 | 0.086263 | 4237 | 0.317655 | 0.006834 | 0.026953 |
| hist | incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| hist | hist15_w0.25 | 0.950119 | 0.088633 | 4113 | 0.279769 | 0.007012 | 0.027771 |
| hist | hist15_w0.5 | 0.950119 | 0.088281 | 4131 | 0.261276 | 0.007075 | 0.027923 |
| hist | hist15_w0.75 | 0.950119 | 0.079036 | 4661 | 0.218524 | 0.007174 | 0.028229 |
| hist | hist15_w1 | 0.950119 | 0.072569 | 5112 | 0.185202 | 0.007309 | 0.028734 |
| hist | hist31_w0.25 | 0.950119 | 0.086806 | 4208 | 0.274914 | 0.007030 | 0.027964 |
| hist | hist31_w0.5 | 0.950119 | 0.086337 | 4233 | 0.246827 | 0.007128 | 0.028340 |
| hist | hist31_w0.75 | 0.950119 | 0.079067 | 4659 | 0.198751 | 0.007276 | 0.028919 |
| hist | hist31_w1 | 0.950119 | 0.070572 | 5268 | 0.161461 | 0.007475 | 0.029793 |
| hist | hist15_recent_w0.25 | 0.950119 | 0.079161 | 4653 | 0.285137 | 0.007040 | 0.029004 |
| hist | hist15_recent_w0.5 | 0.950119 | 0.066401 | 5624 | 0.245625 | 0.007275 | 0.030771 |
| hist | hist15_recent_w0.75 | 0.950119 | 0.055264 | 6838 | 0.128351 | 0.007688 | 0.033388 |
| hist | hist15_recent_w1 | 0.950119 | 0.040912 | 9377 | 0.069388 | 0.008281 | 0.038475 |

## Güncel doğrulama metrikleri

| metric | value |
| --- | --- |
| precision | 0.079622 |
| recall | 0.950064 |
| fp | 8577.000000 |
| fn | 39.000000 |
| tp | 742.000000 |
| tn | 51008.000000 |
| accuracy | 0.857271 |
| balanced_accuracy | 0.903059 |
| f1 | 0.146931 |
| false_positive_rate | 0.143946 |
| false_alarm_ratio | 0.920378 |
| tss | 0.806118 |
| average_precision | 0.220619 |
| brier | 0.011195 |
| log_loss | 0.043996 |
| threshold | 0.009311 |

Geliştirmede model değiştirme kuralı; recall >= 0.95 düzeyinde precision artışı,
AP'nin azalmaması, Brier ve log loss'un artmamasıydı. Hiçbir aday ilk seçim
adımını geçmedi; dondurulmuş ensemble ve eşik seçili kaldı. Mevcut dashboard'ın
kullandığı model ve tahmin dosyaları değiştirilmedi. Bu takipte iyileşme olmadı;
başarısız aramalar da kanıttır.

## Koşullu belirsizlik

| metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- |
| recall | 0.877975 | 0.997118 | 1000 | 0 |
| precision | 0.051430 | 0.111802 | 1000 | 0 |
| false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| brier | 0.007289 | 0.015279 | 1000 | 0 |

Aralıklar, model ve eşik sabit tutularak 24 tohumuyla bütün HARP'ları örnekleyen
1000 bootstrap tekrarından elde edilen %95 yüzdelik aralıklardır. Eğitim,
kalibrasyon, model seçimi ve eşik seçimi belirsizliğini içermez; gelecekteki
recall'u doğrulamaz. Özellikle recall alt sınırı 0.95'in altındadır. Aynı
kalibrasyon verisi hem olasılık kalibrasyonunda hem aday seçiminde kullanıldığı
için kalibrasyon skorları iyimser geliştirme skorlarıdır. Doğrulama daha önce
model tasarımını etkilemişti; süreç hâlâ uyarlamalı geliştirmedir. Bağımsız test
sonucu veya operasyonel hazırlık iddiası yoktur.

## Sonraki araştırma yönü

Yalnızca modeli değiştiren sınırlı aramalar precision'ı artırmadı. Sonraki deney,
doğrulanmış geçmiş patlama bilgisi ve daha ayrıntılı manyetik değişim gibi tahmin
anında bilinen bilgileri eklemeli; eğitimden önce erişilebilirlik zamanları ve
bölge ilişkileri denetlenmelidir. Yeni özellikler yardımcı olabilir, ancak
iyileşme garantisi yoktur. Mevcut recall koşulu 0.95 olarak kalır; alarm eşiğini
yükseltip recall'u sessizce düşürmek kullanıcının hedefini değiştirir.

## Yeniden üretim ve kanıt

```sh
OMP_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-log-v1.json --output artifacts/precision_log_20261027_r1
OMP_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-hist-v1.json --output artifacts/precision_hist_20261027_r1
.venv/bin/python scripts/report_precision_followup.py --output artifacts/precision_followup_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_precision_followup_20261027
```

Komutlar mevcut artifact dizinlerini reddeder; tekrar için yeni yollar kullanın
ve raporlama betiğinin girdi yollarını uyarlayarak bu yolları kullanın.
Raporlama betiği yukarıdaki tarihli girdi yollarını kullanır. Yeni bir hata
denetimi ve eşlenmiş Markdown belgeleri üretir. İçerikleri değişirse yayımdan
önce iki sürümü gözden geçirip katalog kaynak hash'ini yenileyin.

| source | SHA-256 |
| --- | --- |
| artifacts/precision_log_20261027_r1/report.json | 5708ccbb3e6e41735ae41a110ccdc81635e62aac5f6771e7d0cb7697017d6c57 |
| artifacts/precision_hist_20261027_r1/report.json | 56cce200d82344533b630f92b1c81f60c81df711dee9a213c86d47ca2354b69d |
| artifacts/precision_log_20261027_r1/calibration_candidates.csv | 9e5069c5d67a5f21bc1583812633e5295938f0f5d27467926b20727150208805 |
| artifacts/precision_hist_20261027_r1/calibration_candidates.csv | 35b32b13a0c8d8f68acb8470fb539dbdd4f0c47f6a4de8f4a142b5d13dd303e1 |
| artifacts/experiment5_v2_development_20261026_r2/validation_predictions.parquet | 44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff |

Kaynak kod ve protokoller commitlenir; veri, modeller, tahminler ve üretilen
HTML yerel, Git tarafından yok sayılan artifact olarak kalır. Önceki raporlar
ve deney çıktıları korunur. Tarihsel karşılaştırma kaynağı:
[yakalama öncelikli sonuçlar](recall-first-results.md).
