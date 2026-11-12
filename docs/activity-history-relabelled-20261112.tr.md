# Benimsenen hattın alarm katmanında SGAS patlama geçmişi (2026-11-12)

## Karar

Geliştirme temeli: yeniden etiketlenmiş tablo `artifacts/relabelled_development_20261111_r1` ve benimsenen hat
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)); temel 2026-11-12 tarihinde değişti, çünkü
dondurulmuş etiketler eşlenmiş 2022–2023 M/X patlamalarının %30'undan azını kapsıyordu.

Negatif sonuç, okuma `R3_no_gain`. Nedensel SGAS patlama geçmişi özelliklerini 96 manyetik özete eklemek, benimsenen
temelde alarm katmanı precision değerini yükseltmiyor. `history` yıllık birincil kabul ölçütünü 6 yılın
1'inde (2023), `flag` 6 yılın 2'sinde (2015, 2017) karşılıyor; hiçbiri 2022 ve 2023'ün ikisinde birden karşılamıyor.
Alarm precision değeri en az 0.50 olan yıl sayısı her aday için 3 olarak kalıyor (2014, 2015, 2017). `history` ile alarm
accuracy değeri 2016, 2022, 2023 yıllarında hep-negatif accuracy değerinin altında.

- 2022 (tüm adaylar için alarm yedek kural yılı): `history` precision değerini 0.4727 değerinden 0.3894 değerine
  düşürüyor; pencere recall değeri 0.4822 değerinden 0.5836 değerine çıkıyor ve kaçırılan pozitif koşu
  72 içinde 32 iken 22 oluyor. Precision farkının eşli aralığı sıfırın altında
  (-0.1453 ile -0.0331 arası).
- 2023: `history` precision değerini 0.4263 değerinden 0.4352 değerine çıkarıyor; recall 0.3879 değerinden
  0.4163 değerine, kaçırılan pozitif koşu 159 içinde 68 iken 67 oluyor; eşli aralık
  sıfırı içeriyor (-0.0210 ile 0.0396 arası) ve precision 0.50'nin altında kalıyor.
- 2017: `history` precision değerini 0.8676 değerinden 0.6606 değerine düşürüyor.

Hiçbir model terfi ettirilmedi; hiçbir alarm, eşik veya pano ayarı değiştirilmedi; ayrılmış 2024–2025 testine
erişilmedi. Protokol [`config/activity-history-v2.json`](../config/activity-history-v2.json) herhangi bir aday sonucundan
önce donduruldu, commit edildi ve push edildi.

## Neden tekrarlandı

[Yeniden etiketlenmiş 25. döngü teşhisi](cycle25-diagnostic-relabelled-20261112.tr.md), 2022 ve 2023'te alarm FP
pencerelerinin 0.7139 ve 0.7561'inin aynı HARP'ın pozitif bir penceresine 72 saat içinde olduğunu buldu: alarm katmanı
bölgeleri buluyor, günü kaçırıyor. Bir bölgenin kendi yakın geçmişteki patlamaları zamanlama bilgisidir. Bu
özelliklerin [ilk testi](activity-history-20261109.tr.md) dondurulmuş etiketlerle yapılmış ve izleme katmanında
(pencere recall 0.90) değerlendirilmişti. Bu rapor testi değişmeyen özellikler, erişilebilirlik kuralı ve kodla
benimsenen temelde tekrarlıyor ve alarm katmanında değerlendiriyor.

## Yöntem

