# Benimsenen hatta alarm soğuma süresi ve alarm yanlış pozitiflerinin yönü (2026-11-25)

## Karar

Geliştirme temeli: yeniden etiketlenmiş tablo `artifacts/relabelled_development_20261111_r1` ve benimsenen hat
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). Temel 2026-11-12 tarihinde değişti, çünkü dondurulmuş
etiketler eşlenmiş 2022 ile 2023 arası M/X patlamalarının %30'undan azını kapsıyordu. Daha önce incelenmiş yıllar:
uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir.

Okuma `C3_no_gain`, sonuç etiketi `result:no-gain`; kural herhangi bir sonuçtan önce
[`config/alert-cooldown-v1.json`](../config/alert-cooldown-v1.json) içinde donduruldu. Protokol bir `acceptance_rule`
taşıyor (`decision.candidates_meeting_goal >= 1`); Hale `interpret_result`, `artifacts/alert_cooldown_20261125_r1` üzerinde
gözlenen değer 0 ile `reject` döndürüyor. Sonuç bu karardır. 24 veya 48 saatlik sabit ve nedensel bir soğuma süresi,
dondurulmuş kurala göre alarm precision değerini yükseltmiyor.

- Yıllık birincil ölçütü karşılayan yıllar `cooldown_24h` için: yok (altı yılda); `cooldown_48h` bunu yalnızca
  2016 yılında karşılıyor. İkisi de `cycle25_primary` koşulunu (2022 ve 2023) karşılamıyor, dolayısıyla `C2_partial` da
  geçerli değil.
