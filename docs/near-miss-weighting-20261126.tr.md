# Benimsenen hatta alarm katmanında ramak kala eğitim ağırlıkları (2026-11-26)

## Karar

Geliştirme temeli: yeniden etiketlenmiş tablo `artifacts/relabelled_development_20261111_r1` ve benimsenen hat
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). Temel 2026-11-12 tarihinde değişti, çünkü dondurulmuş
etiketler eşlenmiş 2022 ile 2023 arası M/X patlamalarının %30'undan azını kapsıyordu. Daha önce incelenmiş yıllar:
uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir.

Okuma `N3_no_gain`, sonuç etiketi `result:no-gain`; kural herhangi bir sonuçtan önce
[`config/near-miss-weighting-v1.json`](../config/near-miss-weighting-v1.json) içinde donduruldu. Protokol bir
`acceptance_rule` taşıyor (`decision.near_miss_w3_goal_met_and_beats_uniform >= 1`); Hale `interpret_result`,
`artifacts/near_miss_weighting_20261126_r1` üzerinde gözlenen değer 0 ile `reject` döndürüyor. Sonuç bu karardır ve
dondurulmuş okuma onunla uyumludur: hiçbir aday kontrole karşı hedefi karşılamıyor, dolayısıyla `N2_reweighting_only` da
geçerli değil. Eğitimde patlamalı HARP'ların ramak kala negatiflerine 3 ağırlığı vermek, dondurulmuş kurala göre alarm
precision değerini yükseltmiyor; tüm eğitim negatiflerinin eşit toplamlı yeniden ağırlıklandırılması da yükseltmiyor.

- `near_miss_w3` yıllık birincil ölçütü yalnızca 2015 yılında karşılıyor (altı yılda); `uniform_matched` de öyle.
  İkisi de `all_year_primary` veya `cycle25_primary` (2022 ve 2023) koşulunu karşılamıyor.
- `near_miss_w3` hiçbir yılda `uniform_matched` adayını geçmiyor. Alarm precision değeri 2014, 2015, 2016, 2017 ve 2022
  yıllarında `uniform_matched` değerinin altında; 2023'te daha yüksek (0.4510, karşısında 0.4433), ancak daha fazla
  pozitif koşu kaçırıyor (159 koşuda 74, karşısında 72) ve pencere recall değeri 0.0501 daha düşük; bu 0.02
  toleransının üstünde. `near_miss_w3` eksi `uniform_matched` precision farkının eşli HARP kümeli bootstrap aralığı her
  yıl 0'ı içeriyor.
- Kontrole karşı alarm precision: iki aday için de 2014, 2015 ve 2023 yıllarında daha yüksek, 2016, 2017 ve 2022
  yıllarında daha düşük. 2014'te ikisi de kontrolden fazla pozitif koşu kaçırıyor (88 koşuda 68, kontrol 66) ve 0.02'den
  fazla pencere recall kaybediyor (0.0369 ve 0.0213).
- 25. döngü. 2022 yedek kural yılında alarm precision `near_miss_w3` için 0.4542, `uniform_matched` için 0.4718,
  kontrol için 0.4727; `near_miss_w3` daha az pozitif koşu kaçırıyor (72 koşuda 26, kontrol 32) ve 115 fazla yanlış
  pozitif pencere veriyor (1293, kontrol 1178). 2023'te precision 0.4510 ve 0.4433, kontrol 0.4263; eşli bootstrap
  aralığının alt sınırı iki aday için de 0'ın üstünde ([0.0055, 0.0442] ve [0.0065, 0.0297]), ancak ikisi de kontrolden
  fazla pozitif koşu kaçırıyor (159 koşuda 74 ve 72, kontrol 68); `near_miss_w3` pencere recall değeri 0.0648,
  `uniform_matched` pencere recall değeri 0.0147 düşüyor.
- Aday eşikleri ağırlıklı skorlarla birlikte kayıyor. 2017'de `near_miss_w3` alarm eşiğinin kendisi bir yedek kural
  eşiğidir (önceki yıl precision 0.50 değerine ulaşılamadı; en iyi önceki yıl precision 0.4839) ve iki aday da 2017 için
  kontrolden çok daha düşük alarm eşikleri seçiyor (0.2637 ve 0.2961, kontrol 0.4145): alarm precision 0.8676 değerinden
  0.6746 ve 0.6969 değerlerine düşerken 6 pozitif koşudan bir tanesine daha alarm veriliyor. 2022, kontrol ve iki aday
  için de alarm yedek kural yılıdır.
- İkincil, raporlanır ve değerlendirilmez: alarm precision kontrol ve iki aday için 2014, 2015 ve 2017 yıllarında en az
  0.50. 2016, 2022 ve 2023 her aday için 0.50'nin altında kalıyor.
- Betimleyici: `near_miss_w3` için patlamalı HARP içi AP 2022'de 0.4953 ve 2023'te 0.4174; kontrol için 0.4968 ve
  0.4057, `uniform_matched` için 0.4958 ve 0.4108. Aynı HARP'ın pozitif bir penceresine 72 saat içinde olan alarm
  yanlış pozitif pencerelerinin payı `near_miss_w3` için 2022'de 0.6497 ve 2023'te 0.7651; kontrol için 0.7139 ve
  0.7561. Fikri doğuran sorun, yani patlamalı bölgelerin içindeki saatlerin sıralanması, ağırlıklarla gözle görülür
  biçimde değişmiyor.