Adaylar: `control`, benimsenen hattın kayıtlı ensemble olasılıkları ve kayıtlı eşikleridir; yeniden eğitilmez. `flag`,
değişmeyen tarifleri 96 özet artı `history_available`, `reports_3d`, `hours_since_issue` ile yeniden eğitir. `history`,
[`config/activity-history-v1.json`](../config/activity-history-v1.json) içindeki on beş özelliğin tümünü kullanır. Tahmin
zamanı t olan bir pencere yalnızca t eksi 30 dakika veya öncesinde yayımlanmış SGAS ürünlerini kullanır; bölgesel
olaylar, NOAA numarası tahmin tarihinde HARP'ın `NOAA_ARS` alanında bulunan olaylardır. Genişleyen eğitim, önceki yılda
sigmoid kalibrasyon, ensemble ağırlığı 0.45/0.55, hiperparametre araması yok, 24 bileşen eğitimi. Yıllık
popülasyonlar benimsenen hattınkilerle aynıdır. İzleme eşikleri (önceki yıl pencere recall 0.90) ve alarm eşikleri (önceki
yıl precision 0.50, recall tabanı 0.10, yedek kural işareti) kalibrasyon yılı olasılıklarında seçildi, değerlendirme
etiketleri okunmadan önce yazıldı ve özetlendi.

Alarm katmanında `control` adayına karşı yıllık birincil kabul ölçütü: precision daha yüksek, kaçırılan pozitif koşu
daha fazla değil, pencere recall düşüşü en çok 0.02. Sayılar örtüşen tahmin pencereleridir; pozitif koşu, bir HARP'ın
bitişik pozitif pencereler grubudur.

Değerlendirme yılı kapsamı:

| yıl | değerlendirme penceresi | history_available payı | reg_mx_3d > 0 payı |
| --- | --- | --- | --- |
| 2014 | 78351 | 0.5226 | 0.0454 |
| 2015 | 70554 | 0.5460 | 0.0399 |
| 2016 | 43142 | 0.5515 | 0.0068 |
| 2017 | 19843 | 0.6073 | 0.0201 |
| 2022 | 65593 | 0.6169 | 0.0590 |
| 2023 | 96991 | 0.5664 | 0.0905 |

## Alarm katmanı

| yıl | aday | yedek kural | TP | FP | FN | recall | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | kaçırılan pozitif koşu | birincil ölçüt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 688 | 320 | 1748 | 0.2824 | 0.6825 | 0.4308–0.8477 | 0.9736 | 0.9689 | 66/88 |  |
| 2014 | `flag` | hayır | 670 | 301 | 1766 | 0.2750 | 0.6900 | 0.4219–0.8502 | 0.9736 | 0.9689 | 68/88 | hayır |
| 2014 | `history` | hayır | 708 | 296 | 1728 | 0.2906 | 0.7052 | 0.4628–0.8478 | 0.9742 | 0.9689 | 67/88 | hayır |
| 2015 | `control` | hayır | 545 | 457 | 916 | 0.3730 | 0.5439 | 0.3286–0.7166 | 0.9805 | 0.9793 | 27/57 |  |
| 2015 | `flag` | hayır | 558 | 466 | 903 | 0.3819 | 0.5449 | 0.3340–0.7163 | 0.9806 | 0.9793 | 27/57 | evet |
| 2015 | `history` | hayır | 485 | 388 | 976 | 0.3320 | 0.5556 | 0.3463–0.7216 | 0.9807 | 0.9793 | 28/57 | hayır |
| 2016 | `control` | hayır | 94 | 109 | 120 | 0.4393 | 0.4631 | 0.0000–0.6230 | 0.9947 | 0.9950 | 3/8 |  |
| 2016 | `flag` | hayır | 94 | 109 | 120 | 0.4393 | 0.4631 | 0.0000–0.6253 | 0.9947 | 0.9950 | 3/8 | hayır |
| 2016 | `history` | hayır | 64 | 71 | 150 | 0.2991 | 0.4741 | 0.0000–0.6667 | 0.9949 | 0.9950 | 4/8 | hayır |
| 2017 | `control` | hayır | 177 | 27 | 88 | 0.6679 | 0.8676 | 0.0000–1.0000 | 0.9942 | 0.9866 | 3/6 |  |
| 2017 | `flag` | hayır | 176 | 25 | 89 | 0.6642 | 0.8756 | 0.0000–1.0000 | 0.9943 | 0.9866 | 3/6 | evet |
| 2017 | `history` | hayır | 181 | 93 | 84 | 0.6830 | 0.6606 | 0.0000–0.9325 | 0.9911 | 0.9866 | 3/6 | hayır |
| 2022 | `control` | evet | 1056 | 1178 | 1134 | 0.4822 | 0.4727 | 0.3482–0.6021 | 0.9648 | 0.9666 | 32/72 |  |
| 2022 | `flag` | evet | 1064 | 1207 | 1126 | 0.4858 | 0.4685 | 0.3458–0.5997 | 0.9644 | 0.9666 | 31/72 | hayır |
| 2022 | `history` | evet | 1278 | 2004 | 912 | 0.5836 | 0.3894 | 0.2893–0.4982 | 0.9555 | 0.9666 | 22/72 | hayır |
| 2023 | `control` | hayır | 1587 | 2136 | 2504 | 0.3879 | 0.4263 | 0.3483–0.5053 | 0.9522 | 0.9578 | 68/159 |  |
| 2023 | `flag` | hayır | 1605 | 2188 | 2486 | 0.3923 | 0.4231 | 0.3448–0.5019 | 0.9518 | 0.9578 | 67/159 | hayır |
| 2023 | `history` | hayır | 1703 | 2210 | 2388 | 0.4163 | 0.4352 | 0.3583–0.5207 | 0.9526 | 0.9578 | 67/159 | evet |

