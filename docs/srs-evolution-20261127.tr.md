# Benimsenen hatta alarm katmanında yayımlanan SRS bölge tanımının 24 saatlik değişimi (2026-11-27)

## Karar

Geliştirme temeli: yeniden etiketlenmiş tablo `artifacts/relabelled_development_20261111_r1` ve benimsenen hat
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)). Temel 2026-11-12 tarihinde değişti, çünkü dondurulmuş
etiketler eşlenmiş 2022 ile 2023 arası M/X patlamalarının %30'undan azını kapsıyordu. Daha önce incelenmiş yıllar:
uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir.

Okuma `S3_no_gain`, sonuç etiketi `result:no-gain`; kural herhangi bir sonuçtan önce
[`config/srs-evolution-v1.json`](../config/srs-evolution-v1.json) içinde donduruldu. Protokol bir `acceptance_rule`
taşıyor (`decision.srs_evolution_goal_met_and_beats_srs_static >= 1`); Hale `interpret_result`,
`artifacts/srs_evolution_20261127_r1` üzerinde gözlenen değer 0 ile `reject` döndürüyor. Sonuç bu karardır ve dondurulmuş
okuma onunla uyumludur: hiçbir aday kontrole karşı hedefi karşılamıyor (`candidates_meeting_goal_against_control` boş),
dolayısıyla `S2_refit_or_static_only` da geçerli değil. Yayımlanan NOAA SRS tanımının 24 saatlik değişimini statik SRS
bağlamına eklemek, dondurulmuş kurala göre alarm precision değerini yükseltmiyor; statik SRS bağlamı tek başına da
yükseltmiyor.

- `srs_static` yıllık birincil ölçütü 2015, 2016 ve 2017 yıllarında, `srs_evolution` 2015 ve 2016 yıllarında karşılıyor
  (altı yılda). İkisi de `all_year_primary` veya `cycle25_primary` (2022 ve 2023) koşulunu karşılamıyor.
- `srs_evolution`, `srs_static` adayını 2014, 2015 ve 2016 yıllarında geçiyor; precision farkları küçük (0.0067, 0.0014,
  0.0158) ve eşli HARP kümeli bootstrap aralıkları 0'ı içeriyor. 2017, 2022 ve 2023 yıllarında `srs_static` adayını
  geçmiyor.
- 25. döngü. 2022 yedek kural yılında alarm precision `srs_static` için 0.4380, `srs_evolution` için 0.4094, kontrol
  için 0.4727. İkisi de daha az pozitif koşu kaçırıyor (72 koşuda 26 ve 25, kontrol 32) ama daha fazla yanlış pozitif
  pencere veriyor (1454 ve 1705, kontrol 1178); precision farkının eşli bootstrap aralığı ikisi için de tamamen 0'ın
  altında ([-0.0648, -0.0111] ve [-0.1060, -0.0316]), `srs_evolution` eksi `srs_static` için de öyle ([-0.0492,
  -0.0142]). 2023'te alarm precision `srs_static` için 0.4207, `srs_evolution` için 0.4310, kontrol 0.4263; ancak ikisi
  de daha fazla pozitif koşu kaçırıyor (159 koşuda 72 ve 79, kontrol 68) ve 0.02'den fazla pencere recall kaybediyor
  (0.0379 ve 0.0824).
- 2017: `srs_evolution` kontrolden çok daha düşük bir alarm eşiği seçiyor (0.2594, kontrol 0.4145); alarm precision
  0.8676 değerinden 0.6101 değerine düşerken aynı pozitif koşulara alarm veriyor (6 koşuda 3 kaçırılan). `srs_static`
  2017 alarm precision değerini 0.8923'e yükseltiyor.
- 2014: alarm precision 0.6701 (`srs_static`) ve 0.6768 (`srs_evolution`), kontrol 0.6825; kaçırılan pozitif koşu daha
  az (88 koşuda 63, kontrol 66).
- İkincil, raporlanır ve değerlendirilmez: alarm precision kontrol ve iki aday için 2014, 2015 ve 2017 yıllarında en az
  0.50. 2022 üçü için de alarm yedek kural yılıdır ve hiçbir adayın başka bir yedek kural yılı yok.
- Betimleyici: 24 saatlik değişimi hesaplanabilen değerlendirme pencereleri pencerelerin 0.3275 ile 0.3979 arasını
  oluşturuyor, ancak pozitif pencerelerin 0.7853 ile 1.0000 arasını taşıyor. Bu alt kümede 2022 alarm precision
  `srs_evolution` için 0.4212, `srs_static` için 0.4514, kontrol için 0.4811. `srs_evolution` için patlamalı HARP içi AP
  2022'de 0.4873 ve 2023'te 0.3959; kontrol için 0.4968 ve 0.4057. Aynı HARP'ın pozitif bir penceresine 72 saat içinde
  olan alarm yanlış pozitif pencerelerinin payı `srs_evolution` için 2022'de 0.6305 ve 2023'te 0.7733; kontrol için
  0.7139 ve 0.7561.

Sonuç: bu kanıta göre burada dondurulduğu biçimiyle yayımlanan SRS tanımının 24 saatlik değişimi daha yüksek alarm
precision için bir yol değildir; statik SRS tanımı da değildir. Hiçbir model öne çıkarılmadı ve hiçbir alarm, eşik,
çalışma noktası veya pano ayarı değiştirilmedi. Çalıştırma, protokolün bütçesi olan 24 bileşen eğitimi kullandı ve
hiçbir şey indirmedi. Ayrılmış 2024 ile 2025 arası teste erişilmedi.

## Neden denendi

Fikir kaydı #10. Yayımlanan SRS bağlamı yalnızca statik bir anlık görüntü olarak ve yalnızca dondurulmuş etiketlerle,
recall 0.95 kapısında test edilmişti ([bölgesel bağlam sonuçları](region-context-results-20261109.tr.md)): 13 statik
öznitelik (`context`) birincil kuralı 6 yılın 1'inde, yalnızca erişilebilirlik bayrağıyla yeniden eğitim (`flag`) 6
yılın 4'ünde karşıladı; yani geçen şey içerik değil, yeniden eğitim ve erişilebilirlikti. Kayıt, McCloskey, Gallagher ve
Bloomfield (2016, 2018) çalışmalarına dayanıyor; bu çalışmalar bir güneş lekesi grubunun McIntosh sınıfı 24 saatte
yukarı doğru değiştiğinde patlama oranlarının arttığını, aşağı doğru değiştiğinde azaldığını bildiriyor.
[Yeniden etiketlenmiş 25. döngü teşhisi](cycle25-diagnostic-relabelled-20261112.tr.md), 2022 ve 2023 alarm yanlış pozitif
pencerelerinin 0.7139 ve 0.7561'inin aynı HARP'ın pozitif bir penceresine 72 saat içinde olduğunu buldu: alarm katmanı
bölgeyi buluyor ama günü kaçırıyor; yayımlanan bölge tanımının büyümesi veya sönmesi bölge içinde bir zamanlama
sinyalidir.

## Ne çalıştırıldı

Protokolün birleştirildiği haliyle tek bir çalıştırması, `main` commit `2083796` üzerinden: 2 aday, 6 yıl, 2 bileşen, 24
bileşen eğitimi, hiperparametre araması yok, 0 indirme. Duvar saati süresi 306 saniye.

