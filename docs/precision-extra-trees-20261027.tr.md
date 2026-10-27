# Extra Trees precision deneyi

Tarih: 2026-10-27. Kalibrasyonda `incumbent` seçildi. Aday geliştirmedeki tüm model değiştirme kontrollerini geçmedi; mevcut model seçili kaldı.

## Kapsam ve sabitlenmiş arama

Üç ExtraTreesClassifier modeli eğitildi: sınıf ağırlıksız ham özellikler,
dengeli eğitim sınıf ağırlıklarıyla ham özellikler ve dengeli ağırlıklarla
işaret koruyan logaritmik özellikler. Her birinde 256 ağaç, 20 maksimum derinlik,
20 minimum yaprak örneği, sqrt özellik örneklemesi, 24 tohum ve 2 işçi bulunur.
Medyanla eksik değer doldurma ve varsa logaritmik ölçekler yalnızca eğitimde
öğrenilir. Yeni dış veri veya gelecekten türetilen özellik eklenmedi.

Her modelin sigmoid kalibrasyonu 2022 verisini kullandı. 0.25, 0.5, 0.75 ve 1.0
yeni-model karışım ağırlıkları, mevcut modele ek 12 aday üretti. Aday seçimi,
recall >=0.95 düzeyindeki kalibrasyon precision'ını, ardından AP'yi ve aday
kimliğini kullandı. Yalnızca kazanan 2023 doğrulamasına geçti. Model değiştirmek,
recall >=0.95 düzeyinde daha yüksek doğrulama precision'ı, daha düşük olmayan AP,
daha yüksek olmayan Brier/log loss gerektirir. Arama çalıştırılmadan önce
`config/precision-extra-trees-v1.json` içinde sabitlendi. Eğitimde 484549
pencere/8698 pozitif, kalibrasyonda 50756/421, doğrulamada 60366/781 vardır.
Ayrılmış 2024–2025 verisi açılmadı.

## Tüm kalibrasyon adayları

| candidate | recall | precision | fp | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| incumbent | 0.950119 | 0.090662 | 4012 | 0.286706 | 0.006985 | 0.027776 |
| extra_raw_w0.25 | 0.950119 | 0.084442 | 4337 | 0.288349 | 0.006959 | 0.027548 |
| extra_raw_w0.5 | 0.950119 | 0.072661 | 5105 | 0.282479 | 0.006977 | 0.027652 |
| extra_raw_w0.75 | 0.950119 | 0.068942 | 5402 | 0.250442 | 0.007038 | 0.027993 |
| extra_raw_w1 | 0.950119 | 0.064257 | 5825 | 0.211053 | 0.007141 | 0.028597 |
| extra_balanced_w0.25 | 0.950119 | 0.082902 | 4425 | 0.278416 | 0.007002 | 0.027736 |
| extra_balanced_w0.5 | 0.950119 | 0.078355 | 4705 | 0.260593 | 0.007070 | 0.027935 |
| extra_balanced_w0.75 | 0.950119 | 0.070299 | 5290 | 0.218370 | 0.007188 | 0.028370 |
| extra_balanced_w1 | 0.950119 | 0.064568 | 5795 | 0.177435 | 0.007356 | 0.029120 |
| extra_log_balanced_w0.25 | 0.950119 | 0.087623 | 4165 | 0.278113 | 0.007013 | 0.027768 |
| extra_log_balanced_w0.5 | 0.950119 | 0.079349 | 4641 | 0.261196 | 0.007091 | 0.027995 |
| extra_log_balanced_w0.75 | 0.950119 | 0.069252 | 5376 | 0.211912 | 0.007217 | 0.028449 |
| extra_log_balanced_w1 | 0.950119 | 0.064527 | 5799 | 0.161956 | 0.007392 | 0.029198 |

## Doğrulama karşılaştırması

| metric | incumbent | candidate |
| --- | --- | --- |
| precision | 0.079622 | 0.079622 |
| recall | 0.950064 | 0.950064 |
| fp | 8577.000000 | 8577.000000 |
| fn | 39.000000 | 39.000000 |
| tp | 742.000000 | 742.000000 |
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

## Koşullu belirsizlik

| model | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- |
| incumbent | recall | 0.877975 | 0.997118 | 1000 | 0 |
| incumbent | precision | 0.051430 | 0.111802 | 1000 | 0 |
| incumbent | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| incumbent | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| incumbent | brier | 0.007289 | 0.015279 | 1000 | 0 |
| selected | recall | 0.877975 | 0.997118 | 1000 | 0 |
| selected | precision | 0.051430 | 0.111802 | 1000 | 0 |
| selected | false_positive_rate | 0.114612 | 0.173347 | 1000 | 0 |
| selected | false_alarm_ratio | 0.888198 | 0.948570 | 1000 | 0 |
| selected | brier | 0.007289 | 0.015279 | 1000 | 0 |