Yedek kural yılları (2022), kalibrasyon yılında hiçbir eşiğin en az 0.10 recall ile 0.50 precision değerine
ulaşmadığı yıllardır; kural bu durumda erişilebilen en iyi kalibrasyon precision değerini alır. Precision aralıkları her
adayın HARP kümeli bootstrap aralıklarıdır.

Kabul ölçütleri:

| yıl | aday | precision daha yüksek | kaçırılan koşu fazla değil | recall düşüşü en çok 0.02 | birincil ölçüt |
| --- | --- | --- | --- | --- | --- |
| 2014 | `flag` | evet | hayır | evet | hayır |
| 2014 | `history` | evet | hayır | evet | hayır |
| 2015 | `flag` | evet | evet | evet | evet |
| 2015 | `history` | evet | hayır | hayır | hayır |
| 2016 | `flag` | hayır | evet | evet | hayır |
| 2016 | `history` | evet | hayır | hayır | hayır |
| 2017 | `flag` | evet | evet | evet | evet |
| 2017 | `history` | hayır | evet | evet | hayır |
| 2022 | `flag` | hayır | evet | evet | hayır |
| 2022 | `history` | hayır | evet | evet | hayır |
| 2023 | `flag` | hayır | evet | evet | hayır |
| 2023 | `history` | evet | evet | evet | evet |

Seçilen alarm eşikleri:

| yıl | aday | alarm eşiği | kalibrasyon recall | kalibrasyon precision | yedek kural |
| --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.4627 | 0.1326 | 0.5000 | hayır |
| 2014 | `flag` | 0.4640 | 0.1313 | 0.5000 | hayır |
| 2014 | `history` | 0.4278 | 0.1560 | 0.5000 | hayır |
| 2015 | `control` | 0.2631 | 0.4906 | 0.5000 | hayır |
| 2015 | `flag` | 0.2636 | 0.4873 | 0.5000 | hayır |
| 2015 | `history` | 0.2627 | 0.4819 | 0.5000 | hayır |
| 2016 | `control` | 0.2564 | 0.4969 | 0.5000 | hayır |
| 2016 | `flag` | 0.2583 | 0.4887 | 0.5000 | hayır |
| 2016 | `history` | 0.2918 | 0.4052 | 0.5000 | hayır |
| 2017 | `control` | 0.4145 | 0.2196 | 0.5000 | hayır |
| 2017 | `flag` | 0.4292 | 0.1963 | 0.5000 | hayır |
| 2017 | `history` | 0.3538 | 0.2991 | 0.5000 | hayır |
| 2022 | `control` | 0.1570 | 0.2361 | 0.1996 | evet |
| 2022 | `flag` | 0.1543 | 0.2414 | 0.1974 | evet |
| 2022 | `history` | 0.1622 | 0.2281 | 0.2155 | evet |
| 2023 | `control` | 0.2689 | 0.4461 | 0.5000 | hayır |
| 2023 | `flag` | 0.2661 | 0.4511 | 0.5000 | hayır |
| 2023 | `history` | 0.2999 | 0.3767 | 0.5000 | hayır |

