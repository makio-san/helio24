# Benimsenen hatta HARP yaşam evresi özellikleri (2026-11-26)

## Karar

Geliştirme temeli: yeniden etiketlenmiş tablo `artifacts/relabelled_development_20261111_r1` ve benimsenen hat
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). Temel 2026-11-12 tarihinde değişti, çünkü dondurulmuş
etiketler eşlenmiş 2022 ile 2023 arası M/X patlamalarının %30'undan azını kapsıyordu. Daha önce incelenmiş yıllar:
uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir.

Okuma `L3_no_gain`, sonuç etiketi `result:no-gain`; kural herhangi bir sonuçtan önce
[`config/life-phase-v1.json`](../config/life-phase-v1.json) içinde donduruldu. Protokol bir `acceptance_rule` taşıyor
(`decision.life_phase_goal_met_and_beats_age_only >= 1`); Hale `interpret_result`, `artifacts/life_phase_20261126_r1` üzerinde gözlenen değer 0
ile `reject` döndürüyor. Sonuç bu karardır. Her pencereyi kendi HARP'ının kayıtlı yaşamı içine yerleştirmek, dondurulmuş
kurala göre alarm precision değerini yükseltmiyor; yalnızca yaşı bilen yeniden eğitim de yükseltmiyor.

- `life_phase` adayının kontrole karşı yıllık birincil ölçütü karşıladığı yıllar: yok (altı yılda).
  `age_only` bunu 2015, 2017 yıllarında karşılıyor. İki aday da `all_year_primary` veya `cycle25_primary`
  (2022 ve 2023) koşulunu karşılamıyor; dolayısıyla hiçbiri kontrole karşı hedefi karşılamıyor ve `L2_refit_or_age_only` da geçerli değil.
- `life_phase`, altı yılın hiçbirinde `age_only` adayını geçmiyor. Alarm precision değeri 2022, 2023 yıllarında
  `age_only` üstünde, ancak bu yılların her birinde daha fazla pozitif koşu kaçırıyor veya pencere recall değerinden 0.02'den fazla kaybediyor.
- `life_phase` alarm precision değeri 2023 yılında kontrolün üstünde, 2014, 2015, 2016, 2017, 2022 yıllarında altında.
  2023'te 0.4386, kontrol 0.4263; ancak 159 pozitif koşuda 71
  koşu kaçırıyor (kontrol 68) ve pencere recall değeri 0.0318 düşüyor.
  2022 alarm yedek kural yılında 0.4706, kontrol 0.4727; 72 pozitif koşuda
  34 kaçırılan koşu (kontrol 32) ve 0.0589 recall düşüşü var.
- Kontrole karşı alarm precision farkının eşli HARP kümeli bootstrap aralığının alt sınırı iki aday için de hiçbir yılda
  0'ın üstünde değil (`age_only` için 2017 alt sınırı tam olarak 0.0000). Aralık
  tümüyle 0'ın altında: `life_phase` için 2015, `age_only` için 2022;
  `life_phase` eksi `age_only` aralığı 2015 yılında tümüyle 0'ın altında.
- `age_only` alarm precision değeri 2015, 2017 yıllarında kontrolün üstünde, 2014, 2016, 2022, 2023 yıllarında
  altında; farklar küçük (en büyüğü 0.0127).
- İkincil, raporlanır ve yargılanmaz: alarm precision değeri kontrol, `age_only` ve `life_phase` için 2014, 2015, 2017
  yıllarında en az 0.50. 2022 ve 2023 her aday için 0.50 altında kalıyor.
- Betimleyici: `life_phase`, 2015, 2022, 2023 yıllarında kontrolden daha az izleme katmanı yanlış pozitif penceresine ve
  2014, 2016, 2023 yıllarında daha yüksek patlama yapan HARP içi AP değerine sahip. Son 72 saatte kayıtlı pencere boşluğu
  olmayan değerlendirme pencerelerinde `life_phase` alarm precision değeri 2023 yılında kontrolün üstünde.
  Bunların hiçbiri okuma tarafından yargılanmaz.

Sonuç: bu kanıtla altı ölçümlü yaşam evresi özellikleri daha yüksek alarm precision için bir yol değil. Hiçbir model
terfi ettirilmedi; hiçbir alarm, eşik, çalışma noktası veya pano ayarı değişmedi. Çalıştırma 24 bileşen eğitimi yaptı
(bütçe), hiçbir şey indirmedi ve ayrılmış 2024 ile 2025 testine erişmedi.

## Neden denendi

Fikir konusu #11. Benimsenen hattın her özelliği son 12 saati tanımlar; bu yüzden model hâlâ büyüyen bir bölgeyi
tepesini geçmiş bir bölgeden ayıramaz. [Yeniden etiketlenmiş 25. döngü teşhisi](cycle25-diagnostic-relabelled-20261112.md)
2022 ve 2023 için patlama yapan HARP içi AP değerini 0.4968 ve 0.4057 buldu; alarm yanlış pozitif pencerelerinin 0.7139 ve
0.7561 payı aynı HARP'ın bir pozitif penceresine 72 saat içinde. Alarm katmanı bölgeyi buluyor, ancak bölgenin içindeki
saatleri zayıf sıralıyor. [Dondurulmuş etiketli uzun geçmiş deneyi](precision-long-history-20261028.md) yaşam boyu bir
referans olmadan 24 ve 48 saatlik özetleri tek bir bölünmede ve recall 0.95 kapısıyla kullandı.

