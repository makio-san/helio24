# Zamanlama kaynağı taraması ve gecikmesiz patlama geçmişi tavanı (2026-11-12)

## Karar

Geliştirme temeli: yeniden etiketlenmiş tablo `artifacts/relabelled_development_20261111_r1` ve benimsenen hat
`artifacts/walk_forward_v2_20261112_r1` ([`config/walk-forward-v2.json`](../config/walk-forward-v2.json),
[`config/operating-point-v3.json`](../config/operating-point-v3.json)); temel 2026-11-12 tarihinde değişti, çünkü
dondurulmuş etiketler eşlenmiş 2022–2023 M/X patlamalarının %30'undan azını kapsıyordu.

Okuma `L2_no_gain_at_zero_latency`; kural herhangi bir aday sonucundan önce
[`config/history-latency-ceiling-v1.json`](../config/history-latency-ceiling-v1.json) içinde donduruldu. `event_time`,
modele bölgesel patlama geçmişini sıfır yayın gecikmesiyle verir; bunun o anda erişilebilir olduğunu kanıtlayan
arşivlenmiş bir ürün yoktur; iyimser bir tavandır, ulaşılabilir performans değildir. Buna rağmen alarm katmanında yıllık
birincil kabul ölçütünü 6 yılın 2'sinde (2016, 2023) karşılıyor, 2022 ve 2023'ün ikisinde birden karşılamıyor.

Sonuç karışık, tümüyle negatif değil:

- 25. döngü istenen yönde hareket ediyor. 2022 (tüm adaylar için alarm yedek kural yılı): precision 0.4727 değerinden
  0.5357 değerine çıkıyor, eşli aralık sıfırın üstünde (0.0129 ile 0.1382 arası), ancak pencere recall
  0.4822 değerinden 0.3735 değerine düşüyor ve kaçırılan pozitif koşu 72 içinde 32 iken 37
  oluyor; bu yüzden ölçüt karşılanmıyor; kontrolün recall değerinde 2022 precision değeri 0.4526, kontrolün altında. 2023: precision 0.4263 değerinden 0.4409 değerine, recall 0.3879
  değerinden 0.4610 değerine çıkıyor, kaçırılan pozitif koşu 159 içinde 68 iken 60 oluyor; ölçüt
  karşılanıyor ama eşli aralık sıfırı içeriyor (-0.0189 ile 0.0473 arası) ve precision 0.50'nin altında kalıyor.
  AP 2022'de 0.4622 değerinden 0.4937 değerine, 2023'te 0.3626 değerinden
  0.4130 değerine çıkıyor.
- 24. döngü kaybediyor. 2015: precision 0.5439 değerinden 0.4655 değerine düşüyor, eşli aralık sıfırın altında
  (-0.1388 ile -0.0209 arası). 2017: 0.8676 değerinden 0.4812 değerine. 2014: 0.6825 değerinden
  0.6224 değerine. Bu yıllarda seçilen alarm eşiği daha düşük precision ile daha fazla recall ve daha az kaçırılan
  pozitif koşu veriyor.
- Alarm precision değeri en az 0.50 olan yıllar: `control` 2014, 2015, 2017; `event_time` 2014, 2016, 2022. Sayı 3 olarak kalıyor.
- Alarm accuracy değeri `control` için 2016, 2022, 2023, `event_time` için 2015, 2017, 2023 yıllarında hep-negatif accuracy
  değerinin altında.

Sonuç: bu kanıt, alarm precision değerini yükseltmek amacıyla GOES XRS akısının (yaklaşık 153 MB) indirilmesini veya
gerçek zamanlı bir olay kaynağının denetlenmesini gerekçelendirmiyor; dondurulmuş kurala göre patlama geçmişi yolu alarm
katmanı için kapandı. Hiçbir model terfi ettirilmedi; hiçbir alarm, eşik veya pano ayarı değiştirilmedi. Hiçbir şey
indirilmedi. Ayrılmış 2024–2025 testine erişilmedi.

## Kaynak taraması

Yalnızca dizin listeleri; hiçbir dosya indirilmedi.

