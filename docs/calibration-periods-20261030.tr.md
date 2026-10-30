# Yıllar boyunca kalibrasyon ve eşik dönemlerini ayırma

Ayrılmış yöntem, pozitif değerlendirme yıllarının 6 tanesinden 4 tanesinde
recall >=0.95 sağladı. Tüm yıllar için kabul kontrolü `False` oldu. Dashboard modeli
ve alarm kuralı değiştirilmedi; ayrılmış 2024–2025 testi kapalı kaldı. Tek yıldaki
iyileşme genel model iyileşmesi sayılmadı.

## Tasarım ve kontrol kolları

Sabit protokol `config/calibration-periods-v1.json` dosyasındadır. `walk-forward-v1`
deneyinin aynı yıllık lojistik ve XGBoost modelleri, 96 özelliği, 0.45/0.55 birleşimi ve
değerlendirme toplulukları korundu. Bu deney yeni temel sınıflandırıcılar değil, yeni
olasılık kalibratörleri ve eşikler öğrenir. Özgün kaynak özetleri, ayrım denetimleri ve
değerlendirme meta verileri kullanımdan önce doğrulanır.

Üç kol karşılaştırılır. `baseline_full_year`, sabit tam yıllık sigmoid kalibratörleri
ve eşiği korur. `late_threshold_control`, aynı kalibratörleri ve olasılıkları korur,
ancak eşiği yalnızca önceki yılın ikinci yarısında seçer. Eşik verisinin yakın tarihli
olmasını kontrol etmek için kalibrasyon/eşik verisinin tekrar kullanımı bilinçli korunur.
`separated_calibration`, sigmoid kalibratörlerini yalnızca ilk yarıda öğrenir ve eşiği
yalnızca ikinci yarıda seçer. Her eşik kendi seçim döneminde recall >=0.95 hedefler ve
değerlendirme tahminlerinden önce kaydedilir. Değerlendirme etiketleriyle yeniden ayarlanmaz.

Sınır, değerlendirmeden önceki yılın 1 Temmuz tarihidir. Erken tahmin pencereleri bu
sınıra kadar bitmeli, geç gözlem pencereleri sınırda veya sonrasında başlamalıdır.
İlk yarıda görülen HARP'lar iki yeni kolun da geç dönem eşik seçimi verisinden çıkarılır.
Dış eğitim ve değerlendirme satırları değişmez. Bölme hem örnek sayısını hem zamanlamayı
değiştirir; yalnızca veri tekrar kullanımının nedensel etkisini ayırmaz. Kaynak etiket/kalite
dışlamaları geçerlidir.

## Tur kullanılabilirliği ve ayrım denetimi

| year | status | reason | early_rows | early_positives | late_rows | late_positives | boundary_removed | shared_harp_rows_removed | unavailable | passes_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | complete | undefined | 33718.000000 | 406.000000 | 39614.000000 | 881.000000 | 360.000000 | 457.000000 | {} | False |
| 2015 | complete | undefined | 36445.000000 | 1215.000000 | 37472.000000 | 1054.000000 | 292.000000 | 1019.000000 | {} | False |
| 2016 | complete | undefined | 38615.000000 | 692.000000 | 29912.000000 | 663.000000 | 113.000000 | 498.000000 | {} | False |
| 2017 | complete | undefined | 26232.000000 | 111.000000 | 16505.000000 | 70.000000 | 83.000000 | 167.000000 | {} | False |
| 2018 | complete | undefined | 10352.000000 | 65.000000 | 9078.000000 | 188.000000 | 70.000000 | 29.000000 | {} | undefined |
| 2019 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2020 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2021 | skipped | Training/calibration lacks both classes: ['calibration'] | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined |
| 2022 | complete | undefined | 9997.000000 | 75.000000 | 17462.000000 | 129.000000 | 237.000000 | 429.000000 | {} | False |
| 2023 | complete | undefined | 24198.000000 | 192.000000 | 25733.000000 | 229.000000 | 361.000000 | 464.000000 | {} | False |