```sh
OMP_NUM_THREADS=3 python -m scripts.audit_srs_evolution --config config/srs-evolution-v1.json --output artifacts/srs_evolution_20261127_r1
```

| öğe | sha256 |
| --- | --- |
| `config/srs-evolution-v1.json` | `be3f3a46478ac1ae0b2a087a07d0d0427f2fa4561fa4e2449e19420f2ebec39f` |
| `artifacts/walk_forward_v2_20261112_r1/report.json` (kontrol) | `c2b326d90253e824e9dd324158933e01c1216788653b1d284bf22850f67f76f1` |
| `artifacts/relabelled_development_20261111_r1/report.json` (etiketler) | `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43` |
| `config/walk-forward-v2.json` (hat protokolü) | `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb` |
| `config/walk-forward-v1.json` (temel tarifler) | `7c48fd7381456bee22f928b44da537880f06b4d70fd2b38b822279474c616303` |
| `data/region_summaries_20261109_r1/manifest.json` (SRS) | `36c9ba1c475e32cf171b199a4905225d5525fdda21d9ccbaff25610e1eac3c49` |
| `data/harp_noaa_mapping_20261109_r1/manifest.json` (HARP ile NOAA eşlemesi) | `01b8f7cd0489233a49d06af33d5768ee7d256d8ca02dc05618e2b0dd86a27bf8` |
| `artifacts/srs_evolution_20261127_r1/phase1.json` | `b3595807ef556f520fe24a9a8a9619c60aaa4f779e66f63add20521b2b87d98b` |
| `artifacts/srs_evolution_20261127_r1/thresholds.json` | `a51caf355a7ca1ccf92cb94a561f41ff605bb9e04d70b1f65705e80d6f50b011` |
| `artifacts/srs_evolution_20261127_r1/features.json` | `d2f0a739e015d2e3ac4e4a7bc48bc5d227b71160e52c157ade98545b7508bb96` |
| `artifacts/srs_evolution_20261127_r1/srs_coverage.csv` | `af5d88a5d6fe098083774b956b44edce79080f73893e5016b89fcc0204bae6bd` |
| `artifacts/srs_evolution_20261127_r1/results.csv` | `7117f22ecf1755634f6cb130962082916844a3fb92c81ec1ff947123e3befbf2` |
| `artifacts/srs_evolution_20261127_r1/intervals.csv` | `9fbb1427e288fbff70bee5476cd28e54b7496b31ed65bd352c4bb432682d30ef` |
| `artifacts/srs_evolution_20261127_r1/evolution_subset.csv` | `407547daa0ec5b8aa8e64591de78a89d3dd7740417c1c6793b052e79e305d332` |
| `artifacts/srs_evolution_20261127_r1/report.json` | `2dbe1583c607646b7fa31c028d8dca1fce8d277099f5b8588812558bcb98b46d` |

Çalıştırmadan önce protokolün adlandırdığı her girdi sha256 değerine karşı denetlendi: tablo raporu, kontrol raporu, iki
hat protokolü, SRS ve eşleme manifestoları, ve kontrolün yıllık `predictions.parquet` ile `thresholds.json` dosyaları
raporunun `artifact_hashes` alanına karşı. Her SRS ve eşleme dosyası kendi manifestosuna karşı denetlendi. Herhangi bir
ürün dosyası açılmadan önce iki manifesto ayrılmış döneme ait ürünler için okundu ve hiçbiri bulunmadı.
`models.joblib` hiç açılmadı. Çalıştırıcı her katlamanın dokuz nüfus ve kapsama sayısını yeniden hesapladı ve protokolle
eşit buldu; her pencerenin iki yayım zamanını da tahmin zamanı eksi 30 dakikaya karşı denetledi. Eşikler, öznitelik
listeleri, kapsama ve aday olasılıkları herhangi bir değerlendirme etiketi okunmadan önce yazıldı ve özetlendi
(`phase1.json`), değerlendirmeden sonra da kayıtlı özetlerini korudu. Kontrol olasılıklarının yanında saklanan hedef,
her değerlendirme penceresi için tablo etiketine eşittir.

## Yöntem

Nüfus: benimsenen hattın değerlendirme pencereleri, HARP ve saat başına bir pencere; 2014, 2015, 2016, 2017, 2022 ve
2023. 2018 ile 2021 arası benimsenen hatta atlanır ve dışarıda kalır. 2022 kontrolün alarm yedek kural yılıdır: saklanan
alarm eşiği `config/walk-forward-v2.json` yedek kuralından gelir. Her adayın kendi alarm eşiğinin yedek kural bayrağı her
tabloda verilir.

Adaylar. `control`: `artifacts/walk_forward_v2_20261112_r1` içindeki saklanan topluluk olasılıkları ve saklanan yıllık
izleme ve alarm eşikleri, yeniden eğitilmedi. `srs_static`: değiştirilmemiş `walk-forward-v1` tariflerinin 96 SHARP
özeti ile `config/region-context-v1.json` içindeki 13 bağlam özniteliği üzerinde, değiştirilmeden, yeniden eğitimi (109
öznitelik); yeniden eğitimi, erişilebilirliği ve statik içeriği yeni içerikten ayırır. `srs_evolution`: `srs_static` ile
yedi değişim özniteliği (116 öznitelik): `evo__earlier_listed` ve `evo__zurich_rank_change`,
`evo__penumbra_rank_change`, `evo__compact_rank_change`, `evo__mag_rank_change`, `evo__area_log_change` ile
`evo__spots_log_change` değişimleri.

Tahmin zamanı t olan bir pencerenin kullandığı SRS, t eksi 30 dakikada veya daha önce yayımlanmış en son SRS'tir ve
HARP'ın tahmin tarihindeki `NOAA_ARS` listesindeki NOAA numaralarıyla sınırlıdır. Önceki SRS, kullanılan SRS'ten 12 ile
36 saat önce yayımlanmış en son SRS'tir; yoksa daha eskisi yerine konmaz. Değişim, iki üründe de listelenen NOAA
numaraları üzerinden alınır: kullanılan SRS'teki en yüksek sıra eksi önceki SRS'teki en yüksek sıra, alan ve leke sayısı
için ise `log(1 + sum)` farkları. `evo__earlier_listed`, eşleşen bir numara önceki üründe de listeleniyorsa 1, önceki
SRS var ama hiçbirini listelemiyorsa 0'dır. Eksik değerler eksik kalır ve değiştirilmemiş tariflerin eksik göstergeli
medyan doldurucusundan geçer; eksik bir önceki satır hiçbir zaman değişim yok olarak kodlanmaz. `evolution_available`
yalnızca raporlama bayrağıdır, hiçbir zaman model girdisi değildir.

Eğitim: `helio24.walk_forward.annual_fold` ile genişleyen yıllık ileri yürüyüş; `config/walk-forward-v1.json` modelleri ve
hiperparametreleri değişmedi, önceki yıl üzerinde sigmoid kalibrasyon, topluluk 0.45 lojistik ve 0.55 XGBoost. Her aday
ve yıl için izleme eşiği (önceki yıl pencere recall 0.90) ve alarm eşiği (önceki yıl precision 0.50, recall tabanı 0.10,
yedek kural bayrağı) kalibrasyon yılı olasılıkları üzerinde seçilir; böylece her aday kendi önceki yıl eşikleriyle
değerlendirilir.