| kaynak | dosya / konum | boyut | dönem | içerik | durum |
| --- | --- | --- | --- | --- | --- |
| GOES-15 XRS 1 dakikalık bilimsel akı | `sci_xrsf-l2-avg1m_g15_s20100407_e20200304_v2-2-1.nc`, NCEI `goes15/xrsf-l2-avg1m_science/` | 31 MB | 2010-04-07 – 2020-03-04 | tüm disk, bölge yok | indirilmedi |
| GOES-16 XRS 1 dakikalık bilimsel akı | yıllık dosyalar y2020–y2023, NGDC `goes16/l2/data/xrsf-l2-avg1m_science/` | 28, 30, 32, 32 MB | 2020–2023 (241 MB görev dosyası ayrılmış 2024–2025 dönemini de içerir, kullanılmamalı) | tüm disk, bölge yok | indirilmedi |
| GOES-16 XRS patlama konumu | `xrsf-l2-flloc_science` görev dosyası | 595 KB | 2017-02-09 sonrası; 2024–2025 içerir | konum var, 24. döngü eğitim yılları yok | indirilmedi |
| SWPC günlük olay raporları | arşivlenmiş olay listeleri | küçük | 2010–2023 | bölge ve dakika zamanları; yalnızca rapor gününden 39–76 saat sonraki arşiv `:Created:` zamanı | daha önce yoklandı, erişilebilirlik doğrulanamadı |
| AIA / SUVI EUV bölge görüntüleri | JSOC / NGDC | onlarca GB | 2010– / 2017– | bölge çözünürlüklü, ölçüm zamanına göre nedensel | indirilmedi; boş disk alanını (yaklaşık 18 GiB) aşıyor |
| SGAS olay zamanları (bu rapor) | `data/activity_summaries_20261109_r1` | yerel, 22 MB | 2010–2023 | bölge ve dakika zamanları; günde bir kez yayımlanır | gecikmesiz tavan olarak kullanıldı |

| daha önce test edildi, negatif | rapor |
| --- | --- |
| 96 SHARP özeti, türevleri ve ek özellikler | [precision-features](precision-features-20261027.tr.md) |
| 24/48 saatlik özet geçmişleri | [precision-long-history](precision-long-history-20261028.tr.md) |
| 12 dakikalık dizilerde TCN | [temporal-evaluation-final](temporal-evaluation-final-20261106.tr.md) |
| Yayımlanmış SRS bölge bağlamı | [region-context-results](region-context-results-20261109.tr.md) |
| Yayımlanmış SGAS patlama geçmişi, dondurulmuş ve yeniden etiketlenmiş etiketler | [activity-history](activity-history-20261109.tr.md), [activity-history-relabelled](activity-history-relabelled-20261112.tr.md) |
| Günlük Br haritası CNN skoru | [image-features](image-features-20261110.tr.md) |
| Kendi olasılık yörüngesi ve bölge yaşı | [precision-context-results](precision-context-results-20261109.tr.md) |

GOES XRS 1 dakikalık akı projede kullanılmadı. Ölçüm zamanına göre nedenseldir ama tüm diskin toplamıdır: hangi bölgenin
patladığını söyleyemez. [Nedensel SGAS geçmişi](activity-history-relabelled-20261112.tr.md) bölge çözünürlüklüdür ama
günde bir kez, yaklaşık 0245 UTC'de önceki UT günü için yayımlanır; bu yüzden kullanılabilen en yeni olay yaklaşık 3 ile
51 saat yaşındadır. Bu rapor, daha hızlı bir kaynağın bedelini ödemeden önce aynı bilginin gecikmesiz olarak ne
kazandıracağını ölçüyor.

## Yöntem

Her SGAS A bölümü satırı Begin, Max ve End değerlerini yayın tarihinden önceki UT gününde HHMM olarak verir. Olay zamanı
End değeridir (End boşsa Max, sonra Begin); Begin değerinden erken bir zaman ertesi güne taşınır. 12286 olay satırı
ayrıştırıldı. Tahmin zamanı t olan bir pencere, olay zamanı t eksi 30 dakika veya öncesinde olan her olayı, onu
listeleyen ürünün yayın zamanına bakmadan kullanır. Bu, devreye alınabilir kural değildir. Etiketler t anındaki veya
sonrasındaki GOES tepe zamanlarını kullanır; dolayısıyla hiçbir özellik olayı etiket penceresinin içinde değildir.
Bölgesel olaylar, NOAA numarası tahmin tarihinde HARP'ın `NOAA_ARS` alanında bulunan olaylardır; NOAA numarası olmayan
bir HARP için `event_available` = 0 olur ve bölgesel değerler eksiktir.