Önceki kalibrasyon yıllarında pozitif örnek olmadığı için özgün 2019–2021 atlamaları
korunur. Geç yarıda iki sınıf olmasaydı iki yeni yöntem de kullanılamazdı; yalnızca erken
yarıda iki sınıf olmasaydı ayrılmış yöntem kullanılamazdı. Sessizce referansa dönülmez.
`undefined`, ölçülmüş sıfır değildir.

## Precision, recall ve yanlış pozitif pencereler

| year | arm | n | positives | precision | recall | fp | fn | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline_full_year | 75228 | 2310 | 0.135905 | 0.945455 | 13886 | 126 | 0.011475 |
| 2014 | late_threshold_control | 75228 | 2310 | 0.219832 | 0.849351 | 6963 | 348 | 0.037206 |
| 2014 | separated_calibration | 75228 | 2310 | 0.221038 | 0.844156 | 6872 | 360 | 0.032129 |
| 2015 | baseline_full_year | 69138 | 1355 | 0.105164 | 0.993358 | 11453 | 9 | 0.018839 |
| 2015 | late_threshold_control | 69138 | 1355 | 0.196984 | 0.944649 | 5218 | 75 | 0.048456 |
| 2015 | separated_calibration | 69138 | 1355 | 0.191636 | 0.946863 | 5412 | 72 | 0.061086 |
| 2016 | baseline_full_year | 42987 | 181 | 0.071400 | 0.972376 | 2289 | 5 | 0.030831 |
| 2016 | late_threshold_control | 42987 | 181 | 0.069264 | 0.972376 | 2365 | 5 | 0.029657 |
| 2016 | separated_calibration | 42987 | 181 | 0.069620 | 0.972376 | 2352 | 5 | 0.029622 |
| 2017 | baseline_full_year | 19529 | 253 | 0.155512 | 0.936759 | 1287 | 16 | 0.012000 |
| 2017 | late_threshold_control | 19529 | 253 | 0.127043 | 0.952569 | 1656 | 12 | 0.006265 |
| 2017 | separated_calibration | 19529 | 253 | 0.131622 | 0.952569 | 1590 | 12 | 0.005171 |
| 2018 | baseline_full_year | 7799 | 0 | 0.000000 | undefined | 359 | 0 | 0.004351 |
| 2018 | late_threshold_control | 7799 | 0 | 0.000000 | undefined | 1 | 0 | 0.058659 |
| 2018 | separated_calibration | 7799 | 0 | undefined | undefined | 0 | 0 | 0.066088 |
| 2022 | baseline_full_year | 50756 | 421 | 0.039573 | 0.985748 | 10072 | 6 | 0.008994 |
| 2022 | late_threshold_control | 50756 | 421 | 0.070197 | 0.957245 | 5338 | 18 | 0.023981 |
| 2022 | separated_calibration | 50756 | 421 | 0.070566 | 0.957245 | 5308 | 18 | 0.038661 |
| 2023 | baseline_full_year | 60366 | 781 | 0.103397 | 0.884763 | 5992 | 90 | 0.018203 |
| 2023 | late_threshold_control | 60366 | 781 | 0.066412 | 0.956466 | 10501 | 34 | 0.006393 |
| 2023 | separated_calibration | 60366 | 781 | 0.064247 | 0.956466 | 10880 | 34 | 0.005327 |

Tüm skorlar 0–1 ölçeğinde oranlardır. Precision alarm pencerelerindeki pozitiflerin,
recall pozitif pencerelerdeki yakalananların oranıdır. FP/FN bağımsız patlamalar veya
bildirimler değil, örtüşen tahmin pencereleridir. Her kol aynı yıllık değerlendirme
satırlarında kendi sabit eşiğini kullanır. 2018'de korunan pozitif pencere yoktur.
Ayrılmış yöntem ayrıca hiç alarm vermediğinden hem precision hem recall tanımsızdır;
sıfır FP, pozitif olayların yakalanacağını göstermez.

## Tüm metriklerin karşılaştırması