Kabul, [`config/activity-history-v2.json`](../config/activity-history-v2.json) ile aynıdır: bir aday, alarm precision
değeri kontrolden yüksek olduğunda, kaçırdığı pozitif koşular kontrolden fazla olmadığında ve pencere recall değeri en
çok 0.02 düştüğünde yıllık birincil ölçütü karşılar. `all_year_primary`: bu altı yılın hepsinde geçerlidir.
`cycle25_primary`: 2022 ve 2023 yıllarının ikisinde de geçerlidir. Bir aday, `all_year_primary` geçerli olduğunda veya
`cycle25_primary` geçerli olup precision farkının eşli HARP kümeli bootstrap aralığının (1000 çekiliş, tohum 24, yüzde
2.5 ve 97.5 dilimleri) alt sınırı 2022 ve 2023 yıllarının ikisinde de 0'ın üstünde olduğunda kontrole karşı hedefi
karşılar. Bir yılda `srs_evolution`, kontrolün yerine `srs_static` konduğunda yıllık birincil ölçüt geçerliyse
`srs_static` adayını geçer.

Okuma kuralı, bu sırayla uygulanır: `srs_evolution` bir yoldan kontrole karşı hedefi karşılar ve o yolun her yılında
`srs_static` adayını geçerse `S1_evolution_helps`; aksi halde `srs_evolution` veya `srs_static` kontrole karşı hedefi
karşılarsa `S2_refit_or_static_only`; aksi halde `S3_no_gain`.

Sayılar örtüşen saatlik pencerelerdir. Pozitif koşu, bir HARP'ın ardışık pozitif pencerelerinden oluşan bir gruptur.
İkisi de bağımsız bir olay değildir.

## SRS kapsamı

`srs_coverage.csv` dosyasından yıl ve role göre etiketsiz sayılar. `eşleşen SRS satırı`: kullanılan SRS'te en az bir
eşleşen satırı olan pencereler (`srs_available` 1). `değişim hesaplanabilir`: eşleşen en az bir NOAA numarası önceki
SRS'te de listelenen, dolayısıyla altı değişimin bulunduğu pencereler. `her değişimde eksik` altı değişim özniteliği için
aynıdır. Eğitim ve değerlendirme sayıları protokolde dondurulan nüfusa eşittir.

| yıl | rol | pencere | eşleşen SRS satırı | eşleşen payı | değişim hesaplanabilir | hesaplanabilir payı | `evo__earlier_listed` 1 | `evo__earlier_listed` 0 | eksik `evo__earlier_listed` | her değişimde eksik |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `train` | 150935 | 69264 | 0.4589 | 58302 | 0.3863 | 58302 | 10949 | 81684 | 92633 |
| 2014 | `calibration` | 76710 | 35999 | 0.4693 | 30381 | 0.3961 | 30381 | 5468 | 40861 | 46329 |
| 2014 | `evaluation` | 78351 | 32082 | 0.4095 | 27707 | 0.3536 | 27707 | 4375 | 46269 | 50644 |
| 2015 | `train` | 228635 | 106001 | 0.4636 | 89338 | 0.3907 | 89338 | 16500 | 122797 | 139297 |
| 2015 | `calibration` | 78351 | 32082 | 0.4095 | 27707 | 0.3536 | 27707 | 4375 | 46269 | 50644 |
| 2015 | `evaluation` | 70554 | 27965 | 0.3964 | 23672 | 0.3355 | 23672 | 4293 | 42589 | 46882 |
| 2016 | `train` | 307980 | 138742 | 0.4505 | 117669 | 0.3821 | 117669 | 20910 | 169401 | 190311 |
| 2016 | `calibration` | 70554 | 27965 | 0.3964 | 23672 | 0.3355 | 23672 | 4293 | 42589 | 46882 |
| 2016 | `evaluation` | 43142 | 17181 | 0.3982 | 14130 | 0.3275 | 14130 | 3015 | 25997 | 29012 |
| 2017 | `train` | 379962 | 167677 | 0.4413 | 142252 | 0.3744 | 142252 | 25262 | 212448 | 237710 |
| 2017 | `calibration` | 43142 | 17181 | 0.3982 | 14130 | 0.3275 | 14130 | 3015 | 25997 | 29012 |
| 2017 | `evaluation` | 19843 | 9255 | 0.4664 | 7896 | 0.3979 | 7896 | 1359 | 10588 | 11947 |
| 2022 | `train` | 466206 | 203687 | 0.4369 | 171797 | 0.3685 | 171797 | 31667 | 262742 | 294409 |
| 2022 | `calibration` | 29887 | 13879 | 0.4644 | 11282 | 0.3775 | 11282 | 2597 | 16008 | 18605 |
| 2022 | `evaluation` | 65593 | 29343 | 0.4473 | 24594 | 0.3749 | 24594 | 4575 | 36424 | 40999 |
| 2023 | `train` | 496391 | 217710 | 0.4386 | 183223 | 0.3691 | 183223 | 34264 | 278904 | 313168 |
| 2023 | `calibration` | 65593 | 29343 | 0.4473 | 24594 | 0.3749 | 24594 | 4575 | 36424 | 40999 |
| 2023 | `evaluation` | 96991 | 41627 | 0.4292 | 36235 | 0.3736 | 36235 | 5392 | 55364 | 60756 |

Her yılda değerlendirme pencerelerinin yarısından azında eşleşen bir SRS satırı var (0.3964 ile 0.4664 arası), daha da
azında hesaplanabilir bir değişim var (0.3275 ile 0.3979 arası).

## Alarm katmanı

Precision, sağlanan pencere recall değeri ve kaçırılan pozitif koşularla birlikte verilir. Aralıklar her adayın HARP
kümeli bootstrap aralıklarıdır. `yedek kural`, yedek kuralla seçilmiş bir alarm eşiğini işaretler.