On altı özellik: `event_available`, `reg_mx_6h`, `reg_mx_12h`, `reg_mx_24h`, `reg_mx_72h`, `reg_c_24h`, `reg_c_72h`,
`reg_events_24h`, `reg_max_logflux_24h`, `reg_max_logflux_72h`, `reg_hours_since_mx`, `reg_hours_since_event`,
`reg_mx_life`, `reg_max_logflux_life`, `disk_mx_24h`, `disk_max_logflux_24h`.

Adaylar: `control`, benimsenen hattın kayıtlı ensemble olasılıkları ve eşikleridir; `history`,
`artifacts/activity_history_relabelled_20261112_r1` içindeki kayıtlı nedensel SGAS geçmişi adayıdır; ikisi de yeniden
eğitilmez. `event_time`, değişmeyen tarifleri 96 özet artı on altı özellik ile yeniden eğitir: genişleyen eğitim, önceki
yılda sigmoid kalibrasyon, ensemble ağırlığı 0.45/0.55, hiperparametre araması yok, 12 bileşen eğitimi, tek özellik
kümesi. Yıllık popülasyonlar benimsenen hattınkilerle aynıdır. İzleme eşikleri (önceki yıl pencere recall 0.90) ve alarm
eşikleri (önceki yıl precision 0.50, recall tabanı 0.10, yedek kural işareti) kalibrasyon yılı olasılıklarında seçildi,
değerlendirme etiketleri okunmadan önce yazıldı ve özetlendi.

Alarm katmanında `control` adayına karşı yıllık birincil kabul ölçütü: precision daha yüksek, kaçırılan pozitif koşu
daha fazla değil, pencere recall düşüşü en çok 0.02. `L1_latency_binding` okuması bunu altı yılın tümünde, ya da 2022 ve
2023'ün ikisinde birden ve her ikisinde eşli bootstrap alt sınırı 0'ın üstünde olacak şekilde gerektiriyordu. Sayılar
örtüşen tahmin pencereleridir; pozitif koşu, bir HARP'ın bitişik pozitif pencereler grubudur.

Gecikmesiz özelliklerin değerlendirme yılı kapsamı:

| yıl | değerlendirme penceresi | event_available payı | reg_mx_24h > 0 payı | reg_mx_72h > 0 payı |
| --- | --- | --- | --- | --- |
| 2014 | 78351 | 0.5226 | 0.0263 | 0.0475 |
| 2015 | 70554 | 0.5460 | 0.0197 | 0.0409 |
| 2016 | 43142 | 0.5515 | 0.0047 | 0.0083 |
| 2017 | 19843 | 0.6073 | 0.0133 | 0.0209 |
| 2022 | 65593 | 0.6172 | 0.0305 | 0.0605 |
| 2023 | 96991 | 0.5664 | 0.0467 | 0.0934 |

## Alarm katmanı