| year | arm | n | positives | threshold | tp | fp | fn | tn | recall | precision | false_positive_rate | false_alarm_ratio | alarms | tss | average_precision | brier | log_loss | accuracy | balanced_accuracy | f1 | always_quiet_accuracy | precision_defined | recall_defined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline_full_year | 75228 | 2310 | 0.011475 | 2184 | 13886 | 126 | 59032 | 0.945455 | 0.135905 | 0.190433 | 0.864095 | 16070 | 0.755021 | 0.507930 | 0.020661 | 0.076538 | 0.813740 | 0.877511 | 0.237650 | 0.969293 | True | True |
| 2014 | late_threshold_control | 75228 | 2310 | 0.037206 | 1962 | 6963 | 348 | 65955 | 0.849351 | 0.219832 | 0.095491 | 0.780168 | 8925 | 0.753860 | 0.507930 | 0.020661 | 0.076538 | 0.902815 | 0.876930 | 0.349266 | 0.969293 | True | True |
| 2014 | separated_calibration | 75228 | 2310 | 0.032129 | 1950 | 6872 | 360 | 66046 | 0.844156 | 0.221038 | 0.094243 | 0.778962 | 8822 | 0.749913 | 0.504801 | 0.022211 | 0.081103 | 0.903866 | 0.874956 | 0.350341 | 0.969293 | True | True |
| 2015 | baseline_full_year | 69138 | 1355 | 0.018839 | 1346 | 11453 | 9 | 56330 | 0.993358 | 0.105164 | 0.168966 | 0.894836 | 12799 | 0.824392 | 0.492441 | 0.013564 | 0.047847 | 0.834216 | 0.912196 | 0.190194 | 0.980402 | True | True |
| 2015 | late_threshold_control | 69138 | 1355 | 0.048456 | 1280 | 5218 | 75 | 62565 | 0.944649 | 0.196984 | 0.076981 | 0.803016 | 6498 | 0.867668 | 0.492441 | 0.013564 | 0.047847 | 0.923443 | 0.933834 | 0.325990 | 0.980402 | True | True |
| 2015 | separated_calibration | 69138 | 1355 | 0.061086 | 1283 | 5412 | 72 | 62371 | 0.946863 | 0.191636 | 0.079843 | 0.808364 | 6695 | 0.867020 | 0.492655 | 0.013746 | 0.050348 | 0.920680 | 0.933510 | 0.318758 | 0.980402 | True | True |
| 2016 | baseline_full_year | 42987 | 181 | 0.030831 | 176 | 2289 | 5 | 40517 | 0.972376 | 0.071400 | 0.053474 | 0.928600 | 2465 | 0.918902 | 0.366443 | 0.003263 | 0.014523 | 0.946635 | 0.959451 | 0.133031 | 0.995789 | True | True |
| 2016 | late_threshold_control | 42987 | 181 | 0.029657 | 176 | 2365 | 5 | 40441 | 0.972376 | 0.069264 | 0.055249 | 0.930736 | 2541 | 0.917126 | 0.366443 | 0.003263 | 0.014523 | 0.944867 | 0.958563 | 0.129317 | 0.995789 | True | True |
| 2016 | separated_calibration | 42987 | 181 | 0.029622 | 176 | 2352 | 5 | 40454 | 0.972376 | 0.069620 | 0.054946 | 0.930380 | 2528 | 0.917430 | 0.367034 | 0.003257 | 0.014633 | 0.945169 | 0.958715 | 0.129937 | 0.995789 | True | True |
| 2017 | baseline_full_year | 19529 | 253 | 0.012000 | 237 | 1287 | 16 | 17989 | 0.936759 | 0.155512 | 0.066767 | 0.844488 | 1524 | 0.869992 | 0.811694 | 0.004907 | 0.020488 | 0.933279 | 0.934996 | 0.266742 | 0.987045 | True | True |
| 2017 | late_threshold_control | 19529 | 253 | 0.006265 | 241 | 1656 | 12 | 17620 | 0.952569 | 0.127043 | 0.085910 | 0.872957 | 1897 | 0.866659 | 0.811694 | 0.004907 | 0.020488 | 0.914589 | 0.933330 | 0.224186 | 0.987045 | True | True |
| 2017 | separated_calibration | 19529 | 253 | 0.005171 | 241 | 1590 | 12 | 17686 | 0.952569 | 0.131622 | 0.082486 | 0.868378 | 1831 | 0.870083 | 0.808219 | 0.004896 | 0.020118 | 0.917968 | 0.935042 | 0.231286 | 0.987045 | True | True |
| 2018 | baseline_full_year | 7799 | 0 | 0.004351 | 0 | 359 | 0 | 7440 | undefined | 0.000000 | 0.046032 | 1.000000 | 359 | undefined | undefined | 0.000012 | 0.000791 | 0.953968 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | late_threshold_control | 7799 | 0 | 0.058659 | 0 | 1 | 0 | 7798 | undefined | 0.000000 | 0.000128 | 1.000000 | 1 | undefined | undefined | 0.000012 | 0.000791 | 0.999872 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | separated_calibration | 7799 | 0 | 0.066088 | 0 | 0 | 0 | 7799 | undefined | undefined | 0.000000 | undefined | 0 | undefined | undefined | 0.000015 | 0.001024 | 1.000000 | undefined | undefined | 1.000000 | False | False |
| 2022 | baseline_full_year | 50756 | 421 | 0.008994 | 415 | 10072 | 6 | 40263 | 0.985748 | 0.039573 | 0.200099 | 0.960427 | 10487 | 0.785649 | 0.280023 | 0.007064 | 0.029196 | 0.801442 | 0.892824 | 0.076091 | 0.991705 | True | True |
| 2022 | late_threshold_control | 50756 | 421 | 0.023981 | 403 | 5338 | 18 | 44997 | 0.957245 | 0.070197 | 0.106049 | 0.929803 | 5741 | 0.851195 | 0.280023 | 0.007064 | 0.029196 | 0.894476 | 0.925598 | 0.130802 | 0.991705 | True | True |
| 2022 | separated_calibration | 50756 | 421 | 0.038661 | 403 | 5308 | 18 | 45027 | 0.957245 | 0.070566 | 0.105453 | 0.929434 | 5711 | 0.851791 | 0.279087 | 0.007239 | 0.032122 | 0.895067 | 0.925896 | 0.131442 | 0.991705 | True | True |
| 2023 | baseline_full_year | 60366 | 781 | 0.018203 | 691 | 5992 | 90 | 53593 | 0.884763 | 0.103397 | 0.100562 | 0.896603 | 6683 | 0.784201 | 0.220619 | 0.011195 | 0.043996 | 0.899248 | 0.892100 | 0.185155 | 0.987062 | True | True |
| 2023 | late_threshold_control | 60366 | 781 | 0.006393 | 747 | 10501 | 34 | 49084 | 0.956466 | 0.066412 | 0.176236 | 0.933588 | 11248 | 0.780230 | 0.220619 | 0.011195 | 0.043996 | 0.825481 | 0.890115 | 0.124200 | 0.987062 | True | True |
| 2023 | separated_calibration | 60366 | 781 | 0.005327 | 747 | 10880 | 34 | 48705 | 0.956466 | 0.064247 | 0.182596 | 0.935753 | 11627 | 0.773870 | 0.218710 | 0.011253 | 0.044239 | 0.819203 | 0.886935 | 0.120406 | 0.987062 | True | True |