| yıl | aday | yedek kural | alert eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep negatif accuracy | alarm pencereleri | alarm verilen pozitif koşular | kaçırılan / pozitif koşular |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.4627 | 688 | 320 | 1748 | 75595 | 0.2824 | [0.1030, 0.4369] | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 1008 | 22 | 66/88 |
| 2014 | `srs_static` | hayır | 0.4404 | 642 | 316 | 1794 | 75599 | 0.2635 | [0.0996, 0.3988] | 0.6701 | [0.4253, 0.8399] | 0.9731 | 0.9689 | 958 | 25 | 63/88 |
| 2014 | `srs_evolution` | hayır | 0.4184 | 645 | 308 | 1791 | 75607 | 0.2648 | [0.1127, 0.3902] | 0.6768 | [0.4419, 0.8374] | 0.9732 | 0.9689 | 953 | 25 | 63/88 |
| 2015 | `control` | hayır | 0.2631 | 545 | 457 | 916 | 68636 | 0.3730 | [0.1693, 0.5283] | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 1002 | 30 | 27/57 |
| 2015 | `srs_static` | hayır | 0.2639 | 595 | 429 | 866 | 68664 | 0.4073 | [0.1990, 0.5633] | 0.5811 | [0.3710, 0.7500] | 0.9816 | 0.9793 | 1024 | 31 | 26/57 |
| 2015 | `srs_evolution` | hayır | 0.2664 | 590 | 423 | 871 | 68670 | 0.4038 | [0.1903, 0.5640] | 0.5824 | [0.3606, 0.7463] | 0.9817 | 0.9793 | 1013 | 31 | 26/57 |
| 2016 | `control` | hayır | 0.2564 | 94 | 109 | 120 | 42819 | 0.4393 | [0.0000, 0.8506] | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 203 | 5 | 3/8 |
| 2016 | `srs_static` | hayır | 0.2467 | 94 | 108 | 120 | 42820 | 0.4393 | [0.0000, 0.9080] | 0.4653 | [0.0000, 0.5795] | 0.9947 | 0.9950 | 202 | 5 | 3/8 |
| 2016 | `srs_evolution` | hayır | 0.2384 | 102 | 110 | 112 | 42818 | 0.4766 | [0.0000, 0.9080] | 0.4811 | [0.0000, 0.6174] | 0.9949 | 0.9950 | 212 | 5 | 3/8 |
| 2017 | `control` | hayır | 0.4145 | 177 | 27 | 88 | 19551 | 0.6679 | [0.0000, 0.8535] | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 204 | 3 | 3/6 |
| 2017 | `srs_static` | hayır | 0.4308 | 174 | 21 | 91 | 19557 | 0.6566 | [0.0000, 0.8917] | 0.8923 | [0.0000, 0.9929] | 0.9944 | 0.9866 | 195 | 3 | 3/6 |
| 2017 | `srs_evolution` | hayır | 0.2594 | 194 | 124 | 71 | 19454 | 0.7321 | [0.0000, 0.9490] | 0.6101 | [0.0000, 0.8960] | 0.9902 | 0.9866 | 318 | 3 | 3/6 |
| 2022 | `control` | evet | 0.1570 | 1056 | 1178 | 1134 | 62225 | 0.4822 | [0.3268, 0.6058] | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 2234 | 40 | 32/72 |
| 2022 | `srs_static` | evet | 0.1333 | 1133 | 1454 | 1057 | 61949 | 0.5174 | [0.3689, 0.6364] | 0.4380 | [0.3232, 0.5646] | 0.9617 | 0.9666 | 2587 | 46 | 26/72 |
| 2022 | `srs_evolution` | evet | 0.1216 | 1182 | 1705 | 1008 | 61698 | 0.5397 | [0.3926, 0.6597] | 0.4094 | [0.2965, 0.5309] | 0.9586 | 0.9666 | 2887 | 47 | 25/72 |
| 2023 | `control` | hayır | 0.2689 | 1587 | 2136 | 2504 | 90764 | 0.3879 | [0.2918, 0.4663] | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 3723 | 91 | 68/159 |
| 2023 | `srs_static` | hayır | 0.2857 | 1432 | 1972 | 2659 | 90928 | 0.3500 | [0.2501, 0.4327] | 0.4207 | [0.3367, 0.5170] | 0.9523 | 0.9578 | 3404 | 87 | 72/159 |
| 2023 | `srs_evolution` | hayır | 0.3058 | 1250 | 1650 | 2841 | 91250 | 0.3055 | [0.2091, 0.3862] | 0.4310 | [0.3379, 0.5358] | 0.9537 | 0.9578 | 2900 | 80 | 79/159 |

## Kabul

`precision farkı` aday eksi kontroldür. `recall düşüşü` kontrol recall eksi aday recall değeridir; negatif değer bir
kazançtır. Aralık, precision farkının eşli HARP kümeli bootstrap aralığıdır. 2017'de kontrole karşı 1000 çekilişin
982'si kullanılabildi (kontrolün veya adayın hiç alarm penceresi olmayan bir çekiliş atlanır).

| yıl | aday | kontrol yedek kural | aday yedek kural | kontrol precision | aday precision | precision farkı | fark %95 aralığı | kullanılan bootstrap çekilişi | recall düşüşü | kaçırılan koşular kontrol | kaçırılan koşular aday | precision daha yüksek | kaçırılan koşular fazla değil | recall düşüşü en çok 0.02 | yıllık birincil karşılandı |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `srs_static` | hayır | hayır | 0.6825 | 0.6701 | -0.0124 | [-0.0369, 0.0246] | 1000 | 0.0189 | 66 | 63 | hayır | evet | evet | hayır |
| 2014 | `srs_evolution` | hayır | hayır | 0.6825 | 0.6768 | -0.0057 | [-0.0517, 0.0755] | 1000 | 0.0177 | 66 | 63 | hayır | evet | evet | hayır |
| 2015 | `srs_static` | hayır | hayır | 0.5439 | 0.5811 | 0.0371 | [0.0125, 0.0725] | 1000 | -0.0342 | 27 | 26 | evet | evet | evet | evet |
| 2015 | `srs_evolution` | hayır | hayır | 0.5439 | 0.5824 | 0.0385 | [0.0053, 0.0766] | 1000 | -0.0308 | 27 | 26 | evet | evet | evet | evet |
| 2016 | `srs_static` | hayır | hayır | 0.4631 | 0.4653 | 0.0023 | [-0.1032, 0.0254] | 1000 | 0.0000 | 3 | 3 | evet | evet | evet | evet |
| 2016 | `srs_evolution` | hayır | hayır | 0.4631 | 0.4811 | 0.0181 | [-0.0378, 0.0437] | 1000 | -0.0374 | 3 | 3 | evet | evet | evet | evet |
| 2017 | `srs_static` | hayır | hayır | 0.8676 | 0.8923 | 0.0247 | [-0.1084, 0.1336] | 982 | 0.0113 | 3 | 3 | evet | evet | evet | evet |
| 2017 | `srs_evolution` | hayır | hayır | 0.8676 | 0.6101 | -0.2576 | [-0.4478, 0.0000] | 982 | -0.0642 | 3 | 3 | hayır | evet | evet | hayır |
| 2022 | `srs_static` | evet | evet | 0.4727 | 0.4380 | -0.0347 | [-0.0648, -0.0111] | 1000 | -0.0352 | 32 | 26 | hayır | evet | evet | hayır |
| 2022 | `srs_evolution` | evet | evet | 0.4727 | 0.4094 | -0.0633 | [-0.1060, -0.0316] | 1000 | -0.0575 | 32 | 25 | hayır | evet | evet | hayır |
| 2023 | `srs_static` | hayır | hayır | 0.4263 | 0.4207 | -0.0056 | [-0.0279, 0.0182] | 1000 | 0.0379 | 68 | 72 | hayır | hayır | hayır | hayır |
| 2023 | `srs_evolution` | hayır | hayır | 0.4263 | 0.4310 | 0.0048 | [-0.0281, 0.0381] | 1000 | 0.0824 | 68 | 79 | evet | hayır | hayır | hayır |

`srs_evolution` karşısında `srs_static`: kontrolün yerine `srs_static` konarak aynı üç koşul. Aralık betimleyicidir;
2017'de 1000 çekilişin 994'ü kullanılabildi.