- Alarm precision değeri `cooldown_24h` için 2015, 2016 yıllarında, `cooldown_48h` için 2016, 2022, 2023 yıllarında
  kontrolün üstünde; sırasıyla 2014, 2017, 2022, 2023 ve 2014, 2015, 2017 yıllarında kontrolün altında. Precision farkının eşli
  HARP kümeli bootstrap aralığının alt sınırı iki aday için de hiçbir yılda 0'ın üstünde değil
  (`cooldown_48h` için 2016'da alt sınır tam olarak 0.0000).
- 25. döngüde `cooldown_48h` precision değeri kontrolden yüksek (2022 yedek kural yılında 0.4934, kontrol 0.4727;
  2023'te 0.4396, kontrol 0.4263), ancak daha fazla pozitif koşu kaçırıyor
  (72 koşuda 33, kontrol 32; 159 koşuda 73, kontrol 68) ve pencere recall değeri 0.1068 ve 0.0545
  düşüyor; bu 0.02 toleransının üstünde.
- Soğuma süresi yanlış pozitif pencerelerle birlikte doğru pozitif pencereleri de kaldırıyor. Altı yılda `cooldown_24h`
  3040 alarm penceresi kaldırıyor; bunların 1613 tanesi TP, 1427 tanesi FP. `cooldown_48h` 1685 pencere kaldırıyor;
  792 tanesi TP, 893 tanesi FP. Pencere recall düşüşü `cooldown_24h` için 0.1164 ile 0.3774 arasında,
  `cooldown_48h` için 0.0140 ile 0.2189 arasında; yalnızca `cooldown_48h` için 2016 yılında 0.02 içinde kalıyor.
- İkincil, raporlanır ve yargılanmaz: alarm precision değeri kontrol için 2014, 2015, 2017 yıllarında, iki soğuma süresi için
  2014, 2015, 2016, 2017 yıllarında en az 0.50. 2022 ve 2023 her aday için 0.50 altında kalıyor.
- Kontrol alarm yanlış pozitiflerinin betimleyici yön ayrımı (altı yılda 4227 pencere): `lingering` pencerelerinin
  payı 0.1875 (2014), 0.3873 (2015), 0.4862 (2016), 0.8889 (2017), 0.3132 (2022), 0.3305 (2023); `early` pencerelerinin payı
  0.1969 (2014), 0.1860 (2015), 0.0000 (2016), 0.0000 (2017), 0.1528 (2022), 0.2289 (2023); `between` pencerelerinin payı
  0.3219 (2014), 0.2516 (2015), 0.0826 (2016), 0.0000 (2017), 0.2479 (2022), 0.1966 (2023). Üçü birlikte, yeniden etiketlenmiş 25. döngü teşhisinin
  72 saat içindeki payını yeniden veriyor (0.7063 (2014), 0.8249 (2015), 0.5688 (2016), 0.8889 (2017), 0.7139 (2022), 0.7561 (2023)). En büyük sınıf:
  2014 için `between`, 2015 için `lingering`, 2016 için `lingering`, 2017 için `lingering`, 2022 için `lingering`, 2023 için `lingering`. Bu bölümün okuma kuralı yoktur ve hiçbir şeye karar vermez.

Sonuç: bu kanıta göre sabit ve nedensel bir soğuma süresi daha yüksek alarm precision değerine giden bir yol değil.
Hiçbir model terfi ettirilmedi; hiçbir alarm, eşik, çalışma noktası veya pano ayarı değiştirilmedi. Hiçbir model
eğitilmedi (0 model eğitimi) ve hiçbir şey indirilmedi. Ayrılmış 2024 ile 2025 arası teste erişilmedi.

## Neden denendi

Fikir kaydı #2. [Yeniden etiketlenmiş 25. döngü teşhisi](cycle25-diagnostic-relabelled-20261112.tr.md) (D5), 2022 ve 2023'te
alarm yanlış pozitif pencerelerinin 0.7139 ve 0.7561'inin aynı HARP'ın pozitif bir penceresine 72 saat içinde olduğunu
buldu, ancak 72 saatlik aralığı simetrik: bu alarmların patlamadan önce mi geldiğini yoksa sonrasında mı açık kaldığını
söylemiyor. Ek bilgi ([SGAS patlama geçmişi](activity-history-relabelled-20261112.tr.md),
[gecikmesiz geçmiş tavanı](history-latency-ceiling-20261112.tr.md)) ve [daha geniş bir ufuk](horizon-72h-20261116.tr.md) alarm
precision değerini yükseltmedi. Soğuma süresi yeni bilgi gerektirmez: yalnızca modelin kendi geçmiş çıktılarını
kullanır. Önceki kalıcılık kuralları ([alarm kalıcılığı](alarm-persistence-results-20261107.tr.md),
[eşik ve kalıcılık](threshold-tradeoff-results-20261107.tr.md)) dondurulmuş etiket temelinde ve alarm katmanı dışında
sınandı; hiçbir soğuma süresi sınanmadı.

## Ne çalıştırıldı

Protokol, birleştirildiği haliyle tam olarak bir kez, `main` commit `746de33` üzerinden çalıştırıldı: 0 model eğitimi,
2 soğuma süresi adayı ve betimleyici yön ayrımı. Duvar saati süresi 22 saniye.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_alert_cooldown --config config/alert-cooldown-v1.json --output artifacts/alert_cooldown_20261125_r1
```

| öğe | sha256 |
| --- | --- |
| `config/alert-cooldown-v1.json` | `ebae981393830c7b53ed1ff4cce68f8e9a4ebfcdb4b25c8e701fe76224053690` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (kontrol) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `artifacts/relabelled_development_20261111_r1/report.json` (etiketler) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `artifacts/alert_cooldown_20261125_r1/selections.json` | `72baf0591439bf2a648d6fec4f8c9f0e843c838595a5c03ad209094f5ea17e87` |
| `artifacts/alert_cooldown_20261125_r1/report.json` | `f3e45dde103a13d21885e5469f2148db84947be5d36b7ab34812b0334fff6a6f` |
| `artifacts/alert_cooldown_20261125_r1/results.csv` | `f1d7a46ddb5c3bbb3301334c0d9b08340653618a9c5459e7e5024143bc66bb9e` |
| `artifacts/alert_cooldown_20261125_r1/intervals.csv` | `ba697747492632faefb613ff41a3ba20c9ec0cefc2cb50117002d40dcf5bbdb4` |
| `artifacts/alert_cooldown_20261125_r1/directions.csv` | `37e1a312fe8f6c6072cecd99cda9dbbc0272412635a8269e0a9415aa57c9ef7c` |
| `artifacts/alert_cooldown_20261125_r1/offset_quantiles.csv` | `03f4e5409ca8475c41e7d1ac24841e44e24cae1c7a3eab0a1eba909637e49d4e` |
| `artifacts/alert_cooldown_20261125_r1/offset_bins.csv` | `68119525a63277c2c06643071441d9aa4ddbdec9ec1e53d4b443a9a37b435674` |

Çalıştırıcı, kontrol raporunu, yıllık `predictions.parquet` ve `thresholds.json` dosyalarını ve yeniden etiketlenmiş
tablonun her parçasını kullanmadan önce kayıtlı sha256 değerleriyle karşılaştırdı. `models.joblib` hiç açılmadı. Kontrolün
ve iki adayın alarm durumları ile kayıtlı eşikler, herhangi bir değerlendirme etiketi okunmadan önce diske yazıldı ve
özetlendi (`selections.json`). Kontrol, kayıtlı `alert_alarm` sütununu her yıl tam olarak yeniden üretiyor.

## Yöntem

Popülasyon: kontrol çıktısının değerlendirme pencereleri, HARP ve saat başına bir pencere; yıllar 2014, 2015, 2016, 2017,
2022 ve 2023. 2022 bir alarm yedek kural yılıdır: kayıtlı alarm eşiği `config/walk-forward-v2.json` yedek kuralından
gelir ve her tabloda işaretlidir.

Adaylar. `control`: kayıtlı topluluk olasılığı yılın kayıtlı alarm eşiğinde veya üstündeyse alarm. `cooldown_24h`:
olasılık eşikte veya üstündeyse ve HARP'ın eşikte veya üstünde kalan ardışık saatlik pencere dizisi en çok 24 uzunluğundaysa
alarm açıktır; 25. ardışık saatten itibaren alarm, bir pencere eşiğin altına düşene kadar bastırılır. `cooldown_48h`:
aynı kural 48 saatle. Bir HARP'ın saatlik pencerelerindeki boşluk diziyi bitirir. Kural nedenseldir: yalnızca aynı
HARP'ın şimdiki ve önceki pencerelerinin kayıtlı olasılıklarını ve kayıtlı eşiği kullanır; hiçbir etiket, sonraki pencere
veya başka HARP kullanılmaz. Hiçbir eşik seçilmez ve yalnızca alarm katmanı değişir; izleme katmanı kontrolün kayıtlı
izleme katmanıdır.

Kabul ölçütü, [`config/activity-history-v2.json`](../config/activity-history-v2.json) ile aynıdır: bir aday, alarm precision
değeri kontrolden yüksekse, kaçırdığı pozitif koşular kontrolden fazla değilse ve pencere recall değeri en çok 0.02
düşüyorsa yıllık birincil ölçütü karşılar. `all_year_primary`: bu altı yılın hepsinde geçerlidir. `cycle25_primary`: hem
2022 hem 2023'te geçerlidir. Bir aday, `all_year_primary` geçerliyse veya `cycle25_primary` geçerliyse ve precision
farkının eşli HARP kümeli bootstrap aralığının (1000 çekim, tohum 24, yüzde 2.5 ve 97.5 çeyreklikleri) alt sınırı hem
2022 hem 2023'te 0'ın üstündeyse hedefi karşılar.

Okuma kuralı, bu sırayla uygulanır: en az bir soğuma süresi hedefi karşılıyorsa `C1_goal_met`; değilse en az biri
`cycle25_primary` koşulunu karşılıyorsa `C2_partial`; değilse `C3_no_gain`.

Sayılar örtüşen saatlik pencerelerdir. Pozitif koşu, bir HARP'ın bitişik pozitif pencereler grubudur; alarm epizodu,
bir HARP'ın bitişik alarm pencereleri grubudur. Hiçbiri bağımsız bir olay değildir.

## Alarm katmanı

Precision, sağlanan pencere recall değeri ve kaçırılan pozitif koşularla birlikte verilir. Aralıklar her adayın HARP
kümeli bootstrap aralıklarıdır.

| yıl | aday | yedek kural | alarm eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | alarm pencereleri | alarm verilen pozitif koşular | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 22 | 66/88 |
| 2014 | `cooldown_24h` | hayır | 0.4627 | 398 | 240 | 2038 | 75675 | 0.1634 | [0.0698, 0.2416] | 0.6238 | [0.3550, 0.8386] | 0.9709 | 0.9689 | 638 | 20 | 68/88 |
| 2014 | `cooldown_48h` | hayır | 0.4627 | 516 | 298 | 1920 | 75617 | 0.2118 | [0.0878, 0.3180] | 0.6339 | [0.3897, 0.8268] | 0.9717 | 0.9689 | 814 | 21 | 67/88 |
| 2015 | `control` | hayır | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 30 | 27/57 |
| 2015 | `cooldown_24h` | hayır | 0.2631 | 375 | 298 | 1086 | 68795 | 0.2567 | [0.1224, 0.3989] | 0.5572 | [0.3463, 0.7259] | 0.9804 | 0.9793 | 673 | 29 | 28/57 |
| 2015 | `cooldown_48h` | hayır | 0.2631 | 443 | 376 | 1018 | 68717 | 0.3032 | [0.1466, 0.4553] | 0.5409 | [0.3305, 0.7013] | 0.9802 | 0.9793 | 819 | 30 | 27/57 |
| 2016 | `control` | hayır | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 5 | 3/8 |
| 2016 | `cooldown_24h` | hayır | 0.2564 | 61 | 56 | 153 | 42872 | 0.2850 | [0.0000, 0.4713] | 0.5214 | [0.0000, 0.7731] | 0.9952 | 0.9950 | 117 | 5 | 3/8 |
| 2016 | `cooldown_48h` | hayır | 0.2564 | 91 | 56 | 123 | 42872 | 0.4252 | [0.0000, 0.8161] | 0.6190 | [0.0000, 0.8354] | 0.9959 | 0.9950 | 147 | 5 | 3/8 |
| 2017 | `control` | hayır | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3 | 3/6 |
| 2017 | `cooldown_24h` | hayır | 0.4145 | 77 | 15 | 188 | 19563 | 0.2906 | [0.0000, 0.3846] | 0.8370 | [0.0000, 1.0000] | 0.9898 | 0.9866 | 92 | 3 | 3/6 |
| 2017 | `cooldown_48h` | hayır | 0.4145 | 119 | 21 | 146 | 19557 | 0.4491 | [0.0000, 0.6615] | 0.8500 | [0.0000, 1.0000] | 0.9916 | 0.9866 | 140 | 3 | 3/6 |
| 2022 | `control` | evet | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 40 | 32/72 |
| 2022 | `cooldown_24h` | evet | 0.1570 | 543 | 690 | 1647 | 62713 | 0.2479 | [0.1642, 0.3258] | 0.4404 | [0.3110, 0.5438] | 0.9644 | 0.9666 | 1233 | 34 | 38/72 |
| 2022 | `cooldown_48h` | evet | 0.1570 | 822 | 844 | 1368 | 62559 | 0.3753 | [0.2523, 0.4857] | 0.4934 | [0.3703, 0.5956] | 0.9663 | 0.9666 | 1666 | 39 | 33/72 |
| 2023 | `control` | hayır | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 91 | 68/159 |
| 2023 | `cooldown_24h` | hayır | 0.2689 | 1080 | 1501 | 3011 | 91399 | 0.2640 | [0.2080, 0.3180] | 0.4184 | [0.3420, 0.5027] | 0.9535 | 0.9578 | 2581 | 83 | 76/159 |
| 2023 | `cooldown_48h` | hayır | 0.2689 | 1364 | 1739 | 2727 | 91161 | 0.3334 | [0.2634, 0.3965] | 0.4396 | [0.3643, 0.5203] | 0.9540 | 0.9578 | 3103 | 86 | 73/159 |

## Kabul

`precision farkı`, aday eksi kontroldür. `recall düşüşü`, kontrol recall değeri eksi aday recall değeridir. Aralık,
precision farkının eşli HARP kümeli bootstrap aralığıdır. 2017 yılında 1000 çekimin 982 tanesi kullanılabildi
(kontrolün veya adayın hiç alarm penceresi olmayan çekim atlanır).

| yıl | aday | yedek kural | kontrol precision | aday precision | precision farkı | fark %95 aralığı | kullanılan bootstrap çekimi | recall düşüşü | kontrol kaçırılan koşu | aday kaçırılan koşu | precision daha yüksek | kaçırılan koşu daha fazla değil | recall düşüşü en çok 0.02 | yıllık birincil ölçüt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `cooldown_24h` | hayır | 0.6825 | 0.6238 | -0.0587 | [-0.1312, 0.0360] | 1000 | 0.1190 | 66 | 68 | hayır | hayır | hayır | hayır |
| 2014 | `cooldown_48h` | hayır | 0.6825 | 0.6339 | -0.0486 | [-0.0802, -0.0041] | 1000 | 0.0706 | 66 | 67 | hayır | hayır | hayır | hayır |
| 2015 | `cooldown_24h` | hayır | 0.5439 | 0.5572 | 0.0133 | [-0.1480, 0.1566] | 1000 | 0.1164 | 27 | 28 | evet | hayır | hayır | hayır |
| 2015 | `cooldown_48h` | hayır | 0.5439 | 0.5409 | -0.0030 | [-0.1020, 0.0846] | 1000 | 0.0698 | 27 | 27 | hayır | evet | hayır | hayır |
| 2016 | `cooldown_24h` | hayır | 0.4631 | 0.5214 | 0.0583 | [-0.0134, 0.2090] | 1000 | 0.1542 | 3 | 3 | evet | evet | hayır | hayır |
| 2016 | `cooldown_48h` | hayır | 0.4631 | 0.6190 | 0.1560 | [0.0000, 0.2896] | 1000 | 0.0140 | 3 | 3 | evet | evet | evet | evet |
| 2017 | `cooldown_24h` | hayır | 0.8676 | 0.8370 | -0.0307 | [-0.1741, 0.2182] | 982 | 0.3774 | 3 | 3 | hayır | evet | hayır | hayır |
| 2017 | `cooldown_48h` | hayır | 0.8676 | 0.8500 | -0.0176 | [-0.0944, 0.0957] | 982 | 0.2189 | 3 | 3 | hayır | evet | hayır | hayır |
| 2022 | `cooldown_24h` | evet | 0.4727 | 0.4404 | -0.0323 | [-0.1195, 0.0360] | 1000 | 0.2342 | 32 | 38 | hayır | hayır | hayır | hayır |
| 2022 | `cooldown_48h` | evet | 0.4727 | 0.4934 | 0.0207 | [-0.0426, 0.0718] | 1000 | 0.1068 | 32 | 33 | evet | hayır | hayır | hayır |
| 2023 | `cooldown_24h` | hayır | 0.4263 | 0.4184 | -0.0078 | [-0.0553, 0.0349] | 1000 | 0.1239 | 68 | 76 | hayır | hayır | hayır | hayır |
| 2023 | `cooldown_48h` | hayır | 0.4263 | 0.4396 | 0.0133 | [-0.0191, 0.0414] | 1000 | 0.0545 | 68 | 73 | evet | hayır | hayır | hayır |

| aday | yıllık birincil ölçütü karşılayan yıllar | all_year_primary | cycle25_primary | 2022 ve 2023 için bootstrap alt sınırı 0 üstünde | hedef karşılandı | alarm precision en az 0.50 olan yıllar (ikincil) |
| --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  | 2014, 2015, 2017 |
| `cooldown_24h` | yok | hayır | hayır | hayır | hayır | 2014, 2015, 2016, 2017 |
| `cooldown_48h` | 2016 | hayır | hayır | hayır | hayır | 2014, 2015, 2016, 2017 |

Her soğuma süresinin kontrole göre kaldırdığı pencereler:

| yıl | aday | yedek kural | kontrol alarm pencereleri | kaldırılan alarm pencereleri | kaldırılan TP pencereleri | kaldırılan FP pencereleri | kaldırılan pencerelerde FP payı |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `cooldown_24h` | hayır | 1008 | 370 | 290 | 80 | 0.2162 |
| 2014 | `cooldown_48h` | hayır | 1008 | 194 | 172 | 22 | 0.1134 |
| 2015 | `cooldown_24h` | hayır | 1002 | 329 | 170 | 159 | 0.4833 |
| 2015 | `cooldown_48h` | hayır | 1002 | 183 | 102 | 81 | 0.4426 |
| 2016 | `cooldown_24h` | hayır | 203 | 86 | 33 | 53 | 0.6163 |
| 2016 | `cooldown_48h` | hayır | 203 | 56 | 3 | 53 | 0.9464 |
| 2017 | `cooldown_24h` | hayır | 204 | 112 | 100 | 12 | 0.1071 |
| 2017 | `cooldown_48h` | hayır | 204 | 64 | 58 | 6 | 0.0938 |
| 2022 | `cooldown_24h` | evet | 2234 | 1001 | 513 | 488 | 0.4875 |
| 2022 | `cooldown_48h` | evet | 2234 | 568 | 234 | 334 | 0.5880 |
| 2023 | `cooldown_24h` | hayır | 3723 | 1142 | 507 | 635 | 0.5560 |
| 2023 | `cooldown_48h` | hayır | 3723 | 620 | 223 | 397 | 0.6403 |

## Alarm epizotları ve gecikme

Soğuma süresi epizotları kısaltır, hiçbirini bölmez veya eklemez; bu yüzden alarm epizodu sayısı her yıl kontrolle
aynıdır ve isabetli epizot sayısı artamaz. Gecikme, alarm verilen pozitif koşularda, pozitif koşunun başlangıcından ilk
alarm penceresine kadar geçen saattir. Medyan gecikme `cooldown_24h` için 2014, 2015, 2022, 2023 yıllarında,
`cooldown_48h` için 2014, 2023 yıllarında kontrolün üstünde.

| yıl | aday | yedek kural | alarm epizotları | isabetli epizotlar | epizot precision | medyan alarm gecikmesi (saat) | en büyük alarm gecikmesi (saat) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 90 | 51 | 0.5667 | 1.5 | 28.0 |
| 2014 | `cooldown_24h` | hayır | 90 | 51 | 0.5667 | 6.5 | 32.0 |
| 2014 | `cooldown_48h` | hayır | 90 | 51 | 0.5667 | 2.0 | 28.0 |
| 2015 | `control` | hayır | 99 | 47 | 0.4747 | 0.0 | 30.0 |
| 2015 | `cooldown_24h` | hayır | 99 | 47 | 0.4747 | 3.0 | 30.0 |
| 2015 | `cooldown_48h` | hayır | 99 | 47 | 0.4747 | 0.0 | 30.0 |
| 2016 | `control` | hayır | 21 | 6 | 0.2857 | 1.0 | 14.0 |
| 2016 | `cooldown_24h` | hayır | 21 | 6 | 0.2857 | 1.0 | 14.0 |
| 2016 | `cooldown_48h` | hayır | 21 | 6 | 0.2857 | 1.0 | 14.0 |
| 2017 | `control` | hayır | 11 | 7 | 0.6364 | 2.0 | 21.0 |
| 2017 | `cooldown_24h` | hayır | 11 | 7 | 0.6364 | 2.0 | 21.0 |
| 2017 | `cooldown_48h` | hayır | 11 | 7 | 0.6364 | 2.0 | 21.0 |
| 2022 | `control` | evet | 139 | 51 | 0.3669 | 0.0 | 35.0 |
| 2022 | `cooldown_24h` | evet | 139 | 48 | 0.3453 | 0.5 | 69.0 |
| 2022 | `cooldown_48h` | evet | 139 | 50 | 0.3597 | 0.0 | 35.0 |
| 2023 | `control` | hayır | 358 | 137 | 0.3827 | 0.0 | 44.0 |
| 2023 | `cooldown_24h` | hayır | 358 | 134 | 0.3743 | 1.0 | 44.0 |
| 2023 | `cooldown_48h` | hayır | 358 | 137 | 0.3827 | 1.0 | 44.0 |

## İzleme katmanı

Kontrolün kayıtlı izleme katmanı; hiçbir aday onu değiştirmez ve bir kez raporlanır.

| yıl | izleme eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | alarm pencereleri | epizotlar | isabetli epizotlar | epizot precision | medyan gecikme (saat) | en büyük gecikme (saat) | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 561 | 87 | 0.1551 | 0.0 | 17.0 | 6/88 |
| 2015 | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 460 | 44 | 0.0957 | 0.0 | 19.0 | 1/57 |
| 2016 | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 150 | 6 | 0.0400 | 0.0 | 9.0 | 0/8 |
| 2017 | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 81 | 6 | 0.0741 | 0.0 | 15.0 | 1/6 |
| 2022 | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 587 | 53 | 0.0903 | 0.0 | 8.0 | 5/72 |
| 2023 | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 753 | 122 | 0.1620 | 0.0 | 22.0 | 10/159 |

İzleme katmanı accuracy değeri her yıl hep-negatif accuracy değerinin altında.

## Alarm yanlış pozitiflerinin yönü (betimleyici)

Protokolle birlikte donduruldu; okuma kuralı yoktur, hiçbir şeye karar vermez ve hiçbir aday kuralını beslemez.
Değerlendirme etiketlerini kullanır. Her alarm yanlış pozitif penceresi, yılın değerlendirme popülasyonunda aynı HARP'ın
pozitif pencerelerine göre tam olarak bir sınıfa düşer: `never_flaring_harp` (HARP'ın o yıl pozitif penceresi yok), `early`
(0'dan fazla ve en çok 72 saat sonra bir pozitif pencere var, önceki 72 saatte yok), `lingering` (0'dan fazla ve en çok
72 saat önce bir pozitif pencere var, sonraki 72 saatte yok), `between` (iki yanda da 72 saat içinde pozitif pencere var),
`flaring_harp_other` (HARP'ın o yıl pozitif penceresi var ama 72 saat içinde yok). `kaldırılan kontrol FP pencereleri`,
sınıfın soğuma süresinin artık alarm vermediği kontrol yanlış pozitif pencerelerini sayar.

Altı yılda soğuma sürelerinin sınıf başına kaldırdığı kontrol yanlış pozitif pencereleri (kaldırılan / kontrol):
`cooldown_24h` `early` 115/817, `lingering` 736/1389, `between` 372/939, `flaring_harp_other` 128/587, `never_flaring_harp` 76/495; `cooldown_48h` `early` 59/817, `lingering` 525/1389, `between` 187/939, `flaring_harp_other` 102/587, `never_flaring_harp` 20/495.
Yıllık değerler tablodadır.

| yıl | aday | yedek kural | sınıf | FP pencereleri | alarm FP pencerelerindeki pay | HARP sayısı | kaldırılan kontrol FP pencereleri |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | `early` | 63 | 0.1969 | 4 |  |
| 2014 | `control` | hayır | `lingering` | 60 | 0.1875 | 8 |  |
| 2014 | `control` | hayır | `between` | 103 | 0.3219 | 8 |  |
| 2014 | `control` | hayır | `flaring_harp_other` | 48 | 0.1500 | 2 |  |
| 2014 | `control` | hayır | `never_flaring_harp` | 46 | 0.1437 | 3 |  |
| 2014 | `cooldown_24h` | hayır | `early` | 63 | 0.2625 | 4 | 0 |
| 2014 | `cooldown_24h` | hayır | `lingering` | 26 | 0.1083 | 8 | 34 |
| 2014 | `cooldown_24h` | hayır | `between` | 76 | 0.3167 | 6 | 27 |
| 2014 | `cooldown_24h` | hayır | `flaring_harp_other` | 48 | 0.2000 | 2 | 0 |
| 2014 | `cooldown_24h` | hayır | `never_flaring_harp` | 27 | 0.1125 | 3 | 19 |
| 2014 | `cooldown_48h` | hayır | `early` | 63 | 0.2114 | 4 | 0 |
| 2014 | `cooldown_48h` | hayır | `lingering` | 50 | 0.1678 | 8 | 10 |
| 2014 | `cooldown_48h` | hayır | `between` | 91 | 0.3054 | 8 | 12 |
| 2014 | `cooldown_48h` | hayır | `flaring_harp_other` | 48 | 0.1611 | 2 | 0 |
| 2014 | `cooldown_48h` | hayır | `never_flaring_harp` | 46 | 0.1544 | 3 | 0 |
| 2015 | `control` | hayır | `early` | 85 | 0.1860 | 8 |  |
| 2015 | `control` | hayır | `lingering` | 177 | 0.3873 | 8 |  |
| 2015 | `control` | hayır | `between` | 115 | 0.2516 | 6 |  |
| 2015 | `control` | hayır | `flaring_harp_other` | 41 | 0.0897 | 3 |  |
| 2015 | `control` | hayır | `never_flaring_harp` | 39 | 0.0853 | 6 |  |
| 2015 | `cooldown_24h` | hayır | `early` | 85 | 0.2852 | 8 | 0 |
| 2015 | `cooldown_24h` | hayır | `lingering` | 77 | 0.2584 | 7 | 100 |
| 2015 | `cooldown_24h` | hayır | `between` | 62 | 0.2081 | 6 | 53 |
| 2015 | `cooldown_24h` | hayır | `flaring_harp_other` | 35 | 0.1174 | 3 | 6 |
| 2015 | `cooldown_24h` | hayır | `never_flaring_harp` | 39 | 0.1309 | 6 | 0 |
| 2015 | `cooldown_48h` | hayır | `early` | 85 | 0.2261 | 8 | 0 |
| 2015 | `cooldown_48h` | hayır | `lingering` | 124 | 0.3298 | 8 | 53 |
| 2015 | `cooldown_48h` | hayır | `between` | 93 | 0.2473 | 6 | 22 |
| 2015 | `cooldown_48h` | hayır | `flaring_harp_other` | 35 | 0.0931 | 3 | 6 |
| 2015 | `cooldown_48h` | hayır | `never_flaring_harp` | 39 | 0.1037 | 6 | 0 |
| 2016 | `control` | hayır | `early` | 0 | 0.0000 | 0 |  |
| 2016 | `control` | hayır | `lingering` | 53 | 0.4862 | 1 |  |
| 2016 | `control` | hayır | `between` | 9 | 0.0826 | 1 |  |
| 2016 | `control` | hayır | `flaring_harp_other` | 19 | 0.1743 | 1 |  |
| 2016 | `control` | hayır | `never_flaring_harp` | 28 | 0.2569 | 7 |  |
| 2016 | `cooldown_24h` | hayır | `early` | 0 | 0.0000 | 0 | 0 |
| 2016 | `cooldown_24h` | hayır | `lingering` | 0 | 0.0000 | 0 | 53 |
| 2016 | `cooldown_24h` | hayır | `between` | 9 | 0.1607 | 1 | 0 |
| 2016 | `cooldown_24h` | hayır | `flaring_harp_other` | 19 | 0.3393 | 1 | 0 |
| 2016 | `cooldown_24h` | hayır | `never_flaring_harp` | 28 | 0.5000 | 7 | 0 |
| 2016 | `cooldown_48h` | hayır | `early` | 0 | 0.0000 | 0 | 0 |
| 2016 | `cooldown_48h` | hayır | `lingering` | 0 | 0.0000 | 0 | 53 |
| 2016 | `cooldown_48h` | hayır | `between` | 9 | 0.1607 | 1 | 0 |
| 2016 | `cooldown_48h` | hayır | `flaring_harp_other` | 19 | 0.3393 | 1 | 0 |
| 2016 | `cooldown_48h` | hayır | `never_flaring_harp` | 28 | 0.5000 | 7 | 0 |
| 2017 | `control` | hayır | `early` | 0 | 0.0000 | 0 |  |
| 2017 | `control` | hayır | `lingering` | 24 | 0.8889 | 2 |  |
| 2017 | `control` | hayır | `between` | 0 | 0.0000 | 0 |  |
| 2017 | `control` | hayır | `flaring_harp_other` | 0 | 0.0000 | 0 |  |
| 2017 | `control` | hayır | `never_flaring_harp` | 3 | 0.1111 | 1 |  |
| 2017 | `cooldown_24h` | hayır | `early` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_24h` | hayır | `lingering` | 12 | 0.8000 | 1 | 12 |
| 2017 | `cooldown_24h` | hayır | `between` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_24h` | hayır | `flaring_harp_other` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_24h` | hayır | `never_flaring_harp` | 3 | 0.2000 | 1 | 0 |
| 2017 | `cooldown_48h` | hayır | `early` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_48h` | hayır | `lingering` | 18 | 0.8571 | 2 | 6 |
| 2017 | `cooldown_48h` | hayır | `between` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_48h` | hayır | `flaring_harp_other` | 0 | 0.0000 | 0 | 0 |
| 2017 | `cooldown_48h` | hayır | `never_flaring_harp` | 3 | 0.1429 | 1 | 0 |
| 2022 | `control` | evet | `early` | 180 | 0.1528 | 11 |  |
| 2022 | `control` | evet | `lingering` | 369 | 0.3132 | 15 |  |
| 2022 | `control` | evet | `between` | 292 | 0.2479 | 12 |  |
| 2022 | `control` | evet | `flaring_harp_other` | 240 | 0.2037 | 9 |  |
| 2022 | `control` | evet | `never_flaring_harp` | 97 | 0.0823 | 11 |  |
| 2022 | `cooldown_24h` | evet | `early` | 124 | 0.1797 | 11 | 56 |
| 2022 | `cooldown_24h` | evet | `lingering` | 109 | 0.1580 | 10 | 260 |
| 2022 | `cooldown_24h` | evet | `between` | 207 | 0.3000 | 10 | 85 |
| 2022 | `cooldown_24h` | evet | `flaring_harp_other` | 153 | 0.2217 | 8 | 87 |
| 2022 | `cooldown_24h` | evet | `never_flaring_harp` | 97 | 0.1406 | 11 | 0 |
| 2022 | `cooldown_48h` | evet | `early` | 153 | 0.1813 | 11 | 27 |
| 2022 | `cooldown_48h` | evet | `lingering` | 155 | 0.1836 | 13 | 214 |
| 2022 | `cooldown_48h` | evet | `between` | 284 | 0.3365 | 12 | 8 |
| 2022 | `cooldown_48h` | evet | `flaring_harp_other` | 155 | 0.1836 | 8 | 85 |
| 2022 | `cooldown_48h` | evet | `never_flaring_harp` | 97 | 0.1149 | 11 | 0 |
| 2023 | `control` | hayır | `early` | 489 | 0.2289 | 24 |  |
| 2023 | `control` | hayır | `lingering` | 706 | 0.3305 | 31 |  |
| 2023 | `control` | hayır | `between` | 420 | 0.1966 | 25 |  |
| 2023 | `control` | hayır | `flaring_harp_other` | 239 | 0.1119 | 17 |  |
| 2023 | `control` | hayır | `never_flaring_harp` | 282 | 0.1320 | 11 |  |
| 2023 | `cooldown_24h` | hayır | `early` | 430 | 0.2865 | 24 | 59 |
| 2023 | `cooldown_24h` | hayır | `lingering` | 429 | 0.2858 | 31 | 277 |
| 2023 | `cooldown_24h` | hayır | `between` | 213 | 0.1419 | 22 | 207 |
| 2023 | `cooldown_24h` | hayır | `flaring_harp_other` | 204 | 0.1359 | 17 | 35 |
| 2023 | `cooldown_24h` | hayır | `never_flaring_harp` | 225 | 0.1499 | 11 | 57 |
| 2023 | `cooldown_48h` | hayır | `early` | 457 | 0.2628 | 24 | 32 |
| 2023 | `cooldown_48h` | hayır | `lingering` | 517 | 0.2973 | 31 | 189 |
| 2023 | `cooldown_48h` | hayır | `between` | 275 | 0.1581 | 22 | 145 |
| 2023 | `cooldown_48h` | hayır | `flaring_harp_other` | 228 | 0.1311 | 17 | 11 |
| 2023 | `cooldown_48h` | hayır | `never_flaring_harp` | 262 | 0.1507 | 11 | 20 |

Patlayan HARP'ların yanlış pozitif pencerelerinin saat uzaklıkları. `hours_since_last_positive` ve
`hours_to_next_positive` yalnızca HARP'ın o yıl daha önce veya daha sonra pozitif bir penceresi varsa tanımlıdır;
`hours_to_nearest_positive` ikisinin küçüğüdür.

| yıl | aday | ölçü | pencereler | en küçük | q10 | q25 | medyan | q75 | q90 | en büyük |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `hours_since_last_positive` | 251 | 1.0 | 3.0 | 8.00 | 24.0 | 126.00 | 149.0 | 174.0 |
| 2014 | `control` | `hours_to_next_positive` | 168 | 1.0 | 3.0 | 6.00 | 18.5 | 30.25 | 46.3 | 73.0 |
| 2014 | `control` | `hours_to_nearest_positive` | 274 | 1.0 | 2.0 | 5.25 | 15.0 | 36.00 | 127.7 | 174.0 |
| 2014 | `cooldown_24h` | `hours_since_last_positive` | 190 | 1.0 | 3.0 | 10.00 | 49.0 | 134.75 | 153.1 | 174.0 |
| 2014 | `cooldown_24h` | `hours_to_next_positive` | 141 | 1.0 | 4.0 | 11.00 | 19.0 | 34.00 | 49.0 | 73.0 |
| 2014 | `cooldown_24h` | `hours_to_nearest_positive` | 213 | 1.0 | 2.0 | 6.00 | 16.0 | 54.00 | 133.8 | 174.0 |
| 2014 | `cooldown_48h` | `hours_since_last_positive` | 229 | 1.0 | 3.0 | 9.00 | 24.0 | 130.00 | 150.2 | 174.0 |
| 2014 | `cooldown_48h` | `hours_to_next_positive` | 156 | 1.0 | 3.0 | 10.00 | 19.5 | 32.00 | 47.5 | 73.0 |
| 2014 | `cooldown_48h` | `hours_to_nearest_positive` | 252 | 1.0 | 2.0 | 6.00 | 15.0 | 42.25 | 129.9 | 174.0 |
| 2015 | `control` | `hours_since_last_positive` | 334 | 1.0 | 3.0 | 7.00 | 20.0 | 49.75 | 93.7 | 224.0 |
| 2015 | `control` | `hours_to_next_positive` | 200 | 1.0 | 2.9 | 6.75 | 13.0 | 26.00 | 34.0 | 67.0 |
| 2015 | `control` | `hours_to_nearest_positive` | 418 | 1.0 | 2.0 | 6.00 | 16.0 | 39.00 | 71.3 | 224.0 |
| 2015 | `cooldown_24h` | `hours_since_last_positive` | 175 | 1.0 | 2.0 | 5.00 | 12.0 | 32.50 | 200.6 | 224.0 |
| 2015 | `cooldown_24h` | `hours_to_next_positive` | 147 | 1.0 | 3.0 | 7.00 | 14.0 | 26.50 | 35.4 | 67.0 |
| 2015 | `cooldown_24h` | `hours_to_nearest_positive` | 259 | 1.0 | 2.0 | 5.00 | 13.0 | 28.00 | 108.2 | 224.0 |
| 2015 | `cooldown_48h` | `hours_since_last_positive` | 253 | 1.0 | 3.0 | 6.00 | 12.0 | 37.00 | 109.8 | 224.0 |
| 2015 | `cooldown_48h` | `hours_to_next_positive` | 178 | 1.0 | 2.7 | 7.00 | 14.5 | 27.00 | 35.0 | 67.0 |
| 2015 | `cooldown_48h` | `hours_to_nearest_positive` | 337 | 1.0 | 2.0 | 5.00 | 13.0 | 29.00 | 92.4 | 224.0 |
| 2016 | `control` | `hours_since_last_positive` | 62 | 1.0 | 3.0 | 7.25 | 22.5 | 37.75 | 46.9 | 53.0 |
| 2016 | `control` | `hours_to_next_positive` | 28 | 1.0 | 2.0 | 4.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `control` | `hours_to_nearest_positive` | 81 | 1.0 | 2.0 | 12.00 | 32.0 | 52.00 | 170.0 | 217.0 |
| 2016 | `cooldown_24h` | `hours_since_last_positive` | 9 | 1.0 | 1.0 | 2.00 | 3.0 | 4.00 | 4.2 | 5.0 |
| 2016 | `cooldown_24h` | `hours_to_next_positive` | 28 | 1.0 | 2.0 | 4.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `cooldown_24h` | `hours_to_nearest_positive` | 28 | 1.0 | 1.0 | 2.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `cooldown_48h` | `hours_since_last_positive` | 9 | 1.0 | 1.0 | 2.00 | 3.0 | 4.00 | 4.2 | 5.0 |
| 2016 | `cooldown_48h` | `hours_to_next_positive` | 28 | 1.0 | 2.0 | 4.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2016 | `cooldown_48h` | `hours_to_nearest_positive` | 28 | 1.0 | 1.0 | 2.00 | 164.5 | 171.25 | 184.9 | 217.0 |
| 2017 | `control` | `hours_since_last_positive` | 24 | 1.0 | 2.0 | 3.75 | 6.5 | 10.00 | 14.8 | 18.0 |
| 2017 | `control` | `hours_to_next_positive` | 12 | 83.0 | 84.1 | 89.50 | 94.5 | 97.25 | 98.9 | 100.0 |
| 2017 | `control` | `hours_to_nearest_positive` | 24 | 1.0 | 2.0 | 3.75 | 6.5 | 10.00 | 14.8 | 18.0 |
| 2017 | `cooldown_24h` | `hours_since_last_positive` | 12 | 1.0 | 2.1 | 3.75 | 6.5 | 11.50 | 16.9 | 18.0 |
| 2017 | `cooldown_24h` | `hours_to_next_positive` | 12 | 83.0 | 84.1 | 89.50 | 94.5 | 97.25 | 98.9 | 100.0 |
| 2017 | `cooldown_24h` | `hours_to_nearest_positive` | 12 | 1.0 | 2.1 | 3.75 | 6.5 | 11.50 | 16.9 | 18.0 |
| 2017 | `cooldown_48h` | `hours_since_last_positive` | 18 | 1.0 | 1.7 | 3.00 | 5.0 | 7.75 | 16.3 | 18.0 |
| 2017 | `cooldown_48h` | `hours_to_next_positive` | 12 | 83.0 | 84.1 | 89.50 | 94.5 | 97.25 | 98.9 | 100.0 |
| 2017 | `cooldown_48h` | `hours_to_nearest_positive` | 18 | 1.0 | 1.7 | 3.00 | 5.0 | 7.75 | 16.3 | 18.0 |
| 2022 | `control` | `hours_since_last_positive` | 909 | 1.0 | 5.0 | 12.00 | 33.0 | 79.00 | 157.2 | 221.0 |
| 2022 | `control` | `hours_to_next_positive` | 595 | 1.0 | 4.0 | 10.00 | 31.0 | 63.00 | 117.0 | 286.0 |
| 2022 | `control` | `hours_to_nearest_positive` | 1081 | 1.0 | 3.0 | 9.00 | 26.0 | 64.00 | 112.0 | 286.0 |
| 2022 | `cooldown_24h` | `hours_since_last_positive` | 428 | 1.0 | 5.0 | 11.75 | 27.5 | 75.00 | 156.0 | 193.0 |
| 2022 | `cooldown_24h` | `hours_to_next_positive` | 449 | 1.0 | 4.0 | 13.00 | 41.0 | 75.00 | 127.2 | 286.0 |
| 2022 | `cooldown_24h` | `hours_to_nearest_positive` | 593 | 1.0 | 3.0 | 9.00 | 25.0 | 74.00 | 114.8 | 286.0 |
| 2022 | `cooldown_48h` | `hours_since_last_positive` | 575 | 1.0 | 4.0 | 9.00 | 27.0 | 64.50 | 160.6 | 194.0 |
| 2022 | `cooldown_48h` | `hours_to_next_positive` | 560 | 1.0 | 4.0 | 10.00 | 34.0 | 66.00 | 119.1 | 286.0 |
| 2022 | `cooldown_48h` | `hours_to_nearest_positive` | 747 | 1.0 | 3.0 | 7.00 | 20.0 | 55.00 | 101.0 | 286.0 |
| 2023 | `control` | `hours_since_last_positive` | 1341 | 1.0 | 4.0 | 11.00 | 28.0 | 58.00 | 91.0 | 193.0 |
| 2023 | `control` | `hours_to_next_positive` | 1409 | 1.0 | 6.8 | 17.00 | 49.0 | 95.00 | 174.2 | 248.0 |
| 2023 | `control` | `hours_to_nearest_positive` | 1854 | 1.0 | 4.0 | 9.00 | 22.5 | 50.00 | 83.0 | 213.0 |
| 2023 | `cooldown_24h` | `hours_since_last_positive` | 835 | 1.0 | 4.0 | 10.50 | 30.0 | 70.00 | 115.0 | 193.0 |
| 2023 | `cooldown_24h` | `hours_to_next_positive` | 945 | 1.0 | 6.0 | 15.00 | 38.0 | 89.00 | 152.0 | 248.0 |
| 2023 | `cooldown_24h` | `hours_to_nearest_positive` | 1276 | 1.0 | 4.0 | 9.00 | 22.0 | 57.00 | 99.5 | 213.0 |
| 2023 | `cooldown_48h` | `hours_since_last_positive` | 985 | 1.0 | 4.0 | 11.00 | 27.0 | 63.00 | 111.0 | 193.0 |
| 2023 | `cooldown_48h` | `hours_to_next_positive` | 1120 | 1.0 | 6.9 | 16.75 | 46.0 | 93.00 | 158.0 | 248.0 |
| 2023 | `cooldown_48h` | `hours_to_nearest_positive` | 1477 | 1.0 | 4.0 | 9.00 | 22.0 | 54.00 | 94.0 | 213.0 |

Aynı uzaklıkların sabit saat aralıklarındaki sayıları:

| yıl | aday | ölçü | (0,6] | (6,12] | (12,24] | (24,48] | (48,72] | (72,120] | 120 üstü |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `hours_since_last_positive` | 53 | 35 | 40 | 28 | 7 | 15 | 73 |
| 2014 | `control` | `hours_to_next_positive` | 43 | 16 | 53 | 41 | 13 | 2 | 0 |
| 2014 | `control` | `hours_to_nearest_positive` | 77 | 47 | 58 | 35 | 9 | 14 | 34 |
| 2014 | `cooldown_24h` | `hours_since_last_positive` | 32 | 27 | 20 | 16 | 7 | 15 | 73 |
| 2014 | `cooldown_24h` | `hours_to_next_positive` | 27 | 15 | 47 | 37 | 13 | 2 | 0 |
| 2014 | `cooldown_24h` | `hours_to_nearest_positive` | 56 | 39 | 38 | 23 | 9 | 14 | 34 |
| 2014 | `cooldown_48h` | `hours_since_last_positive` | 41 | 35 | 40 | 18 | 7 | 15 | 73 |
| 2014 | `cooldown_48h` | `hours_to_next_positive` | 32 | 15 | 53 | 41 | 13 | 2 | 0 |
| 2014 | `cooldown_48h` | `hours_to_nearest_positive` | 65 | 47 | 58 | 25 | 9 | 14 | 34 |
| 2015 | `control` | `hours_since_last_positive` | 77 | 55 | 49 | 67 | 44 | 21 | 21 |
| 2015 | `control` | `hours_to_next_positive` | 50 | 42 | 55 | 45 | 8 | 0 | 0 |
| 2015 | `control` | `hours_to_nearest_positive` | 118 | 62 | 77 | 75 | 45 | 21 | 20 |
| 2015 | `cooldown_24h` | `hours_since_last_positive` | 56 | 36 | 24 | 17 | 6 | 15 | 21 |
| 2015 | `cooldown_24h` | `hours_to_next_positive` | 34 | 32 | 40 | 33 | 8 | 0 | 0 |
| 2015 | `cooldown_24h` | `hours_to_nearest_positive` | 84 | 43 | 53 | 37 | 7 | 15 | 20 |
| 2015 | `cooldown_48h` | `hours_since_last_positive` | 72 | 55 | 43 | 31 | 16 | 15 | 21 |
| 2015 | `cooldown_48h` | `hours_to_next_positive` | 44 | 34 | 47 | 45 | 8 | 0 | 0 |
| 2015 | `cooldown_48h` | `hours_to_nearest_positive` | 107 | 56 | 71 | 51 | 17 | 15 | 20 |
| 2016 | `control` | `hours_since_last_positive` | 15 | 6 | 12 | 24 | 5 | 0 | 0 |
| 2016 | `control` | `hours_to_next_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `control` | `hours_to_nearest_positive` | 15 | 6 | 12 | 24 | 5 | 2 | 17 |
| 2016 | `cooldown_24h` | `hours_since_last_positive` | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2016 | `cooldown_24h` | `hours_to_next_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `cooldown_24h` | `hours_to_nearest_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `cooldown_48h` | `hours_since_last_positive` | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2016 | `cooldown_48h` | `hours_to_next_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2016 | `cooldown_48h` | `hours_to_nearest_positive` | 9 | 0 | 0 | 0 | 0 | 2 | 17 |
| 2017 | `control` | `hours_since_last_positive` | 12 | 9 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `control` | `hours_to_next_positive` | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | `control` | `hours_to_nearest_positive` | 12 | 9 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_24h` | `hours_since_last_positive` | 6 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_24h` | `hours_to_next_positive` | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | `cooldown_24h` | `hours_to_nearest_positive` | 6 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_48h` | `hours_since_last_positive` | 12 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2017 | `cooldown_48h` | `hours_to_next_positive` | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | `cooldown_48h` | `hours_to_nearest_positive` | 12 | 3 | 3 | 0 | 0 | 0 | 0 |
| 2022 | `control` | `hours_since_last_positive` | 127 | 102 | 125 | 219 | 88 | 92 | 156 |
| 2022 | `control` | `hours_to_next_positive` | 103 | 64 | 89 | 138 | 78 | 68 | 55 |
| 2022 | `control` | `hours_to_nearest_positive` | 214 | 140 | 162 | 219 | 106 | 149 | 91 |
| 2022 | `cooldown_24h` | `hours_since_last_positive` | 57 | 58 | 75 | 99 | 27 | 44 | 68 |
| 2022 | `cooldown_24h` | `hours_to_next_positive` | 68 | 40 | 60 | 90 | 73 | 66 | 52 |
| 2022 | `cooldown_24h` | `hours_to_nearest_positive` | 115 | 84 | 93 | 106 | 42 | 99 | 54 |
| 2022 | `cooldown_48h` | `hours_since_last_positive` | 103 | 79 | 83 | 147 | 27 | 44 | 92 |
| 2022 | `cooldown_48h` | `hours_to_next_positive` | 97 | 58 | 69 | 135 | 78 | 68 | 55 |
| 2022 | `cooldown_48h` | `hours_to_nearest_positive` | 184 | 111 | 108 | 144 | 45 | 101 | 54 |
| 2023 | `control` | `hours_since_last_positive` | 196 | 183 | 240 | 300 | 207 | 145 | 70 |
| 2023 | `control` | `hours_to_next_positive` | 141 | 126 | 199 | 236 | 207 | 235 | 265 |
| 2023 | `control` | `hours_to_nearest_positive` | 322 | 281 | 370 | 400 | 242 | 152 | 87 |
| 2023 | `cooldown_24h` | `hours_since_last_positive` | 131 | 119 | 129 | 153 | 110 | 123 | 70 |
| 2023 | `cooldown_24h` | `hours_to_next_positive` | 101 | 103 | 151 | 169 | 119 | 156 | 146 |
| 2023 | `cooldown_24h` | `hours_to_nearest_positive` | 224 | 202 | 246 | 238 | 162 | 117 | 87 |
| 2023 | `cooldown_48h` | `hours_since_last_positive` | 151 | 143 | 175 | 189 | 134 | 123 | 70 |
| 2023 | `cooldown_48h` | `hours_to_next_positive` | 112 | 104 | 163 | 196 | 157 | 202 | 186 |
| 2023 | `cooldown_48h` | `hours_to_nearest_positive` | 255 | 227 | 300 | 283 | 184 | 141 | 87 |

Her kontrol alarm yanlış pozitif penceresi için sınıfı, iki uzaklığı ve her adayın alarmı koruyup korumadığını içeren
birer satır `artifacts/alert_cooldown_20261125_r1/control_fp_windows_<year>.parquet` dosyalarında saklanır.

## Dondurulmuş etiket sonuçları

Karşılaştırma için görünür tutulur; [dondurulmuş etiketli iki katmanlı rapor](two-tier-20261110.tr.md) içindeki `alert_0.5`
satırlarından kopyalandı, yeniden hesaplanmadı: temel değişmeden önce, dondurulmuş etiketlerle alarm katmanı. Dondurulmuş
etiketlerde hiçbir soğuma süresi çalıştırılmadı ve etiketler farklı olduğu için değerler yukarıdaki tablolarla
karşılaştırılabilir değildir.

| yıl | yedek kural | eşik | TP | FP | FN | recall | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | alarm pencereleri | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | hayır | 0.4743 | 644 | 248 | 1666 | 0.2788 | 0.7220 | [0.4414, 0.8625] | 0.9746 | 0.9693 | 892 | 63/83 |
| 2015 | hayır | 0.2578 | 551 | 476 | 804 | 0.4066 | 0.5365 | [0.3109, 0.7080] | 0.9815 | 0.9804 | 1027 | 24/51 |
| 2016 | hayır | 0.2515 | 76 | 112 | 105 | 0.4199 | 0.4043 | [0.0000, 0.5249] | 0.9950 | 0.9958 | 188 | 2/7 |
| 2017 | hayır | 0.3397 | 182 | 43 | 71 | 0.7194 | 0.8089 | [0.0000, 0.9691] | 0.9942 | 0.9870 | 225 | 2/6 |
| 2022 | evet | 0.0931 | 221 | 1111 | 200 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 1332 | 2/16 |
| 2023 | hayır | 0.3538 | 79 | 106 | 702 | 0.1012 | 0.4270 | [0.0968, 0.7441] | 0.9866 | 0.9871 | 185 | 30/38 |

## Sınırlar

Daha önce incelenmiş yıllar: uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir. Soğuma süresi yalnızca
alarm pencerelerini kaldırır: pencere recall değeri artamaz, kaçırılan pozitif koşular azalamaz ve alarm gecikmesi
kısalamaz; olası tek kazanç precision idi. Ardışık saatlik pencereler 24 saatlerinin 23'ünde örtüşür ve HARP'lar tekrar
eder; bu yüzden sayılar pencereler ve pozitif koşulardır, asla bağımsız olaylar değildir ve aralıklar HARP kümelidir.
2016 ve 2017'de az pozitif koşu var (8 ve 6) ve aralıkları geniştir; `cooldown_48h` adayının 2016'daki tek yıllık kabulü
147 alarm penceresine dayanır. Yön sınıfları değerlendirme etiketlerini kullanır ve değerlendirme
popülasyonunun kenarlarında (bir HARP'ın kayıtlı pencerelerinin ve yılın başı ve sonu) sansürlüdür; hemen dışarıdaki bir
patlama bir pencereyi ilgisiz gösterebilir. Sınıflar patlama tepe zamanlarına göre değil, pozitif pencerelere göredir.
Yeniden etiketlenmiş etiketler NOAA SGAS ve JSOC `NOAA_ARS` ile yapılan bir ilişkilendirmedir, kesin gerçek değildir. İki
soğuma süresi önceden sabitlendi; başka bir süre denenmedi ve bu sonuçlardan hiçbiri seçilemez. 2022 bir alarm yedek
kural yılıdır.

## Yeniden üretim

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_alert_cooldown --config config/alert-cooldown-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/alert-cooldown-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `ebae981393830c7b53ed1ff4cce68f8e9a4ebfcdb4b25c8e701fe76224053690`; selections sha256
`72baf0591439bf2a648d6fec4f8c9f0e843c838595a5c03ad209094f5ea17e87`; `report.json` sha256
`f3e45dde103a13d21885e5469f2148db84947be5d36b7ab34812b0334fff6a6f`. Yeni bir çıktı dizini kullanın; çalıştırıcı var olan
bir dizinin üzerine yazmayı reddeder.