## Ne çalıştırıldı

Protokolün birleştirildiği haliyle tek bir çalıştırması; protokol birleştirmesi `bb8826f` içeren `main` commit `da5fae0`
üzerinden, 24 bileşen eğitimi (2 aday, 6 yıl, 2 bileşen), hiperparametre araması yok ve indirme yok. Süre 299 saniye.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_life_phase --config config/life-phase-v1.json --output artifacts/life_phase_20261126_r1
```

| öğe | sha256 |
| --- | --- |
| `config/life-phase-v1.json` | `7339ad5fbd85fdcfc579e599c9c0b0635603fbd330119f1948c2fc6e451a74f2` |
| `artifacts/relabelled_development_20261111_r1/report.json` (tablo) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (kontrol) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `config/walk-forward-v2.json` | `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb` |
| `config/walk-forward-v1.json` | `7c48fd7381456bee22f928b44da537880f06b4d70fd2b38b822279474c616303` |
| `artifacts/life_phase_20261126_r1/phase1.json` | `62489c3dfb77a14a44219bd509233be914534ea1bc4b7d80b263b61e9dd42feb` |
| `artifacts/life_phase_20261126_r1/thresholds.json` | `4d2901e3f055a5f2703ab4a5ccb9b694894c3017f0e88d20864ba21304271189` |
| `artifacts/life_phase_20261126_r1/features.json` | `4d1697ebfbbbdda8b49fd29266ff00f73cfde12ede52118c12bf1e707902fdeb` |
| `artifacts/life_phase_20261126_r1/life_coverage.csv` | `adac7b44bf70c499313a186a5ae7eec5ae49f7ed8d989406ad2607b81cfc43fc` |
| `artifacts/life_phase_20261126_r1/results.csv` | `6e775deeac2971ff2bfe5fed2d8fcfae918e6d4cb61b214ab502ca72ddea556f` |
| `artifacts/life_phase_20261126_r1/intervals.csv` | `bfc803050abfa78771904222f0917d1ca9da9e487e67d072a2a7a661fb81849f` |
| `artifacts/life_phase_20261126_r1/complete_history.csv` | `d13d56adab69f84bbf36616ec6879f6b52e2428321ecaf4044dedfcbc145a41a` |
| `artifacts/life_phase_20261126_r1/report.json` | `c305b5aa3f77024ef54b5e62518ec0d7fc96fbc80b7b6bcdead53fb167d4d129` |

Çalıştırıcı, tablo raporunu, kontrol raporunu, iki hat protokolünü ve yıllık kontrol `predictions.parquet` ile
`thresholds.json` dosyalarını kullanmadan önce kayıtlı sha256 değerleriyle karşılaştırdı; `models.joblib` hiç açılmadı.
Her yılın sekiz popülasyon sayısını yeniden hesapladı ve protokole eşit buldu. Kayıtlı alarm yedek kural işaretleri (2022)
protokole eşit. Eşikler, özellik listeleri, kapsama ve aday olasılıkları herhangi bir değerlendirme etiketi okunmadan önce
diske yazıldı ve hash'lendi (`phase1.json`); değerlendirmeden sonra da kayıtlı hash değerlerini korudu. Kayıtlı kontrol
etiketleri her değerlendirme penceresinde yeniden etiketlenmiş tablonun etiketine eşit.

## Yöntem

Popülasyon: benimsenen hattın değerlendirme pencereleri, HARP ve saat başına bir pencere; yıllar 2014, 2015, 2016, 2017,
2022 ve 2023; genişleyen yıllık ileri yürüyüş (kalibrasyon yılından önce eğitim, önceki yılda kalibrasyon). 2022 bir alarm
yedek kural yılıdır: önceki yıl precision 0.50 ulaşılamadığı için kayıtlı alarm eşiği `config/walk-forward-v2.json` yedek
kuralından gelir. Adayların kendi alarm eşikleri de 2022'de yedek kural eşikleridir, başka hiçbir yılda değildir. Yedek
kural yılları her tabloda işaretlidir.

Adaylar. `control`: kayıtlı topluluk olasılıkları ve kayıtlı izleme ve alarm eşikleri, yeniden eğitilmeden. `age_only`:
değişmemiş walk-forward-v1 tariflerinin (0.45 lojistik ve 0.55 XGBoost, önceki yılda sigmoid kalibrasyonu) 96 SHARP özeti
ve `life__log1p_hours_since_first_window` (97 özellik) üzerinde yeniden eğitimi. `life_phase`: `age_only` artı 36 yaşam evresi
özelliği (133 özellik): `USFLUX`, `TOTUSJH`, `TOTPOT`, `SAVNCPP`, `R_VALUE` ve `MEANSHR` için şimdiki `__mean` değerinin HARP'ın
önceki kayıtlı pencerelerinin yürüyen maksimumuna oranı (100'de kırpılmış), ortalamalarına ve standart sapmalarına göre
yürüyen z değeri (-100 ile 100 arasında kırpılmış), yürüyen maksimumdan bu yana geçen saat ve 24, 48 ve 72 saatte veya
daha önceki en son kayıtlı pencereye göre değişim. Özellikler yalnızca tahmin anahtarlarını ve aynı HARP'ın önceki
pencerelerinin altı `__mean` özetini kullanır; asla etiket, etiket durumu, rol, sonraki pencere veya başka HARP kullanmaz.
Hiçbir pencere sayısı ve hiçbir boşluk işareti model girdisi değildir. Her aday kendi izleme eşiğini (önceki yıl pencere
recall 0.90) ve alarm eşiğini (önceki yıl precision 0.50, recall tabanı 0.10, yedek kural işareti) kalibrasyon yılı
olasılıkları üzerinde seçer.

Kabul ölçütü, [`config/activity-history-v2.json`](../config/activity-history-v2.json) ile aynıdır: bir aday, alarm precision
değeri kontrolden yüksekse, kaçırdığı pozitif koşular kontrolden fazla değilse ve pencere recall değeri en çok 0.02
düşüyorsa yıllık birincil ölçütü karşılar. `all_year_primary`: bu altı yılın hepsinde geçerlidir. `cycle25_primary`: hem
2022 hem 2023'te geçerlidir. Bir aday kontrole karşı hedefi tüm yıllar yoluyla veya 25. döngü yoluyla karşılar; ikincisinde
precision farkının eşli HARP kümeli bootstrap aralığının (1000 çekim, tohum 24, yüzde 2.5 ve 97.5 çeyreklikleri) alt sınırı
hem 2022 hem 2023'te 0'ın üstünde olmalıdır. Bir yılda aynı yıllık kural kontrol yerine `age_only` ile geçerliyse `life_phase`
`age_only` adayını geçer. `specific_goal`: `life_phase` hedefi bir yolla karşılar ve o yolun her yılında `age_only` adayını geçer.

Okuma kuralı, bu sırayla uygulanır: `life_phase` `specific_goal` koşulunu karşılıyorsa `L1_life_phase_helps`; değilse
adaylardan biri kontrole karşı hedefi karşılıyorsa `L2_refit_or_age_only`; değilse `L3_no_gain`.

Sayılar örtüşen saatlik pencerelerdir. Pozitif koşu, bir HARP'ın bitişik pozitif pencereler grubudur. Hiçbiri bağımsız bir
olay değildir.

## Popülasyon ve özellik kapsamı

Herhangi bir eğitimden önce sayıldı, protokole eşit ve çalıştırıcı tarafından yeniden hesaplandı. Yakın boşluk, son 72
saatte HARP'ın ardışık kayıtlı pencereleri arasında 1.5 saati aşan bir aralıktır; yalnızca raporlama için hesaplanır.

| yıl | eğitim satırları | eğitim pozitifleri | kalibrasyon satırları | kalibrasyon pozitifleri | değerlendirme satırları | yakın boşluklu eğitim pencereleri | yakın boşluklu değerlendirme pencereleri | 72 saatten genç değerlendirme pencereleri |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 150935 | 3161 | 76710 | 1455 | 78351 | 27432 | 18877 | 31437 |
| 2015 | 228635 | 4616 | 78351 | 2436 | 70554 | 41882 | 14648 | 29127 |
| 2016 | 307980 | 7129 | 70554 | 1461 | 43142 | 60765 | 8294 | 18972 |
| 2017 | 379962 | 8638 | 43142 | 214 | 19843 | 75419 | 3299 | 8263 |
| 2022 | 466206 | 9141 | 29887 | 377 | 65593 | 90404 | 16677 | 26771 |
| 2023 | 496391 | 9518 | 65593 | 2190 | 96991 | 95330 | 21883 | 37863 |

Değerlendirme pencerelerinde seçilmiş yaşam özelliklerinin eksik değerleri (`life_coverage.csv` her rol için 37 özelliğin
hepsini tutar). `life__log1p_hours_since_first_window` hiçbir zaman eksik değildir.

| yıl | değerlendirme satırları | yakın boşluklu pencereler | eksik `life__USFLUX__ratio_to_running_max` | eksik `life__USFLUX__running_z` | eksik `life__USFLUX__change_24h` | eksik `life__USFLUX__change_48h` | eksik `life__USFLUX__change_72h` | eksik `life__R_VALUE__ratio_to_running_max` | eksik `life__R_VALUE__running_z` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 78351 | 18877 | 635 | 1261 | 12134 | 22351 | 31437 | 17574 | 17837 |
| 2015 | 70554 | 14648 | 598 | 1187 | 11296 | 20622 | 29127 | 14287 | 14691 |
| 2016 | 43142 | 8294 | 356 | 709 | 7260 | 13486 | 18972 | 7774 | 8007 |
| 2017 | 19843 | 3299 | 162 | 323 | 3232 | 5846 | 8263 | 3312 | 3428 |
| 2022 | 65593 | 16677 | 544 | 1085 | 10472 | 19053 | 26771 | 8873 | 9256 |
| 2023 | 96991 | 21883 | 751 | 1492 | 14684 | 26714 | 37863 | 15167 | 15684 |

## Alarm katmanı

Precision, teslim edilen pencere recall değeri ve kaçırılan pozitif koşularla birlikte verilir. Aralıklar her adayın HARP
kümeli bootstrap aralıklarıdır.

| yıl | aday | yedek kural | alarm eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | alarm pencereleri | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 66/88 |
| 2014 | `age_only` | hayır | 0.4538 | 704 | 335 | 1732 | 75580 | 0.2890 | [0.1084, 0.4438] | 0.6776 | [0.4284, 0.8425] | 0.9736 | 0.9689 | 1039 | 65/88 |
| 2014 | `life_phase` | hayır | 0.4318 | 773 | 381 | 1663 | 75534 | 0.3173 | [0.1181, 0.4897] | 0.6698 | [0.4190, 0.8322] | 0.9739 | 0.9689 | 1154 | 66/88 |
| 2015 | `control` | hayır | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 27/57 |
| 2015 | `age_only` | hayır | 0.2633 | 546 | 435 | 915 | 68658 | 0.3737 | [0.1711, 0.5244] | 0.5566 | [0.3369, 0.7317] | 0.9809 | 0.9793 | 981 | 27/57 |
| 2015 | `life_phase` | hayır | 0.2492 | 572 | 555 | 889 | 68538 | 0.3915 | [0.1775, 0.5518] | 0.5075 | [0.2947, 0.6697] | 0.9795 | 0.9793 | 1127 | 27/57 |
| 2016 | `control` | hayır | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 3/8 |
| 2016 | `age_only` | hayır | 0.2525 | 95 | 111 | 119 | 42817 | 0.4439 | [0.0000, 0.8736] | 0.4612 | [0.0000, 0.6196] | 0.9947 | 0.9950 | 206 | 3/8 |
| 2016 | `life_phase` | hayır | 0.2505 | 103 | 154 | 111 | 42774 | 0.4813 | [0.0000, 0.8621] | 0.4008 | [0.0000, 0.5357] | 0.9939 | 0.9950 | 257 | 2/8 |
| 2017 | `control` | hayır | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3/6 |
| 2017 | `age_only` | hayır | 0.4356 | 177 | 25 | 88 | 19553 | 0.6679 | [0.0000, 0.8535] | 0.8762 | [0.0000, 1.0000] | 0.9943 | 0.9866 | 202 | 3/6 |
| 2017 | `life_phase` | hayır | 0.3661 | 187 | 58 | 78 | 19520 | 0.7057 | [0.0233, 0.9108] | 0.7633 | [0.0000, 0.9481] | 0.9931 | 0.9866 | 245 | 2/6 |
| 2022 | `control` | evet | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 32/72 |
| 2022 | `age_only` | evet | 0.1515 | 1100 | 1273 | 1090 | 62130 | 0.5023 | [0.3491, 0.6270] | 0.4635 | [0.3432, 0.5899] | 0.9640 | 0.9666 | 2373 | 29/72 |
| 2022 | `life_phase` | evet | 0.1641 | 927 | 1043 | 1263 | 62360 | 0.4233 | [0.2913, 0.5378] | 0.4706 | [0.3388, 0.6204] | 0.9648 | 0.9666 | 1970 | 34/72 |
| 2023 | `control` | hayır | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 68/159 |
| 2023 | `age_only` | hayır | 0.2648 | 1618 | 2211 | 2473 | 90689 | 0.3955 | [0.2997, 0.4710] | 0.4226 | [0.3481, 0.5033] | 0.9517 | 0.9578 | 3829 | 69/159 |
| 2023 | `life_phase` | hayır | 0.2749 | 1457 | 1865 | 2634 | 91035 | 0.3561 | [0.2673, 0.4279] | 0.4386 | [0.3580, 0.5248] | 0.9536 | 0.9578 | 3322 | 71/159 |

## Kabul

`precision farkı` aday eksi kontroldür. `recall düşüşü` kontrol recall eksi aday recall değeridir. Aralık, precision
farkının eşli HARP kümeli bootstrap aralığıdır. 2017'de 1000 çekimin 982 tanesi kullanılabildi (taraflardan birinde hiç alarm penceresi olmayan çekim atlanır).

| yıl | aday | yedek kural | kontrol precision | aday precision | precision farkı | fark %95 aralığı | kullanılan bootstrap çekimi | recall düşüşü | kontrol kaçırılan koşu | aday kaçırılan koşu | precision daha yüksek | kaçırılan koşu daha fazla değil | recall düşüşü en çok 0.02 | yıllık birincil ölçüt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `age_only` | hayır | 0.6825 | 0.6776 | -0.0050 | [-0.0148, 0.0072] | 1000 | -0.0066 | 66 | 65 | hayır | evet | evet | hayır |
| 2014 | `life_phase` | hayır | 0.6825 | 0.6698 | -0.0127 | [-0.0590, 0.0199] | 1000 | -0.0349 | 66 | 66 | hayır | evet | evet | hayır |
| 2015 | `age_only` | hayır | 0.5439 | 0.5566 | 0.0127 | [-0.0017, 0.0322] | 1000 | -0.0007 | 27 | 27 | evet | evet | evet | evet |
| 2015 | `life_phase` | hayır | 0.5439 | 0.5075 | -0.0364 | [-0.0943, -0.0078] | 1000 | -0.0185 | 27 | 27 | hayır | evet | evet | hayır |
| 2016 | `age_only` | hayır | 0.4631 | 0.4612 | -0.0019 | [-0.0294, 0.0092] | 1000 | -0.0047 | 3 | 3 | hayır | evet | evet | hayır |
| 2016 | `life_phase` | hayır | 0.4631 | 0.4008 | -0.0623 | [-0.2215, 0.0067] | 1000 | -0.0421 | 3 | 2 | hayır | evet | evet | hayır |
| 2017 | `age_only` | hayır | 0.8676 | 0.8762 | 0.0086 | [0.0000, 0.0288] | 982 | 0.0000 | 3 | 3 | evet | evet | evet | evet |
| 2017 | `life_phase` | hayır | 0.8676 | 0.7633 | -0.1044 | [-0.2202, 0.0294] | 982 | -0.0377 | 3 | 2 | hayır | evet | evet | hayır |
| 2022 | `age_only` | evet | 0.4727 | 0.4635 | -0.0091 | [-0.0209, -0.0003] | 1000 | -0.0201 | 32 | 29 | hayır | evet | evet | hayır |
| 2022 | `life_phase` | evet | 0.4727 | 0.4706 | -0.0021 | [-0.0390, 0.0304] | 1000 | 0.0589 | 32 | 34 | hayır | hayır | hayır | hayır |
| 2023 | `age_only` | hayır | 0.4263 | 0.4226 | -0.0037 | [-0.0105, 0.0033] | 1000 | -0.0076 | 68 | 69 | hayır | hayır | evet | hayır |
| 2023 | `life_phase` | hayır | 0.4263 | 0.4386 | 0.0123 | [-0.0101, 0.0366] | 1000 | 0.0318 | 68 | 71 | evet | hayır | hayır | hayır |

| aday | yıllık birincil ölçütü karşılayan yıllar | all_year_primary | cycle25_primary | 2022 ve 2023 için bootstrap alt sınırı 0 üstünde | kontrole karşı hedef karşılandı | alarm precision en az 0.50 olan yıllar (ikincil) |
| --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  | 2014, 2015, 2017 |
| `age_only` | 2015, 2017 | hayır | hayır | hayır | hayır | 2014, 2015, 2017 |
| `life_phase` | yok | hayır | hayır | hayır | hayır | 2014, 2015, 2017 |

`life_phase` adayı `age_only` adayına karşı, her biri kendi önceki yıl eşikleriyle:

| yıl | yedek kural | age_only precision | life_phase precision | precision farkı | fark %95 aralığı | kullanılan bootstrap çekimi | recall düşüşü | age_only kaçırılan koşu | life_phase kaçırılan koşu | age_only adayını geçiyor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | hayır | 0.6776 | 0.6698 | -0.0077 | [-0.0487, 0.0208] | 1000 | -0.0283 | 65 | 66 | hayır |
| 2015 | hayır | 0.5566 | 0.5075 | -0.0490 | [-0.1126, -0.0158] | 1000 | -0.0178 | 27 | 27 | hayır |
| 2016 | hayır | 0.4612 | 0.4008 | -0.0604 | [-0.2200, 0.0028] | 1000 | -0.0374 | 3 | 2 | hayır |
| 2017 | hayır | 0.8762 | 0.7633 | -0.1130 | [-0.2310, 0.0294] | 982 | -0.0377 | 3 | 2 | hayır |
| 2022 | evet | 0.4635 | 0.4706 | 0.0070 | [-0.0307, 0.0412] | 1000 | 0.0790 | 29 | 34 | hayır |
| 2023 | hayır | 0.4226 | 0.4386 | 0.0160 | [-0.0084, 0.0425] | 1000 | 0.0394 | 69 | 71 | hayır |

## İzleme katmanı

Her aday kendi önceki yıl izleme eşiğiyle. Okumanın parçası değildir.

| yıl | aday | yedek kural | izleme eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | alarm pencereleri | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 6/88 |
| 2014 | `age_only` | hayır | 0.0309 | 2154 | 9030 | 282 | 66885 | 0.8842 | [0.8106, 0.9382] | 0.1926 | [0.1320, 0.2598] | 0.8812 | 0.9689 | 11184 | 6/88 |
| 2014 | `life_phase` | hayır | 0.0269 | 2199 | 10204 | 237 | 65711 | 0.9027 | [0.8403, 0.9470] | 0.1773 | [0.1223, 0.2394] | 0.8667 | 0.9689 | 12403 | 5/88 |
| 2015 | `control` | hayır | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 1/57 |
| 2015 | `age_only` | hayır | 0.0365 | 1396 | 8032 | 65 | 61061 | 0.9555 | [0.8908, 0.9964] | 0.1481 | [0.0910, 0.2053] | 0.8852 | 0.9793 | 9428 | 1/57 |
| 2015 | `life_phase` | hayır | 0.0405 | 1374 | 7227 | 87 | 61866 | 0.9405 | [0.8627, 0.9865] | 0.1597 | [0.0998, 0.2202] | 0.8963 | 0.9793 | 8601 | 2/57 |
| 2016 | `control` | hayır | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 0/8 |
| 2016 | `age_only` | hayır | 0.0488 | 200 | 1650 | 14 | 41278 | 0.9346 | [0.4545, 1.0000] | 0.1081 | [0.0000, 0.1974] | 0.9614 | 0.9950 | 1850 | 0/8 |
| 2016 | `life_phase` | hayır | 0.0407 | 203 | 2323 | 11 | 40605 | 0.9486 | [0.5000, 1.0000] | 0.0804 | [0.0000, 0.1522] | 0.9459 | 0.9950 | 2526 | 0/8 |
| 2017 | `control` | hayır | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 1/6 |
| 2017 | `age_only` | hayır | 0.0241 | 243 | 1110 | 22 | 18468 | 0.9170 | [0.7692, 1.0000] | 0.1796 | [0.0000, 0.4515] | 0.9430 | 0.9866 | 1353 | 1/6 |
| 2017 | `life_phase` | hayır | 0.0235 | 243 | 1082 | 22 | 18496 | 0.9170 | [0.7538, 1.0000] | 0.1834 | [0.0000, 0.4496] | 0.9444 | 0.9866 | 1325 | 1/6 |
| 2022 | `control` | hayır | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 5/72 |
| 2022 | `age_only` | hayır | 0.0193 | 2023 | 11565 | 167 | 51838 | 0.9237 | [0.8493, 0.9728] | 0.1489 | [0.1034, 0.2015] | 0.8211 | 0.9666 | 13588 | 6/72 |
| 2022 | `life_phase` | hayır | 0.0218 | 2010 | 10494 | 180 | 52909 | 0.9178 | [0.8386, 0.9699] | 0.1607 | [0.1125, 0.2165] | 0.8373 | 0.9666 | 12504 | 7/72 |
| 2023 | `control` | hayır | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 10/159 |
| 2023 | `age_only` | hayır | 0.0407 | 3696 | 16101 | 395 | 76799 | 0.9034 | [0.8496, 0.9424] | 0.1867 | [0.1512, 0.2221] | 0.8299 | 0.9578 | 19797 | 8/159 |
| 2023 | `life_phase` | hayır | 0.0410 | 3698 | 15883 | 393 | 77017 | 0.9039 | [0.8500, 0.9432] | 0.1889 | [0.1530, 0.2248] | 0.8322 | 0.9578 | 19581 | 8/159 |

İzleme katmanı accuracy değeri her yılda her aday için hep-negatif accuracy değerinin altında.

## Sıralama ve alarm yanlış pozitiflerinin kaynağı (betimleyici)

AP, bölge AP ve patlama yapan HARP içi AP tüm değerlendirme yılı sıralamasını kullanır. Yanlış pozitif payları her adayın
alarm pencerelerine göredir. `precision_at_control_recall`, adayın kontrolün alarm recall değerini veren değerlendirme yılı
eşiğindeki precision değeridir: değerlendirme etiketlerini kullanan, kâhin eşlemeli bir betimlemedir ve asla
uygulanamaz (kontrol için kendi alarm precision değeridir). `life_phase` bu ölçüde 2014 yılında,
`age_only` 2014, 2015, 2017, 2022 yıllarında kontrolün üstünde.

| yıl | aday | yedek kural | average precision | bölge AP | patlama yapan HARP içi AP | hiç patlama yapmayan HARP kaynaklı alarm FP payı | pozitif pencereye 72 saat içindeki alarm FP payı | precision_at_control_recall (kâhin) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.5015 | 0.7600 | 0.5528 | 0.1437 | 0.7063 | 0.6825 |
| 2014 | `age_only` | hayır | 0.5041 | 0.7615 | 0.5552 | 0.1373 | 0.7194 | 0.6894 |
| 2014 | `life_phase` | hayır | 0.5027 | 0.7724 | 0.5599 | 0.1286 | 0.7428 | 0.7311 |
| 2015 | `control` | hayır | 0.4823 | 0.8264 | 0.5331 | 0.0853 | 0.8249 | 0.5439 |
| 2015 | `age_only` | hayır | 0.4752 | 0.8237 | 0.5259 | 0.0782 | 0.8322 | 0.5561 |
| 2015 | `life_phase` | hayır | 0.4601 | 0.7890 | 0.5143 | 0.1441 | 0.7387 | 0.5113 |
| 2016 | `control` | hayır | 0.4060 | 0.6333 | 0.4853 | 0.2569 | 0.5688 | 0.4631 |
| 2016 | `age_only` | hayır | 0.4121 | 0.6005 | 0.4909 | 0.2523 | 0.5586 | 0.4585 |
| 2016 | `life_phase` | hayır | 0.4385 | 0.7375 | 0.5117 | 0.2792 | 0.3831 | 0.4455 |
| 2017 | `control` | hayır | 0.7975 | 1.0000 | 0.8727 | 0.1111 | 0.8889 | 0.8676 |
| 2017 | `age_only` | hayır | 0.8015 | 1.0000 | 0.8755 | 0.1200 | 0.8800 | 0.8850 |
| 2017 | `life_phase` | hayır | 0.7932 | 1.0000 | 0.8657 | 0.4310 | 0.5690 | 0.8592 |
| 2022 | `control` | evet | 0.4622 | 0.8315 | 0.4968 | 0.0823 | 0.7139 | 0.4727 |
| 2022 | `age_only` | evet | 0.4633 | 0.8356 | 0.4975 | 0.0943 | 0.6952 | 0.4813 |
| 2022 | `life_phase` | evet | 0.4482 | 0.8183 | 0.4866 | 0.0911 | 0.6855 | 0.4131 |
| 2023 | `control` | hayır | 0.3626 | 0.8655 | 0.4057 | 0.1320 | 0.7561 | 0.4263 |
| 2023 | `age_only` | hayır | 0.3636 | 0.8612 | 0.4066 | 0.1316 | 0.7553 | 0.4263 |
| 2023 | `life_phase` | hayır | 0.3654 | 0.8610 | 0.4118 | 0.1421 | 0.7662 | 0.4252 |

## Yakın boşluğu olmayan pencereler (betimleyici)

Son 72 saatte kayıtlı pencere boşluğu olmayan değerlendirme pencerelerinde, her adayın kendi alarm eşiğiyle alarm
sayıları. Boşluklu pencerelerin pozitif oranı 2014, 2016, 2017, 2022, 2023 yıllarında boşluksuz pencerelerinkinden yüksek
(2015 yılında biraz daha düşük, dört ondalıkta eşit): protokolün sızıntı sorusunun beklediği gibi boşluklar etiket bilgisi taşıyor. Bu alt
kümede `life_phase` precision değeri 2023 yılında, `age_only` 2015, 2016, 2017 yıllarında kontrolün
üstünde. Bu tablonun okuma kuralı yoktur.

| yıl | aday | yedek kural | yakın boşluksuz pencereler | pencere payı | pozitifler | pozitif payı | boşluklu pozitif oranı | boşluksuz pozitif oranı | TP | FP | FN | precision | recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 59474 | 0.7591 | 1750 | 0.7184 | 0.0363 | 0.0294 | 526 | 293 | 1224 | 0.6422 | 0.3006 |
| 2014 | `age_only` | hayır | 59474 | 0.7591 | 1750 | 0.7184 | 0.0363 | 0.0294 | 541 | 308 | 1209 | 0.6372 | 0.3091 |
| 2014 | `life_phase` | hayır | 59474 | 0.7591 | 1750 | 0.7184 | 0.0363 | 0.0294 | 586 | 333 | 1164 | 0.6376 | 0.3349 |
| 2015 | `control` | hayır | 55906 | 0.7924 | 1158 | 0.7926 | 0.0207 | 0.0207 | 420 | 384 | 738 | 0.5224 | 0.3627 |
| 2015 | `age_only` | hayır | 55906 | 0.7924 | 1158 | 0.7926 | 0.0207 | 0.0207 | 420 | 365 | 738 | 0.5350 | 0.3627 |
| 2015 | `life_phase` | hayır | 55906 | 0.7924 | 1158 | 0.7926 | 0.0207 | 0.0207 | 444 | 450 | 714 | 0.4966 | 0.3834 |
| 2016 | `control` | hayır | 34848 | 0.8078 | 156 | 0.7290 | 0.0070 | 0.0045 | 84 | 100 | 72 | 0.4565 | 0.5385 |
| 2016 | `age_only` | hayır | 34848 | 0.8078 | 156 | 0.7290 | 0.0070 | 0.0045 | 86 | 102 | 70 | 0.4574 | 0.5513 |
| 2016 | `life_phase` | hayır | 34848 | 0.8078 | 156 | 0.7290 | 0.0070 | 0.0045 | 88 | 141 | 68 | 0.3843 | 0.5641 |
| 2017 | `control` | hayır | 16544 | 0.8337 | 157 | 0.5925 | 0.0327 | 0.0095 | 93 | 27 | 64 | 0.7750 | 0.5924 |
| 2017 | `age_only` | hayır | 16544 | 0.8337 | 157 | 0.5925 | 0.0327 | 0.0095 | 93 | 25 | 64 | 0.7881 | 0.5924 |
| 2017 | `life_phase` | hayır | 16544 | 0.8337 | 157 | 0.5925 | 0.0327 | 0.0095 | 101 | 53 | 56 | 0.6558 | 0.6433 |
| 2022 | `control` | evet | 48916 | 0.7458 | 1567 | 0.7155 | 0.0374 | 0.0320 | 693 | 916 | 874 | 0.4307 | 0.4422 |
| 2022 | `age_only` | evet | 48916 | 0.7458 | 1567 | 0.7155 | 0.0374 | 0.0320 | 725 | 982 | 842 | 0.4247 | 0.4627 |
| 2022 | `life_phase` | evet | 48916 | 0.7458 | 1567 | 0.7155 | 0.0374 | 0.0320 | 599 | 824 | 968 | 0.4209 | 0.3823 |
| 2023 | `control` | hayır | 75108 | 0.7744 | 2785 | 0.6808 | 0.0597 | 0.0371 | 1091 | 1763 | 1694 | 0.3823 | 0.3917 |
| 2023 | `age_only` | hayır | 75108 | 0.7744 | 2785 | 0.6808 | 0.0597 | 0.0371 | 1107 | 1808 | 1678 | 0.3798 | 0.3975 |
| 2023 | `life_phase` | hayır | 75108 | 0.7744 | 2785 | 0.6808 | 0.0597 | 0.0371 | 968 | 1482 | 1817 | 0.3951 | 0.3476 |

## Dondurulmuş etiket sonuçları

Karşılaştırma için görünür tutuldu; [dondurulmuş etiketli uzun geçmiş deneyinden](precision-long-history-20261028.md)
kopyalandı, yeniden hesaplanmadı: dondurulmuş etiketlerde 24 ve 48 saatlik geçmiş özetleri, tek bölünme (2022 kalibrasyon,
2023 doğrulama) ve recall 0.95 kapısı. Kalibrasyon `incumbent` adayını seçti; en güçlü geçmiş adayının AP değeri daha
yüksek, ancak kapıdaki precision değeri daha düşüktü. Farklı bir temel, bölünme ve kapı: yukarıdaki tablolarla asla
birleştirilmez.

| bölüm | aday | precision | recall | FP | average precision |
| --- | --- | --- | --- | --- | --- |
| kalibrasyon 2022, recall 0.95 kapısı | `incumbent` | 0.090662 | 0.950119 | 4012 | 0.286706 |
| kalibrasyon 2022, recall 0.95 kapısı | `history_logistic_w0.5` | 0.087432 | 0.950119 | 4175 | 0.320887 |
| doğrulama 2023, aktarılan kalibrasyon eşiği | `incumbent` (seçilen) | 0.103397 | 0.884763 | 5992 | 0.220619 |

## Sınırlar

Daha önce incelenmiş yıllar: uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir. Kontrol kayıtlı hattır ve
yeniden eğitilmez; `age_only` yeniden eğitim ve kayıt uzunluğu kontrolüdür. Bir HARP'ın kayıtlı geçmişi bölgenin ortaya
çıkışında değil, ilk kayıtlı penceresinde başlar; bu yüzden yürüyen maksimum gözlenenin maksimumudur. Birçok pencere
gençtir: her yılda değerlendirme pencerelerinin büyük bir kısmının 72 saat önce kayıtlı penceresi yoktur; orada 72 saatlik
değişim eksiktir ve yürüyen istatistikler az pencereye dayanır. Kayıtlı pencereler etiket durumuna göre süzülmüştür: sayım
özelliği çıkarıldı ve hiçbir özellik belirli bir önceki pencerenin var olup olmadığını söylemez, ancak yaşam özelliklerinin
değerleri yine yalnızca kayıtlı önceki pencerelere dayanır; tam geçmiş tablosu bunu betimler ve okuma bunu yargılamaz.
Boşluklar kalite ve kadans retlerinden de gelir. Altı ölçüm, üç gecikme ve iki kırpma önceden sabitlendi; boş bir sonuç
başka seçimler hakkında bir şey söylemez ve bu sonuçlardan hiçbiri seçilemez. Ardışık saatlik pencereler 12 gözlem
saatlerinin 11'inde örtüşür ve HARP'lar tekrar eder; bu yüzden sayılar pencereler ve pozitif koşulardır, asla bağımsız olaylar
değildir ve aralıklar HARP kümelidir. 2016 ve 2017'de az pozitif koşu var (8 ve 6) ve aralıklar geniştir. Yeniden etiketlenmiş
etiketler NOAA SGAS ve JSOC `NOAA_ARS` ile yapılan bir ilişkilendirmedir, kesin gerçek değildir. 2022 bir alarm yedek kural yılıdır.

## Yeniden üretim

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_life_phase --config config/life-phase-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/life-phase-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `7339ad5fbd85fdcfc579e599c9c0b0635603fbd330119f1948c2fc6e451a74f2`; `phase1.json` sha256 `62489c3dfb77a14a44219bd509233be914534ea1bc4b7d80b263b61e9dd42feb`; `report.json` sha256 `c305b5aa3f77024ef54b5e62518ec0d7fc96fbc80b7b6bcdead53fb167d4d129`. Yeni bir
çıktı dizini kullanın; çalıştırıcı var olan bir dizinin üzerine yazmayı reddeder. Eğitimler, kayan nokta iş parçacığı
farkları dışında belirlenimcidir.