| yıl | `srs_static` yedek kural | `srs_evolution` yedek kural | `srs_static` precision | `srs_evolution` precision | precision farkı | fark %95 aralığı | kullanılan bootstrap çekilişi | recall düşüşü | kaçırılan koşular `srs_static` | kaçırılan koşular `srs_evolution` | precision daha yüksek | kaçırılan koşular fazla değil | recall düşüşü en çok 0.02 | `srs_static` adayını geçiyor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | hayır | hayır | 0.6701 | 0.6768 | 0.0067 | [-0.0252, 0.0644] | 1000 | -0.0012 | 63 | 63 | evet | evet | evet | evet |
| 2015 | hayır | hayır | 0.5811 | 0.5824 | 0.0014 | [-0.0273, 0.0261] | 1000 | 0.0034 | 26 | 26 | evet | evet | evet | evet |
| 2016 | hayır | hayır | 0.4653 | 0.4811 | 0.0158 | [-0.0092, 0.1158] | 1000 | -0.0374 | 3 | 3 | evet | evet | evet | evet |
| 2017 | hayır | hayır | 0.8923 | 0.6101 | -0.2822 | [-0.4404, 0.0000] | 994 | -0.0755 | 3 | 3 | hayır | evet | evet | hayır |
| 2022 | evet | evet | 0.4380 | 0.4094 | -0.0285 | [-0.0492, -0.0142] | 1000 | -0.0224 | 26 | 25 | hayır | evet | evet | hayır |
| 2023 | hayır | hayır | 0.4207 | 0.4310 | 0.0104 | [-0.0067, 0.0289] | 1000 | 0.0445 | 72 | 79 | evet | hayır | hayır | hayır |

| aday | yıllık birincil ölçütü karşılayan yıllar | all_year_primary | cycle25_primary | 2022 ve 2023 yıllarında bootstrap alt sınırı 0 üstünde | kontrole karşı hedef karşılandı | `srs_static` adayını geçtiği yıllar | alarm yedek kural yılları | alarm precision en az 0.50 olan yıllar (ikincil) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `control` |  |  |  |  |  |  | 2022 | 2014, 2015, 2017 |
| `srs_static` | 2015, 2016, 2017 | hayır | hayır | hayır | hayır |  | 2022 | 2014, 2015, 2017 |
| `srs_evolution` | 2015, 2016 | hayır | hayır | hayır | hayır | 2014, 2015, 2016 | 2022 | 2014, 2015, 2017 |

## Değişim özniteliklerinin bulunduğu yer (betimleyici)

`evolution_subset.csv` dosyasından, her adayın kendi alarm eşiğinde, 24 saatlik değişimi hesaplanabilen
(`change_available`) ve hesaplanamayan (`change_missing`) değerlendirme pencerelerindeki alarm sayıları. `pozitif payı`,
yılın pozitif pencerelerinin alt kümedeki payıdır. 2017'de `change_missing` alt kümesinde hiç pozitif pencere yok.

| yıl | aday | alt küme | pencere | pencere payı | pozitif | pozitif payı | alarm TP | alarm FP | alarm FN | alarm precision | alarm recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `change_available` | 27707 | 0.3536 | 1913 | 0.7853 | 584 | 276 | 1329 | 0.6791 | 0.3053 |
| 2014 | `srs_static` | `change_available` | 27707 | 0.3536 | 1913 | 0.7853 | 556 | 287 | 1357 | 0.6595 | 0.2906 |
| 2014 | `srs_evolution` | `change_available` | 27707 | 0.3536 | 1913 | 0.7853 | 581 | 282 | 1332 | 0.6732 | 0.3037 |
| 2014 | `control` | `change_missing` | 50644 | 0.6464 | 523 | 0.2147 | 104 | 44 | 419 | 0.7027 | 0.1989 |
| 2014 | `srs_static` | `change_missing` | 50644 | 0.6464 | 523 | 0.2147 | 86 | 29 | 437 | 0.7478 | 0.1644 |
| 2014 | `srs_evolution` | `change_missing` | 50644 | 0.6464 | 523 | 0.2147 | 64 | 26 | 459 | 0.7111 | 0.1224 |
| 2015 | `control` | `change_available` | 23672 | 0.3355 | 1229 | 0.8412 | 482 | 369 | 747 | 0.5664 | 0.3922 |
| 2015 | `srs_static` | `change_available` | 23672 | 0.3355 | 1229 | 0.8412 | 530 | 353 | 699 | 0.6002 | 0.4312 |
| 2015 | `srs_evolution` | `change_available` | 23672 | 0.3355 | 1229 | 0.8412 | 524 | 342 | 705 | 0.6051 | 0.4264 |
| 2015 | `control` | `change_missing` | 46882 | 0.6645 | 232 | 0.1588 | 63 | 88 | 169 | 0.4172 | 0.2716 |
| 2015 | `srs_static` | `change_missing` | 46882 | 0.6645 | 232 | 0.1588 | 65 | 76 | 167 | 0.4610 | 0.2802 |
| 2015 | `srs_evolution` | `change_missing` | 46882 | 0.6645 | 232 | 0.1588 | 66 | 81 | 166 | 0.4490 | 0.2845 |
| 2016 | `control` | `change_available` | 14130 | 0.3275 | 174 | 0.8131 | 84 | 95 | 90 | 0.4693 | 0.4828 |
| 2016 | `srs_static` | `change_available` | 14130 | 0.3275 | 174 | 0.8131 | 84 | 96 | 90 | 0.4667 | 0.4828 |
| 2016 | `srs_evolution` | `change_available` | 14130 | 0.3275 | 174 | 0.8131 | 84 | 96 | 90 | 0.4667 | 0.4828 |
| 2016 | `control` | `change_missing` | 29012 | 0.6725 | 40 | 0.1869 | 10 | 14 | 30 | 0.4167 | 0.2500 |
| 2016 | `srs_static` | `change_missing` | 29012 | 0.6725 | 40 | 0.1869 | 10 | 12 | 30 | 0.4545 | 0.2500 |
| 2016 | `srs_evolution` | `change_missing` | 29012 | 0.6725 | 40 | 0.1869 | 18 | 14 | 22 | 0.5625 | 0.4500 |
| 2017 | `control` | `change_available` | 7896 | 0.3979 | 265 | 1.0000 | 177 | 24 | 88 | 0.8806 | 0.6679 |
| 2017 | `srs_static` | `change_available` | 7896 | 0.3979 | 265 | 1.0000 | 174 | 18 | 91 | 0.9062 | 0.6566 |
| 2017 | `srs_evolution` | `change_available` | 7896 | 0.3979 | 265 | 1.0000 | 194 | 105 | 71 | 0.6488 | 0.7321 |
| 2017 | `control` | `change_missing` | 11947 | 0.6021 | 0 | 0.0000 | 0 | 3 | 0 | 0.0000 |  |
| 2017 | `srs_static` | `change_missing` | 11947 | 0.6021 | 0 | 0.0000 | 0 | 3 | 0 | 0.0000 |  |
| 2017 | `srs_evolution` | `change_missing` | 11947 | 0.6021 | 0 | 0.0000 | 0 | 19 | 0 | 0.0000 |  |
| 2022 | `control` | `change_available` | 24594 | 0.3749 | 1773 | 0.8096 | 877 | 946 | 896 | 0.4811 | 0.4946 |
| 2022 | `srs_static` | `change_available` | 24594 | 0.3749 | 1773 | 0.8096 | 943 | 1146 | 830 | 0.4514 | 0.5319 |
| 2022 | `srs_evolution` | `change_available` | 24594 | 0.3749 | 1773 | 0.8096 | 986 | 1355 | 787 | 0.4212 | 0.5561 |
| 2022 | `control` | `change_missing` | 40999 | 0.6251 | 417 | 0.1904 | 179 | 232 | 238 | 0.4355 | 0.4293 |
| 2022 | `srs_static` | `change_missing` | 40999 | 0.6251 | 417 | 0.1904 | 190 | 308 | 227 | 0.3815 | 0.4556 |
| 2022 | `srs_evolution` | `change_missing` | 40999 | 0.6251 | 417 | 0.1904 | 196 | 350 | 221 | 0.3590 | 0.4700 |
| 2023 | `control` | `change_available` | 36235 | 0.3736 | 3231 | 0.7898 | 1306 | 1831 | 1925 | 0.4163 | 0.4042 |
| 2023 | `srs_static` | `change_available` | 36235 | 0.3736 | 3231 | 0.7898 | 1181 | 1699 | 2050 | 0.4101 | 0.3655 |
| 2023 | `srs_evolution` | `change_available` | 36235 | 0.3736 | 3231 | 0.7898 | 1018 | 1413 | 2213 | 0.4188 | 0.3151 |
| 2023 | `control` | `change_missing` | 60756 | 0.6264 | 860 | 0.2102 | 281 | 305 | 579 | 0.4795 | 0.3267 |
| 2023 | `srs_static` | `change_missing` | 60756 | 0.6264 | 860 | 0.2102 | 251 | 273 | 609 | 0.4790 | 0.2919 |
| 2023 | `srs_evolution` | `change_missing` | 60756 | 0.6264 | 860 | 0.2102 | 232 | 237 | 628 | 0.4947 | 0.2698 |