| yıl | aday | yedek kural | TP | FP | FN | recall | precision | precision %95 aralığı | accuracy | hep-negatif accuracy | kaçırılan pozitif koşu | birincil ölçüt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | hayır | 688 | 320 | 1748 | 0.2824 | 0.6825 | 0.4308–0.8477 | 0.9736 | 0.9689 | 66/88 |  |
| 2014 | `history` | hayır | 708 | 296 | 1728 | 0.2906 | 0.7052 | 0.4628–0.8478 | 0.9742 | 0.9689 | 67/88 | hayır |
| 2014 | `event_time` | hayır | 801 | 486 | 1635 | 0.3288 | 0.6224 | 0.3865–0.7877 | 0.9729 | 0.9689 | 61/88 | hayır |
| 2015 | `control` | hayır | 545 | 457 | 916 | 0.3730 | 0.5439 | 0.3286–0.7166 | 0.9805 | 0.9793 | 27/57 |  |
| 2015 | `history` | hayır | 485 | 388 | 976 | 0.3320 | 0.5556 | 0.3463–0.7216 | 0.9807 | 0.9793 | 28/57 | hayır |
| 2015 | `event_time` | hayır | 648 | 744 | 813 | 0.4435 | 0.4655 | 0.2792–0.6266 | 0.9779 | 0.9793 | 22/57 | hayır |
| 2016 | `control` | hayır | 94 | 109 | 120 | 0.4393 | 0.4631 | 0.0000–0.6230 | 0.9947 | 0.9950 | 3/8 |  |
| 2016 | `history` | hayır | 64 | 71 | 150 | 0.2991 | 0.4741 | 0.0000–0.6667 | 0.9949 | 0.9950 | 4/8 | hayır |
| 2016 | `event_time` | hayır | 99 | 74 | 115 | 0.4626 | 0.5723 | 0.0000–0.7091 | 0.9956 | 0.9950 | 2/8 | evet |
| 2017 | `control` | hayır | 177 | 27 | 88 | 0.6679 | 0.8676 | 0.0000–1.0000 | 0.9942 | 0.9866 | 3/6 |  |
| 2017 | `history` | hayır | 181 | 93 | 84 | 0.6830 | 0.6606 | 0.0000–0.9325 | 0.9911 | 0.9866 | 3/6 | hayır |
| 2017 | `event_time` | hayır | 205 | 221 | 60 | 0.7736 | 0.4812 | 0.0000–0.8440 | 0.9858 | 0.9866 | 1/6 | hayır |
| 2022 | `control` | evet | 1056 | 1178 | 1134 | 0.4822 | 0.4727 | 0.3482–0.6021 | 0.9648 | 0.9666 | 32/72 |  |
| 2022 | `history` | evet | 1278 | 2004 | 912 | 0.5836 | 0.3894 | 0.2893–0.4982 | 0.9555 | 0.9666 | 22/72 | hayır |
| 2022 | `event_time` | evet | 818 | 709 | 1372 | 0.3735 | 0.5357 | 0.4051–0.6836 | 0.9683 | 0.9666 | 37/72 | hayır |
| 2023 | `control` | hayır | 1587 | 2136 | 2504 | 0.3879 | 0.4263 | 0.3483–0.5053 | 0.9522 | 0.9578 | 68/159 |  |
| 2023 | `history` | hayır | 1703 | 2210 | 2388 | 0.4163 | 0.4352 | 0.3583–0.5207 | 0.9526 | 0.9578 | 67/159 | evet |
| 2023 | `event_time` | hayır | 1886 | 2392 | 2205 | 0.4610 | 0.4409 | 0.3674–0.5199 | 0.9526 | 0.9578 | 60/159 | evet |

Yedek kural yılları (2022), kalibrasyon yılında hiçbir eşiğin en az 0.10 recall ile 0.50 precision değerine
ulaşmadığı yıllardır; kural bu durumda erişilebilen en iyi kalibrasyon precision değerini alır. Precision aralıkları her
adayın HARP kümeli bootstrap aralıklarıdır.

Kabul ölçütleri:

| yıl | aday | precision daha yüksek | kaçırılan koşu fazla değil | recall düşüşü en çok 0.02 | birincil ölçüt |
| --- | --- | --- | --- | --- | --- |
| 2014 | `history` | evet | hayır | evet | hayır |
| 2014 | `event_time` | hayır | evet | evet | hayır |
| 2015 | `history` | evet | hayır | hayır | hayır |
| 2015 | `event_time` | hayır | evet | evet | hayır |
| 2016 | `history` | evet | hayır | hayır | hayır |
| 2016 | `event_time` | evet | evet | evet | evet |
| 2017 | `history` | hayır | evet | evet | hayır |
| 2017 | `event_time` | hayır | evet | evet | hayır |
| 2022 | `history` | hayır | evet | evet | hayır |
| 2022 | `event_time` | evet | hayır | hayır | hayır |
| 2023 | `history` | evet | evet | evet | evet |
| 2023 | `event_time` | evet | evet | evet | evet |

Seçilen alarm eşikleri:

