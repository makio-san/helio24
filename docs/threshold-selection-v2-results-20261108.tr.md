# Eşik seçimi v2 sonuçları: baseline kolu kapıyı geçiyor ve önceki yıl kurallarının hiçbiri geçmiyor

## Karar ve kapsam

[Donmuş v2 protokolü](threshold-selection-v2-protocol-20261108.tr.md), tamamlanan yedi yıllık karşılaştırmanın
donmuş yıllık tahminleri üzerinde bir kez çalıştırıldı (kaynak rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`). Eşikler yalnızca her değerlendirme yılından
önceki yılın kalibrasyon pencerelerinden seçildi, hiçbir değerlendirme etiketi okunmadan önce diske yazılıp
hash'lendi (SHA256 `0cd0c51e523f9ded6e7f20bfc059b1e4855cf3f7e57ee5a27ed0a50e29c5a0f2`) ve kontrol kuralı her yılda saklanan baseline eşiğini yeniden üretti.
Hiçbir model eğitilmedi veya yeniden kalibre edilmedi, hiçbir etiket değişmedi ve ayrılmış 2024–2025 testi kapalı
kaldı.

Kararlar:

1. Uygulanabilirlik kapısı baseline kolu için yedi yılın hepsinde geçti, yani kol değerlendirilebilir. Yeniden
   hesaplanan olasılıklar donmuş olanlarla birebir aynıdır.
2. Hiçbir kural altı pozitif yılın hepsinde geçmiyor. `w93` 6 yılın 3'ünde, `w90`, `run95` ve `run90` ise her biri
   6 yılın 2'sinde geçiyor.
3. Hiçbir şey benimsenmedi. Hiçbir uyarı, eşik veya model değişmez. Önceki yıl recall hedefi, bu kayıtta iki TCN
   kolu için olduğu gibi baseline kolu için de eşik açısından güvenilmez bir rehberdir.

## Uygulanabilirlik kapısı

| kontrol | sonuç |
| --- | --- |
| G1 | 20 / 20 |
| G2 | 7 / 7 |
| G3 | 7 / 7 |
| G4 | 7 / 7 |

Kimlik kontrolü, saklanan donmuş modellerin kalibre edilmiş topluluk olasılığını yalnızca çıkarımla yeniden
hesaplar ve donmuş tahminlerin `baseline` kolonuyla karşılaştırır. Hiçbir etiket kullanmaz.

| yıl | saklanan eşik | yeniden hesaplanan eşik | eşleşen satır | en büyük mutlak fark |
| --- | --- | --- | --- | --- |
| 2014 | 0.011475 | 0.011475 | 75228 | 0.0 |
| 2015 | 0.018839 | 0.018839 | 69138 | 0.0 |
| 2016 | 0.030831 | 0.030831 | 42987 | 0.0 |
| 2017 | 0.012000 | 0.012000 | 19529 | 0.0 |
| 2018 | 0.004351 | 0.004351 | 7799 | 0.0 |
| 2022 | 0.008994 | 0.008994 | 50756 | 0.0 |
| 2023 | 0.018203 | 0.018203 | 60366 | 0.0 |

Saklanan yedi model dosyasının hepsi donmuş SHA256 değerleriyle eşleşti. Yeniden hesaplanan kontrol eşiği, her
yılda walk-forward artifact'ında `ensemble` için saklanan eşiğe de eşittir.

## Kabul sonucu

| arm | rule | years_met | required_years | all_year_primary |
| --- | --- | --- | --- | --- |
| baseline | w93 | 3 | 6 | hayır |
| baseline | w90 | 2 | 6 | hayır |
| baseline | run95 | 2 | 6 | hayır |
| baseline | run90 | 2 | 6 | hayır |

Bir kural, altı pozitif yılın hepsinde yıl başına dört koşulun hepsini sağlamalıdır.

| year | rule | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | w93 | evet | evet | hayır | evet | hayır |
| 2014 | w90 | evet | evet | hayır | hayır | hayır |
| 2014 | run95 | evet | evet | hayır | evet | hayır |
| 2014 | run90 | evet | evet | hayır | hayır | hayır |
| 2015 | w93 | evet | evet | evet | evet | evet |
| 2015 | w90 | evet | evet | evet | hayır | hayır |
| 2015 | run95 | evet | evet | evet | hayır | hayır |
| 2015 | run90 | evet | evet | hayır | hayır | hayır |
| 2016 | w93 | evet | evet | evet | hayır | hayır |
| 2016 | w90 | evet | evet | evet | hayır | hayır |
| 2016 | run95 | evet | evet | evet | hayır | hayır |
| 2016 | run90 | evet | evet | hayır | hayır | hayır |
| 2017 | w93 | evet | evet | evet | evet | evet |
| 2017 | w90 | evet | evet | evet | evet | evet |
| 2017 | run95 | evet | evet | evet | evet | evet |
| 2017 | run90 | evet | evet | evet | evet | evet |
| 2022 | w93 | evet | evet | evet | evet | evet |
| 2022 | w90 | evet | evet | evet | evet | evet |
| 2022 | run95 | evet | evet | evet | evet | evet |
| 2022 | run90 | evet | evet | evet | evet | evet |
| 2023 | w93 | hayır | evet | evet | hayır | hayır |
| 2023 | w90 | evet | evet | hayır | hayır | hayır |
| 2023 | run95 | evet | evet | hayır | hayır | hayır |
| 2023 | run90 | evet | evet | hayır | hayır | hayır |

Dört kuralın hepsinin geçtiği iki yıl 2017 ve 2022'dir. 2016 ve 2023'te hiçbir kural pencere recall düşüşünü
0,02 içinde tutmaz. 2014'te `w93` ve `run95` alarm verilen pozitif serilerde (kontrolde 80, bunlarda 79) başarısız
olur; `w90` ve `run90` ise recall düşüşünde başarısız olur. 2015'te yalnızca `w93` geçer.

## Yıl ve kurala göre metrikler

Kontrol `control_w95`'tir. Recall ve sayılar değerlendirme yılına aittir. Kalibrasyon recall'u, eşiği seçmek için
kullanılan kalibrasyon pencerelerinde ölçülür.

| yıl | kural | eşik | kontrole oran | kalibrasyon recall | değerlendirme recall | YA pencereleri | dönemler | dönem kesinliği | alarm verilen pozitif seriler |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control_w95 | 0.0115 | 1.0000 | 0.9503 | 0.9455 | 13886 | 686 | 0.0977 | 80 / 83 |
| 2014 | w93 | 0.0135 | 1.1754 | 0.9301 | 0.9407 | 12895 | 634 | 0.1057 | 79 / 83 |
| 2014 | w90 | 0.0324 | 2.8212 | 0.9005 | 0.8688 | 7634 | 483 | 0.1636 | 77 / 83 |
| 2014 | run95 | 0.0164 | 1.4335 | 0.9192 | 0.9290 | 11607 | 613 | 0.1126 | 79 / 83 |
| 2014 | run90 | 0.0561 | 4.8866 | 0.8159 | 0.7684 | 5158 | 411 | 0.1971 | 72 / 83 |
| 2015 | control_w95 | 0.0188 | 1.0000 | 0.9502 | 0.9934 | 11453 | 568 | 0.0669 | 51 / 51 |
| 2015 | w93 | 0.0269 | 1.4257 | 0.9303 | 0.9897 | 9048 | 480 | 0.0813 | 51 / 51 |
| 2015 | w90 | 0.0407 | 2.1597 | 0.9000 | 0.9653 | 6294 | 378 | 0.1138 | 51 / 51 |
| 2015 | run95 | 0.0407 | 2.1597 | 0.9000 | 0.9653 | 6294 | 378 | 0.1138 | 51 / 51 |
| 2015 | run90 | 0.0576 | 3.0587 | 0.8398 | 0.9240 | 4410 | 298 | 0.1477 | 49 / 51 |
| 2016 | control_w95 | 0.0308 | 1.0000 | 0.9506 | 0.9724 | 2289 | 204 | 0.0196 | 7 / 7 |
| 2016 | w93 | 0.0380 | 1.2311 | 0.9306 | 0.9448 | 1825 | 183 | 0.0273 | 7 / 7 |
| 2016 | w90 | 0.0539 | 1.7473 | 0.9004 | 0.8950 | 1303 | 144 | 0.0347 | 7 / 7 |
| 2016 | run95 | 0.0687 | 2.2274 | 0.8620 | 0.8729 | 1013 | 116 | 0.0517 | 7 / 7 |
| 2016 | run90 | 0.1025 | 3.3238 | 0.7616 | 0.8343 | 602 | 88 | 0.0455 | 6 / 7 |
| 2017 | control_w95 | 0.0120 | 1.0000 | 0.9503 | 0.9368 | 1287 | 85 | 0.0588 | 5 / 6 |
| 2017 | w93 | 0.0143 | 1.1935 | 0.9337 | 0.9328 | 1223 | 83 | 0.0602 | 5 / 6 |
| 2017 | w90 | 0.0219 | 1.8211 | 0.9006 | 0.9289 | 1035 | 64 | 0.0781 | 5 / 6 |
| 2017 | run95 | 0.0578 | 4.8197 | 0.7901 | 0.9249 | 645 | 56 | 0.0893 | 5 / 6 |
| 2017 | run90 | 0.0578 | 4.8197 | 0.7901 | 0.9249 | 645 | 56 | 0.0893 | 5 / 6 |
| 2022 | control_w95 | 0.0090 | 1.0000 | 0.9510 | 0.9857 | 10072 | 622 | 0.0257 | 16 / 16 |
| 2022 | w93 | 0.0094 | 1.0464 | 0.9314 | 0.9857 | 9803 | 605 | 0.0264 | 16 / 16 |
| 2022 | w90 | 0.0110 | 1.2186 | 0.9020 | 0.9834 | 8949 | 538 | 0.0316 | 16 / 16 |
| 2022 | run95 | 0.0115 | 1.2804 | 0.8824 | 0.9834 | 8700 | 540 | 0.0315 | 16 / 16 |
| 2022 | run90 | 0.0115 | 1.2804 | 0.8824 | 0.9834 | 8700 | 540 | 0.0315 | 16 / 16 |
| 2023 | control_w95 | 0.0182 | 1.0000 | 0.9501 | 0.8848 | 5992 | 475 | 0.0842 | 36 / 38 |
| 2023 | w93 | 0.0209 | 1.1481 | 0.9311 | 0.8630 | 5433 | 470 | 0.0830 | 36 / 38 |
| 2023 | w90 | 0.0242 | 1.3301 | 0.9002 | 0.8361 | 4852 | 442 | 0.0905 | 35 / 38 |
| 2023 | run95 | 0.0329 | 1.8075 | 0.7910 | 0.7721 | 3782 | 388 | 0.1108 | 33 / 38 |
| 2023 | run90 | 0.0366 | 2.0091 | 0.7767 | 0.7401 | 3421 | 370 | 0.1216 | 33 / 38 |

Bir kuralın geçtiği yerlerde kazanç küçüktür. 2022'de `w90`, yanlış-alarm pencerelerini 10072'den 8949'a düşürür ve
dönem kesinliğini 0.0257'den 0.0316'ya çıkarır. Geçen hücreler arasındaki en yüksek dönem kesinliği, 2017'de
`run95` ve `run90` için 0.0893'tür; kontrolde 0.0588'dir. Değerlendirme recall'u kalibrasyon recall'unun epeyce altına
düşebilir: 2023'te kontrol için 0.8848, kalibrasyonda 0.9501'dir.

## Pozitif penceresi olmayan yıl

2018'de pozitif pencere yoktur, bu yüzden recall tabanlı koşullar uygulanamaz ve yıl kapıya tabi değildir. Tablo
yalnızca yanlış alarmları gösterir.

| kural | eşik | YA pencereleri | dönemler |
| --- | --- | --- | --- |
| control_w95 | 0.0044 | 359 | 30 |
| w93 | 0.0140 | 104 | 15 |
| w90 | 0.0529 | 1 | 1 |
| run95 | 0.0031 | 442 | 40 |
| run90 | 0.0031 | 442 | 40 |

## Belirsizlik

Altı pozitif yıl için kontrole karşı farkların eşleştirilmiş tam-HARP bootstrap aralıkları (1000 çekim, seed 24).
Negatif bir yanlış-alarm farkı, kontrolden daha az yanlış-alarm penceresi demektir. Aralıklar, donmuş seçilen
eşiklere koşulludur. Eşik seçiminin kendi belirsizliğini ve yeniden eğitim belirsizliğini içermez ve çoklu
karşılaştırma için düzeltilmemiştir.

| yıl | kural | dönem kesinliği farkı alt | dönem kesinliği farkı üst | YA pencere farkı alt | YA pencere farkı üst |
| --- | --- | --- | --- | --- | --- |
| 2014 | w93 | -0.0046 | 0.0208 | -1234.1 | -780.0 |
| 2014 | w90 | 0.0340 | 0.1015 | -7582.2 | -5007.9 |
| 2014 | run95 | -0.0025 | 0.0317 | -2774.1 | -1825.0 |
| 2014 | run90 | 0.0597 | 0.1466 | -10535.5 | -6973.9 |
| 2015 | w93 | 0.0035 | 0.0284 | -3015.2 | -1846.8 |
| 2015 | w90 | 0.0215 | 0.0808 | -6490.0 | -3996.9 |
| 2015 | run95 | 0.0215 | 0.0808 | -6490.0 | -3996.9 |
| 2015 | run90 | 0.0403 | 0.1338 | -8742.1 | -5428.7 |
| 2016 | w93 | -0.0002 | 0.0244 | -724.0 | -279.0 |
| 2016 | w90 | 0.0000 | 0.0418 | -1506.2 | -600.0 |
| 2016 | run95 | 0.0026 | 0.0913 | -1946.0 | -767.9 |
| 2016 | run90 | -0.0060 | 0.0531 | -2541.4 | -1068.8 |
| 2017 | w93 | -0.0056 | 0.0122 | -95.0 | -33.0 |
| 2017 | w90 | 0.0000 | 0.0704 | -401.0 | -124.0 |
| 2017 | run95 | -0.0031 | 0.1307 | -1019.0 | -293.9 |
| 2017 | run90 | -0.0031 | 0.1307 | -1019.0 | -293.9 |
| 2022 | w93 | -0.0002 | 0.0020 | -342.0 | -203.0 |
| 2022 | w90 | 0.0015 | 0.0129 | -1438.2 | -854.0 |
| 2022 | run95 | 0.0015 | 0.0125 | -1775.0 | -1044.8 |
| 2022 | run90 | 0.0015 | 0.0125 | -1775.0 | -1044.8 |
| 2023 | w93 | -0.0086 | 0.0066 | -724.0 | -408.0 |
| 2023 | w90 | -0.0087 | 0.0241 | -1463.0 | -845.0 |
| 2023 | run95 | 0.0008 | 0.0552 | -2778.2 | -1656.9 |
| 2023 | run90 | 0.0036 | 0.0725 | -3227.2 | -1936.8 |

## Sınırlar

- Sonuç, zaten incelenmiş yıllar üzerinde uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir. Sayılar
  örtüşen tahmin pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir.
- Bazı kalibrasyon yıllarında az sayıda pozitif seri vardır (2017 için kalibrasyon yılında 7), bu yüzden seçilen
  eşikler gürültülü olabilir. Bir başarısızlık, bu kayıtta önceki yıl recall hedefinin güvenilmez bir rehber
  olduğunu gösterir, daha iyi bir eşiğin var olmadığını değil.
- Kurallar, hedefler ve kabul koşulları sürüm 1 ile aynıdır ve bu kol için ayarlanmamıştır. İki TCN kolu için
  olumsuz sonuç, bu protokol dondurulmadan önce biliniyordu.
- Özgün dosyalar yerine shard'lar yeniden üretildi. 20'sinin hepsi donmuş hash'leriyle eşleşti; kod hash farkı ve
  önceki iki indirme denemesinin bilinmeyen boyutu için [kanıt kurtarma raporuna](evidence-recovery-20261108.tr.md)
  bakın.
- Bu çalıştırmada kullanılan model dosyaları ve girdiler yeni bir klona kopyalandı. Model dosyalarının iki yarım
  kopyası hash ile tespit edilip tek çalıştırmadan önce değiştirildi. G2 kontrolü de her model dosyasını doğruladı.

## Yeniden üretim

Çalıştırma, yeni bir çıktı dizinine tek geçiştir. `artifacts/` içinde donmuş girdileri gerektirir: yıllık tahminler,
walk-forward artifact'ı ve doğrulanmış shard'lar.

```sh
python scripts/audit_threshold_selection_baseline.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/threshold_selection_baseline_20261108_r1
python -m pytest -q tests/test_threshold_selection_baseline_audit.py
```
