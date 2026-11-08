# Bölgesel bağlam sonuçları: yayımlanmış SRS özellikleri kesinliği artırmıyor

## Karar ve kapsam

[Donmuş protokol](region-context-protocol-20261109.tr.md) bir kez çalıştırıldı. 96 manyetik özet artı nedensel
SRS bağlamı, donmuş baseline'ın yıllık katlarında değiştirilmemiş walk-forward reçeteleriyle yeniden eğitildi
(28 bileşen eğitimi); her kat denetimi donmuş baseline denetimine eşitti. Tüm adayların eşikleri, hiçbir
değerlendirme etiketi okunmadan önce diske yazılıp hash'lendi (SHA256 `dc2a7d1606234d72c400b07c4b45de5dec267b9d34460330d38a6082566b0f84`). Hiçbir etiket değişmedi ve
ayrılmış 2024–2025 testi kapalı kaldı.

Kararlar:

1. `context`, yıl başına dört koşulu 6 pozitif yılın 1'inde (2015) geçiyor. Yalnızca erişilebilirlik bayrağı ve
   yayından bu yana geçen saatle yeniden eğitilen `flag`, 6 yılın 4'ünde geçiyor (2014, 2016, 2022, 2023).
   İkisi de altı yılın hepsinde geçmiyor; tüm yıllar sonucu ikisi için de olumsuz.
2. SRS içeriğine hiçbir kazanç atfedilmiyor. `flag`'ın geçtiği yerde `context` geçmiyor; `context`'in geçtiği
   yerde (2015) kazanç 11453 yanlış-alarm penceresinden 156'sı ve dönem kesinliğinde 0.0669'dan 0.0690'a
   yükseliş. 2014, 2016, 2022 ve 2023'te `context` kontrolden daha fazla yanlış alarm veriyor.
3. Hiçbir şey benimsenmedi. Hiçbir uyarı, eşik veya model değişmez. Yayımlanmış SRS'ten gelen manyetik sınıf,
   McIntosh sınıfı, alan, leke sayısı ve bölge yaşı, bu kayıtta bu reçeteyle SHARP özetlerinin üzerine ayırt
   edici güç eklemiyor.

## Katlarda bağlam erişilebilirliği

Kat rolüne göre `srs_available` değeri 1 olan pencerelerin payı. 0 olduğu yerde her bağlam değeri eksiktir ve
eksiklik göstergesiyle doldurucudan geçer.

| yıl | train | calibration | evaluation |
| --- | --- | --- | --- |
| 2014 | 45.9% | 46.7% | 40.8% |
| 2015 | 46.3% | 40.8% | 39.8% |
| 2016 | 45.0% | 39.8% | 39.8% |
| 2017 | 44.1% | 39.8% | 46.2% |
| 2018 | 43.6% | 46.2% | 40.7% |
| 2022 | 43.6% | 45.9% | 44.8% |
| 2023 | 43.8% | 44.8% | 40.5% |

## Kabul sonucu

| candidate | years_met | required_years | all_year_primary | met_years |
| --- | --- | --- | --- | --- |
| flag | 4 | 6 | hayır | [2014, 2016, 2022, 2023] |
| context | 1 | 6 | hayır | [2015] |

| year | candidate | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | flag | evet | evet | evet | evet | evet |
| 2014 | context | hayır | hayır | evet | evet | hayır |
| 2015 | flag | evet | hayır | evet | evet | hayır |
| 2015 | context | evet | evet | evet | evet | evet |
| 2016 | flag | evet | evet | evet | evet | evet |
| 2016 | context | hayır | hayır | evet | evet | hayır |
| 2017 | flag | hayır | hayır | evet | evet | hayır |
| 2017 | context | hayır | hayır | evet | evet | hayır |
| 2022 | flag | evet | evet | evet | evet | evet |
| 2022 | context | evet | hayır | evet | evet | hayır |
| 2023 | flag | evet | evet | evet | evet | evet |
| 2023 | context | hayır | hayır | evet | evet | hayır |

`flag` geçişleri küçük yeniden eğitim etkileridir: yanlış-alarm azalması 2014'te 125, 2016'da 55, 2022'de 204 ve
2023'te 19 pencere; her biri kontrolün yanlış alarmlarının %2,1'inin altında ve 2016 üç doğru pozitif
kaybediyor. `flag` içerik taşımadığı için bunlar SRS içeriğine atfedilemez.

## Yıl ve adaya göre metrikler

| yıl | aday | eşik | TP | FP | recall | recall ≥ 0.95 | kesinlik | dönemler | dönem kesinliği | alarm verilen pozitif seriler | AP | Brier | log loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.011475 | 2184 | 13886 | 0.9455 | hayır | 0.1359 | 686 | 0.0977 | 80 / 83 | 0.5079 | 0.020661 | 0.076538 |
| 2014 | flag | 0.011701 | 2183 | 13761 | 0.9450 | hayır | 0.1369 | 669 | 0.1001 | 80 / 83 | 0.5082 | 0.020658 | 0.076536 |
| 2014 | context | 0.009703 | 2202 | 14833 | 0.9532 | evet | 0.1293 | 734 | 0.0913 | 80 / 83 | 0.4992 | 0.020852 | 0.076997 |
| 2015 | control | 0.018839 | 1346 | 11453 | 0.9934 | evet | 0.1052 | 568 | 0.0669 | 51 / 51 | 0.4924 | 0.013564 | 0.047847 |
| 2015 | flag | 0.018485 | 1346 | 11551 | 0.9934 | evet | 0.1044 | 561 | 0.0677 | 51 / 51 | 0.4930 | 0.013557 | 0.047811 |
| 2015 | context | 0.018868 | 1347 | 11297 | 0.9941 | evet | 0.1065 | 551 | 0.0690 | 51 / 51 | 0.5118 | 0.013329 | 0.047211 |
| 2016 | control | 0.030831 | 176 | 2289 | 0.9724 | evet | 0.0714 | 204 | 0.0196 | 7 / 7 | 0.3664 | 0.003263 | 0.014523 |
| 2016 | flag | 0.031593 | 173 | 2234 | 0.9558 | evet | 0.0719 | 198 | 0.0253 | 7 / 7 | 0.3620 | 0.003273 | 0.014583 |
| 2016 | context | 0.026925 | 176 | 2380 | 0.9724 | evet | 0.0689 | 208 | 0.0192 | 7 / 7 | 0.3645 | 0.003224 | 0.014176 |
| 2017 | control | 0.012000 | 237 | 1287 | 0.9368 | hayır | 0.1555 | 85 | 0.0588 | 5 / 6 | 0.8117 | 0.004907 | 0.020488 |
| 2017 | flag | 0.010120 | 238 | 1370 | 0.9407 | hayır | 0.1480 | 94 | 0.0532 | 5 / 6 | 0.8118 | 0.004909 | 0.020551 |
| 2017 | context | 0.012045 | 237 | 1303 | 0.9368 | hayır | 0.1539 | 86 | 0.0581 | 5 / 6 | 0.7988 | 0.005077 | 0.021297 |
| 2022 | control | 0.008994 | 415 | 10072 | 0.9857 | evet | 0.0396 | 622 | 0.0257 | 16 / 16 | 0.2800 | 0.007064 | 0.029196 |
| 2022 | flag | 0.009298 | 415 | 9868 | 0.9857 | evet | 0.0404 | 608 | 0.0263 | 16 / 16 | 0.2791 | 0.007064 | 0.029208 |
| 2022 | context | 0.009014 | 415 | 10192 | 0.9857 | evet | 0.0391 | 610 | 0.0262 | 16 / 16 | 0.2775 | 0.007043 | 0.029255 |
| 2023 | control | 0.018203 | 691 | 5992 | 0.8848 | hayır | 0.1034 | 475 | 0.0842 | 36 / 38 | 0.2206 | 0.011195 | 0.043996 |
| 2023 | flag | 0.018357 | 689 | 5973 | 0.8822 | hayır | 0.1034 | 474 | 0.0844 | 36 / 38 | 0.2205 | 0.011194 | 0.044039 |
| 2023 | context | 0.017289 | 686 | 6374 | 0.8784 | hayır | 0.0972 | 512 | 0.0781 | 36 / 38 | 0.2258 | 0.011145 | 0.044139 |

## Kesinlik hedefine mesafe

| yıl | aday | TP | FP | kesinlik | 0,30 için izin verilen FP | FP fazlası |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2184 | 13886 | 0.1359 | 5096 | 8790 |
| 2014 | flag | 2183 | 13761 | 0.1369 | 5093 | 8668 |
| 2014 | context | 2202 | 14833 | 0.1293 | 5138 | 9695 |
| 2015 | control | 1346 | 11453 | 0.1052 | 3140 | 8313 |
| 2015 | flag | 1346 | 11551 | 0.1044 | 3140 | 8411 |
| 2015 | context | 1347 | 11297 | 0.1065 | 3143 | 8154 |
| 2016 | control | 176 | 2289 | 0.0714 | 410 | 1879 |
| 2016 | flag | 173 | 2234 | 0.0719 | 403 | 1831 |
| 2016 | context | 176 | 2380 | 0.0689 | 410 | 1970 |
| 2017 | control | 237 | 1287 | 0.1555 | 553 | 734 |
| 2017 | flag | 238 | 1370 | 0.1480 | 555 | 815 |
| 2017 | context | 237 | 1303 | 0.1539 | 553 | 750 |
| 2022 | control | 415 | 10072 | 0.0396 | 968 | 9104 |
| 2022 | flag | 415 | 9868 | 0.0404 | 968 | 8900 |
| 2022 | context | 415 | 10192 | 0.0391 | 968 | 9224 |
| 2023 | control | 691 | 5992 | 0.1034 | 1612 | 4380 |
| 2023 | flag | 689 | 5973 | 0.1034 | 1607 | 4366 |
| 2023 | context | 686 | 6374 | 0.0972 | 1600 | 4774 |

