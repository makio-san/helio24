# Çalışma noktası v3'ün benimsenmesi ve geliştirme hattının yeniden kurulması (2026-11-12)

## Karar

Proje sahibi 2026-11-12'de [`config/operating-point-v3.json`](../config/operating-point-v3.json) dosyasını benimsedi:
yeniden etiketlenmiş geliştirme tablosu (`config/relabel-v1.json` altında kurulan
`artifacts/relabelled_development_20261111_r1`), geliştirme raporlamasının ve gelecek geliştirme protokollerinin
temeli olarak dondurulmuş etiketli `artifacts/v2_development_features_20261025_r2` tablosunun yerini alır; izleme
katmanı (önceki yıl pencere recall 0,90) ve alarm katmanı (önceki yıl precision 0,50, recall tabanı 0,10, geri dönüş
işareti) ile. `config/operating-point-v2.json` yerini bırakmıştır; recall 0,90 kuralı izleme katmanı olarak sürer ve
dondurulmuş etiket sonuçları karşılaştırma için görünür kalır. Bu rapor benimsemeyi ve benimsemenin koşul olarak
koyduğu, yeni iş gerektiren tek maddeyi kayda geçirir: geliştirme hattını yeniden etiketlenmiş tablodan yeniden kuran
ve `artifacts/relabel_walk_forward_20261111_r1` sonucunu yeniden üreten dondurulmuş bir protokol,
[`config/walk-forward-v2.json`](../config/walk-forward-v2.json). Protokol, çalıştırıcı ve durum değişikliği her
sonuçtan önce commit edildi; yeniden kurma, değerlendirilen her yılda (2014, 2015, 2016, 2017, 2022, 2023) yeniden etiketlenmiş walk-forward
sonucunu bit bit yeniden üretti; dolayısıyla `pipeline_reproduced` ve `adoption_effective` true.

Üretimde hiçbir şey değişmedi: `app.py` içindeki panel alarm eşiği, dağıtılan uyarı ve dondurulmuş artefaktlar
dokunulmadan duruyor; ayrılmış 2024–2025 testi okunmadı. Benimseme, geliştirme temelinin ve çalışma noktasının
değişmesidir, performans iyileştirmesi değildir: olasılıklar dondurulmuş hattan yalnızca eğitim etiketleri farklı
olduğu için farklıdır.

## Yeniden kurulan hat nedir