Bu %95 aralıklar, sabit model/eşik ve 24 tohumla bütün HARP'ları örnekleyen
1000 bootstrap tekrarı kullanır. Eğitim, kalibrasyon ve seçim belirsizliğini
içermez. Kalibrasyon hem olasılık öğreniminde hem aday seçiminde kullanılır;
önceki doğrulama sonuçları geliştirmeyi etkiledi. Sonuç uyarlamalı geliştirmedir;
bağımsız test veya gelecekteki recall garantisi değildir. Sayılar bağımsız
patlama veya alarmları değil, örtüşen tahmin pencerelerini anlatır. Eşik,
kalibrasyondan değiştirilmeden aktarılmaz; doğrulamada seçilir.

## Precision artırmak için başka ne yapılabilir?

Mevcut modelin kaçırdığı pozitif pencereler şu bölgelerde yoğunlaşıyor:

| harp | positive_windows | missed_windows |
| --- | --- | --- |
| 9152 | 24 | 22 |
| 9584 | 48 | 12 |
| 8990 | 47 | 3 |
| 9091 | 24 | 2 |

HARP 9152 ve 9584, kaçırılan 39 pencerenin 34'ünü oluşturuyor. Bu bölgelerin
patlama ilişkileri, özgün zaman damgaları ve ölçüm kalitesi bağımsız denetlenmeli.
Bu bir inceleme önceliğidir; etiketlerin yanlış olduğuna kanıt değildir.
Metrikleri artırmak amacıyla zor bölgeler çıkarılmamalı veya etiketleri değiştirilmemeli.

Ardından ham, filtrelenmemiş gözlemlerden daha uzun geçmiş üretilmeli; 24/48
saatlik değişim, süreklilik ve akı gelişimi aynı popülasyonda sınanmalı. Daha
önce tutulmuş etiketli pencereler tek başına geçmiş girdisi olmaya uygun değildir:
bu pencerelerin tutulması gelecekteki etiket dışlamalarına bağlı olabilir.
Geçmiş patlama özellikleri de doğrulanmış rapor erişilebilirliği ve bölge
ilişkisi kaynağı gerektirir. Son olarak tek kalibrasyon yılına bağımlılığı
azaltmak için aday aileleri ek kronolojik geliştirme bölümlerinde karşılaştırılmalı.
Bunlar sonraki deneylere yönelik hipotezlerdir; bu turda gösterilmiş iyileşmeler değildir.

Aşağıdaki tablo, değişmeyen mevcut modelin eşik incelemesidir:

| recall | precision | fp | fn | threshold |
| --- | --- | --- | --- | --- |
| 0.950064 | 0.079622 | 8577 | 39 | 0.009311 |
| 0.900128 | 0.098515 | 6433 | 78 | 0.016103 |
| 0.800256 | 0.132415 | 4095 | 156 | 0.029984 |
| 0.500640 | 0.182115 | 1756 | 390 | 0.070622 |

Daha yüksek eşikler recall'dan vazgeçerek precision'ı artırabilir. Bu satırlar
model iyileşmesi değildir; kullanıcı hedefi recall >=0.95 olarak kalır. Çalışma
noktası değişimini daha iyi sıralamadan ayırmak için gösterilmiştir. Tek başına
olasılık kalibrasyonunun iyileşmesi o çalışma noktasındaki precision'ı garanti etmez.

## Yeniden üretim ve kanıt

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \
  --protocol config/precision-extra-trees-v1.json --output artifacts/precision_extra_trees_20261027_r1
.venv/bin/python scripts/report_extra_trees_precision.py --output artifacts/precision_extra_trees_audit_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_extra_trees_20261027
```

Mevcut artifact dizinleri korunur. Tekrar için yeni yollar kullanın ve raporlama
betiğindeki tarihli girdi yollarını buna göre güncelleyin. Yayımdan önce iki
belge sürümü gözden geçirilmeli ve kaydedilmelidir. Mevcut dashboard modeli
otomatik değiştirilmez. Modeller, veri, tahminler ve HTML yerel, yok sayılan
artifact olarak kalır; kaynak kod ve bu raporlar commitlenir.

| source | SHA-256 |
| --- | --- |
| artifacts/precision_extra_trees_20261027_r1/report.json | 86fe4cbf1c59e451a0f05b09614eb872c2efac217c3babf6ddf17477105b3ab3 |
| artifacts/precision_extra_trees_20261027_r1/calibration_candidates.csv | aa0528ffc5e40f6df4640387204dda174ae03b93b62709575b26b92ee29c7c52 |
| artifacts/precision_extra_trees_20261027_r1/validation_predictions.parquet | 615de72ac7bf51ab9436d7b790755c222635a2b893caa785b9ddd9e60757a445 |
| artifacts/experiment5_v2_development_20261026_r2/validation_predictions.parquet | 44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff |

