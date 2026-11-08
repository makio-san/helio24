# Kesinlik bağlamı sonuçları: nedensel bölgesel gidişat kesinliği artırmıyor

## Karar ve kapsam

[Donmuş protokol](precision-context-protocol-20261108.tr.md), donmuş yıllık tahminler üzerinde bir kez
çalıştırıldı (kaynak rapor SHA256 `e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`). Tüm
adayların eşikleri, hiçbir değerlendirme etiketi okunmadan önce diske yazılıp hash'lendi (SHA256 `8bd3b5231402245ddf97dae1c236c9d425412d664d1551b71c3ee33182a541e0`).
Birinci aşama, saklanan donmuş modellerle yalnızca çıkarımdı; ikinci aşama kalibrasyon yıllarında 84 küçük
lojistik eğitimdi. Hiçbir etiket değişmedi ve ayrılmış 2024–2025 testi kapalı kaldı.

Kararlar:

1. Hiçbir aday altı pozitif yılın hiçbirinde geçmiyor. Tüm yıllar sonucu `recal` için (6'da 0) ve `context`
   için (6'da 0) olumsuz.
2. Hiçbir şey benimsenmedi. Hiçbir uyarı, eşik veya model değişmez.
3. Bir bölgenin kendi olasılık gidişatının ve yaşının, sürekli alarmda kalan sakin bölgeleri patlamaya yaklaşan
   bölgelerden ayırdığı hipotezi, bu kayıtta bu ikinci aşamayla desteklenmiyor. Patlama geçmişi yolu kaynak
   kanıtı nedeniyle kapalı kalır ve bu sonuçla yeniden açılmaz.

## Baseline kapısı

Kontrol eşiği her yılda yeniden üretildi ve yeniden hesaplanan birinci aşama olasılıkları her satırda donmuş
tahminlere eşit.

| yıl | kalibrasyon pozitifleri | kalibrasyon HARP'ları | kontrol eşiği yeniden üretildi | kimlik eşleşen satır |
| --- | --- | --- | --- | --- |
| 2014 | 1287 | 588 | evet | 75228 |
| 2015 | 2310 | 629 | evet | 69138 |
| 2016 | 1355 | 599 | evet | 42987 |
| 2017 | 181 | 357 | evet | 19529 |
| 2018 | 253 | 163 | evet | 7799 |
| 2022 | 204 | 255 | evet | 50756 |
| 2023 | 421 | 528 | evet | 60366 |

## Kabul sonucu

| candidate | years_met | required_years | all_year_primary | met_years |
| --- | --- | --- | --- | --- |
| recal | 0 | 6 | hayır | [] |
| context | 0 | 6 | hayır | [] |

| year | candidate | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | recal | hayır | hayır | evet | evet | hayır |
| 2014 | context | evet | evet | hayır | evet | hayır |
| 2015 | recal | hayır | hayır | evet | evet | hayır |
| 2015 | context | evet | hayır | evet | evet | hayır |
| 2016 | recal | hayır | hayır | evet | evet | hayır |
| 2016 | context | hayır | hayır | evet | evet | hayır |
| 2017 | recal | evet | evet | evet | hayır | hayır |
| 2017 | context | hayır | hayır | evet | evet | hayır |
| 2022 | recal | evet | hayır | evet | evet | hayır |
| 2022 | context | hayır | hayır | evet | evet | hayır |
| 2023 | recal | hayır | hayır | evet | evet | hayır |
| 2023 | context | hayır | hayır | evet | evet | hayır |

`context` yanlış-alarm pencerelerini yalnızca 2014'te azaltır (13886'ya karşı 12951) ve orada dönem kesinliğini
yükseltir (0.0977'ye karşı 0.1328), ama kontrolün 80'ine karşı 83 pozitif serinin 78'ine alarm verir, bu yüzden
yıl başarısız olur. `recal` yanlış alarmları yalnızca 2017'de azaltır; orada recall'u 0.9368'den 0.8814'e düşer,
tolerans aşılır. Diğer her pozitif yılda iki aday da kontrolden daha fazla pencereye alarm verir.

## Yıl ve adaya göre metrikler

| yıl | aday | eşik | TP | FP | recall | kesinlik | dönemler | dönem kesinliği | alarm verilen pozitif seriler | AP | Brier | log loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.011475 | 2184 | 13886 | 0.9455 | 0.1359 | 686 | 0.0977 | 80 / 83 | 0.5079 | 0.020661 | 0.076538 |
| 2014 | recal | 0.007997 | 2201 | 15161 | 0.9528 | 0.1268 | 725 | 0.0897 | 80 / 83 | 0.5023 | 0.020774 | 0.077533 |
| 2014 | context | 0.009852 | 2163 | 12951 | 0.9364 | 0.1431 | 497 | 0.1328 | 78 / 83 | 0.4918 | 0.021063 | 0.079022 |
| 2015 | control | 0.018839 | 1346 | 11453 | 0.9934 | 0.1052 | 568 | 0.0669 | 51 / 51 | 0.4924 | 0.013564 | 0.047847 |
| 2015 | recal | 0.014615 | 1346 | 11597 | 0.9934 | 0.1040 | 606 | 0.0627 | 51 / 51 | 0.4999 | 0.013269 | 0.046413 |
| 2015 | context | 0.012352 | 1344 | 11553 | 0.9919 | 0.1042 | 509 | 0.0747 | 51 / 51 | 0.4933 | 0.013318 | 0.046577 |
| 2016 | control | 0.030831 | 176 | 2289 | 0.9724 | 0.0714 | 204 | 0.0196 | 7 / 7 | 0.3664 | 0.003263 | 0.014523 |
| 2016 | recal | 0.022311 | 176 | 2740 | 0.9724 | 0.0604 | 253 | 0.0158 | 7 / 7 | 0.3296 | 0.003353 | 0.014374 |
| 2016 | context | 0.013638 | 176 | 3244 | 0.9724 | 0.0515 | 240 | 0.0167 | 7 / 7 | 0.3699 | 0.003237 | 0.013707 |
| 2017 | control | 0.012000 | 237 | 1287 | 0.9368 | 0.1555 | 85 | 0.0588 | 5 / 6 | 0.8117 | 0.004907 | 0.020488 |
| 2017 | recal | 0.006207 | 223 | 1240 | 0.8814 | 0.1524 | 98 | 0.1020 | 5 / 6 | 0.5832 | 0.007895 | 0.034740 |
| 2017 | context | 0.000000 | 253 | 18721 | 1.0000 | 0.0133 | 350 | 0.0171 | 6 / 6 | 0.2836 | 0.011217 | 0.061819 |
| 2022 | control | 0.008994 | 415 | 10072 | 0.9857 | 0.0396 | 622 | 0.0257 | 16 / 16 | 0.2800 | 0.007064 | 0.029196 |
| 2022 | recal | 0.007065 | 416 | 11281 | 0.9881 | 0.0356 | 660 | 0.0258 | 16 / 16 | 0.2797 | 0.007092 | 0.029177 |
| 2022 | context | 0.003310 | 421 | 14303 | 1.0000 | 0.0286 | 639 | 0.0235 | 16 / 16 | 0.2028 | 0.007758 | 0.030726 |
| 2023 | control | 0.018203 | 691 | 5992 | 0.8848 | 0.1034 | 475 | 0.0842 | 36 / 38 | 0.2206 | 0.011195 | 0.043996 |
| 2023 | recal | 0.011625 | 719 | 7178 | 0.9206 | 0.0910 | 489 | 0.0818 | 38 / 38 | 0.2240 | 0.011220 | 0.044252 |
| 2023 | context | 0.005197 | 742 | 9211 | 0.9501 | 0.0746 | 504 | 0.0754 | 38 / 38 | 0.2081 | 0.011621 | 0.043913 |

## Kesinlik hedefine mesafe

Son sütun, ulaşılan doğru pozitiflerde 0,30 kesinlik verecek en büyük sayının üzerindeki yanlış-alarm penceresi
sayısıdır.

| yıl | aday | TP | FP | kesinlik | 0,30 için izin verilen FP | FP fazlası |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2184 | 13886 | 0.1359 | 5096 | 8790 |
| 2014 | recal | 2201 | 15161 | 0.1268 | 5135 | 10026 |
| 2014 | context | 2163 | 12951 | 0.1431 | 5047 | 7904 |
| 2015 | control | 1346 | 11453 | 0.1052 | 3140 | 8313 |
| 2015 | recal | 1346 | 11597 | 0.1040 | 3140 | 8457 |
| 2015 | context | 1344 | 11553 | 0.1042 | 3136 | 8417 |
| 2016 | control | 176 | 2289 | 0.0714 | 410 | 1879 |
| 2016 | recal | 176 | 2740 | 0.0604 | 410 | 2330 |
| 2016 | context | 176 | 3244 | 0.0515 | 410 | 2834 |
| 2017 | control | 237 | 1287 | 0.1555 | 553 | 734 |
| 2017 | recal | 223 | 1240 | 0.1524 | 520 | 720 |
| 2017 | context | 253 | 18721 | 0.0133 | 590 | 18131 |
| 2022 | control | 415 | 10072 | 0.0396 | 968 | 9104 |
| 2022 | recal | 416 | 11281 | 0.0356 | 970 | 10311 |
| 2022 | context | 421 | 14303 | 0.0286 | 982 | 13321 |
| 2023 | control | 691 | 5992 | 0.1034 | 1612 | 4380 |
| 2023 | recal | 719 | 7178 | 0.0910 | 1677 | 5501 |
| 2023 | context | 742 | 9211 | 0.0746 | 1731 | 7480 |

Herhangi bir hücrenin en iyi kesinliği 0.1555'tir (kontrol, 2017). Hiçbir aday hiçbir yılı kontrolden daha
fazla 0,30'a yaklaştırmaz; tek istisna 2014'te `context`'in 886 pencerelik yaklaşması, o da alarm verilen iki
pozitif seriyi kaybederek.

## Pozitif penceresi olmayan yıl

2018'de pozitif pencere yoktur ve kapıya tabi değildir.

| aday | eşik | YA pencereleri | dönemler |
| --- | --- | --- | --- |
| control | 0.004351 | 359 | 30 |
| recal | 0.000506 | 936 | 66 |
| context | 0.001387 | 502 | 43 |

## İkinci aşama neden başarısız

İkinci aşama modelinin kalibrasyon yılı eşiği, kontrol eşiğinden daha kötü aktarılır. İkinci aşama eşiği çapraz
uyarlanmış kalibrasyon olasılıkları üzerinde seçilir, ama değerlendirme yılı tüm kalibrasyon yılında yeniden
eğitilen modeli alır ve bağlam özelliklerinin değerlendirme yılındaki dağılımı kalibrasyon yılından farklıdır.
2017'de 2016 kalibrasyon yılında (181 pozitif pencere) eğitilen `context` modeli sıfıra yakın bir eşik seçti ve
2017'nin her penceresine alarm verdi: 253 doğru pozitif, 18721 yanlış alarm. İkinci aşama katsayıları da çoğu
bağlam özelliği için yıldan yıla işaret değiştirir; bu, bir yılda öğrenilen gidişat ilişkisinin sonraki yılda
geçerli olmadığını gösterir.

| özellik | 2014 | 2015 | 2016 | 2017 | 2022 | 2023 |
| --- | --- | --- | --- | --- | --- | --- |
| logit_p | 2.083 | 1.228 | 2.095 | 2.156 | 1.333 | 1.560 |
| age_log_hours | 0.445 | 0.096 | 0.162 | 0.893 | -0.400 | -0.245 |
| past24_max_logit | -0.029 | 2.362 | 0.786 | 0.911 | 0.920 | 1.576 |
| past24_mean_logit | 0.760 | -0.902 | 0.044 | 0.998 | 1.427 | 0.624 |
| past72_max_logit | -0.258 | -0.131 | -0.084 | -1.694 | -1.962 | 0.266 |
| past72_mean_logit | -0.262 | -0.021 | -0.223 | -0.555 | 0.526 | -1.546 |
| past72_hours_above_control | 0.653 | 0.229 | 0.240 | 1.128 | -0.262 | 0.165 |
| slope6 | 0.007 | 0.168 | 0.040 | 0.231 | -0.363 | -0.024 |
| coverage24 | 0.408 | -0.041 | -0.166 | 0.324 | -0.464 | -0.235 |
| coverage72 | -1.539 | -0.419 | -0.090 | -3.110 | 1.012 | -0.304 |
| missing_fraction | -0.165 | 0.089 | 0.203 | -2.143 | 0.031 | -0.135 |

## Belirsizlik

Altı pozitif yıl için kontrole karşı farkların eşleştirilmiş tam-HARP bootstrap aralıkları (1000 çekim,
seed 24). Negatif bir yanlış-alarm farkı, kontrolden daha az yanlış-alarm penceresi demektir. Aralıklar donmuş
eşiklere koşulludur; ikinci aşama eğitimi veya eşik seçimi belirsizliğini içermez ve çoklu karşılaştırma için
düzeltilmemiştir.

| yıl | aday | dönem kesinliği farkı alt | dönem kesinliği farkı üst | YA pencere farkı alt | YA pencere farkı üst |
| --- | --- | --- | --- | --- | --- |
| 2014 | recal | -0.0173 | -0.0001 | 975.0 | 1612.0 |
| 2014 | context | 0.0172 | 0.0539 | -1357.3 | -557.8 |
| 2015 | recal | -0.0084 | -0.0015 | 86.0 | 216.0 |
| 2015 | context | -0.0008 | 0.0183 | -181.0 | 358.0 |
| 2016 | recal | -0.0116 | -0.0001 | 311.9 | 617.0 |
| 2016 | context | -0.0128 | 0.0020 | 645.0 | 1365.0 |
| 2017 | recal | -0.0160 | 0.1458 | -296.0 | 151.0 |
| 2017 | context | -0.1144 | 0.0000 | 15384.4 | 19568.2 |
| 2022 | recal | -0.0028 | 0.0036 | 951.0 | 1477.0 |
| 2022 | context | -0.0078 | 0.0014 | 3223.0 | 5404.2 |
| 2023 | recal | -0.0183 | 0.0125 | 885.9 | 1498.0 |
| 2023 | context | -0.0267 | 0.0045 | 2664.8 | 3843.1 |

## Sınırlar

- Zaten incelenmiş yıllar üzerinde uyarlanabilir geliştirme kanıtı, bağımsız bir test değil. Sayılar örtüşen
  tahmin pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir.
- Bağlam özellikleri, aynı yıllarda yanlış alarmların nerede yoğunlaştığı görüldükten sonra seçildi; bu
  uyarlanabilirlik sonucu geçiş yönünde yanlı kılardı, sonuç yine de olumsuz.
- Dondurulduğu gibi yalnızca bir ikinci aşama reçetesi ve bir geriye bakış kümesi sınandı. Sonuç bu reçeteyi
  reddeder, bölgesel geçmişin her kullanımını değil.
- Az pozitif pencereli kalibrasyon yılları (2017 için 181, 2022 için 204) ikinci aşamayı kararsız kılar; 2017
  çöküşü en açık örnektir.

## Yeniden üretim

```sh
python scripts/audit_precision_context.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/precision_context_20261109_r1
python -m pytest -q tests/test_precision_context_audit.py tests/test_precision_context_protocol.py
```