Accuracy tüm doğru sınıflandırılan pencereleri ölçer; sınıf dengesizliğinde yanıltıcı
olabilir. AP sıralamayı ölçer; düşük Brier/log loss daha iyi olasılıksal puanlamadır.
Sabit kabul kontrolü, tüm karşılaştırılabilir pozitif yılların kapsanmasını, her yılda
recall >=0.95 koşulunda kesinlikle daha yüksek precision, referansa göre düşmeyen AP ve
artmayan Brier/log loss gerektirir. Geç eşik kontrolü olasılıkları değiştirmez; dolayısıyla
AP, Brier ve log loss referansla aynıdır. Eşik ayarı tek başına sıralama iyileşmesi değildir.

## Yorum

2022'de ayrılmış yöntem precision'ı 0.039573'ten 0.070566'ya yükseltip FP'yi 10072'den
5308'e indirirken recall 0.957245 kalır. Ancak geç eşik kontrolü aynı recall ile zaten
0.070197 precision ve 5338 FP üretir. O yıl gözlenen kazancın çoğu, olasılık öğrenimiyle
eşik seçimini ayırmadan yeniden elde edilir. Ayrılmış olasılıkların Brier/log loss
değerleri daha kötü, AP biraz daha düşüktür; dolayısıyla o yıl da tüm kabul kontrolünü geçmez.