Sonuç: bu kanıta göre 72 saat içindeki ramak kala negatiflere 3 eğitim ağırlığı vermek, daha yüksek alarm precision
için bir yol değildir. Hiçbir model öne çıkarılmadı ve hiçbir alarm, eşik, çalışma noktası veya pano ayarı
değiştirilmedi. Çalıştırma, protokolün bütçesi olan 24 bileşen eğitimi kullandı ve hiçbir şey indirmedi. Ayrılmış 2024
ile 2025 arası teste erişilmedi.

## Neden denendi

Fikir kaydı #3. [Yeniden etiketlenmiş 25. döngü teşhisi](cycle25-diagnostic-relabelled-20261112.tr.md), 2022 ve 2023'te
bölge AP değerini 0.8315 ve 0.8655, patlamalı HARP içi AP değerini 0.4968 ve 0.4057 buldu; ayrıca alarm yanlış pozitif
pencerelerinin 0.7139 ve 0.7561'inin aynı HARP'ın pozitif bir penceresine 72 saat içinde olduğunu gösterdi: alarm
katmanı bölgeyi buluyor, bölgenin içindeki saatleri ise kötü sıralıyor. Ek patlama geçmişi öznitelikleri bunu
değiştirmedi ([SGAS patlama geçmişi](activity-history-relabelled-20261112.tr.md), okuma `R3_no_gain`). Önceki
ağırlıklandırma deneyi ([zor negatif eğitimi](hard-negative-years-20261029.tr.md)) dondurulmuş etiket temelinde, recall
0.95 kapısıyla, öğretmen modelin seçtiği zor negatifleri kullandı, yalnızca XGBoost bileşenini yeniden eğitti;
negatiflerini ramak kala üyeliğiyle tanımlamadı ve alarm katmanını değerlendirmedi. Ramak kala negatifleri
ağırlıklandırmak, değişmeyen tariflerden patlama gününü komşu günlerden ayırmasını ister; hiçbir öznitelik, model veya
katman kuralı değişmez.

## Ne çalıştırıldı