## Betimleyici ölçüler

`kontrol recall değerinde precision`, adayın değerlendirme yılında kontrolün alarm recall değerini veren eşikteki
precision değeridir. Değerlendirme etiketlerini kullanır, devreye alınamaz ve kabul ölçütünün parçası değildir. Precision
farkı aday eksi kontroldür; eşli HARP kümeli bootstrap, 1000 çekim, seed 24. AP ve FP kaynağı payları 25. döngü
teşhisindeki tanımları izler.

| yıl | aday | AP | patlayan HARP içi AP | bölge AP | kontrol recall değerinde precision | precision farkı %95 aralığı | FP payı: hiç patlamayan HARP | FP payı: pozitife 72 saat içinde |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.5015 | 0.5528 | 0.7600 | 0.6825 |  | 0.1437 | 0.7063 |
| 2014 | `flag` | 0.5029 | 0.5529 | 0.7602 | 0.6805 | -0.0092 / 0.0227 | 0.1229 | 0.7243 |
| 2014 | `history` | 0.5136 | 0.5576 | 0.7959 | 0.7159 | -0.0616 / 0.1081 | 0.1047 | 0.7939 |
| 2015 | `control` | 0.4823 | 0.5331 | 0.8264 | 0.5439 |  | 0.0853 | 0.8249 |
| 2015 | `flag` | 0.4833 | 0.5338 | 0.8330 | 0.5488 | -0.0063 / 0.0108 | 0.0794 | 0.8326 |
| 2015 | `history` | 0.4487 | 0.4945 | 0.8593 | 0.5018 | -0.0306 / 0.0645 | 0.0438 | 0.8660 |
| 2016 | `control` | 0.4060 | 0.4853 | 0.6333 | 0.4631 |  | 0.2569 | 0.5688 |
| 2016 | `flag` | 0.4124 | 0.4901 | 0.7125 | 0.4653 | -0.0115 / 0.0256 | 0.2385 | 0.5688 |
| 2016 | `history` | 0.4430 | 0.4976 | 0.7589 | 0.4541 | -0.3060 / 0.1235 | 0.0423 | 0.7606 |
| 2017 | `control` | 0.7975 | 0.8727 | 1.0000 | 0.8676 |  | 0.1111 | 0.8889 |
| 2017 | `flag` | 0.8005 | 0.8746 | 1.0000 | 0.8762 | -0.0045 / 0.0233 | 0.1200 | 0.8800 |
| 2017 | `history` | 0.7571 | 0.8459 | 0.8333 | 0.8592 | -0.4631 / 0.0000 | 0.6344 | 0.3656 |
| 2022 | `control` | 0.4622 | 0.4968 | 0.8315 | 0.4727 |  | 0.0823 | 0.7139 |
| 2022 | `flag` | 0.4599 | 0.4946 | 0.8319 | 0.4725 | -0.0102 / -0.0003 | 0.0845 | 0.7017 |
| 2022 | `history` | 0.4692 | 0.4975 | 0.8628 | 0.4638 | -0.1453 / -0.0331 | 0.1108 | 0.6607 |
| 2023 | `control` | 0.3626 | 0.4057 | 0.8655 | 0.4263 |  | 0.1320 | 0.7561 |
| 2023 | `flag` | 0.3638 | 0.4069 | 0.8668 | 0.4248 | -0.0068 / 0.0003 | 0.1316 | 0.7550 |
| 2023 | `history` | 0.3737 | 0.4142 | 0.8779 | 0.4486 | -0.0210 / 0.0396 | 0.1285 | 0.7719 |

- `history` alarm precision değeri 2014, 2015, 2016, 2023 yıllarında kontrolün üstünde, 2017, 2022 yıllarında altında. Hiçbir eşli aralık
  sıfırın üstünde değil.