2014 ve 2015'te precision artar fakat recall sırasıyla 0.844156 ve 0.946863'e, gereken
hedefin altına düşer. 2023'te recall 0.884763'ten 0.956466'ya çıkarken precision
0.103397'den 0.064247'ye düşer ve FP 5992'den 10880'e çıkar. Geç eşik kontrolü aynı
recall'a 10501 FP ile ulaşır; bu, ayrılmış yöntemden daha azdır. Dolayısıyla denge yıla
göre değişir; dönemleri ayırmak tutarlı bir precision çözümü değildir. Hiçbir pozitif
değerlendirme yılı tüm kabul kontrollerini geçmez.

## Eşleştirilmiş koşullu belirsizlik

| year | control | metric | lower | upper | valid_draws |
| --- | --- | --- | --- | --- | --- |
| 2014 | baseline_full_year | precision | 0.053878 | 0.122584 | 1000 |
| 2014 | baseline_full_year | recall | -0.169959 | -0.057813 | 1000 |
| 2014 | baseline_full_year | fp | -8377.075000 | -5600.375000 | 1000 |
| 2014 | late_threshold_control | precision | -0.000056 | 0.002342 | 1000 |
| 2014 | late_threshold_control | recall | -0.011351 | -0.000495 | 1000 |
| 2014 | late_threshold_control | fp | -128.000000 | -56.975000 | 1000 |
| 2015 | baseline_full_year | precision | 0.054081 | 0.122242 | 1000 |
| 2015 | baseline_full_year | recall | -0.110954 | -0.012522 | 1000 |
| 2015 | baseline_full_year | fp | -7524.175000 | -4545.675000 | 1000 |
| 2015 | late_threshold_control | precision | -0.007918 | -0.003062 | 1000 |
| 2015 | late_threshold_control | recall | 0.000000 | 0.005406 | 1000 |
| 2015 | late_threshold_control | fp | 128.000000 | 265.025000 | 1000 |
| 2016 | baseline_full_year | precision | -0.003562 | 0.000000 | 1000 |
| 2016 | baseline_full_year | recall | 0.000000 | 0.000000 | 973 |
| 2016 | baseline_full_year | fp | 33.000000 | 99.000000 | 1000 |
| 2016 | late_threshold_control | precision | 0.000000 | 0.000727 | 1000 |
| 2016 | late_threshold_control | recall | 0.000000 | 0.000000 | 973 |
| 2016 | late_threshold_control | fp | -23.000000 | -5.000000 | 1000 |
| 2017 | baseline_full_year | precision | -0.069991 | 0.000000 | 1000 |
| 2017 | baseline_full_year | recall | 0.000000 | 0.061538 | 949 |
| 2017 | baseline_full_year | fp | 171.000000 | 465.100000 | 1000 |
| 2017 | late_threshold_control | precision | 0.000000 | 0.011735 | 1000 |
| 2017 | late_threshold_control | recall | 0.000000 | 0.000000 | 949 |
| 2017 | late_threshold_control | fp | -103.025000 | -32.000000 | 1000 |
| 2018 | baseline_full_year | precision | undefined | undefined | 0 |
| 2018 | baseline_full_year | recall | undefined | undefined | 0 |
| 2018 | baseline_full_year | fp | -806.050000 | -46.925000 | 1000 |
| 2018 | late_threshold_control | precision | undefined | undefined | 0 |
| 2018 | late_threshold_control | recall | undefined | undefined | 0 |
| 2018 | late_threshold_control | fp | -3.000000 | 0.000000 | 1000 |
| 2022 | baseline_full_year | precision | 0.014695 | 0.050292 | 1000 |
| 2022 | baseline_full_year | recall | -0.093797 | 0.000000 | 1000 |
| 2022 | baseline_full_year | fp | -6038.000000 | -3731.950000 | 1000 |
| 2022 | late_threshold_control | precision | 0.000163 | 0.000662 | 1000 |
| 2022 | late_threshold_control | recall | 0.000000 | 0.000000 | 1000 |
| 2022 | late_threshold_control | fp | -45.000000 | -17.000000 | 1000 |
| 2023 | baseline_full_year | precision | -0.058085 | -0.023437 | 1000 |
| 2023 | baseline_full_year | recall | 0.021894 | 0.133131 | 1000 |
| 2023 | baseline_full_year | fp | 3863.950000 | 5995.200000 | 1000 |
| 2023 | late_threshold_control | precision | -0.003351 | -0.001268 | 1000 |
| 2023 | late_threshold_control | recall | 0.000000 | 0.000000 | 1000 |
| 2023 | late_threshold_control | fp | 273.975000 | 498.000000 | 1000 |