Protokol, birleştirildiği haliyle tam olarak bir kez, `main` commit `da5fae0` üzerinden çalıştırıldı: 2 aday, 6 yıl,
2 bileşen, 24 bileşen eğitimi, hiperparametre araması yok, 0 indirme. Duvar saati süresi 237 saniye.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_near_miss_weighting --config config/near-miss-weighting-v1.json --output artifacts/near_miss_weighting_20261126_r1
```

| öğe | sha256 |
| --- | --- |
| `config/near-miss-weighting-v1.json` | `7831b49802bb4ff7e9aa99def23582ade1bf25a758eb5fb1caed1450a1dafaed` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (kontrol) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `artifacts/relabelled_development_20261111_r1/report.json` (etiketler) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `config/walk-forward-v2.json` (hat protokolü) | `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb` |
| `config/walk-forward-v1.json` (temel tarifler) | `7c48fd7381456bee22f928b44da537880f06b4d70fd2b38b822279474c616303` |
| `artifacts/near_miss_weighting_20261126_r1/phase1.json` | `1e89be264456db4d4e3322a0f1ebba91ac208b3555accbc92fdb0009de35489c` |
| `artifacts/near_miss_weighting_20261126_r1/thresholds.json` | `24d0fb16dc6122a477ae36ee9b39e8dd923cd8309618e44f225973c1fa320240` |
| `artifacts/near_miss_weighting_20261126_r1/weights.csv` | `cc6c78fc91ca39ba370912dfb8f73905301c200cb5f11790bf44469a72b1ffa1` |
| `artifacts/near_miss_weighting_20261126_r1/results.csv` | `6867d877aa1879019cab96ace67dccddcfb321bea10eac7f88acffd09a7fcb7c` |
| `artifacts/near_miss_weighting_20261126_r1/intervals.csv` | `5177bfc62075c986ba9167eeee7cc88c2e9882e9eff40ab93a0cb630b4d3bccb` |
| `artifacts/near_miss_weighting_20261126_r1/report.json` | `03ffa9b2bc525fb3cf55855c71b0c9c60f6f41c5a50fd9667a4ea825f52dc5c4` |

Çalıştırmadan önce protokolün adını verdiği her girdi sha256 değeriyle karşılaştırıldı: tablo raporu, kontrol raporu,
iki hat protokolü ve kontrolün yıllık `predictions.parquet` ile `thresholds.json` dosyaları (kontrol raporunun
`artifact_hashes` alanına karşı). `models.joblib` hiç açılmadı. Çalıştırıcı her katın eğitim popülasyonunu ve ramak kala
üyeliğini yeniden hesapladı ve protokoldeki değerlere eşit buldu. Eşikler, ağırlıklar ve aday olasılıkları, herhangi bir
değerlendirme etiketi okunmadan önce yazıldı ve özetlendi (`phase1.json`); değerlendirmeden sonra da kayıtlı özetleri
taşıyordu. Kontrol olasılıklarının yanında kayıtlı hedef, her değerlendirme penceresinde tablo etiketine eşittir.

## Yöntem

Popülasyon: benimsenen hattın değerlendirme pencereleri, HARP ve saat başına bir pencere; yıllar 2014, 2015, 2016, 2017,
2022 ve 2023. 2018 ile 2021 arası yıllar benimsenen hat tarafından atlanır ve dışarıda kalır. 2022, kontrolün alarm
yedek kural yılıdır: kayıtlı alarm eşiği `config/walk-forward-v2.json` yedek kuralından gelir. Her adayın kendi alarm
eşiğinin yedek kural işareti her tabloda verilir.

Adaylar. `control`: `artifacts/walk_forward_v2_20261112_r1` içindeki kayıtlı topluluk olasılıkları ile kayıtlı yıllık
izleme ve alarm eşikleri; yeniden eğitilmez. `near_miss_w3`: değişmeyen `walk-forward-v1` tariflerinin 96 SHARP özeti
üzerinde yeniden eğitimi; aynı HARP'ın pozitif bir eğitim penceresine önce veya sonra 72 saat içinde olan her negatif
eğitim penceresi örnek ağırlığı 3, diğer her eğitim satırı ağırlık 1 alır. `uniform_matched`: aynı yeniden eğitim; her
eğitim negatifi kendi katının `1 + 2 * near_miss_negatives / train_negatives` ağırlığını, pozitifler ağırlık 1 alır;
böylece toplam negatif ağırlığı `near_miss_w3` ile eşittir ve yalnızca ek ağırlığın yerleşimi farklıdır. Bu, ağırlık
kontrolüdür.

Ramak kala üyeliği, `helio24.walk_forward.annual_fold` sınır pencerelerini ayıkladıktan sonra, yalnızca eğitim rolünün
satırlarını ve etiketlerini kullanır. Ağırlık her bileşenin son kestiricisine (lojistik regresyon ve XGBoost) verilir;
eksik değer doldurucu, ölçekleyici, önceki yıl üzerindeki sigmoid kalibrasyon, eşik seçimi ve her ölçü ağırlıksızdır.
Topluluk 0.45 lojistik ve 0.55 XGBoost'tur. Aday ve yıl başına izleme eşiği (önceki yıl pencere recall 0.90) ve alarm
eşiği (önceki yıl precision 0.50, recall tabanı 0.10, yedek kural işareti) kalibrasyon yılı olasılıkları üzerinde
seçilir; dolayısıyla her aday kendi önceki yıl eşiklerinde değerlendirilir.

Kabul ölçütü, [`config/activity-history-v2.json`](../config/activity-history-v2.json) ile aynıdır: bir aday, alarm precision
değeri kontrolden yüksekse, kaçırdığı pozitif koşular kontrolden fazla değilse ve pencere recall değeri en çok 0.02
düşüyorsa yıllık birincil ölçütü karşılar. `all_year_primary`: bu altı yılın hepsinde geçerlidir. `cycle25_primary`: hem
2022 hem 2023'te geçerlidir. Bir aday, `all_year_primary` geçerliyse veya `cycle25_primary` geçerliyse ve precision
farkının eşli HARP kümeli bootstrap aralığının (1000 çekim, tohum 24, yüzde 2.5 ve 97.5 çeyreklikleri) alt sınırı hem
2022 hem 2023'te 0'ın üstündeyse kontrole karşı hedefi karşılar. Bir yılda `near_miss_w3`, yıllık birincil ölçüt
kontrolün yerine `uniform_matched` konduğunda geçerliyse `uniform_matched` adayını geçer.

Okuma kuralı, bu sırayla uygulanır: `near_miss_w3` kontrole karşı hedefi bir yoldan karşılıyorsa ve o yolun her yılında
`uniform_matched` adayını geçiyorsa `N1_near_miss_helps`; değilse `near_miss_w3` veya `uniform_matched` kontrole karşı
hedefi karşılıyorsa `N2_reweighting_only`; değilse `N3_no_gain`.

Sayılar örtüşen saatlik pencerelerdir. Pozitif koşu, bir HARP'ın bitişik pozitif pencereler grubudur. Hiçbiri bağımsız
bir olay değildir.

## Eğitim ağırlıkları

Yalnızca eğitim rolünün etiket sayıları. Ramak kala payı `near_miss_negatives / train_negatives` değeridir. Kalibrasyon
ve değerlendirme satırları her zaman 1.0 ağırlığındadır.

| yıl | eğitim satırları | eğitim pozitifleri | eğitim negatifleri | ramak kala negatifler | negatifler içinde ramak kala payı | patlamalı eğitim HARP sayısı | ramak kala ağırlığı | tekdüze negatif ağırlığı | toplam negatif ağırlığı `near_miss_w3` | toplam negatif ağırlığı `uniform_matched` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 150935 | 3161 | 147774 | 7344 | 0.0497 | 60 | 3.0 | 1.099395 | 162462.0 | 162462.0 |
| 2015 | 228635 | 4616 | 224019 | 11185 | 0.0499 | 93 | 3.0 | 1.099858 | 246389.0 | 246389.0 |
| 2016 | 307980 | 7129 | 300851 | 16421 | 0.0546 | 138 | 3.0 | 1.109164 | 333693.0 | 333693.0 |
| 2017 | 379962 | 8638 | 371324 | 19634 | 0.0529 | 167 | 3.0 | 1.105751 | 410592.0 | 410592.0 |
| 2022 | 466206 | 9141 | 457065 | 20530 | 0.0449 | 174 | 3.0 | 1.089834 | 498125.0 | 498125.0 |
| 2023 | 496391 | 9518 | 486873 | 21974 | 0.0451 | 186 | 3.0 | 1.090266 | 530821.0 | 530821.0 |

## Alarm katmanı

Precision, ulaşılan pencere recall değeri ve kaçırılan pozitif koşularla birlikte verilir. Aralıklar her adayın HARP
kümeli bootstrap aralıklarıdır. `yedek kural`, yedek kuralla seçilmiş bir alarm eşiğini işaretler.

| yıl | aday | yedek kural | alarm eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | alarm pencereleri | alarm verilen pozitif koşular | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 22 | 66/88 |
| 2014 | `near_miss_w3` | hayır | 0.4460 | 598 | 236 | 1838 | 75679 | 0.2455 | [0.0761, 0.3923] | 0.7170 | [0.4360, 0.8674] | 0.9735 | 0.9689 | 834 | 20 | 68/88 |
| 2014 | `uniform_matched` | hayır | 0.4924 | 636 | 232 | 1800 | 75683 | 0.2611 | [0.0804, 0.4205] | 0.7327 | [0.4716, 0.8709] | 0.9741 | 0.9689 | 868 | 20 | 68/88 |
| 2015 | `control` | hayır | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 30 | 27/57 |
| 2015 | `near_miss_w3` | hayır | 0.2601 | 582 | 455 | 879 | 68638 | 0.3984 | [0.2216, 0.5403] | 0.5612 | [0.3702, 0.7208] | 0.9811 | 0.9793 | 1037 | 30 | 27/57 |
| 2015 | `uniform_matched` | hayır | 0.2611 | 562 | 435 | 899 | 68658 | 0.3847 | [0.1758, 0.5377] | 0.5637 | [0.3464, 0.7397] | 0.9811 | 0.9793 | 997 | 31 | 26/57 |
| 2016 | `control` | hayır | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 5 | 3/8 |
| 2016 | `near_miss_w3` | hayır | 0.2419 | 91 | 142 | 123 | 42786 | 0.4252 | [0.0000, 0.7471] | 0.3906 | [0.0000, 0.5652] | 0.9939 | 0.9950 | 233 | 6 | 2/8 |
| 2016 | `uniform_matched` | hayır | 0.2574 | 88 | 115 | 126 | 42813 | 0.4112 | [0.0000, 0.8391] | 0.4335 | [0.0000, 0.5691] | 0.9944 | 0.9950 | 203 | 5 | 3/8 |
| 2017 | `control` | hayır | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3 | 3/6 |
| 2017 | `near_miss_w3` | evet | 0.2637 | 199 | 96 | 66 | 19482 | 0.7509 | [0.1860, 0.9172] | 0.6746 | [0.0000, 0.9028] | 0.9918 | 0.9866 | 295 | 4 | 2/6 |
| 2017 | `uniform_matched` | hayır | 0.2961 | 200 | 87 | 65 | 19491 | 0.7547 | [0.1860, 0.9363] | 0.6969 | [0.0000, 0.9143] | 0.9923 | 0.9866 | 287 | 4 | 2/6 |
| 2022 | `control` | evet | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 40 | 32/72 |
| 2022 | `near_miss_w3` | evet | 0.1401 | 1076 | 1293 | 1114 | 62110 | 0.4913 | [0.3570, 0.6030] | 0.4542 | [0.3329, 0.5854] | 0.9633 | 0.9666 | 2369 | 46 | 26/72 |
| 2022 | `uniform_matched` | evet | 0.1549 | 1056 | 1182 | 1134 | 62221 | 0.4822 | [0.3291, 0.6038] | 0.4718 | [0.3492, 0.6014] | 0.9647 | 0.9666 | 2238 | 40 | 32/72 |
| 2023 | `control` | hayır | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 91 | 68/159 |
| 2023 | `near_miss_w3` | hayır | 0.2935 | 1322 | 1609 | 2769 | 91291 | 0.3231 | [0.2387, 0.3955] | 0.4510 | [0.3708, 0.5383] | 0.9549 | 0.9578 | 2931 | 85 | 74/159 |
| 2023 | `uniform_matched` | hayır | 0.2777 | 1527 | 1918 | 2564 | 90982 | 0.3733 | [0.2782, 0.4510] | 0.4433 | [0.3656, 0.5280] | 0.9538 | 0.9578 | 3445 | 87 | 72/159 |

## Kabul

`precision farkı` aday eksi kontroldür. `recall düşüşü` kontrol recall eksi aday recall değeridir; negatif değer
kazançtır. Aralık, precision farkının eşli HARP kümeli bootstrap aralığıdır. 2017'de kontrole karşı 1000 çekimin 982
tanesi kullanılabildi (kontrolün veya adayın hiç alarm penceresi olmayan bir çekim atlanır).

| yıl | aday | kontrol yedek kural | aday yedek kural | kontrol precision | aday precision | precision farkı | fark %95 aralığı | kullanılan bootstrap çekimi | recall düşüşü | kontrol kaçırılan koşu | aday kaçırılan koşu | precision daha yüksek | kaçırılan koşu daha fazla değil | recall düşüşü en çok 0.02 | yıllık birincil ölçüt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `near_miss_w3` | hayır | hayır | 0.6825 | 0.7170 | 0.0345 | [-0.0215, 0.0701] | 1000 | 0.0369 | 66 | 68 | evet | hayır | hayır | hayır |
| 2014 | `uniform_matched` | hayır | hayır | 0.6825 | 0.7327 | 0.0502 | [0.0134, 0.0813] | 1000 | 0.0213 | 66 | 68 | evet | hayır | hayır | hayır |
| 2015 | `near_miss_w3` | hayır | hayır | 0.5439 | 0.5612 | 0.0173 | [-0.0244, 0.0726] | 1000 | -0.0253 | 27 | 27 | evet | evet | evet | evet |
| 2015 | `uniform_matched` | hayır | hayır | 0.5439 | 0.5637 | 0.0198 | [0.0022, 0.0413] | 1000 | -0.0116 | 27 | 26 | evet | evet | evet | evet |
| 2016 | `near_miss_w3` | hayır | hayır | 0.4631 | 0.3906 | -0.0725 | [-0.1491, 0.0000] | 1000 | 0.0140 | 3 | 2 | hayır | evet | evet | hayır |
| 2016 | `uniform_matched` | hayır | hayır | 0.4631 | 0.4335 | -0.0296 | [-0.1273, 0.0000] | 1000 | 0.0280 | 3 | 3 | hayır | evet | hayır | hayır |
| 2017 | `near_miss_w3` | hayır | evet | 0.8676 | 0.6746 | -0.1931 | [-0.3577, 0.1328] | 982 | -0.0830 | 3 | 2 | hayır | evet | evet | hayır |
| 2017 | `uniform_matched` | hayır | hayır | 0.8676 | 0.6969 | -0.1708 | [-0.3319, 0.1599] | 982 | -0.0868 | 3 | 2 | hayır | evet | evet | hayır |
| 2022 | `near_miss_w3` | evet | evet | 0.4727 | 0.4542 | -0.0185 | [-0.0416, 0.0021] | 1000 | -0.0091 | 32 | 26 | hayır | evet | evet | hayır |
| 2022 | `uniform_matched` | evet | evet | 0.4727 | 0.4718 | -0.0008 | [-0.0090, 0.0054] | 1000 | 0.0000 | 32 | 32 | hayır | evet | evet | hayır |
| 2023 | `near_miss_w3` | hayır | hayır | 0.4263 | 0.4510 | 0.0248 | [0.0055, 0.0442] | 1000 | 0.0648 | 68 | 74 | evet | hayır | hayır | hayır |
| 2023 | `uniform_matched` | hayır | hayır | 0.4263 | 0.4433 | 0.0170 | [0.0065, 0.0297] | 1000 | 0.0147 | 68 | 72 | evet | hayır | evet | hayır |

`uniform_matched` karşısında `near_miss_w3`: aynı üç koşul, kontrolün yerine `uniform_matched` konarak. Aralık
betimleyicidir.

| yıl | `uniform_matched` yedek kural | `near_miss_w3` yedek kural | `uniform_matched` precision | `near_miss_w3` precision | precision farkı | fark %95 aralığı | kullanılan bootstrap çekimi | recall düşüşü | `uniform_matched` kaçırılan koşu | `near_miss_w3` kaçırılan koşu | precision daha yüksek | kaçırılan koşu daha fazla değil | recall düşüşü en çok 0.02 | `uniform_matched` adayını geçiyor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | hayır | hayır | 0.7327 | 0.7170 | -0.0157 | [-0.0624, 0.0201] | 1000 | 0.0156 | 68 | 68 | hayır | evet | evet | hayır |
| 2015 | hayır | hayır | 0.5637 | 0.5612 | -0.0025 | [-0.0485, 0.0522] | 1000 | -0.0137 | 26 | 27 | hayır | hayır | evet | hayır |
| 2016 | hayır | hayır | 0.4335 | 0.3906 | -0.0429 | [-0.0861, 0.0554] | 1000 | -0.0140 | 3 | 2 | hayır | evet | evet | hayır |
| 2017 | hayır | evet | 0.6969 | 0.6746 | -0.0223 | [-0.0642, 0.0189] | 1000 | 0.0038 | 2 | 2 | hayır | evet | evet | hayır |
| 2022 | evet | evet | 0.4718 | 0.4542 | -0.0176 | [-0.0394, 0.0022] | 1000 | -0.0091 | 32 | 26 | hayır | evet | evet | hayır |
| 2023 | hayır | hayır | 0.4433 | 0.4510 | 0.0078 | [-0.0102, 0.0244] | 1000 | 0.0501 | 72 | 74 | evet | hayır | hayır | hayır |

| aday | yıllık birincil ölçütü karşılayan yıllar | all_year_primary | cycle25_primary | 2022 ve 2023 için bootstrap alt sınırı 0 üstünde | kontrole karşı hedef karşılandı | `uniform_matched` adayını geçtiği yıllar | alarm yedek kural yılları | alarm precision en az 0.50 olan yıllar (ikincil) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  |  | 2022 | 2014, 2015, 2017 |
| `near_miss_w3` | 2015 | hayır | hayır | hayır | hayır | yok | 2017, 2022 | 2014, 2015, 2017 |
| `uniform_matched` | 2015 | hayır | hayır | hayır | hayır |  | 2022 | 2014, 2015, 2017 |

## Sıralama ve alarm yanlış pozitiflerinin kaynağı (betimleyici)

Raporlanır, değerlendirilmez. Average precision, bölge AP ve patlamalı HARP içi AP bir eşiğe bağlı değildir. Yanlış
pozitif payları her adayın kendi alarm eşiğinde alınır. `kontrol recall değerinde precision`, adayın, kontrolün alarm
recall değerini veren değerlendirme yılı eşiğindeki precision değeridir: değerlendirme etiketlerini kullanan, oracle ile
eşlenmiş bir betimlemedir ve asla kullanıma alınamaz.

| yıl | aday | yedek kural | average precision | bölge AP | patlamalı HARP içi AP | alarm FP pencereleri | hiç patlamayan HARP kaynaklı alarm FP payı | pozitif pencereye 72 saat içindeki alarm FP payı | kontrol alarm recall | kontrol recall değerinde precision (oracle) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.5015 | 0.7600 | 0.5528 | 320 | 0.1437 | 0.7063 | 0.2824 | 0.6825 |
| 2014 | `near_miss_w3` | hayır | 0.4857 | 0.7446 | 0.5400 | 236 | 0.1525 | 0.7288 | 0.2824 | 0.6546 |
| 2014 | `uniform_matched` | hayır | 0.5026 | 0.7625 | 0.5536 | 232 | 0.1336 | 0.7241 | 0.2824 | 0.7006 |
| 2015 | `control` | hayır | 0.4823 | 0.8264 | 0.5331 | 457 | 0.0853 | 0.8249 | 0.3730 | 0.5439 |
| 2015 | `near_miss_w3` | hayır | 0.4798 | 0.8173 | 0.5336 | 455 | 0.0813 | 0.8286 | 0.3730 | 0.5761 |
| 2015 | `uniform_matched` | hayır | 0.4881 | 0.8161 | 0.5381 | 435 | 0.0759 | 0.8138 | 0.3730 | 0.5731 |
| 2016 | `control` | hayır | 0.4060 | 0.6333 | 0.4853 | 109 | 0.2569 | 0.5688 | 0.4393 | 0.4631 |
| 2016 | `near_miss_w3` | hayır | 0.3346 | 0.8125 | 0.4330 | 142 | 0.3451 | 0.4859 | 0.4393 | 0.3917 |
| 2016 | `uniform_matched` | hayır | 0.4114 | 0.8125 | 0.4952 | 115 | 0.2783 | 0.5478 | 0.4393 | 0.4434 |
| 2017 | `control` | hayır | 0.7975 | 1.0000 | 0.8727 | 27 | 0.1111 | 0.8889 | 0.6679 | 0.8676 |
| 2017 | `near_miss_w3` | evet | 0.7968 | 1.0000 | 0.8784 | 96 | 0.6146 | 0.3750 | 0.6679 | 0.8592 |
| 2017 | `uniform_matched` | hayır | 0.8031 | 1.0000 | 0.8770 | 87 | 0.5632 | 0.4253 | 0.6679 | 0.8762 |
| 2022 | `control` | evet | 0.4622 | 0.8315 | 0.4968 | 1178 | 0.0823 | 0.7139 | 0.4822 | 0.4727 |
| 2022 | `near_miss_w3` | evet | 0.4554 | 0.8262 | 0.4953 | 1293 | 0.1284 | 0.6497 | 0.4822 | 0.4716 |
| 2022 | `uniform_matched` | evet | 0.4611 | 0.8297 | 0.4958 | 1182 | 0.0854 | 0.7090 | 0.4822 | 0.4718 |
| 2023 | `control` | hayır | 0.3626 | 0.8655 | 0.4057 | 2136 | 0.1320 | 0.7561 | 0.3879 | 0.4263 |
| 2023 | `near_miss_w3` | hayır | 0.3694 | 0.8557 | 0.4174 | 1609 | 0.1374 | 0.7651 | 0.3879 | 0.4267 |
| 2023 | `uniform_matched` | hayır | 0.3670 | 0.8634 | 0.4108 | 1918 | 0.1330 | 0.7633 | 0.3879 | 0.4357 |

## İzleme katmanı

Her aday kendi önceki yıl izleme eşiğinde (önceki yılda pencere recall 0.90). Hiçbir izleme eşiği yedek kural eşiği
değildir.

| yıl | aday | yedek kural | izleme eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | alarm pencereleri | alarm verilen pozitif koşular | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 82 | 6/88 |
| 2014 | `near_miss_w3` | hayır | 0.0306 | 2185 | 9716 | 251 | 66199 | 0.8970 | [0.8286, 0.9452] | 0.1836 | [0.1260, 0.2481] | 0.8728 | 0.9689 | 11901 | 82 | 6/88 |
| 2014 | `uniform_matched` | hayır | 0.0302 | 2148 | 9198 | 288 | 66717 | 0.8818 | [0.8055, 0.9348] | 0.1893 | [0.1295, 0.2561] | 0.8789 | 0.9689 | 11346 | 82 | 6/88 |
| 2015 | `control` | hayır | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 56 | 1/57 |
| 2015 | `near_miss_w3` | hayır | 0.0375 | 1399 | 8441 | 62 | 60652 | 0.9576 | [0.8947, 0.9971] | 0.1422 | [0.0868, 0.1990] | 0.8795 | 0.9793 | 9840 | 56 | 1/57 |
| 2015 | `uniform_matched` | hayır | 0.0343 | 1399 | 8550 | 62 | 60543 | 0.9576 | [0.8947, 0.9971] | 0.1406 | [0.0859, 0.1973] | 0.8779 | 0.9793 | 9949 | 56 | 1/57 |
| 2016 | `control` | hayır | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 8 | 0/8 |
| 2016 | `near_miss_w3` | hayır | 0.0507 | 205 | 1814 | 9 | 41114 | 0.9579 | [0.7727, 1.0000] | 0.1015 | [0.0000, 0.1849] | 0.9577 | 0.9950 | 2019 | 8 | 0/8 |
| 2016 | `uniform_matched` | hayır | 0.0478 | 200 | 1697 | 14 | 41231 | 0.9346 | [0.4545, 1.0000] | 0.1054 | [0.0000, 0.1928] | 0.9603 | 0.9950 | 1897 | 8 | 0/8 |
| 2017 | `control` | hayır | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 5 | 1/6 |
| 2017 | `near_miss_w3` | hayır | 0.0277 | 243 | 1069 | 22 | 18509 | 0.9170 | [0.7692, 1.0000] | 0.1852 | [0.0000, 0.4544] | 0.9450 | 0.9866 | 1312 | 5 | 1/6 |
| 2017 | `uniform_matched` | hayır | 0.0255 | 242 | 1067 | 23 | 18511 | 0.9132 | [0.7692, 1.0000] | 0.1849 | [0.0000, 0.4533] | 0.9451 | 0.9866 | 1309 | 5 | 1/6 |
| 2022 | `control` | hayır | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 67 | 5/72 |
| 2022 | `near_miss_w3` | hayır | 0.0197 | 2016 | 11867 | 174 | 51536 | 0.9205 | [0.8444, 0.9705] | 0.1452 | [0.1006, 0.1967] | 0.8164 | 0.9666 | 13883 | 67 | 5/72 |
| 2022 | `uniform_matched` | hayır | 0.0189 | 2021 | 11609 | 169 | 51794 | 0.9228 | [0.8475, 0.9727] | 0.1483 | [0.1031, 0.2011] | 0.8204 | 0.9666 | 13630 | 66 | 6/72 |
| 2023 | `control` | hayır | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 149 | 10/159 |
| 2023 | `near_miss_w3` | hayır | 0.0447 | 3691 | 15804 | 400 | 77096 | 0.9022 | [0.8479, 0.9412] | 0.1893 | [0.1531, 0.2254] | 0.8329 | 0.9578 | 19495 | 151 | 8/159 |
| 2023 | `uniform_matched` | hayır | 0.0410 | 3705 | 16111 | 386 | 76789 | 0.9056 | [0.8503, 0.9449] | 0.1870 | [0.1511, 0.2226] | 0.8299 | 0.9578 | 19816 | 149 | 10/159 |

İzleme katmanı accuracy değeri her aday için her yıl hep-negatif accuracy değerinin altındadır.

## Seçilen eşikler

Herhangi bir değerlendirme etiketi okunmadan önce kalibrasyon yılı olasılıkları üzerinde seçildi. `önceki yıl recall`
ve `önceki yıl precision`, seçilen eşikteki kalibrasyon yılı değerleridir.

| yıl | aday | katman | eşik | önceki yıl recall | önceki yıl precision | yedek kural |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `watch` | 0.0311 |  |  | hayır |
| 2014 | `control` | `alert` | 0.4627 | 0.1326 | 0.5000 | hayır |
| 2014 | `near_miss_w3` | `watch` | 0.0306 |  |  | hayır |
| 2014 | `near_miss_w3` | `alert` | 0.4460 | 0.1230 | 0.5000 | hayır |
| 2014 | `uniform_matched` | `watch` | 0.0302 |  |  | hayır |
| 2014 | `uniform_matched` | `alert` | 0.4924 | 0.1038 | 0.5000 | hayır |
| 2015 | `control` | `watch` | 0.0364 |  |  | hayır |
| 2015 | `control` | `alert` | 0.2631 | 0.4906 | 0.5000 | hayır |
| 2015 | `near_miss_w3` | `watch` | 0.0375 |  |  | hayır |
| 2015 | `near_miss_w3` | `alert` | 0.2601 | 0.4462 | 0.5000 | hayır |
| 2015 | `uniform_matched` | `watch` | 0.0343 |  |  | hayır |
| 2015 | `uniform_matched` | `alert` | 0.2611 | 0.4881 | 0.5000 | hayır |
| 2016 | `control` | `watch` | 0.0471 |  |  | hayır |
| 2016 | `control` | `alert` | 0.2564 | 0.4969 | 0.5000 | hayır |
| 2016 | `near_miss_w3` | `watch` | 0.0507 |  |  | hayır |
| 2016 | `near_miss_w3` | `alert` | 0.2419 | 0.5079 | 0.5000 | hayır |
| 2016 | `uniform_matched` | `watch` | 0.0478 |  |  | hayır |
| 2016 | `uniform_matched` | `alert` | 0.2574 | 0.4949 | 0.5000 | hayır |
| 2017 | `control` | `watch` | 0.0270 |  |  | hayır |
| 2017 | `control` | `alert` | 0.4145 | 0.2196 | 0.5000 | hayır |
| 2017 | `near_miss_w3` | `watch` | 0.0277 |  |  | hayır |
| 2017 | `near_miss_w3` | `alert` | 0.2637 | 0.3505 | 0.4839 | evet |
| 2017 | `uniform_matched` | `watch` | 0.0255 |  |  | hayır |
| 2017 | `uniform_matched` | `alert` | 0.2961 | 0.3598 | 0.5000 | hayır |
| 2022 | `control` | `watch` | 0.0183 |  |  | hayır |
| 2022 | `control` | `alert` | 0.1570 | 0.2361 | 0.1996 | evet |
| 2022 | `near_miss_w3` | `watch` | 0.0197 |  |  | hayır |
| 2022 | `near_miss_w3` | `alert` | 0.1401 | 0.2812 | 0.2070 | evet |
| 2022 | `uniform_matched` | `watch` | 0.0189 |  |  | hayır |
| 2022 | `uniform_matched` | `alert` | 0.1549 | 0.2493 | 0.2026 | evet |
| 2023 | `control` | `watch` | 0.0405 |  |  | hayır |
| 2023 | `control` | `alert` | 0.2689 | 0.4461 | 0.5000 | hayır |
| 2023 | `near_miss_w3` | `watch` | 0.0447 |  |  | hayır |
| 2023 | `near_miss_w3` | `alert` | 0.2935 | 0.3753 | 0.5000 | hayır |
| 2023 | `uniform_matched` | `watch` | 0.0410 |  |  | hayır |
| 2023 | `uniform_matched` | `alert` | 0.2777 | 0.4183 | 0.5000 | hayır |

## Dondurulmuş etiket sonuçları

Karşılaştırma için görünür tutulur; [zor negatif eğitimi](hard-negative-years-20261029.tr.md) raporundan kopyalandı,
yeniden hesaplanmadı: dondurulmuş etiketlerde öğretmen modelin seçtiği zor negatiflere 3 ağırlığı, önceki yıl recall
0.95 eşikleri, yalnızca XGBoost yeniden eğitildi. Bu farklı bir temel, ağırlıklandırılan negatiflerin farklı bir tanımı
ve farklı bir katmandır; değerler yukarıdaki tablolarla asla birleştirilmez ve onlarla karşılaştırılabilir değildir. O
rapor, ağırlıklı kol için karşılaştırılabilir 6 pozitif değerlendirme yılının 3 tanesinde recall değerini en az 0.95
ve tüm yıl kapısı sonucunu `False` buldu.

| yıl | kol | pencereler | pozitifler | precision | recall | FP | FN | eşik |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `baseline_unweighted` | 75228 | 2310 | 0.135905 | 0.945455 | 13886 | 126 | 0.011475 |
| 2014 | `hard_negative_weighted` | 75228 | 2310 | 0.140464 | 0.940260 | 13291 | 138 | 0.011643 |
| 2014 | `uniform_negative_matched_weight` | 75228 | 2310 | 0.132063 | 0.948052 | 14393 | 120 | 0.010818 |
| 2015 | `baseline_unweighted` | 69138 | 1355 | 0.105164 | 0.993358 | 11453 | 9 | 0.018839 |
| 2015 | `hard_negative_weighted` | 69138 | 1355 | 0.106261 | 0.997048 | 11363 | 4 | 0.019888 |
| 2015 | `uniform_negative_matched_weight` | 69138 | 1355 | 0.104511 | 0.993358 | 11533 | 9 | 0.018748 |
| 2016 | `baseline_unweighted` | 42987 | 181 | 0.071400 | 0.972376 | 2289 | 5 | 0.030831 |
| 2016 | `hard_negative_weighted` | 42987 | 181 | 0.076453 | 0.966851 | 2114 | 6 | 0.035959 |
| 2016 | `uniform_negative_matched_weight` | 42987 | 181 | 0.070683 | 0.972376 | 2314 | 5 | 0.030137 |
| 2017 | `baseline_unweighted` | 19529 | 253 | 0.155512 | 0.936759 | 1287 | 16 | 0.012000 |
| 2017 | `hard_negative_weighted` | 19529 | 253 | 0.149527 | 0.936759 | 1348 | 16 | 0.012829 |
| 2017 | `uniform_negative_matched_weight` | 19529 | 253 | 0.156229 | 0.936759 | 1280 | 16 | 0.012192 |
| 2022 | `baseline_unweighted` | 50756 | 421 | 0.039573 | 0.985748 | 10072 | 6 | 0.008994 |
| 2022 | `hard_negative_weighted` | 50756 | 421 | 0.039281 | 0.985748 | 10150 | 6 | 0.009074 |
| 2022 | `uniform_negative_matched_weight` | 50756 | 421 | 0.038778 | 0.985748 | 10287 | 6 | 0.008743 |
| 2023 | `baseline_unweighted` | 60366 | 781 | 0.103397 | 0.884763 | 5992 | 90 | 0.018203 |
| 2023 | `hard_negative_weighted` | 60366 | 781 | 0.097381 | 0.895006 | 6479 | 82 | 0.016408 |
| 2023 | `uniform_negative_matched_weight` | 60366 | 781 | 0.101536 | 0.888604 | 6141 | 87 | 0.017537 |

## Sınırlar

Daha önce incelenmiş yıllar: uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir. Kontrol kayıtlı hattır ve
yeniden eğitilmez; `uniform_matched` yeniden eğitim ve ağırlık kontrolüdür. Ramak kala negatifler eğitim negatiflerinin
0.0449 ile 0.0546 arasındaki bir payıdır; bu yüzden eşlenmiş tekdüze ağırlık 1.0898 ile 1.1092 arasındadır ve
`uniform_matched` adayının kontrole yakın kalması bekleniyordu; kontrolden ayrıldığı yerde (örneğin 2017 alarm eşiği)
fark ramak kala üyeliğine atfedilemez. Ağırlıklı eğitim ham skorları değiştirir; önceki yıl üzerindeki kalibrasyon
ağırlıksızdır, bu yüzden adayların eşikleri skorlarla birlikte kayar ve her aday kendi önceki yıl eşiklerinde
değerlendirilir. Tek bir çarpan (3) ve tek bir aralık (72 saat) önceden sabitlendi; bu sonuç başka değerler hakkında
hiçbir şey söylemez ve bu sonuçlardan hiçbiri seçilemez. Ramak kala üyeliği patlama tepe zamanlarını değil pencere
etiketlerini kullanır ve eğitim rolünün kenarlarında sansürlüdür. Ardışık saatlik pencereler 24 saatlerinin 23'ünde
örtüşür ve HARP'lar tekrar eder; bu yüzden sayılar pencereler ve pozitif koşulardır, asla bağımsız olaylar değildir ve
aralıklar HARP kümelidir. 2016 ve 2017'de az pozitif koşu var (8 ve 6) ve aralıkları geniştir. Bootstrap aralıkları
eğitilmiş modelleri ve eşikleri sabit tutar; eğitim ve kalibrasyon belirsizliğini içermez. Yeniden etiketlenmiş
etiketler NOAA SGAS ve JSOC `NOAA_ARS` ile yapılan bir ilişkilendirmedir, kesin gerçek değildir. 2022 üçü için de alarm
yedek kural yılıdır; 2017 `near_miss_w3` için öyledir.

## Yeniden üretim

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_near_miss_weighting --config config/near-miss-weighting-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/near-miss-weighting-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `7831b49802bb4ff7e9aa99def23582ade1bf25a758eb5fb1caed1450a1dafaed`; `phase1.json` sha256
`1e89be264456db4d4e3322a0f1ebba91ac208b3555accbc92fdb0009de35489c`; `report.json` sha256
`03ffa9b2bc525fb3cf55855c71b0c9c60f6f41c5a50fd9667a4ea825f52dc5c4`. Yeni bir çıktı dizini kullanın; çalıştırıcı var olan
bir dizinin üzerine yazmayı reddeder.