| yıl | aday | alarm eşiği | kalibrasyon recall | kalibrasyon precision | yedek kural |
| --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.4627 | 0.1326 | 0.5000 | hayır |
| 2014 | `history` | 0.4278 | 0.1560 | 0.5000 | hayır |
| 2014 | `event_time` | 0.3534 | 0.2502 | 0.5000 | hayır |
| 2015 | `control` | 0.2631 | 0.4906 | 0.5000 | hayır |
| 2015 | `history` | 0.2627 | 0.4819 | 0.5000 | hayır |
| 2015 | `event_time` | 0.2519 | 0.5115 | 0.5000 | hayır |
| 2016 | `control` | 0.2564 | 0.4969 | 0.5000 | hayır |
| 2016 | `history` | 0.2918 | 0.4052 | 0.5000 | hayır |
| 2016 | `event_time` | 0.3132 | 0.4073 | 0.5000 | hayır |
| 2017 | `control` | 0.4145 | 0.2196 | 0.5000 | hayır |
| 2017 | `history` | 0.3538 | 0.2991 | 0.5000 | hayır |
| 2017 | `event_time` | 0.2307 | 0.5187 | 0.5000 | hayır |
| 2022 | `control` | 0.1570 | 0.2361 | 0.1996 | evet |
| 2022 | `history` | 0.1622 | 0.2281 | 0.2155 | evet |
| 2022 | `event_time` | 0.2466 | 0.1326 | 0.2463 | evet |
| 2023 | `control` | 0.2689 | 0.4461 | 0.5000 | hayır |
| 2023 | `history` | 0.2999 | 0.3767 | 0.5000 | hayır |
| 2023 | `event_time` | 0.2855 | 0.4292 | 0.5000 | hayır |

Alarm precision farkının eşli HARP kümeli bootstrap aralıkları (aday eksi karşılaştırılan aday, 1000 çekim, seed 24):

| yıl | aday | karşılaştırılan | alt | üst | kullanılan çekim |
| --- | --- | --- | --- | --- | --- |
| 2014 | `history` | `control` | -0.0616 | 0.1081 | 1000 |
| 2014 | `event_time` | `control` | -0.1184 | 0.0144 | 1000 |
| 2014 | `event_time` | `history` | -0.1366 | -0.0148 | 1000 |
| 2015 | `history` | `control` | -0.0306 | 0.0645 | 1000 |
| 2015 | `event_time` | `control` | -0.1388 | -0.0209 | 1000 |
| 2015 | `event_time` | `history` | -0.1497 | -0.0306 | 1000 |
| 2016 | `history` | `control` | -0.3060 | 0.1235 | 994 |
| 2016 | `event_time` | `control` | 0.0000 | 0.3070 | 999 |
| 2016 | `event_time` | `history` | 0.0000 | 0.4745 | 994 |
| 2017 | `history` | `control` | -0.4631 | 0.0000 | 982 |
| 2017 | `event_time` | `control` | -0.5652 | 0.0990 | 982 |
| 2017 | `event_time` | `history` | -0.3277 | 0.1000 | 1000 |
| 2022 | `history` | `control` | -0.1453 | -0.0331 | 1000 |
| 2022 | `event_time` | `control` | 0.0129 | 0.1382 | 1000 |
| 2022 | `event_time` | `history` | 0.0645 | 0.2507 | 1000 |
| 2023 | `history` | `control` | -0.0210 | 0.0396 | 1000 |
| 2023 | `event_time` | `control` | -0.0189 | 0.0473 | 1000 |
| 2023 | `event_time` | `history` | -0.0214 | 0.0307 | 1000 |

## Betimleyici ölçüler

`kontrol recall değerinde precision`, adayın değerlendirme yılında kontrolün alarm recall değerini veren eşikteki
precision değeridir. Değerlendirme etiketlerini kullanır, devreye alınamaz ve kabul ölçütünün parçası değildir. AP ve FP
kaynağı payları 25. döngü teşhisindeki tanımları izler.