## Sıralama ve alarm yanlış pozitiflerinin kaynağı (betimleyici)

Raporlanır, değerlendirilmez. Average precision, bölge AP ve patlamalı HARP içi AP bir eşiğe bağlı değildir. Yanlış
pozitif payları her adayın kendi alarm eşiğinde alınır. `kontrol recall değerinde precision`, adayın kontrolün alarm
recall değerini sağlayan değerlendirme yılı eşiğindeki precision değeridir: değerlendirme etiketlerini kullanan, kâhinle
eşlenmiş bir betimlemedir ve hiçbir zaman uygulanabilir değildir.

| yıl | aday | yedek kural | average precision | bölge AP | patlamalı HARP içi AP | alarm FP pencereleri | hiç patlamamış HARP kaynaklı alarm FP payı | pozitif pencereye 72 saat içindeki alarm FP payı | kontrol alarm recall | kontrol recall değerinde precision (kâhin) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.5015 | 0.7600 | 0.5528 | 320 | 0.1437 | 0.7063 | 0.2824 | 0.6825 |
| 2014 | `srs_static` | hayır | 0.4920 | 0.7731 | 0.5411 | 316 | 0.1203 | 0.6867 | 0.2824 | 0.6577 |
| 2014 | `srs_evolution` | hayır | 0.4889 | 0.7660 | 0.5395 | 308 | 0.1266 | 0.6721 | 0.2824 | 0.6673 |
| 2015 | `control` | hayır | 0.4823 | 0.8264 | 0.5331 | 457 | 0.0853 | 0.8249 | 0.3730 | 0.5439 |
| 2015 | `srs_static` | hayır | 0.4898 | 0.8193 | 0.5413 | 429 | 0.0956 | 0.8345 | 0.3730 | 0.5911 |
| 2015 | `srs_evolution` | hayır | 0.4918 | 0.8055 | 0.5435 | 423 | 0.0827 | 0.8416 | 0.3730 | 0.6009 |
| 2016 | `control` | hayır | 0.4060 | 0.6333 | 0.4853 | 109 | 0.2569 | 0.5688 | 0.4393 | 0.4631 |
| 2016 | `srs_static` | hayır | 0.4210 | 0.5625 | 0.5016 | 108 | 0.2685 | 0.5741 | 0.4393 | 0.4724 |
| 2016 | `srs_evolution` | hayır | 0.4287 | 0.6841 | 0.5020 | 110 | 0.2364 | 0.5636 | 0.4393 | 0.5281 |
| 2017 | `control` | hayır | 0.7975 | 1.0000 | 0.8727 | 27 | 0.1111 | 0.8889 | 0.6679 | 0.8676 |
| 2017 | `srs_static` | hayır | 0.7891 | 0.8667 | 0.8737 | 21 | 0.3810 | 0.6190 | 0.6679 | 0.8939 |
| 2017 | `srs_evolution` | hayır | 0.7852 | 0.8667 | 0.8718 | 124 | 0.6855 | 0.3145 | 0.6679 | 0.8719 |
| 2022 | `control` | evet | 0.4622 | 0.8315 | 0.4968 | 1178 | 0.0823 | 0.7139 | 0.4822 | 0.4727 |
| 2022 | `srs_static` | evet | 0.4584 | 0.8251 | 0.4931 | 1454 | 0.1114 | 0.6575 | 0.4822 | 0.4615 |
| 2022 | `srs_evolution` | evet | 0.4523 | 0.8247 | 0.4873 | 1705 | 0.1220 | 0.6305 | 0.4822 | 0.4492 |
| 2023 | `control` | hayır | 0.3626 | 0.8655 | 0.4057 | 2136 | 0.1320 | 0.7561 | 0.3879 | 0.4263 |
| 2023 | `srs_static` | hayır | 0.3513 | 0.8600 | 0.3976 | 1972 | 0.1476 | 0.7475 | 0.3879 | 0.4140 |
| 2023 | `srs_evolution` | hayır | 0.3501 | 0.8627 | 0.3959 | 1650 | 0.1339 | 0.7733 | 0.3879 | 0.4071 |

## İzleme katmanı

Her aday kendi önceki yıl izleme eşiğinde (önceki yılda pencere recall 0.90). Hiçbir izleme eşiği yedek kural değildir.

