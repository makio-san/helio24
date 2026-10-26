# SWAN-SF-V2 ölçüm semantiği denetimi

Denetim tarihi: 2026-10-26. Karar: **24 ağırlıksız manyetik alan, dönüşüm
uygulanmadan veri kümesine özgü tahmin kullanımı için onaylandı**. Bu karar,
Helio24'ün arşivi ham magnetogramlardan yeniden üretebildiğini veya kesin üst
akış üretim commit'inin bilindiğini iddia etmez.

## Kanıt ve sınırlı kaynak geçmişi

V2 makalesi kesinleşmiş `hmi.sharp_cea_720s` serisini tanımlar, 24 manyetik
niceliğin adlarını ve formüllerini yayımlar ve bunların `swdatatoolkit` ile
yeniden hesaplandığını belirtir. Resmî toolkit deposunun açık `V0.0.1` geçmişi
incelendi. Arşiv zamanlarından önce görünen son commit,
2026-10-01 15:15:45 UTC zamanlı
`69e6b65d48159078194e04a7ab4a784c03954fd2` değeridir. Sonraki görünen commit,
2026-10-02 13:03:55 UTC zamanlı
`27b6e5a4cdc99c6d0be2f5ef329b6240c6578314` değeridir. Dört arşivin son
değiştirilme zamanları 2026-10-01 17:52:32 ile 17:56:22 UTC arasındadır.

Bu zamanlama açık kaynak durumunu sınırlar fakat veriyi hangi checkout'un
ürettiğini kanıtlamaz. Parquet metadata'sı Spark 4.2.0 ve parquet-mr 1.17.0
kaydeder, Git revizyonu kaydetmez. Lorentz uygulaması Mart ayındaki `c82ef1d`
kaynak değişikliğinde, sınırlı `69e6b65` durumunda ve incelenen açık dal
anlık görüntüsünde bayt düzeyinde aynıdır; SHA-256 değeri
`bfb11c1dbe3d255811ca26ce0a723bc09998d156c2aeea4fda5077ce700b3959`.

## Sayısal kontroller

Dondurulmuş beş 2011 örtüşme penceresi değişken başına 296 sonlu V1/V2 çifti ve
tarihsel V1 kalite maskesinden sonra 282 çift sağladı. Aşağıdaki kontroller
öğrenilmiş dönüşümler değil, tanısal özdeşliklerdir.

| Kontrol | Tüm sonlu çiftler | Tarihsel maskeli çiftler |
| --- | ---: | ---: |
| `V2 TOTFX = V1 TOTFX / (4π)` | 296 / 296 | 282 / 282 |
| `V2 TOTFY = -V1 TOTFY / (4π)` | 296 / 296 | 282 / 282 |
| `V2 TOTFZ = V1 TOTFZ / (8π)` | 296 / 296 | 282 / 282 |
| V2 içinde `EPSX = TOTFX / TOTBSQ` | 296 / 296 | 282 / 282 |
| V2 içinde `EPSY = TOTFY / TOTBSQ` | 296 / 296 | 282 / 282 |
| V2 içinde `EPSZ = TOTFZ / TOTBSQ` | 296 / 296 | 282 / 282 |

Zamanı hizalanmış beş JSOC başlık anlık görüntüsü ayrı bir sınırlı kontrol sunar.

| Ölçüm | V1–JSOC eşleşmeleri | V2–JSOC eşleşmeleri |
| --- | ---: | ---: |
| USFLUX | 5 / 5 | 5 / 5 |
| MEANPOT | 0 / 5 | 5 / 5 |
| TOTPOT | 0 / 5 | 5 / 5 |
| MEANSHR | 0 / 5 | 2 / 5 |
| SHRGT45 | 3 / 5 | 4 / 5 |

İlk üç sonuç bu noktalardaki V2 yeniden hesaplamasını destekler. Yazdırılan
başlık hassasiyeti son iki karşılaştırmayı sınırlar. Beş kayıt tam arşivi veya
her formülü doğrulayamaz.

## Dondurulmuş sonraki aşama sözleşmesi

Helio24 doğrulanmış V2 arşiv değerlerini kaynak kayıt olarak ele alır. 24
ağırlıksız alan adını depolandığı biçimde kullanır; V1 ölçekleme, işaret
düzeltmesi, deneysel EPS dönüşümü, ağırlıklı alan değişimi veya JSOC başlık
değişimi uygulamaz. Her 60 satırlık gözlem penceresi ortalama, popülasyon standart
sapması, son değer ve başlangıçtan sona fark olmak üzere 96 özellik üretir.
Eksik ve sonlu olmayan değerler ayrıca doğrulanmış V2 kalite politikasını izler;
model imputasyonu yalnız eğitim verisinde öğrenilir.

Bu sınırlı sözleşme altında `measurement_semantics`, tahmin kullanımı için
doğrulanmıştır. “Doğrulanmış”, girdi kimliğinin, dönüşümlerin ve sınırlamaların
dondurulup denetlenebilir olduğu anlamına gelir. V1 ile fiziksel eşdeğerlik veya
üst akış hesaplamasının tamamen yeniden üretilebilir olduğu anlamına gelmez.

## Sınırlamalar ve belirsizlik

- Arşiv üreticisinin kullandığı kesin Git revizyonu ve ortam veriye gömülü
  değildir ve bilinmemektedir.
- Açık kaynak zamanlaması kaynak geçmişi kanıtıdır; üretim checkout'unun kanıtı
  değildir.
- İç denklemler tutarsızlığı yakalayabilir fakat fiziksel doğruluğu veya
  birimleri bağımsız biçimde kanıtlayamaz.
- Beş JSOC kaydı sınırlı bir nokta kontrolüdür. Bir kaydın tarihsel `QUALITY`
  değeri sıfır değildir; sayısal kullanılabilirlik tarihsel kalite eşdeğerliği
  değildir.
- Sözleşme bu dondurulmuş arşiv üzerinde model eğitimini destekler. Canlı bir
  işlem hattı eşleşen alanları, hesaplamaları ve kullanılabilirliği ayrıca
  göstermelidir.

## Yeniden üretim

```sh
.venv/bin/python scripts/trace_measurement_differences.py
git -C data/toolkit_source show 69e6b65:\
py_src/swdatatoolkit/magparam/_lorentz_calculator.py | shasum -a 256
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_semantics_20261026
```

Dondurulmuş sayısal denetim `artifacts/measurement_trace/report.json`
dosyasıdır; SHA-256 değeri
`d48a767cd81076c2bdbe4963a3e7bcb309e18cb109ccee975bb95b305ac5abcc`.

Kaynaklar: [SWAN-SF-V2 ön baskısı](https://arxiv.org/abs/2610.04591),
[swdatatoolkit makalesi](https://arxiv.org/abs/2604.22741),
[resmî toolkit deposu](https://bitbucket.org/gsudmlab/spaceweather_toolkit/).