| yıl | aday | AP | patlayan HARP içi AP | bölge AP | kontrol recall değerinde precision | FP payı: hiç patlamayan HARP | FP payı: pozitife 72 saat içinde |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 0.5015 | 0.5528 | 0.7600 | 0.6846 | 0.1437 | 0.7063 |
| 2014 | `history` | 0.5136 | 0.5576 | 0.7959 | 0.7159 | 0.1047 | 0.7939 |
| 2014 | `event_time` | 0.5072 | 0.5506 | 0.8042 | 0.6647 | 0.1111 | 0.7325 |
| 2015 | `control` | 0.4823 | 0.5331 | 0.8264 | 0.5439 | 0.0853 | 0.8249 |
| 2015 | `history` | 0.4487 | 0.4945 | 0.8593 | 0.5018 | 0.0438 | 0.8660 |
| 2015 | `event_time` | 0.4344 | 0.4783 | 0.8613 | 0.4802 | 0.0954 | 0.7540 |
| 2016 | `control` | 0.4060 | 0.4853 | 0.6333 | 0.4631 | 0.2569 | 0.5688 |
| 2016 | `history` | 0.4430 | 0.4976 | 0.7589 | 0.4541 | 0.0423 | 0.7606 |
| 2016 | `event_time` | 0.4804 | 0.5191 | 0.9167 | 0.5839 | 0.0405 | 0.8243 |
| 2017 | `control` | 0.7975 | 0.8727 | 1.0000 | 0.8762 | 0.1111 | 0.8889 |
| 2017 | `history` | 0.7571 | 0.8459 | 0.8333 | 0.8592 | 0.6344 | 0.3656 |
| 2017 | `event_time` | 0.7763 | 0.8607 | 1.0000 | 0.7902 | 0.6154 | 0.3801 |
| 2022 | `control` | 0.4622 | 0.4968 | 0.8315 | 0.4752 | 0.0823 | 0.7139 |
| 2022 | `history` | 0.4692 | 0.4975 | 0.8628 | 0.4638 | 0.1108 | 0.6607 |
| 2022 | `event_time` | 0.4937 | 0.5195 | 0.8801 | 0.4526 | 0.0028 | 0.8702 |
| 2023 | `control` | 0.3626 | 0.4057 | 0.8655 | 0.4263 | 0.1320 | 0.7561 |
| 2023 | `history` | 0.3737 | 0.4142 | 0.8779 | 0.4486 | 0.1285 | 0.7719 |
| 2023 | `event_time` | 0.4130 | 0.4464 | 0.9026 | 0.4740 | 0.0911 | 0.8399 |

- `event_time` alarm precision değeri 2016, 2022, 2023 yıllarında kontrolün üstünde, 2014, 2015, 2017 yıllarında altında. Eşli aralık
  2022 yılında sıfırın üstünde, 2015 yılında sıfırın altında.
- `event_time` ile AP 2014, 2016, 2022, 2023 yıllarında kontrolün üstünde, 2015, 2017 yıllarında altında.
- Kontrolün verdiği recall değerinde `event_time` precision değeri 2016, 2023 yıllarında kontrolün üstünde, 2014, 2015, 2017, 2022
  yıllarında altında. Dolayısıyla kayıplar yalnızca eşik kayması değil; seçilen eşikteki 2022 kazancı da daha düşük
  recall değerinde çalışmaktan geliyor: kontrolün recall değerinde 2022 precision değeri 0.4727 değerine karşı
  0.4526.
- `event_time` ile alarm FP pencerelerinin 72 saatlik yakın-ıska payı 2022'de 0.8702, 2023'te
  0.8399 (kontrol 0.7139 ve 0.7561).

## İzleme katmanı