Hiçbir aday hiçbir yılı 0,30 kesinliğe 204 yanlış-alarm penceresinden fazla yaklaştırmıyor; fazlalık 734 ile
9104 pencere arasında.

## Pozitif penceresi olmayan yıl

| aday | eşik | YA pencereleri | dönemler |
| --- | --- | --- | --- |
| control | 0.004351 | 359 | 30 |
| flag | 0.004148 | 374 | 32 |
| context | 0.004442 | 444 | 41 |

## Belirsizlik

Kontrole karşı farkların eşleştirilmiş tam-HARP bootstrap aralıkları (1000 çekim, seed 24). Negatif bir
yanlış-alarm farkı, daha az yanlış-alarm penceresi demektir. Aralıklar donmuş eşiklere koşulludur; yeniden
eğitim ve eşik seçimi belirsizliğini dışarıda bırakır ve çoklu karşılaştırma için düzeltilmemiştir.

| yıl | aday | dönem kesinliği farkı alt | dönem kesinliği farkı üst | YA pencere farkı alt | YA pencere farkı üst |
| --- | --- | --- | --- | --- | --- |
| 2014 | flag | 0.0005 | 0.0047 | -173.0 | -87.0 |
| 2014 | context | -0.0152 | 0.0011 | 659.0 | 1260.0 |
| 2015 | flag | -0.0012 | 0.0031 | 64.0 | 132.0 |
| 2015 | context | -0.0023 | 0.0071 | -277.0 | -34.0 |
| 2016 | flag | 0.0000 | 0.0175 | -95.0 | -25.0 |
| 2016 | context | -0.0045 | 0.0018 | -78.0 | 245.1 |
| 2017 | flag | -0.0251 | 0.0046 | 41.0 | 130.0 |
| 2017 | context | -0.0169 | 0.0156 | -79.0 | 94.0 |
| 2022 | flag | -0.0003 | 0.0017 | -261.0 | -155.0 |
| 2022 | context | -0.0009 | 0.0021 | -25.0 | 265.0 |
| 2023 | flag | -0.0015 | 0.0023 | -40.0 | 0.0 |
| 2023 | context | -0.0145 | 0.0017 | 197.0 | 576.1 |

## Bağlam neden yardımcı olmuyor

SRS, numaralı bir bölgeyi günde bir kez, önceki günün 24:00 UT durumuyla tanımlar; SHARP özetleri aynı bölgenin
fotosfer alanını saatlik tanımlar. Manyetik sınıf ve McIntosh sınıfı, sürekli alan ölçümlerinin büyük ölçüde
zaten kodladığı kaba etiketlerdir ve pencerelerin %55 ile %60'ında hiç SRS satırı yoktur. Patlayan bölge ile
sürekli alarm veren sakin bölge arasındaki kalan fark, bu kadansta iki kaynak tarafından da yakalanmıyor. Sonuç bu
özellik kümesini bu reçeteyle reddeder; SRS'nin hiçbir kullanımının yardımcı olamayacağını göstermez.

## Sınırlar

- Zaten incelenmiş yıllar üzerinde uyarlanabilir geliştirme kanıtı, bağımsız bir test değil. Sayılar örtüşen
  tahmin pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir.
- Özellik listesi, aynı yıllarda yanlış alarmların nerede yoğunlaştığı görüldükten sonra sabitlendi; bu
  uyarlanabilirlik sonucu geçiş yönünde yanlı kılardı, sonuç yine de olumsuz.
- Dondurulduğu gibi tek reçete, tek kodlama ve tek erişilebilirlik payı sınandı.
- SRS yayın zamanı yayımlanmayı kanıtlar, alınmayı değil; 30 dakikalık pay proje kuralıdır.

## Yeniden üretim

```sh
python scripts/audit_region_context_features.py --output artifacts/region_context_20261109_r1
python -m pytest -q tests/test_region_context_features.py tests/test_region_context_protocol.py
```