| yıl | aday | yedek kural | watch eşiği | TP | FP | FN | TN | recall | recall %95 aralığı | precision | precision %95 aralığı | accuracy | hep negatif accuracy | alarm pencereleri | alarm verilen pozitif koşular | kaçırılan / pozitif koşular |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 0.0311 | 2146 | 9020 | 290 | 66895 | 0.8810 | [0.8065, 0.9357] | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 11166 | 82 | 6/88 |
| 2014 | `srs_static` | hayır | 0.0262 | 2191 | 10161 | 245 | 65754 | 0.8994 | [0.8333, 0.9481] | 0.1774 | [0.1222, 0.2402] | 0.8672 | 0.9689 | 12352 | 83 | 5/88 |
| 2014 | `srs_evolution` | hayır | 0.0251 | 2219 | 10516 | 217 | 65399 | 0.9109 | [0.8503, 0.9548] | 0.1742 | [0.1203, 0.2360] | 0.8630 | 0.9689 | 12735 | 84 | 4/88 |
| 2015 | `control` | hayır | 0.0364 | 1396 | 8079 | 65 | 61014 | 0.9555 | [0.8917, 0.9971] | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 9475 | 56 | 1/57 |
| 2015 | `srs_static` | hayır | 0.0350 | 1393 | 8000 | 68 | 61093 | 0.9535 | [0.8876, 0.9934] | 0.1483 | [0.0917, 0.2054] | 0.8856 | 0.9793 | 9393 | 56 | 1/57 |
| 2015 | `srs_evolution` | hayır | 0.0360 | 1381 | 7770 | 80 | 61323 | 0.9452 | [0.8745, 0.9863] | 0.1509 | [0.0935, 0.2094] | 0.8887 | 0.9793 | 9151 | 56 | 1/57 |
| 2016 | `control` | hayır | 0.0471 | 201 | 1722 | 13 | 41206 | 0.9393 | [0.4545, 1.0000] | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 1923 | 8 | 0/8 |
| 2016 | `srs_static` | hayır | 0.0476 | 198 | 1609 | 16 | 41319 | 0.9252 | [0.4091, 1.0000] | 0.1096 | [0.0000, 0.2015] | 0.9623 | 0.9950 | 1807 | 8 | 0/8 |
| 2016 | `srs_evolution` | hayır | 0.0495 | 198 | 1551 | 16 | 41377 | 0.9252 | [0.4091, 1.0000] | 0.1132 | [0.0000, 0.2061] | 0.9637 | 0.9950 | 1749 | 8 | 0/8 |
| 2017 | `control` | hayır | 0.0270 | 243 | 1058 | 22 | 18520 | 0.9170 | [0.7692, 1.0000] | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1301 | 5 | 1/6 |
| 2017 | `srs_static` | hayır | 0.0271 | 246 | 1017 | 19 | 18561 | 0.9283 | [0.7692, 1.0000] | 0.1948 | [0.0000, 0.4787] | 0.9478 | 0.9866 | 1263 | 5 | 1/6 |
| 2017 | `srs_evolution` | hayır | 0.0216 | 247 | 1100 | 18 | 18478 | 0.9321 | [0.7692, 1.0000] | 0.1834 | [0.0000, 0.4490] | 0.9437 | 0.9866 | 1347 | 5 | 1/6 |
| 2022 | `control` | hayır | 0.0183 | 2024 | 11917 | 166 | 51486 | 0.9242 | [0.8502, 0.9731] | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 13941 | 67 | 5/72 |
| 2022 | `srs_static` | hayır | 0.0176 | 2039 | 12169 | 151 | 51234 | 0.9311 | [0.8576, 0.9798] | 0.1435 | [0.0998, 0.1935] | 0.8122 | 0.9666 | 14208 | 67 | 5/72 |
| 2022 | `srs_evolution` | hayır | 0.0168 | 2044 | 12458 | 146 | 50945 | 0.9333 | [0.8619, 0.9818] | 0.1409 | [0.0983, 0.1901] | 0.8078 | 0.9666 | 14502 | 67 | 5/72 |
| 2023 | `control` | hayır | 0.0405 | 3695 | 16022 | 396 | 76878 | 0.9032 | [0.8486, 0.9425] | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 19717 | 149 | 10/159 |
| 2023 | `srs_static` | hayır | 0.0431 | 3679 | 15264 | 412 | 77636 | 0.8993 | [0.8455, 0.9398] | 0.1942 | [0.1579, 0.2306] | 0.8384 | 0.9578 | 18943 | 150 | 9/159 |
| 2023 | `srs_evolution` | hayır | 0.0427 | 3686 | 15425 | 405 | 77475 | 0.9010 | [0.8470, 0.9409] | 0.1929 | [0.1569, 0.2287] | 0.8368 | 0.9578 | 19111 | 150 | 9/159 |

İzleme katmanı accuracy değeri her yıl her aday için hep negatif accuracy değerinin altındadır.

## Seçilen eşikler

Herhangi bir değerlendirme etiketi okunmadan önce kalibrasyon yılı olasılıkları üzerinde seçildi. `önceki yıl recall` ve
`önceki yıl precision`, seçilen eşikteki kalibrasyon yılı değerleridir.

| yıl | aday | katman | eşik | önceki yıl recall | önceki yıl precision | yedek kural |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | `watch` | 0.0311 |  |  | hayır |
| 2014 | `control` | `alert` | 0.4627 | 0.1326 | 0.5000 | hayır |
| 2014 | `srs_static` | `watch` | 0.0262 |  |  | hayır |
| 2014 | `srs_static` | `alert` | 0.4404 | 0.1079 | 0.5000 | hayır |
| 2014 | `srs_evolution` | `watch` | 0.0251 |  |  | hayır |
| 2014 | `srs_evolution` | `alert` | 0.4184 | 0.1237 | 0.5000 | hayır |
| 2015 | `control` | `watch` | 0.0364 |  |  | hayır |
| 2015 | `control` | `alert` | 0.2631 | 0.4906 | 0.5000 | hayır |
| 2015 | `srs_static` | `watch` | 0.0350 |  |  | hayır |
| 2015 | `srs_static` | `alert` | 0.2639 | 0.4823 | 0.5000 | hayır |
| 2015 | `srs_evolution` | `watch` | 0.0360 |  |  | hayır |
| 2015 | `srs_evolution` | `alert` | 0.2664 | 0.4762 | 0.5000 | hayır |
| 2016 | `control` | `watch` | 0.0471 |  |  | hayır |
| 2016 | `control` | `alert` | 0.2564 | 0.4969 | 0.5000 | hayır |
| 2016 | `srs_static` | `watch` | 0.0476 |  |  | hayır |
| 2016 | `srs_static` | `alert` | 0.2467 | 0.5311 | 0.5000 | hayır |
| 2016 | `srs_evolution` | `watch` | 0.0495 |  |  | hayır |
| 2016 | `srs_evolution` | `alert` | 0.2384 | 0.5366 | 0.5000 | hayır |
| 2017 | `control` | `watch` | 0.0270 |  |  | hayır |
| 2017 | `control` | `alert` | 0.4145 | 0.2196 | 0.5000 | hayır |
| 2017 | `srs_static` | `watch` | 0.0271 |  |  | hayır |
| 2017 | `srs_static` | `alert` | 0.4308 | 0.2664 | 0.5000 | hayır |
| 2017 | `srs_evolution` | `watch` | 0.0216 |  |  | hayır |
| 2017 | `srs_evolution` | `alert` | 0.2594 | 0.4159 | 0.5000 | hayır |
| 2022 | `control` | `watch` | 0.0183 |  |  | hayır |
| 2022 | `control` | `alert` | 0.1570 | 0.2361 | 0.1996 | evet |
| 2022 | `srs_static` | `watch` | 0.0176 |  |  | hayır |
| 2022 | `srs_static` | `alert` | 0.1333 | 0.2653 | 0.1645 | evet |
| 2022 | `srs_evolution` | `watch` | 0.0168 |  |  | hayır |
| 2022 | `srs_evolution` | `alert` | 0.1216 | 0.2891 | 0.1542 | evet |
| 2023 | `control` | `watch` | 0.0405 |  |  | hayır |
| 2023 | `control` | `alert` | 0.2689 | 0.4461 | 0.5000 | hayır |
| 2023 | `srs_static` | `watch` | 0.0431 |  |  | hayır |
| 2023 | `srs_static` | `alert` | 0.2857 | 0.4068 | 0.5000 | hayır |
| 2023 | `srs_evolution` | `watch` | 0.0427 |  |  | hayır |
| 2023 | `srs_evolution` | `alert` | 0.3058 | 0.3676 | 0.5000 | hayır |