Aralıklar ayrılmış yöntem eksi belirtilen kontroldür; yıl başına 24 tohumla eşleştirilmiş
bütün HARP'ları örnekleyen 1000 bootstrap tekrarı kullanır. İki kola aynı örneklenmiş
bölgeler katkı yapar. Öğrenilmiş sınıflandırıcılar, kalibratörler ve eşikler sabittir;
öğrenim ve geçmiş seçim belirsizliği dahil değildir. Tanımsız precision/recall tekrarları
`valid_draws` ile izlenir; pozitif olmayan yılda geçerli recall tekrarı yoktur. Sıfırı
içeren aralık, o aralık düzeyinde yönlü değişimi göstermez. Yıllar geçmiş eğitimi paylaşır
ve bağımsız tekrarlar değildir.

## Sınırlamalar ve sonraki karar

Bu, önceki hataların yönlendirdiği uyarlamalı, geçmişe dönük geliştirmedir; yeni bağımsız
test değildir. Zamansal değişimlerin fiziksel nedenini belirlemez. Kalibrasyonda daha
az pozitif örnek, öğrenilmiş olasılık dönüşümünü ve seçilen eşiği kararsızlaştırabilir.
Sonuç, tüm kronolojik kalibrasyon kurallarını değil, bu sabit yarım yıllık düzeni genel
model değişikliği olarak eler. Bu sonuçlar üzerinde bölme tarihini tekrar tekrar
ayarlayarak veya recall hedefini düşürerek başarı ilan edilmemelidir.

Yeni kural aramasından önce, kalibrasyon dönemi skor dağılımları ve pozitif bölge sayıları
yıllar arasında incelenmeli; ardından aday, daha erken iç kronolojik bölümlerde
sabitlenmelidir. Pratik kural hem recall'ı hem yanlış alarm yükünü farklı dönemlerde
göstermelidir; kalibrasyon tek başına pozitif ve negatiflerin daha iyi ayrılmasını
garanti etmez. Bu takip incelemesinin veya ek eğitimin burada yapıldığı iddia edilmez.
Ayrılmış test geliştirme dışında kalır.

## Yeniden üretim

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_calibration_periods.py \
  --protocol config/calibration-periods-v1.json --output artifacts/calibration_periods_20261030_r1
.venv/bin/python scripts/report_calibration_periods.py --source artifacts/calibration_periods_20261030_r1 --report-name calibration-periods-20261030
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_calibration-periods-20261030
```

Yeni çıktı dizinleri ve rapor adları kullanın; sabit kanıtın üzerine yazmayın.
İki tam belge sürümünü gözden geçirip kaynak özetini ve bağlantıları `docs/reports.json`
ve `docs/reports.md` dosyalarına kaydedin; ardından yeni HTML dizinine yayımlayın.
Kalibratörler, tahminler, eşikler ve HTML yerel, Git dışında çıktılar olarak kalır.
Kaynak, kod ve çıktı özetleri deney raporunda kayıtlıdır.

| source | SHA-256 |
| --- | --- |
| artifacts/calibration_periods_20261030_r1/report.json | b6b7a18f4e0eac9a10396eb46451b10eb82beb8cc7140f62e188bc581573e527 |
| artifacts/calibration_periods_20261030_r1/metrics.csv | 92e493f451c49edf8b6761fa1f49198359a84b73321e922c158fbba3d2e526ea |