- `history` ile AP 2014, 2016, 2022, 2023 yıllarında kontrolün üstünde, 2015, 2017 yıllarında altında.
- Kontrolün verdiği recall değerinde `history` precision değeri 2014, 2023 yıllarında kontrolün üstünde,
  2015, 2016, 2017, 2022 yıllarında altında. Dolayısıyla 2022 kaybı yalnızca bir eşik kayması değil: eşit recall değerinde precision
  0.4727 değerine karşı 0.4638.
- `flag` kontrolden az ayrılıyor (alarm precision değerindeki en büyük mutlak değişim
  0.0080); 2015, 2017 yıllarındaki geçişleri içeriğe atfedilmez.
- `history` ile alarm FP pencerelerinin 72 saatlik yakın-ıska payı 2022'de 0.6607, 2023'te
  0.7719 (kontrol 0.7139 ve 0.7561): zamanlama sorunu çözülmüyor.

## İzleme katmanı

| yıl | aday | TP | FP | FN | recall | precision | accuracy | hep-negatif accuracy | kaçırılan pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 2146 | 9020 | 290 | 0.8810 | 0.1922 | 0.8812 | 0.9689 | 6/88 |
| 2014 | `flag` | 2136 | 8911 | 300 | 0.8768 | 0.1934 | 0.8824 | 0.9689 | 6/88 |
| 2014 | `history` | 2191 | 10033 | 245 | 0.8994 | 0.1792 | 0.8688 | 0.9689 | 5/88 |
| 2015 | `control` | 1396 | 8079 | 65 | 0.9555 | 0.1473 | 0.8846 | 0.9793 | 1/57 |
| 2015 | `flag` | 1396 | 7998 | 65 | 0.9555 | 0.1486 | 0.8857 | 0.9793 | 1/57 |
| 2015 | `history` | 1378 | 7551 | 83 | 0.9432 | 0.1543 | 0.8918 | 0.9793 | 1/57 |
| 2016 | `control` | 201 | 1722 | 13 | 0.9393 | 0.1045 | 0.9598 | 0.9950 | 0/8 |
| 2016 | `flag` | 201 | 1742 | 13 | 0.9393 | 0.1034 | 0.9593 | 0.9950 | 0/8 |
| 2016 | `history` | 195 | 1276 | 19 | 0.9112 | 0.1326 | 0.9700 | 0.9950 | 0/8 |
| 2017 | `control` | 243 | 1058 | 22 | 0.9170 | 0.1868 | 0.9456 | 0.9866 | 1/6 |
| 2017 | `flag` | 243 | 1055 | 22 | 0.9170 | 0.1872 | 0.9457 | 0.9866 | 1/6 |
| 2017 | `history` | 244 | 1059 | 21 | 0.9208 | 0.1873 | 0.9456 | 0.9866 | 1/6 |
| 2022 | `control` | 2024 | 11917 | 166 | 0.9242 | 0.1452 | 0.8158 | 0.9666 | 5/72 |
| 2022 | `flag` | 2025 | 11890 | 165 | 0.9247 | 0.1455 | 0.8162 | 0.9666 | 5/72 |
| 2022 | `history` | 2065 | 14935 | 125 | 0.9429 | 0.1215 | 0.7704 | 0.9666 | 4/72 |
| 2023 | `control` | 3695 | 16022 | 396 | 0.9032 | 0.1874 | 0.8307 | 0.9578 | 10/159 |
| 2023 | `flag` | 3697 | 16118 | 394 | 0.9037 | 0.1866 | 0.8298 | 0.9578 | 10/159 |
| 2023 | `history` | 3770 | 17668 | 321 | 0.9215 | 0.1759 | 0.8145 | 0.9578 | 7/159 |

İzleme katmanı accuracy değeri her aday için her yıl hep-negatif accuracy değerinin altında.

## Dondurulmuş etiket sonuçları

`artifacts/activity_history_20261109_r1` dizininden kopyalandı, yeniden hesaplanmadı: dondurulmuş etiketlerle, önceki yıl
pencere recall 0.90 eşiğinde, `config/activity-history-v1.json` kabul ölçütüyle yapılan ilk test.