## Dondurulmuş etiket sonuçları

Karşılaştırma için görünür tutuldu; [bölgesel bağlam sonuçları](region-context-results-20261109.tr.md) raporundan
kopyalandı, yeniden hesaplanmadı: dondurulmuş etiketlerde statik SRS bağlamı, önceki yıl recall 0.95 eşikleri, adaylar
`flag` (yalnızca erişilebilirlik) ve `context` (13 statik öznitelik). Farklı bir temel, etiket kümesi ve kapıdır;
değerler yukarıdaki tablolarla hiçbir zaman birleştirilmez ve onlarla karşılaştırılamaz.

| candidate | years_met | required_years | all_year_primary | met_years |
| --- | --- | --- | --- | --- |
| flag | 4 | 6 | hayır | [2014, 2016, 2022, 2023] |
| context | 1 | 6 | hayır | [2015] |

| yıl | aday | eşik | TP | FP | recall | recall ≥ 0.95 | precision | alarm verilen pozitif koşular | AP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.011475 | 2184 | 13886 | 0.9455 | hayır | 0.1359 | 80/83 | 0.5079 |
| 2014 | flag | 0.011701 | 2183 | 13761 | 0.9450 | hayır | 0.1369 | 80/83 | 0.5082 |
| 2014 | context | 0.009703 | 2202 | 14833 | 0.9532 | evet | 0.1293 | 80/83 | 0.4992 |
| 2015 | control | 0.018839 | 1346 | 11453 | 0.9934 | evet | 0.1052 | 51/51 | 0.4924 |
| 2015 | flag | 0.018485 | 1346 | 11551 | 0.9934 | evet | 0.1044 | 51/51 | 0.4930 |
| 2015 | context | 0.018868 | 1347 | 11297 | 0.9941 | evet | 0.1065 | 51/51 | 0.5118 |
| 2016 | control | 0.030831 | 176 | 2289 | 0.9724 | evet | 0.0714 | 7/7 | 0.3664 |
| 2016 | flag | 0.031593 | 173 | 2234 | 0.9558 | evet | 0.0719 | 7/7 | 0.3620 |
| 2016 | context | 0.026925 | 176 | 2380 | 0.9724 | evet | 0.0689 | 7/7 | 0.3645 |
| 2017 | control | 0.012000 | 237 | 1287 | 0.9368 | hayır | 0.1555 | 5/6 | 0.8117 |
| 2017 | flag | 0.010120 | 238 | 1370 | 0.9407 | hayır | 0.1480 | 5/6 | 0.8118 |
| 2017 | context | 0.012045 | 237 | 1303 | 0.9368 | hayır | 0.1539 | 5/6 | 0.7988 |
| 2022 | control | 0.008994 | 415 | 10072 | 0.9857 | evet | 0.0396 | 16/16 | 0.2800 |
| 2022 | flag | 0.009298 | 415 | 9868 | 0.9857 | evet | 0.0404 | 16/16 | 0.2791 |
| 2022 | context | 0.009014 | 415 | 10192 | 0.9857 | evet | 0.0391 | 16/16 | 0.2775 |
| 2023 | control | 0.018203 | 691 | 5992 | 0.8848 | hayır | 0.1034 | 36/38 | 0.2206 |
| 2023 | flag | 0.018357 | 689 | 5973 | 0.8822 | hayır | 0.1034 | 36/38 | 0.2205 |
| 2023 | context | 0.017289 | 686 | 6374 | 0.8784 | hayır | 0.0972 | 36/38 | 0.2258 |

## Sınırlar

Daha önce incelenmiş yıllar: uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir. Kontrol saklanan hattır ve
yeniden eğitilmedi; `srs_static` yeniden eğitim, erişilebilirlik ve statik içerik kontrolüdür ve her yılda kontrolden
farklıdır (örneğin 2022 alarm eşiği 0.1333, kontrol 0.1570); bu yüzden `srs_static` ile kontrol arasındaki farklar
yalnızca SRS içeriğine atfedilemez. SRS günde bir kez yayımlanır, dolayısıyla tahmin zamanında değişim iki güne kadar
eskidir; bu bir sınırdır, sızıntı değildir. Kapsam kısmidir: değerlendirme pencerelerinin yarısından azında eşleşen bir
SRS satırı, daha da azında hesaplanabilir bir değişim vardır; bu yüzden değişim öznitelikleri pencerelerin bir
azınlığında etkili olabilir, ancak bu azınlık pozitif pencerelerin çoğunu taşır. SRS yalnızca lekeli bölgeleri listeler;
iki günün hiçbirinde lekesi olmayan bir bölgenin değişimi yoktur. NOAA numaraları, sonradan sabitlenen kesin JSOC
eşlemesi `NOAA_ARS` alanından gelir: hangi SRS satırlarının bir HARP'a ait olduğunun tahmin zamanında bilinip
bilinemeyeceği bilinmiyor. Arşivlenen SRS metni ilk yayımlanan baytlardan farklı olabilir. Yeniden etiketlenmiş etiketler
SGAS ürünleri ve aynı `NOAA_ARS` eşlemesiyle elde edildi; dolayısıyla öznitelikler ve etiketler kaynağın bölge atama
hatalarını paylaşır. Yedi öznitelik, bir gecikme ve önceki ürün için bir kural önceden sabitlendi; boş bir sonuç, 48 veya
72 saatlik değişimler ya da tam McIntosh geçişi gibi başka seçimler hakkında bir şey söylemez ve bu sonuçlardan hiçbiri
seçilemez. Ardışık saatlik pencereler 12 gözlem saatinin 11'inde örtüşür, HARP'lar tekrarlanır ve bir günün her penceresi
tek bir SRS'i paylaşır; dolayısıyla sayılar pencere ve pozitif koşudur, hiçbir zaman bağımsız olay değildir, aralıklar
da HARP kümelidir. 2016 ve 2017 yıllarında pozitif koşu azdır (8 ve 6) ve aralıklar geniştir. Bootstrap aralıkları
eğitilmiş modelleri ve eşikleri sabit tutar, eğitim ve kalibrasyon belirsizliğini dışarıda bırakır. 2022 üçü için de
alarm yedek kural yılıdır.

## Yeniden üretim

```sh
bash agents/bin/evidence.sh seed
OMP_NUM_THREADS=3 python -m scripts.audit_srs_evolution --config config/srs-evolution-v1.json --output artifacts/<new directory>
python agents/bin/hale_call.py interpret_result '{"protocol": "config/srs-evolution-v1.json", "artifact": "artifacts/<new directory>"}'
```

Config sha256 `be3f3a46478ac1ae0b2a087a07d0d0427f2fa4561fa4e2449e19420f2ebec39f`; `phase1.json` sha256
`b3595807ef556f520fe24a9a8a9619c60aaa4f779e66f63add20521b2b87d98b`; `report.json` sha256
`2dbe1583c607646b7fa31c028d8dca1fce8d277099f5b8588812558bcb98b46d`. Yeni bir çıktı dizini kullanın; çalıştırıcı var olan
bir dizinin üzerine yazmayı reddeder.