| yıl | aday | TP | FP | FN | recall | precision | accuracy | hep-negatif accuracy | kaçırılan pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | `control` | 2146 | 9020 | 290 | 0.8810 | 0.1922 | 0.8812 | 0.9689 | 6/88 |
| 2014 | `history` | 2191 | 10033 | 245 | 0.8994 | 0.1792 | 0.8688 | 0.9689 | 5/88 |
| 2014 | `event_time` | 2208 | 10256 | 228 | 0.9064 | 0.1772 | 0.8662 | 0.9689 | 6/88 |
| 2015 | `control` | 1396 | 8079 | 65 | 0.9555 | 0.1473 | 0.8846 | 0.9793 | 1/57 |
| 2015 | `history` | 1378 | 7551 | 83 | 0.9432 | 0.1543 | 0.8918 | 0.9793 | 1/57 |
| 2015 | `event_time` | 1371 | 7173 | 90 | 0.9384 | 0.1605 | 0.8971 | 0.9793 | 1/57 |
| 2016 | `control` | 201 | 1722 | 13 | 0.9393 | 0.1045 | 0.9598 | 0.9950 | 0/8 |
| 2016 | `history` | 195 | 1276 | 19 | 0.9112 | 0.1326 | 0.9700 | 0.9950 | 0/8 |
| 2016 | `event_time` | 198 | 1626 | 16 | 0.9252 | 0.1086 | 0.9619 | 0.9950 | 0/8 |
| 2017 | `control` | 243 | 1058 | 22 | 0.9170 | 0.1868 | 0.9456 | 0.9866 | 1/6 |
| 2017 | `history` | 244 | 1059 | 21 | 0.9208 | 0.1873 | 0.9456 | 0.9866 | 1/6 |
| 2017 | `event_time` | 245 | 1038 | 20 | 0.9245 | 0.1910 | 0.9467 | 0.9866 | 1/6 |
| 2022 | `control` | 2024 | 11917 | 166 | 0.9242 | 0.1452 | 0.8158 | 0.9666 | 5/72 |
| 2022 | `history` | 2065 | 14935 | 125 | 0.9429 | 0.1215 | 0.7704 | 0.9666 | 4/72 |
| 2022 | `event_time` | 2016 | 10280 | 174 | 0.9205 | 0.1640 | 0.8406 | 0.9666 | 6/72 |
| 2023 | `control` | 3695 | 16022 | 396 | 0.9032 | 0.1874 | 0.8307 | 0.9578 | 10/159 |
| 2023 | `history` | 3770 | 17668 | 321 | 0.9215 | 0.1759 | 0.8145 | 0.9578 | 7/159 |
| 2023 | `event_time` | 3747 | 15561 | 344 | 0.9159 | 0.1941 | 0.8360 | 0.9578 | 7/159 |

İzleme katmanı accuracy değeri her aday için her yıl hep-negatif accuracy değerinin altında.

## Dondurulmuş etiket sonuçları

Bu tavan dondurulmuş etiketlerle çalıştırılmadı. Nedensel SGAS geçmişinin dondurulmuş etiket sonuçları
[activity-history-20261109](activity-history-20261109.tr.md) içinde duruyor ve
[activity-history-relabelled-20261112](activity-history-relabelled-20261112.tr.md) içinde tekrarlanıyor; negatiftir.

## Sınırlar

İyimser ve devreye alınamaz: olayın, sınıfının ve NOAA numarasının olay bittikten 30 dakika sonra gerçek zamanlı olarak
bilindiği varsayılıyor ve bunu kanıtlayan arşivlenmiş bir ürün yok. Daha önce incelenmiş yıllar: uyarlamalı geliştirme
kanıtı, bağımsız test değil. Sayılar örtüşen tahmin pencereleri ve bunların gruplarıdır, fiziksel patlamalar değil. SGAS
enerjik olayları listeler, her C sınıfı patlamayı değil. On üç günün SGAS dosyası, bir günün yayın zamanı yok; bu
günlerin olayları eksiktir ve kodlanmamıştır. `NOAA_ARS` kesinleşmiş JSOC eşlemesidir ve sonradan sabitlenmiştir. Yeniden
etiketlenmiş M/X etiketleri aynı SGAS satırlarından elde edildi; dolayısıyla geçmiş bölgesel M/X özellikleri aynı
bölgenin gecikmesiz görülen geçmiş etiketleridir; operasyonel bir kaynak daha gürültülü olurdu. 2022 alarm eşiği her
aday için yedek kural eşiğidir. 2016 ve 2017'de birkaç bootstrap çekiminde bir adayın hiç alarmı yoktu ve bu çekimler
atıldı (`kullanılan çekim`). Tarama, boyutları dizin listelerinden verir; dosya içerikleri incelenmedi. Okuma, değişmeyen
tariflere eklenen bir özellik olarak patlama geçmişiyle ilgilidir; GOES XRS akısının kendisini test etmez.

## Yeniden üretim

```sh
python -m scripts.fetch_activity_summaries --output data/activity_summaries_20261109_r1
python -m scripts.audit_activity_history_relabelled --output artifacts/activity_history_relabelled_20261112_r1
python -m scripts.audit_history_latency_ceiling --output artifacts/history_latency_ceiling_20261112_r1
```

Config sha256 `986cf5894c78ece27306cebf5e85baad58cb4bcc45d608d489a26ebad5ba3628`; thresholds sha256 `1cd295c8245de4767e2618e1c12ee3b661bde921fe624030151b2be95023a6da`. Yeni çıktı dizinleri kullanın;
mevcut çıktının üzerine yazılmaz.