Tarifler `config/walk-forward-v1.json` tarifleridir, değiştirilmemiştir (sabit hiperparametreli ve 24 tohumlu
lojistik regresyon ile XGBoost, önceki takvim yılında sigmoid kalibrasyon, 0,45/0,55 topluluk ağırlıkları, sınır
geçen pencerelerin ve önceki rollerle paylaşılan HARP'lerin arındırıldığı genişleyen eğitim). Kaynak yeniden
etiketlenmiş tablodur (rapor sha256 `2847215ce5a5dedb9ebb93d7fa0ba1bcb7b4a7bf9fdcd80bab95e63726b9ac43`). Çalıştırıcı her değerlendirme yılı için
tarifleri uydurur, önceki yeniden etiketlenmiş kalibrasyon yılında üç eşik seçer, herhangi bir değerlendirme etiketi
okunmadan önce bunları diske yazar ve modelleri, kalibratörleri, eşikleri ve tahminleri
`artifacts/walk_forward_v2_20261112_r1/<year>/` altında saklar. 2018, 2019, 2020, 2021 katları, eğitim veya kalibrasyonda iki
sınıf bulunmadığı ya da yılda değerlendirilebilir pozitif olmadığı için atlanır; bu yıllardaki önceki her
walk-forward çalışmasında da böyleydi.

## Yeniden etiketlenmiş walk-forward sonucunun yeniden üretimi

Yeniden kurulan her yıl, `artifacts/relabel_walk_forward_20261111_r1` içindeki saklı `relabelled_models` koluyla ve
`artifacts/two_tier_relabelled_20261111_r1` ile karşılaştırıldı: aynı değerlendirme pencereleri, bit bit eşit
kalibre topluluk olasılığı (`np.array_equal`), eşit recall 0,95 ve recall 0,90 eşikleri, kalibrasyon recall'ı,
precision'ı ve geri dönüş işaretiyle birlikte eşit alarm eşiği ve her iki katmanda eşit tp, fp, fn, tn, pozitif
koşu ve kaçırılan pozitif koşu sayıları.

| yıl | aynı pencereler | olasılıklar özdeş | maks mutlak Δp | recall eşikleri özdeş | alarm eşiği özdeş | sayımlar özdeş | yeniden üretildi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | evet | evet | 0.0e+00 | evet | evet | evet | evet |
| 2015 | evet | evet | 0.0e+00 | evet | evet | evet | evet |
| 2016 | evet | evet | 0.0e+00 | evet | evet | evet | evet |
| 2017 | evet | evet | 0.0e+00 | evet | evet | evet | evet |
| 2022 | evet | evet | 0.0e+00 | evet | evet | evet | evet |
| 2023 | evet | evet | 0.0e+00 | evet | evet | evet | evet |

## Alarm katmanı (önceki yıl precision 0,50, recall tabanı 0,10)

Yeniden etiketlenmiş satırlar benimsenen hattır; dondurulmuş satırlar dondurulmuş etiket referansı olarak
`artifacts/two_tier_20261110_r1` dosyasından kopyalanmıştır. İki etiket kümesi farklı pencere kümelerinde ölçülür
ve birleştirilmez.

| yıl | etiketler | geri dönüş | tp | fp | recall | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşular |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | hayır | 688 | 320 | 0.2824 | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 66 / 88 |
| 2014 | dondurulmuş | hayır | 644 | 248 | 0.2788 | 0.7220 | [0.4414, 0.8625] | 0.9746 | 0.9693 | 63 / 83 |
| 2015 | yeniden etiketlenmiş | hayır | 545 | 457 | 0.3730 | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 27 / 57 |
| 2015 | dondurulmuş | hayır | 551 | 476 | 0.4066 | 0.5365 | [0.3109, 0.7080] | 0.9815 | 0.9804 | 24 / 51 |
| 2016 | yeniden etiketlenmiş | hayır | 94 | 109 | 0.4393 | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 3 / 8 |
| 2016 | dondurulmuş | hayır | 76 | 112 | 0.4199 | 0.4043 | [0.0000, 0.5249] | 0.9950 | 0.9958 | 2 / 7 |
| 2017 | yeniden etiketlenmiş | hayır | 177 | 27 | 0.6679 | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 3 / 6 |
| 2017 | dondurulmuş | hayır | 182 | 43 | 0.7194 | 0.8089 | [0.0000, 0.9691] | 0.9942 | 0.9870 | 2 / 6 |
| 2022 | yeniden etiketlenmiş | evet | 1056 | 1178 | 0.4822 | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | dondurulmuş | evet | 221 | 1111 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | yeniden etiketlenmiş | hayır | 1587 | 2136 | 0.3879 | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 68 / 159 |
| 2023 | dondurulmuş | hayır | 79 | 106 | 0.1012 | 0.4270 | [0.0968, 0.7441] | 0.9866 | 0.9871 | 30 / 38 |

## İzleme katmanı (önceki yıl recall 0,90)

Dondurulmuş satırlar `artifacts/two_tier_20261110_r1` dosyasından kopyalanmıştır.

| yıl | etiketler | geri dönüş | tp | fp | recall | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşular |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş |  | 2146 | 9020 | 0.8810 | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 6 / 88 |
| 2014 | dondurulmuş |  | 2007 | 7634 | 0.8688 | 0.2082 | [0.1327, 0.2868] | 0.8945 | 0.9693 | 6 / 83 |
| 2015 | yeniden etiketlenmiş |  | 1396 | 8079 | 0.9555 | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 1 / 57 |
| 2015 | dondurulmuş |  | 1308 | 6294 | 0.9653 | 0.1721 | [0.1069, 0.2401] | 0.9083 | 0.9804 | 0 / 51 |
| 2016 | yeniden etiketlenmiş |  | 201 | 1722 | 0.9393 | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 0 / 8 |
| 2016 | dondurulmuş |  | 162 | 1303 | 0.8950 | 0.1106 | [0.0000, 0.2039] | 0.9692 | 0.9958 | 0 / 7 |
| 2017 | yeniden etiketlenmiş |  | 243 | 1058 | 0.9170 | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1 / 6 |
| 2017 | dondurulmuş |  | 235 | 1035 | 0.9289 | 0.1850 | [0.0000, 0.4581] | 0.9461 | 0.9870 | 1 / 6 |
| 2022 | yeniden etiketlenmiş |  | 2024 | 11917 | 0.9242 | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 5 / 72 |
| 2022 | dondurulmuş |  | 414 | 8949 | 0.9834 | 0.0442 | [0.0222, 0.0724] | 0.8235 | 0.9917 | 0 / 16 |
| 2023 | yeniden etiketlenmiş |  | 3695 | 16022 | 0.9032 | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 10 / 159 |
| 2023 | dondurulmuş |  | 653 | 4852 | 0.8361 | 0.1186 | [0.0765, 0.1630] | 0.9175 | 0.9871 | 3 / 38 |

## Karşılaştırma noktası: önceki yıl recall 0,95

`config/operating-point-v2.json` gerektirdiği için görünür tutulur. Dondurulmuş satırlar
`artifacts/walk_forward_20261028_r1` dosyasının `ensemble` satırlarıdır; o çalışma pozitif koşuları ve aralıkları
kaydetmemişti.

| yıl | etiketler | geri dönüş | tp | fp | recall | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşular |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş |  | 2294 | 14074 | 0.9417 | 0.1402 | [0.0965, 0.1918] | 0.8186 | 0.9689 | 3 / 88 |
| 2014 | dondurulmuş |  | 2184 | 13886 | 0.9455 | 0.1359 |  | 0.8137 | 0.9693 |  |
| 2015 | yeniden etiketlenmiş |  | 1430 | 13784 | 0.9788 | 0.0940 | [0.0569, 0.1366] | 0.8042 | 0.9793 | 1 / 57 |
| 2015 | dondurulmuş |  | 1346 | 11453 | 0.9934 | 0.1052 |  | 0.8342 | 0.9804 |  |
| 2016 | yeniden etiketlenmiş |  | 211 | 3257 | 0.9860 | 0.0608 | [0.0000, 0.1182] | 0.9244 | 0.9950 | 0 / 8 |
| 2016 | dondurulmuş |  | 176 | 2289 | 0.9724 | 0.0714 |  | 0.9466 | 0.9958 |  |
| 2017 | yeniden etiketlenmiş |  | 245 | 1349 | 0.9245 | 0.1537 | [0.0000, 0.3707] | 0.9310 | 0.9866 | 1 / 6 |
| 2017 | dondurulmuş |  | 237 | 1287 | 0.9368 | 0.1555 |  | 0.9333 | 0.9870 |  |
| 2022 | yeniden etiketlenmiş |  | 2052 | 13825 | 0.9370 | 0.1292 | [0.0889, 0.1749] | 0.7871 | 0.9666 | 5 / 72 |
| 2022 | dondurulmuş |  | 415 | 10072 | 0.9857 | 0.0396 |  | 0.8014 | 0.9917 |  |
| 2023 | yeniden etiketlenmiş |  | 3939 | 25760 | 0.9628 | 0.1326 | [0.1052, 0.1604] | 0.7328 | 0.9578 | 1 / 159 |
| 2023 | dondurulmuş |  | 691 | 5992 | 0.8848 | 0.1034 |  | 0.8992 | 0.9871 |  |

## Okuma

- `pipeline_reproduced`: değerlendirilen 6 yılın hepsinde true; en büyük mutlak olasılık farkı her
  yerde 0. Benimsenen çalışma noktası böylece yalnızca yeniden etiketlenmiş tablo, dondurulmuş tarifler, protokol
  özeti ve kod özetlerinden yeniden üretilebilen bir hatta dayanır.
- `years_meeting_alert_target`: 2014, 2015, 2017 (6 yılın 3'ü). Alarm katmanı 2022 yılında geri dönüş
  yılıdır (yeniden etiketlenmiş 2021 kalibrasyon yılı, recall tabanında en iyi precision 0,1996). 2022'de recall
  0.4822 ile precision 0.4727 verir (dondurulmuş: 0.5249 ile 0.1659); 2023'te recall 0.3879 ile
  0.4263 (dondurulmuş: 0.1012 ile 0.4270). İki 25. döngü yılı da 0,50'yi 0,08'den az kaçırır ve ikisinde
  de accuracy hep-negatifin altındadır; hedefi tutan yıl sayısı protokolde şart değil, raporlanan bir bilgidir.
- Proje hedefi açısından (precision yukarı, accuracy her yıl hep-negatifin üstünde): alarm katmanı accuracy
  koşulunu yalnızca 2014, 2015 ve 2017'de tutar; izleme katmanı hiçbir yılda tutmaz. Benimseme, etiket kapsamı
  denetiminin 25. döngüde yanlış olduğunu gösterdiği ölçüm temelini taşır; 2022 ve 2023'teki kalan açığı kendi
  başına kapatmaz.

## Sonraki çalışmalar için ne değişir

- Bu tarihten sonra yazılan geliştirme raporları geliştirme temelinin yeniden etiketlenmiş tablo olduğunu ve
  nedenini belirtir, yıl ve katman başına precision'ı teslim edilen recall ve kaçırılan pozitif koşularla birlikte
  verir, alarm geri dönüş yıllarını işaretler ve dondurulmuş etiket sonuçlarını görünür tutar (`AGENTS.md`'ye
  eklenen kural).
- `artifacts/walk_forward_v2_20261112_r1` gelecek geliştirme protokolleri için referans hattır. Dondurulmuş etiket
  artefaktları kanıt olarak olduğu gibi kalır.
- Panel alarm eşiği ve dağıtılan uyarı değişmemiştir; ayrılmış 2024–2025 testiyle ayrı bir karar gerektirir;
  `app.py` olduğu gibi kalır.

## Sınırlar

Daha önce incelenmiş geliştirme yıllarında uyarlamalı betimleme; bağımsız test değil. Yeniden etiketlenmiş
etiketler NOAA SGAS bölge numaraları ve JSOC `NOAA_ARS` ile yapılan bir ilişkilendirmedir, temel gerçek değildir;
atanmamış kalan 133 olay kapalı-güvenli biçimde dışlanmış durumdadır. Sayımlar örtüşen tahmin pencereleri ve
bunların gruplamalarıdır, fiziksel patlamalar değildir. 2016 ve 2017 alarm precision'ı 8 ve 6 pozitif koşuya
dayanır ve aralıkları 0,0000'a ulaşır. Bit bit yeniden üretim aynı makine ve çalışma zamanında
(`runtime-py314-20261101`) elde edildi; başka bir platformda XGBoost histogram uydurmaları son bitlerde farklı
olabilir; bu durumda protokolün özdeşlik denetimleri tasarım gereği başarısız olur ve fark hoş görülmek yerine
raporlanmalıdır.

## Yeniden üretim

```sh
python -m scripts.rebuild_walk_forward_v2 --output artifacts/walk_forward_v2_20261112_r1
python -m pytest -q tests
```

Protokol sha256 `d6e08a575193162afe59e068c568b51dee5e34c3950dcb5b6ed98b817e63d3bb`. `report.json` içinde kayıtlı kod özetleri:

- `scripts/rebuild_walk_forward_v2.py` `59d757bb2fc4d89872dbec265af8f4be25c9c1399490e0973f90313bf9b44605`
- `scripts/audit_two_tier.py` `a2c871ca50dc187e64f2b8fc65d581990e53ec609c05c7408745a7e87b792a57`
- `helio24/two_tier.py` `0b94f907f1f3db4a05d799bb99e02cf9ead571279405e7ac54769868d001d60e`
- `helio24/walk_forward.py` `9c1ed05bc0e4456680faa5d4532303c098e22a86f811db435c78f31d12d43f44`
- `helio24/v2_training.py` `647289a915cf31a7fbd7e09277be0e75dc83292004b8b1b737a46439322c4618`
- `helio24/calibration.py` `0c43ad5027d20d50c233351829c4c13325cc65d140f1fb2bac2a44428b24dc16`

Yeni çıktı dizinleri kullanın; var olan çıktının üzerine yazılmaz.
