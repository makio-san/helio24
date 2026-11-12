# Benimsenen yeniden etiketlenmiş hatta 25. döngü sıralama teşhisi (2026-11-12)

## Karar

Geliştirme temeli: yeniden etiketlenmiş tablo `artifacts/relabelled_development_20261111_r1` ve benimsenen hat
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)); temel 2026-11-12'de değişti, çünkü
dondurulmuş etiketler eşlenen 2022–2023 M/X patlamalarının %30'undan azını kapsıyordu. Bu rapor
[ilk 25. döngü teşhisini](cycle25-diagnostic-20261110.tr.md) bu temelde, her sonuçtan önce dondurulup commit edilen
[`config/cycle25-diagnostic-v2.json`](../config/cycle25-diagnostic-v2.json) altında yineler.

Üç bulgu:

- Etiket düzeltmesi, ilk teşhisin betimlediği 25. döngü açığının büyük bir bölümünü kaldırdı. Walk-forward AP 0.2800 ve
  0.2206 değerlerinden 0.4622 ve 0.3626 değerlerine, en iyi ham özet 0.2089 ve 0.1823 değerlerinden 0.3984 ve
  0.3254 değerlerine, bölge AP 0.7187 ve 0.5951 değerlerinden 0.8315 ve 0.8655 değerlerine yükseldi; bu, 24. döngü
  düzeyidir (2014 ve 2015'te 0.7600 ve 0.8264).
- Dondurulmuş kurala göre ilk teşhisin "bilgi düştü" ifadesi daha zayıf bir biçimde hâlâ geçerlidir: en iyi ham
  özet ve dönem içi uydurma, iki yılda birden en düşük 2014, 2015 ve 2017 değerine ulaşmaz (en iyi özet 0.3895
  tabanına karşı 0.3984 ve 0.3254; dönem içi uydurma 0.4487 tabanına karşı 0.3590 ve 0.3402). R1 geçerli,
  R2 (kayma) yanlış, R3 (zamanlama baskın) hiçbir yılda geçerli değil.
- Alarm katmanında kalan açık bir bölge sorunu değil, patlayan bölgelerin içindeki bir zamanlama sorunudur: 2022
  ve 2023'te alarm FP pencerelerinin yalnızca 0.0823 ve 0.1320 payı yıl içinde pozitif penceresi olmayan
  HARP'lerden gelirken, 0.7139 ve 0.7561 payı aynı HARP'in bir pozitif penceresine 72 saat içindedir. Patlayan
  HARP içi AP 0.4968 ve 0.4057 değerindedir.

25. döngüye duyarlı bir eğitim protokolü bu kanıtla gerekçelendirilemez. Hiçbir model, eşik veya uyarı
değiştirilmedi; `app.py` içindeki panel eşiğine dokunulmadı; ayrılmış 2024–2025 testine erişilmedi.

## Bu temelde çalışma noktası

`artifacts/walk_forward_v2_20261112_r1/metrics.csv` dosyasından kopyalanmıştır; dondurulmuş satırlar o
çalışmanın dondurulmuş etiket referansıdır. İki etiket kümesi farklı pencere kümelerinde ölçülür ve
birleştirilmez. 2022 bir alarm geri dönüş yılıdır.

### Alarm katmanı (önceki yıl precision 0,50, recall tabanı 0,10)

| yıl | etiketler | geri dönüş | recall | precision | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşular |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | hayır | 0.2824 | 0.6825 | 0.9736 | 0.9689 | 66 / 88 |
| 2014 | dondurulmuş | hayır | 0.2788 | 0.7220 | 0.9746 | 0.9693 | 63 / 83 |
| 2015 | yeniden etiketlenmiş | hayır | 0.3730 | 0.5439 | 0.9805 | 0.9793 | 27 / 57 |
| 2015 | dondurulmuş | hayır | 0.4066 | 0.5365 | 0.9815 | 0.9804 | 24 / 51 |
| 2016 | yeniden etiketlenmiş | hayır | 0.4393 | 0.4631 | 0.9947 | 0.9950 | 3 / 8 |
| 2016 | dondurulmuş | hayır | 0.4199 | 0.4043 | 0.9950 | 0.9958 | 2 / 7 |
| 2017 | yeniden etiketlenmiş | hayır | 0.6679 | 0.8676 | 0.9942 | 0.9866 | 3 / 6 |
| 2017 | dondurulmuş | hayır | 0.7194 | 0.8089 | 0.9942 | 0.9870 | 2 / 6 |
| 2022 | yeniden etiketlenmiş | evet | 0.4822 | 0.4727 | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | dondurulmuş | evet | 0.5249 | 0.1659 | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | yeniden etiketlenmiş | hayır | 0.3879 | 0.4263 | 0.9522 | 0.9578 | 68 / 159 |
| 2023 | dondurulmuş | hayır | 0.1012 | 0.4270 | 0.9866 | 0.9871 | 30 / 38 |

### İzleme katmanı (önceki yıl recall 0,90)

| yıl | etiketler | geri dönüş | recall | precision | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşular |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş |  | 0.8810 | 0.1922 | 0.8812 | 0.9689 | 6 / 88 |
| 2014 | dondurulmuş |  | 0.8688 | 0.2082 | 0.8945 | 0.9693 | 6 / 83 |
| 2015 | yeniden etiketlenmiş |  | 0.9555 | 0.1473 | 0.8846 | 0.9793 | 1 / 57 |
| 2015 | dondurulmuş |  | 0.9653 | 0.1721 | 0.9083 | 0.9804 | 0 / 51 |
| 2016 | yeniden etiketlenmiş |  | 0.9393 | 0.1045 | 0.9598 | 0.9950 | 0 / 8 |
| 2016 | dondurulmuş |  | 0.8950 | 0.1106 | 0.9692 | 0.9958 | 0 / 7 |
| 2017 | yeniden etiketlenmiş |  | 0.9170 | 0.1868 | 0.9456 | 0.9866 | 1 / 6 |
| 2017 | dondurulmuş |  | 0.9289 | 0.1850 | 0.9461 | 0.9870 | 1 / 6 |
| 2022 | yeniden etiketlenmiş |  | 0.9242 | 0.1452 | 0.8158 | 0.9666 | 5 / 72 |
| 2022 | dondurulmuş |  | 0.9834 | 0.0442 | 0.8235 | 0.9917 | 0 / 16 |
| 2023 | yeniden etiketlenmiş |  | 0.9032 | 0.1874 | 0.8307 | 0.9578 | 10 / 159 |
| 2023 | dondurulmuş |  | 0.8361 | 0.1186 | 0.9175 | 0.9871 | 3 / 38 |

## Yöntem

Benimsenen yıllık katların saklı `ensemble` olasılıkları; değerlendirme yılı pencereleri yeniden etiketlenmiş
tablonun 96 özetiyle birleştirildi. D1–D4, `config/cycle25-diagnostic-v1.json` ölçüleridir ve
`scripts/audit_cycle25.py` içindeki değiştirilmemiş fonksiyonlarla hesaplanır: bileşim; sıralamanın bir bölge
sorununa (HARP başına en yüksek olasılık, HARP'in herhangi bir pozitif penceresi olup olmadığına karşı) ve bir
zamanlama sorununa (yalnızca patlayan HARP'lerin içinde pencere sıralaması) ayrıştırılması, her yılın saklı izleme
eşiğinde hiç patlamayan HARP kaynaklı FP payıyla birlikte; her ham özetin ve negatifinin AP'si; ve değiştirilmemiş
walk-forward-v1 tariflerinin her dönem içinde HARP gruplu 5 katlı uydurması, ham olasılıklar 0,45/0,55
birleştirilir, 20 uydurma, hiçbir zaman dağıtılamayan bir tavan. D5 yenidir ve protokolle birlikte donduruldu: her
yılın saklı alarm eşiğinde, hiç patlamayan HARP kaynaklı FP pencerelerinin payı ve aynı HARP'in bir pozitif
penceresine 72 saat içindeki payı. Dondurulmuş etiket satırları `artifacts/cycle25_diagnostic_20261110_r1`
dosyasından değiştirilmeden kopyalanmıştır; dondurulmuş etiketlerde hiçbir şey yeniden hesaplanmadı. Referans
kapasite medyanı (24. döngü pozitif pencereleri, `USFLUX__last`) 3.54e+22 değerindedir.

## D1 Bileşim

| yıl | etiketler | pencereler | HARP | patlayan HARP | pozitif pencereler | pozitif koşular | pozitif payı | patlayan HARP başına medyan pencere | medyan USFLUX__last pozitif | medyan USFLUX__last tümü | 24. döngü medyanının altındaki pozitif payı | ortalama missing_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | 78351 | 637 | 45 | 2436 | 88 | 0.0311 | 276.0 | 4.23e+22 | 2.77e+21 | 0.4257 | 0.0141 |
| 2014 | dondurulmuş | 75228 | 629 | 44 | 2310 | 83 | 0.0307 | 260.0 | 4.34e+22 | 2.80e+21 | 0.4281 | 0.0139 |
| 2015 | yeniden etiketlenmiş | 70554 | 600 | 28 | 1461 | 57 | 0.0207 | 275.5 | 3.09e+22 | 1.83e+21 | 0.5941 | 0.0140 |
| 2015 | dondurulmuş | 69138 | 599 | 24 | 1355 | 51 | 0.0196 | 274.5 | 3.18e+22 | 1.84e+21 | 0.5934 | 0.0138 |
| 2016 | yeniden etiketlenmiş | 43142 | 357 | 4 | 214 | 8 | 0.0050 | 301.5 | 3.77e+22 | 1.64e+21 | 0.4346 | 0.0155 |
| 2016 | dondurulmuş | 42987 | 357 | 4 | 181 | 7 | 0.0042 | 285.0 | 3.77e+22 | 1.63e+21 | 0.4641 | 0.0155 |
| 2017 | yeniden etiketlenmiş | 19843 | 163 | 3 | 265 | 6 | 0.0134 | 253.0 | 3.67e+22 | 2.28e+21 | 0.4566 | 0.0163 |
| 2017 | dondurulmuş | 19529 | 163 | 3 | 253 | 6 | 0.0130 | 253.0 | 3.79e+22 | 2.24e+21 | 0.4466 | 0.0156 |
| 2022 | yeniden etiketlenmiş | 65593 | 544 | 39 | 2190 | 72 | 0.0334 | 282.0 | 3.09e+22 | 3.05e+21 | 0.5475 | 0.0168 |
| 2022 | dondurulmuş | 50756 | 528 | 12 | 421 | 16 | 0.0083 | 193.0 | 3.86e+22 | 3.02e+21 | 0.4466 | 0.0167 |
| 2023 | yeniden etiketlenmiş | 96991 | 751 | 73 | 4091 | 159 | 0.0422 | 283.0 | 3.31e+22 | 2.82e+21 | 0.5363 | 0.0160 |
| 2023 | dondurulmuş | 60366 | 703 | 27 | 781 | 38 | 0.0129 | 134.0 | 3.38e+22 | 2.53e+21 | 0.5493 | 0.0148 |

## D2 Sıralamanın ayrıştırılması

| yıl | etiketler | genel AP | bölge AP | patlayan HARP içi AP | izleme eşiğinde FP pencereleri | hiç patlamayan HARP kaynaklı FP payı |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | 0.5015 | 0.7600 | 0.5528 | 9020 | 0.4425 |
| 2014 | dondurulmuş | 0.5079 | 0.7618 | 0.5609 | 7634 | 0.4353 |
| 2015 | yeniden etiketlenmiş | 0.4823 | 0.8264 | 0.5331 | 8079 | 0.5368 |
| 2015 | dondurulmuş | 0.4924 | 0.8266 | 0.5469 | 6294 | 0.5261 |
| 2016 | yeniden etiketlenmiş | 0.4060 | 0.6333 | 0.4853 | 1722 | 0.6533 |
| 2016 | dondurulmuş | 0.3664 | 0.4958 | 0.4371 | 1303 | 0.6078 |
| 2017 | yeniden etiketlenmiş | 0.7975 | 1.0000 | 0.8727 | 1058 | 0.7410 |
| 2017 | dondurulmuş | 0.8117 | 1.0000 | 0.8821 | 1035 | 0.7459 |
| 2022 | yeniden etiketlenmiş | 0.4622 | 0.8315 | 0.4968 | 11917 | 0.4922 |
| 2022 | dondurulmuş | 0.2800 | 0.7187 | 0.3860 | 8949 | 0.8301 |
| 2023 | yeniden etiketlenmiş | 0.3626 | 0.8655 | 0.4057 | 16022 | 0.3722 |
| 2023 | dondurulmuş | 0.2206 | 0.5951 | 0.4024 | 4852 | 0.7422 |

## D3 ve D4 Tavanlar

| yıl | etiketler | walk-forward AP | en iyi ham özet | en iyi ham özet AP | USFLUX__last AP | dönem içi uydurma AP | dönem içi eksi walk-forward |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | 0.5015 | `TOTUSJH__mean` | 0.4850 | 0.4306 | 0.4576 | -0.0440 |
| 2014 | dondurulmuş | 0.5079 | `TOTUSJH__mean` | 0.4900 | 0.4362 | 0.4270 | -0.0810 |
| 2015 | yeniden etiketlenmiş | 0.4823 | `R_VALUE__mean` | 0.3895 | 0.2093 | 0.4487 | -0.0336 |
| 2015 | dondurulmuş | 0.4924 | `R_VALUE__mean` | 0.3960 | 0.2181 | 0.4569 | -0.0355 |
| 2016 | yeniden etiketlenmiş | 0.4060 | `TOTFX__mean` | 0.4428 | 0.1506 | 0.2801 | -0.1259 |
| 2016 | dondurulmuş | 0.3664 | `TOTFX__mean` | 0.4637 | 0.1407 | 0.2376 | -0.1289 |
| 2017 | yeniden etiketlenmiş | 0.7975 | `ABSNJZH__std` | 0.7092 | 0.5192 | 0.7878 | -0.0098 |
| 2017 | dondurulmuş | 0.8117 | `TOTUSJH__mean` | 0.7216 | 0.5602 | 0.8011 | -0.0106 |
| 2022 | yeniden etiketlenmiş | 0.4622 | `ABSNJZH__std` | 0.3984 | 0.2808 | 0.3590 | -0.1032 |
| 2022 | dondurulmuş | 0.2800 | `ABSNJZH__last` | 0.2089 | 0.1390 | 0.1877 | -0.0924 |
| 2023 | yeniden etiketlenmiş | 0.3626 | `ABSNJZH__std` | 0.3254 | 0.2326 | 0.3402 | -0.0224 |
| 2023 | dondurulmuş | 0.2206 | `ABSNJZH__std` | 0.1823 | 0.0825 | 0.2190 | -0.0016 |

## D5 Alarm katmanı yanlış pozitiflerinin kaynağı (yeniden etiketlenmiş)

| yıl | alarm geri dönüş | alarm pencereleri | alarm FP pencereleri | hiç patlamayan HARP kaynaklı FP payı | aynı HARP'in pozitif penceresine 72 saat içindeki FP payı |
| --- | --- | --- | --- | --- | --- |
| 2014 | hayır | 1008 | 320 | 0.1437 | 0.7063 |
| 2015 | hayır | 1002 | 457 | 0.0853 | 0.8249 |
| 2016 | hayır | 203 | 109 | 0.2569 | 0.5688 |
| 2017 | hayır | 204 | 27 | 0.1111 | 0.8889 |
| 2022 | evet | 2234 | 1178 | 0.0823 | 0.7139 |
| 2023 | hayır | 3723 | 2136 | 0.1320 | 0.7561 |

## Okuma

- R1 (`R1_information_fell`): doğru. Dönem içi uydurma walk-forward AP'ye göre -0.1032 (2022) ve -0.0224
  (2023) değerindedir; iki yılda da 0,10 sınırının altındadır. R2 (`R2_drift`): yanlış. 25. döngüyü geride tutan
  şey önceki yıllarla eğitim değildir; walk-forward modeli 2022 ve 2023'ü, dönemin kendisini gören bir uydurma
  kadar iyi ya da daha iyi sıralar.
- R3: hiçbir yılda bölge AP en az 0,50 iken patlayan HARP içi AP 0,30'un altında değildir. Dondurulmuş sınır
  karşılanmaz, ancak 25. döngüde yön açıktır: 0.4968 ve 0.4057 patlayan HARP içi AP'ye karşı 0.8315 ve
  0.8655 bölge AP.
- Etiket etkisi: `first_diagnostic_information_statement` değeri `stands`. 2022'de en iyi ham özet (0.3984)
  24. döngü tabanına (0.3895) ulaşır; 2023 (0.3254) ulaşmaz ve dönem içi uydurma iki yılda da ulaşmaz.
  2026-11-10'da betimlenen açık etiket düzeltmesiyle kabaca yarıya indi, ortadan kalkmadı.
- Bileşim etiketlerle değişti: 2022 ve 2023'te patlayan HARP sayısı 12 ve 27 değerlerinden 39 ve 73
  değerlerine, pozitif koşular 16 ve 38 değerlerinden 72 ve 159 değerlerine yükseldi; izleme katmanında hiç
  patlamayan HARP kaynaklı FP payı 0.8301 ve 0.7422 değerlerinden 0.4922 ve 0.3722 değerlerine düştü. İlk teşhisin
  "patlamaya yetenekli görünen ve patlamayan" bölgelerinin çoğu, patlamaları iliştirilmemiş patlayan bölgelerdi.
- D5: her yılda alarm FP pencerelerinin yarısından fazlası (0,57 ile 0,89 arası) patlayan HARP'lerde, bir pozitif
  pencereye 72 saat içinde durur. Alarm katmanı doğru bölgelerde alarm verir ve doğru günü kaçırır.

## Proje hedefi için anlamı

- Alarm katmanının eksiği, hangi bölgenin patlayacağına dair daha fazla veri değildir; özetler 25. döngüde
  bölgeleri zaten bulur. Yeni bir veri kaynağı, ancak patlayan bir bölgenin ne zaman patlayacağına dair bilgi
  taşıyorsa maliyetine değer.
- Bir sonraki aday yön, aktif bölge içindeki zamanlama bilgisidir; örneğin bölgenin projenin zaten elinde olan
  GOES olay listesinden kendi yakın patlama geçmişi ya da özetlerin önceki günlerdeki değişimi. Bu, uydurma
  bütçesi ve kabul kuralı olan kendi dondurulmuş protokolünü gerektirir; burada bir öneridir, sonuç değildir.
- Alarm FP pencerelerinin bir pozitif pencereye 72 saat içindeki payı, katı 24 saatlik pencere etiketinin zaman
  olarak yakın alarmları tümüyle yanlış saydığı anlamına da gelir. Bu, hedefin bir özelliğidir ve burada olduğu
  gibi raporlanır; hedef değiştirilmemiştir.

## Sınırlar

Daha önce incelenmiş yıllar: uyarlamalı geliştirme betimlemesi, bağımsız test değil. Sayımlar örtüşen tahmin
pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir. Yeniden etiketlenmiş etiketler NOAA SGAS
bölge numaraları ve JSOC `NOAA_ARS` ile yapılan bir ilişkilendirmedir, temel gerçek değildir; atanmamış 133 olay
kapalı-güvenli biçimde dışlanmış durumdadır. Dönem içi tavan 25. döngünün iki yılını (6281 pozitif pencere)
kullanır ve kendisi küçük örneklemli bir tahmindir. Tek özellik AP'si uydurma içermeyen ham bir sıralamadır. D5
betimleyicidir, protokolde sınırı ve okuması yoktur; 72 saatlik aralığı sonuçlardan önce yapılmış sabit bir
seçimdir. Betiğin ilk çalıştırması, herhangi bir sonuç yazmadan önce D5'teki bir zaman damgası tür hatasında durdu;
boş çıktı dizini kaldırıldı, düzeltme commit edildi ve çalıştırma yinelendi. Teşhis 96 özeti sınırlar,
25. döngüye dair başka verileri değil.

## Yeniden üretim

```sh
python -m scripts.audit_cycle25_relabelled --output artifacts/cycle25_diagnostic_relabelled_20261112_r1
python -m pytest -q tests
```

Config sha256 `01a91bff4b899316d31c700194ab736fa2dda25e865eed5d0356e063dd63d89f`. Yeni çıktı dizinleri kullanın; var olan çıktının üzerine yazılmaz.