| yıl | aday | TP | FP | recall | precision | AP | birincil ölçüt (v1 kuralı) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 2007 | 7634 | 0.8688 | 0.2082 | 0.5079 |  |
| 2014 | `flag` | 1988 | 7411 | 0.8606 | 0.2115 | 0.5089 | hayır |
| 2014 | `history` | 2042 | 8134 | 0.8840 | 0.2007 | 0.5176 | hayır |
| 2015 | `control` | 1308 | 6294 | 0.9653 | 0.1721 | 0.4924 |  |
| 2015 | `flag` | 1319 | 6536 | 0.9734 | 0.1679 | 0.4937 | hayır |
| 2015 | `history` | 1296 | 6423 | 0.9565 | 0.1679 | 0.4725 | hayır |
| 2016 | `control` | 162 | 1303 | 0.8950 | 0.1106 | 0.3664 |  |
| 2016 | `flag` | 162 | 1313 | 0.8950 | 0.1098 | 0.3612 | hayır |
| 2016 | `history` | 158 | 942 | 0.8729 | 0.1436 | 0.4356 | hayır |
| 2017 | `control` | 235 | 1035 | 0.9289 | 0.1850 | 0.8117 |  |
| 2017 | `flag` | 235 | 1015 | 0.9289 | 0.1880 | 0.8135 | hayır |
| 2017 | `history` | 234 | 1123 | 0.9249 | 0.1724 | 0.7735 | hayır |
| 2022 | `control` | 414 | 8949 | 0.9834 | 0.0442 | 0.2800 |  |
| 2022 | `flag` | 414 | 8996 | 0.9834 | 0.0440 | 0.2808 | hayır |
| 2022 | `history` | 416 | 12238 | 0.9881 | 0.0329 | 0.3094 | hayır |
| 2023 | `control` | 653 | 4852 | 0.8361 | 0.1186 | 0.2206 |  |
| 2023 | `flag` | 653 | 4818 | 0.8361 | 0.1194 | 0.2209 | evet |
| 2023 | `history` | 719 | 6343 | 0.9206 | 0.1018 | 0.2342 | hayır |

Sonuç iki temelde de negatif.

## Sınırlar

Daha önce incelenmiş yıllar: uyarlamalı geliştirme kanıtı, bağımsız test değil. Sayılar örtüşen tahmin pencereleri ve
bunların gruplarıdır, fiziksel patlamalar değil. SGAS enerjik olayları listeler, her C sınıfı patlamayı değil; arşivlenmiş
metin ilk yayımlanan baytlardan farklı olabilir. `NOAA_ARS` kesinleşmiş JSOC eşlemesidir ve sonradan sabitlenmiştir.
Yeniden etiketlenmiş etiketler aynı SGAS ürünleri ve `NOAA_ARS` eşlemesiyle elde edildi; özellikler yalnızca tahmin
zamanından önce yayımlanmış ürünlerdeki olayları, etiketler ise sonraki tepe zamanlarını kullandığı için zamanda
örtüşmezler, ancak kaynağın bölge atama hatalarını paylaşırlar. Bölgesel geçmiş, değerlendirme pencerelerinin yaklaşık
%52–62'sinde mevcut. 2022 alarm eşiği her aday için yedek kural eşiğidir. 2016 ve 2017'de birkaç bootstrap çekiminde bir
adayın hiç alarmı yoktu ve bu çekimler atıldı (`intervals.csv` içindeki `draws_used`).

## Yeniden üretim

```sh
python -m scripts.fetch_activity_summaries --output data/activity_summaries_20261109_r1
python -m scripts.audit_activity_history_relabelled --output artifacts/activity_history_relabelled_20261112_r1
```

Config sha256 `4c3da3f030a6154585c016e03277654e8ca1a86dd8275170deadd0b8d149064a`; thresholds sha256 `7f6171291d4b70d379acff7b3598eca38d45a7a4e1344d97bb4da547f96abdec`. Yeni çıktı dizinleri kullanın;
mevcut çıktının üzerine yazılmaz.
