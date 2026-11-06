# Yıllık TCN karşılaştırması: performans, kalibrasyon ve belirsizlik

**TAMAMLANMIŞ DENEYİN SON DEĞERLENDİRMESİ.** Dahil edilen yıllar: 2014, 2015, 2016, 2017, 2018, 2022, 2023. Bu kayıtta bulunmayan uygun dönemler:
none. Bu, tamamlanmış çıktıların sabit karşılaştırmasıdır; canlı dashboard değildir.
Mevcut model kullanılmaya devam eder; yeni model alınmadı ve 2024–2025 testi kapalı kaldı.

## Kapsam ve kontroller

| year | status | rows | positives | reason |
| --- | --- | --- | --- | --- |
| 2014 | included | 75228 | 2310 | undefined |
| 2015 | included | 69138 | 1355 | undefined |
| 2016 | included | 42987 | 181 | undefined |
| 2017 | included | 19529 | 253 | undefined |
| 2018 | included | 7799 | 0 | undefined |
| 2019 | skipped | 4919 | 0 | Training/calibration lacks both classes: ['calibration'] |
| 2020 | skipped | 9813 | 0 | Training/calibration lacks both classes: ['calibration'] |
| 2021 | skipped | 28125 | 204 | Training/calibration lacks both classes: ['calibration'] |
| 2022 | included | 50756 | 421 | undefined |
| 2023 | included | 60366 | 781 | undefined |


Özgün sabit ayrıma göre yedi yıllık dönem uygundur. Önceki kalibrasyon örneklemlerinde
pozitif bulunmadığından özgün 2019–2021 bölümleri atlanır. Pozitif olmayan 2018 değerlendirmesi
korunur: recall ve AP tanımsızdır; yanlış alarm ve olasılık kayıpları ölçülebilir.
Sıfır-pozitif yıllar dahil eksik uygun dönemler, tamamlanmış tüm-yıllar koşulunu engeller.
Son değerlendirme modu, tüm uygun yıllık çıktılar ve son deney kaydı oluşmadan çalışmaz.

Dört kol raporlanır: özgün 96 özet özellikli birleşim (`baseline`), daha kısa eğitimli
referansı (`short_training`), ham sıralı TCN (`chronological`) ve iç adımları karıştırılmış
aynı mimari (`shuffled_interior`). Kısa eğitim referansı farklı sınıflandırıcı geçmişi
kullanır; ayrı bir karşılaştırmadır. İki sinir ağı kolu aynı eğitim/kalibrasyon/değerlendirme
satırlarını ve 24/42/97 tohumlarını kullanır. Ham sigmoid olasılıkları eşit ortalandıktan
sonra sigmoid kalibrasyonu yapılır. Tekil tohum sonuçları da korunur; kazanan tohum seçilmez.
Dashboard'ın Historical replay alanı Deney 1'i, Experiment progress sekmesi bu V2 eğitim
kayıtlarını gösterir.

Sabit çıktı hash değerleri doğrulanır; tohumlar dahil her kayıtlı metrik, saklanan tahmin
ve eşiklerden yeniden hesaplanır. Eşikler önceki kalibrasyon yılından değiştirilmeden
aktarılır. Bu rapor eğitim, yeniden kalibrasyon, eşik ayarı veya dışlama yapmaz. Dış yıllar
geliştirmede tekrar tekrar incelendiğinden sonuçlar uyarlamalı geçmiş değerlendirmesidir;
bağımsız son test değildir.

## Çalışma noktasındaki performans

| year | arm | n | positives | threshold | tp | fp | fn | tn | precision | recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | chronological | 75228 | 2310 | 0.003306 | 2184 | 19639 | 126 | 53279 | 0.100078 | 0.945455 |
| 2014 | shuffled_interior | 75228 | 2310 | 0.002317 | 2172 | 21645 | 138 | 51273 | 0.091195 | 0.940260 |
| 2014 | baseline | 75228 | 2310 | 0.011475 | 2184 | 13886 | 126 | 59032 | 0.135905 | 0.945455 |
| 2014 | short_training | 75228 | 2310 | 0.010974 | 2200 | 15543 | 110 | 57375 | 0.123993 | 0.952381 |
| 2015 | chronological | 69138 | 1355 | 0.014138 | 1316 | 11137 | 39 | 56646 | 0.105677 | 0.971218 |
| 2015 | shuffled_interior | 69138 | 1355 | 0.010597 | 1320 | 12168 | 35 | 55615 | 0.097865 | 0.974170 |
| 2015 | baseline | 69138 | 1355 | 0.018839 | 1346 | 11453 | 9 | 56330 | 0.105164 | 0.993358 |
| 2015 | short_training | 69138 | 1355 | 0.020398 | 1347 | 10848 | 8 | 56935 | 0.110455 | 0.994096 |
| 2016 | chronological | 42987 | 181 | 0.008422 | 173 | 6385 | 8 | 36421 | 0.026380 | 0.955801 |
| 2016 | shuffled_interior | 42987 | 181 | 0.013181 | 178 | 6440 | 3 | 36366 | 0.026896 | 0.983425 |
| 2016 | baseline | 42987 | 181 | 0.030831 | 176 | 2289 | 5 | 40517 | 0.071400 | 0.972376 |
| 2016 | short_training | 42987 | 181 | 0.032370 | 176 | 2137 | 5 | 40669 | 0.076092 | 0.972376 |
| 2017 | chronological | 19529 | 253 | 0.017731 | 237 | 1538 | 16 | 17738 | 0.133521 | 0.936759 |
| 2017 | shuffled_interior | 19529 | 253 | 0.019844 | 228 | 1390 | 25 | 17886 | 0.140915 | 0.901186 |
| 2017 | baseline | 19529 | 253 | 0.012000 | 237 | 1287 | 16 | 17989 | 0.155512 | 0.936759 |
| 2017 | short_training | 19529 | 253 | 0.014550 | 239 | 1238 | 14 | 18038 | 0.161814 | 0.944664 |
| 2018 | chronological | 7799 | 0 | 0.004784 | 0 | 518 | 0 | 7281 | 0.000000 | undefined |
| 2018 | shuffled_interior | 7799 | 0 | 0.000605 | 0 | 896 | 0 | 6903 | 0.000000 | undefined |
| 2018 | baseline | 7799 | 0 | 0.004351 | 0 | 359 | 0 | 7440 | 0.000000 | undefined |
| 2018 | short_training | 7799 | 0 | 0.004511 | 0 | 351 | 0 | 7448 | 0.000000 | undefined |
| 2022 | chronological | 50756 | 421 | 0.006156 | 402 | 12971 | 19 | 37364 | 0.030061 | 0.954869 |
| 2022 | shuffled_interior | 50756 | 421 | 0.000749 | 421 | 21871 | 0 | 28464 | 0.018886 | 1.000000 |
| 2022 | baseline | 50756 | 421 | 0.008994 | 415 | 10072 | 6 | 40263 | 0.039573 | 0.985748 |
| 2022 | short_training | 50756 | 421 | 0.009790 | 414 | 9592 | 7 | 40743 | 0.041375 | 0.983373 |
| 2023 | chronological | 60366 | 781 | 0.004442 | 717 | 12483 | 64 | 47102 | 0.054318 | 0.918054 |
| 2023 | shuffled_interior | 60366 | 781 | 0.003842 | 705 | 14375 | 76 | 45210 | 0.046751 | 0.902689 |
| 2023 | baseline | 60366 | 781 | 0.018203 | 691 | 5992 | 90 | 53593 | 0.103397 | 0.884763 |
| 2023 | short_training | 60366 | 781 | 0.018942 | 695 | 5840 | 86 | 53745 | 0.106350 | 0.889885 |


Oranlar 0–1 ölçeğindedir. Precision TP/(TP+FP), recall TP/(TP+FN), FPR FP/(FP+TN)'dir.
TP, FP, FN ve TN bağımsız patlama veya bildirimleri değil, örtüşen saatlik tahmin
pencerelerini sayar. Adaylar kendi kalibrasyon eşiklerini korur; karşılaştırmalar eşit
recall'da değildir. Recall 0.95 altındayken precision artışı hedefi karşılamaz.

## Sıralama, olasılık skorları ve accuracy

| year | arm | accuracy | always_quiet_accuracy | balanced_accuracy | f1 | tss | false_positive_rate | average_precision | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | chronological | 0.737265 | 0.969293 | 0.838062 | 0.180997 | 0.676125 | 0.269330 | 0.421566 | 0.022812 | 0.089042 |
| 2014 | shuffled_interior | 0.710440 | 0.969293 | 0.821710 | 0.166265 | 0.643419 | 0.296840 | 0.405285 | 0.023068 | 0.090261 |
| 2014 | baseline | 0.813740 | 0.969293 | 0.877511 | 0.237650 | 0.755021 | 0.190433 | 0.507930 | 0.020661 | 0.076538 |
| 2014 | short_training | 0.791926 | 0.969293 | 0.869612 | 0.219419 | 0.739224 | 0.213157 | 0.483201 | 0.020988 | 0.078063 |
| 2015 | chronological | 0.838352 | 0.980402 | 0.903457 | 0.190614 | 0.806914 | 0.164304 | 0.461100 | 0.014098 | 0.052287 |
| 2015 | shuffled_interior | 0.823498 | 0.980402 | 0.897328 | 0.177862 | 0.794656 | 0.179514 | 0.433877 | 0.014456 | 0.053142 |
| 2015 | baseline | 0.834216 | 0.980402 | 0.912196 | 0.190194 | 0.824392 | 0.168966 | 0.492441 | 0.013564 | 0.047847 |
| 2015 | short_training | 0.842981 | 0.980402 | 0.917028 | 0.198819 | 0.834056 | 0.160040 | 0.488445 | 0.013474 | 0.047741 |
| 2016 | chronological | 0.851281 | 0.995789 | 0.903320 | 0.051343 | 0.806640 | 0.149161 | 0.146877 | 0.004133 | 0.019767 |
| 2016 | shuffled_interior | 0.850117 | 0.995789 | 0.916490 | 0.052361 | 0.832979 | 0.150446 | 0.187088 | 0.004151 | 0.019610 |
| 2016 | baseline | 0.946635 | 0.995789 | 0.959451 | 0.133031 | 0.918902 | 0.053474 | 0.366443 | 0.003263 | 0.014523 |
| 2016 | short_training | 0.950171 | 0.995789 | 0.961226 | 0.141139 | 0.922453 | 0.049923 | 0.433388 | 0.003128 | 0.013935 |
| 2017 | chronological | 0.920426 | 0.987045 | 0.928485 | 0.233728 | 0.856971 | 0.079788 | 0.617747 | 0.008032 | 0.030570 |
| 2017 | shuffled_interior | 0.927544 | 0.987045 | 0.914538 | 0.243720 | 0.829075 | 0.072110 | 0.638564 | 0.007435 | 0.031611 |
| 2017 | baseline | 0.933279 | 0.987045 | 0.934996 | 0.266742 | 0.869992 | 0.066767 | 0.811694 | 0.004907 | 0.020488 |
| 2017 | short_training | 0.935890 | 0.987045 | 0.940220 | 0.276301 | 0.880439 | 0.064225 | 0.806978 | 0.004954 | 0.020646 |
| 2018 | chronological | 0.933581 | 1.000000 | undefined | 0.000000 | undefined | 0.066419 | undefined | 0.000136 | 0.002176 |
| 2018 | shuffled_interior | 0.885113 | 1.000000 | undefined | 0.000000 | undefined | 0.114887 | undefined | 0.000141 | 0.002111 |
| 2018 | baseline | 0.953968 | 1.000000 | undefined | 0.000000 | undefined | 0.046032 | undefined | 0.000012 | 0.000791 |
| 2018 | short_training | 0.954994 | 1.000000 | undefined | 0.000000 | undefined | 0.045006 | undefined | 0.000012 | 0.000796 |
| 2022 | chronological | 0.744070 | 0.991705 | 0.848588 | 0.058286 | 0.697176 | 0.257693 | 0.159519 | 0.007562 | 0.033393 |
| 2022 | shuffled_interior | 0.569095 | 0.991705 | 0.782746 | 0.037071 | 0.565491 | 0.434509 | 0.130510 | 0.007747 | 0.034871 |
| 2022 | baseline | 0.801442 | 0.991705 | 0.892824 | 0.076091 | 0.785649 | 0.200099 | 0.280023 | 0.007064 | 0.029196 |
| 2022 | short_training | 0.810880 | 0.991705 | 0.896405 | 0.079409 | 0.792810 | 0.190563 | 0.284225 | 0.007028 | 0.029089 |
| 2023 | chronological | 0.792151 | 0.987062 | 0.854277 | 0.102568 | 0.708555 | 0.209499 | 0.163628 | 0.011627 | 0.051924 |
| 2023 | shuffled_interior | 0.760610 | 0.987062 | 0.830718 | 0.088897 | 0.661437 | 0.241252 | 0.199684 | 0.011628 | 0.051994 |
| 2023 | baseline | 0.899248 | 0.987062 | 0.892100 | 0.185155 | 0.784201 | 0.100562 | 0.220619 | 0.011195 | 0.043996 |
| 2023 | short_training | 0.901832 | 0.987062 | 0.895937 | 0.189995 | 0.791874 | 0.098011 | 0.229153 | 0.011149 | 0.043730 |


Accuracy (TP+TN)/n'dir; balanced accuracy, recall ile özgüllüğün ortalamasıdır; F1,
precision ve recall'un harmonik ortalamasıdır; TSS recall eksi FPR'dir. Sürekli olay yok
diyen modelin accuracy değeri, yüksek accuracy'nin tek başına nadir olay başarısı olmadığını
gösterir. AP farklı çalışma noktaları boyunca sıralamayı ölçer; belirli alarm eşiğine
bağlı değildir. Brier ortalama karesel olasılık hatasıdır; log loss emin yanlış tahminleri
cezalandırır. İkisi de doğru olasılıklara yönelten skorlardır; kalibrasyonu tek başına
ayırmak yerine kalibrasyon ve ayırt etmeyi birlikte içerir.

Dahil edilen 7 yılda kronolojik AP, AP tanımlı 6 yılın 6 tanesinde referanstan
düşüktür; Brier 7 yılda, log loss 7 yılda daha yüksektir. Kronolojik AP,
karıştırılmış AP'den karşılaştırılabilir 6 AP yılının 3 tanesinde yüksektir. Bu, zaman sırasının kararlı faydasını göstermez;
kontrol eksiklik maskelerinin sırasını da değiştirdiği için fiziksel manyetik gelişimi
erişilebilirlik örüntülerinden ayırmaz. Ortak ortalamayla zayıf yıllar gizlenmez.
Tüm ölçülen alanlar ve tekil tohum satırları metrics.csv içinde korunur.

## Açık kabul koşulları ve eksik kapsam

| candidate | control | required_positive_years | comparable_years | missing_eligible_years | precision_win_count | recall_met_count | fp_reduced_count | primary_met_count | full_met_count | all_year_full |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chronological | baseline | 6 | 6 | none | 1 | 3 | 1 | 1 | 0 | 0 |
| shuffled_interior | baseline | 6 | 6 | none | 0 | 3 | 0 | 0 | 0 | 0 |
| chronological | shuffled_interior | 6 | 6 | none | 4 | 3 | 5 | 2 | 2 | 0 |
| chronological | short_training | 6 | 6 | none | 0 | 3 | 0 | 0 | 0 | 0 |


Ortak birincil kontrol, daha yüksek precision, recall >=0.95 ve daha az FP'yi birlikte
ister. Tam kontrol ayrıca belirtilen kontrole göre düşmeyen AP ve artmayan Brier/log loss
ister. Nokta kazançları ve aynı anda geçilen koşullar ayrı sayılır. Tüm-yıllar başarısı,
eksik aday olmadan tüm gerekli pozitif yılları ve özgün uygun dönemleri de gerektirir.
Bunlar sabit tasarımın uygulama karşılaştırma kurallarıdır; evrensel kabul edilebilir metrik
aralıkları veya istatistiksel anlamlılık kanıtı değildir. Gelecekte eksiksiz karşılaştırma
geçse bile otomatik model değişikliği yapılmaz.

## Koşullu eşleştirilmiş belirsizlik

Kronolojik eksi referans aralıkları:

| year | metric | estimate | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | precision | -0.035828 | -0.050744 | -0.023858 | 1000 | 0 |
| 2014 | recall | 0.000000 | -0.038392 | 0.036012 | 1000 | 0 |
| 2014 | fp | 5753.000000 | 4488.800000 | 7035.675000 | 1000 | 0 |
| 2014 | brier | 0.002151 | 0.000317 | 0.004329 | 1000 | 0 |
| 2014 | log_loss | 0.012504 | 0.005873 | 0.020113 | 1000 | 0 |
| 2015 | precision | 0.000513 | -0.007348 | 0.008657 | 1000 | 0 |
| 2015 | recall | -0.022140 | -0.061816 | -0.002144 | 1000 | 0 |
| 2015 | fp | -316.000000 | -1277.425000 | 554.250000 | 1000 | 0 |
| 2015 | brier | 0.000534 | -0.000364 | 0.001431 | 1000 | 0 |
| 2015 | log_loss | 0.004440 | 0.000929 | 0.008508 | 1000 | 0 |
| 2016 | precision | -0.045020 | -0.082771 | 0.000000 | 1000 | 0 |
| 2016 | recall | -0.016575 | -0.136364 | 0.000000 | 973 | 27 |
| 2016 | fp | 4096.000000 | 3057.900000 | 5347.175000 | 1000 | 0 |
| 2016 | brier | 0.000870 | 0.000344 | 0.001533 | 1000 | 0 |
| 2016 | log_loss | 0.005244 | 0.002670 | 0.008084 | 1000 | 0 |
| 2017 | precision | -0.021991 | -0.101752 | 0.010301 | 1000 | 0 |
| 2017 | recall | 0.000000 | 0.000000 | 0.000000 | 949 | 51 |
| 2017 | fp | 251.000000 | -160.025000 | 668.100000 | 1000 | 0 |
| 2017 | brier | 0.003126 | -0.000092 | 0.008754 | 1000 | 0 |
| 2017 | log_loss | 0.010082 | 0.000128 | 0.026375 | 1000 | 0 |
| 2018 | precision | 0.000000 | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | recall | undefined | undefined | undefined | 0 | 1000 |
| 2018 | fp | 159.000000 | 57.950000 | 278.000000 | 1000 | 0 |
| 2018 | brier | 0.000124 | 0.000009 | 0.000284 | 1000 | 0 |
| 2018 | log_loss | 0.001385 | 0.000193 | 0.002890 | 1000 | 0 |
| 2022 | precision | -0.009512 | -0.016179 | -0.004612 | 1000 | 0 |
| 2022 | recall | -0.030879 | -0.098241 | 0.000000 | 1000 | 0 |
| 2022 | fp | 2899.000000 | 2038.925000 | 3854.275000 | 1000 | 0 |
| 2022 | brier | 0.000498 | -0.000154 | 0.001341 | 1000 | 0 |
| 2022 | log_loss | 0.004197 | 0.001227 | 0.007654 | 1000 | 0 |
| 2023 | precision | -0.049078 | -0.072364 | -0.030691 | 1000 | 0 |
| 2023 | recall | 0.033291 | -0.021202 | 0.090807 | 1000 | 0 |
| 2023 | fp | 6491.000000 | 5200.800000 | 7803.500000 | 1000 | 0 |
| 2023 | brier | 0.000432 | -0.000371 | 0.001317 | 1000 | 0 |
| 2023 | log_loss | 0.007928 | 0.002001 | 0.015502 | 1000 | 0 |


Kronolojik eksi karıştırılmış sıra aralıkları:

| year | metric | estimate | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | precision | 0.008883 | 0.005436 | 0.012968 | 1000 | 0 |
| 2014 | recall | 0.005195 | -0.008779 | 0.020001 | 1000 | 0 |
| 2014 | fp | -2006.000000 | -2616.050000 | -1425.775000 | 1000 | 0 |
| 2014 | brier | -0.000255 | -0.001452 | 0.000756 | 1000 | 0 |
| 2014 | log_loss | -0.001219 | -0.005446 | 0.002716 | 1000 | 0 |
| 2015 | precision | 0.007813 | 0.003651 | 0.012135 | 1000 | 0 |
| 2015 | recall | -0.002952 | -0.011691 | 0.003910 | 1000 | 0 |
| 2015 | fp | -1031.000000 | -1482.125000 | -582.000000 | 1000 | 0 |
| 2015 | brier | -0.000358 | -0.001101 | 0.000201 | 1000 | 0 |
| 2015 | log_loss | -0.000855 | -0.002921 | 0.001041 | 1000 | 0 |
| 2016 | precision | -0.000516 | -0.003177 | 0.001729 | 1000 | 0 |
| 2016 | recall | -0.027624 | -0.227273 | 0.000000 | 973 | 27 |
| 2016 | fp | -55.000000 | -444.025000 | 371.200000 | 1000 | 0 |
| 2016 | brier | -0.000018 | -0.000311 | 0.000250 | 1000 | 0 |
| 2016 | log_loss | 0.000157 | -0.001601 | 0.002589 | 1000 | 0 |
| 2017 | precision | -0.007394 | -0.031138 | 0.006230 | 1000 | 0 |
| 2017 | recall | 0.035573 | 0.000000 | 0.092308 | 949 | 51 |
| 2017 | fp | 148.000000 | -3.000000 | 337.100000 | 1000 | 0 |
| 2017 | brier | 0.000597 | -0.000405 | 0.002316 | 1000 | 0 |
| 2017 | log_loss | -0.001041 | -0.005447 | 0.003566 | 1000 | 0 |
| 2018 | precision | 0.000000 | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | recall | undefined | undefined | undefined | 0 | 1000 |
| 2018 | fp | -378.000000 | -639.125000 | -145.975000 | 1000 | 0 |
| 2018 | brier | -0.000006 | -0.000025 | 0.000012 | 1000 | 0 |
| 2018 | log_loss | 0.000065 | -0.000126 | 0.000303 | 1000 | 0 |
| 2022 | precision | 0.011175 | 0.004663 | 0.019026 | 1000 | 0 |
| 2022 | recall | -0.045131 | -0.151016 | 0.000000 | 1000 | 0 |
| 2022 | fp | -8900.000000 | -10438.425000 | -7579.825000 | 1000 | 0 |
| 2022 | brier | -0.000185 | -0.000589 | 0.000148 | 1000 | 0 |
| 2022 | log_loss | -0.001478 | -0.004244 | 0.000828 | 1000 | 0 |
| 2023 | precision | 0.007568 | 0.004562 | 0.011710 | 1000 | 0 |
| 2023 | recall | 0.015365 | -0.004719 | 0.049052 | 1000 | 0 |
| 2023 | fp | -1892.000000 | -2427.025000 | -1360.900000 | 1000 | 0 |
| 2023 | brier | -0.000001 | -0.000262 | 0.000261 | 1000 | 0 |
| 2023 | log_loss | -0.000070 | -0.002304 | 0.002691 | 1000 | 0 |


Aralıklar 24 tohumuyla 1000 eşleştirilmiş tam-HARP bootstrap çekilişinin yüzde 95 yüzdelik
aralıklarıdır. Aynı örneklenen bölgeler ve tüm pencereleri iki kola da katkı verir.
Mevcut precision/recall/FP aralıkları korunur; eşleştirilmiş Brier/log-loss fark aralıkları
sabit olasılıklardan yeni hesaplanır. Pozitif precision/recall farkı aday lehinedir;
negatif FP/Brier/log-loss farkı aday lehinedir. Sıfırı kesen veya sıfıra değen aralık,
o aralık düzeyinde yönlü fark göstermez. `valid_draws` ve `undefined_draws`, precision/recall
hesaplanamayan örneklemeleri görünür tutar. AP nokta tahmini olarak verilir; burada
bootstrap AP aralığı yoktur.

Modeller, kalibratörler, eşikler ve özgün HARP kimlikleri sabittir. Aralıklar yeniden
eğitim, kalibrasyon öğrenimi ve tarihsel seçim belirsizliğini içermez. Komşu yıllar eğitim
geçmişini paylaşır; çoklu karşılaştırma düzeltmesi yapılmaz. HARP örneklemesi bölge içi
pencere bağımlılığını ele alır; katalog bölgelerinin birbirinden bağımsızlığını kanıtlamaz.
2015’in referansa göre küçük precision kazancının aralığı sıfırı kapsar; güvenilir iyileşme olarak kurulmuş değildir. Yıl ve alt grup sonuçları evrensel nedensel iddia gibi okunmamalıdır.

## Olasılık güvenilirliği

Aşağıda her referans/kronolojik çifti için örnek ve bölge desteğini göstermek üzere en
çok pencere içeren grup verilir. Bu seçim yalnızca gösterim içindir, model kuralı değildir.
Tüm gruplar ve dört kol reliability.csv içinde korunur.

| year | arm | left | right | n | regions | positive_regions | mean_probability | observed_rate | lower | upper | valid_draws |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline | 0.000000 | 0.005000 | 53274 | 617 | 8 | 0.000660 | 0.001408 | 0.000446 | 0.002634 | 1000 |
| 2014 | chronological | 0.000000 | 0.005000 | 54866 | 625 | 12 | 0.000529 | 0.002515 | 0.000907 | 0.004676 | 1000 |
| 2015 | baseline | 0.000000 | 0.005000 | 47839 | 572 | 0 | 0.000823 | 0.000000 | 0.000000 | 0.000000 | 1000 |
| 2015 | chronological | 0.000000 | 0.005000 | 53266 | 596 | 1 | 0.000952 | 0.000413 | 0.000000 | 0.001605 | 1000 |
| 2016 | baseline | 0.000000 | 0.005000 | 34457 | 356 | 0 | 0.000593 | 0.000000 | 0.000000 | 0.000000 | 1000 |
| 2016 | chronological | 0.000000 | 0.005000 | 35548 | 355 | 1 | 0.000433 | 0.000113 | 0.000000 | 0.000352 | 1000 |
| 2017 | baseline | 0.000000 | 0.005000 | 17509 | 163 | 2 | 0.000373 | 0.000685 | 0.000000 | 0.001926 | 1000 |
| 2017 | chronological | 0.000000 | 0.005000 | 16747 | 163 | 2 | 0.000251 | 0.000776 | 0.000000 | 0.002210 | 1000 |
| 2018 | baseline | 0.000000 | 0.005000 | 7471 | 74 | 0 | 0.000222 | 0.000000 | 0.000000 | 0.000000 | 1000 |
| 2018 | chronological | 0.000000 | 0.005000 | 7292 | 74 | 0 | 0.000136 | 0.000000 | 0.000000 | 0.000000 | 1000 |
| 2022 | baseline | 0.000000 | 0.005000 | 36707 | 510 | 1 | 0.000938 | 0.000027 | 0.000000 | 0.000085 | 1000 |
| 2022 | chronological | 0.000000 | 0.005000 | 36636 | 520 | 2 | 0.000461 | 0.000464 | 0.000000 | 0.001324 | 1000 |
| 2023 | baseline | 0.000000 | 0.005000 | 47867 | 690 | 3 | 0.000520 | 0.000689 | 0.000000 | 0.001851 | 1000 |
| 2023 | chronological | 0.000000 | 0.005000 | 47593 | 686 | 6 | 0.000281 | 0.001345 | 0.000243 | 0.002896 | 1000 |


Grup sınırları config/temporal-evaluation-report-v1.json içinde 0–1 arasında sabittir;
düşük olasılıklarda daha ince ayrım vardır. Aralıklar sağdan kapalıdır, sıfır ilk gruptadır.
Dolu gruplarda mean_probability ile observed_rate karşılaştırılır. Gözlenen eksi tahmin
farkı CSV'ye kaydedilir. Gözlenen oran sınırları, olasılık ve üyeliği sabit tutarak tam
HARP'ları yeniden örnekler. Boş gruplar tanımsız kalır; seyrek gruplarda az geçerli çekiliş
veya az pozitif bölge olabilir. Hiç olay gözlenmeyen gruptaki 0–0 oran aralığı, gelecekteki
patlama olasılığının sıfır olacağını garanti etmez.

Yerel bağımsız `reliability.png` görseli referans ve kronolojik kolların tüm dolu gruplarını
tam 0–1 aralığında gösterir. Desteği düşük grupları gizlemez ve belirsizlik çubuklarını
çizmez; sayısal destek ve koşullu sınırlar CSV ve tablodadır. Güvenilirlik grafikleri
olasılık uyumunu inceler, tahminleri değiştirmez.

## Tohum değişkenliği

| year | arm | seeds | precision_min | precision_max | recall_min | recall_max | fp_min | fp_max | average_precision_min | average_precision_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | chronological | 3 | 0.030707 | 0.093915 | 0.946753 | 1.000000 | 21100.000000 | 72918.000000 | 0.336176 | 0.419672 |
| 2014 | shuffled_interior | 3 | 0.030707 | 0.096875 | 0.916450 | 1.000000 | 19736.000000 | 72918.000000 | 0.360440 | 0.381745 |
| 2015 | chronological | 3 | 0.089060 | 0.097409 | 0.971218 | 0.980074 | 12194.000000 | 13573.000000 | 0.389913 | 0.442830 |
| 2015 | shuffled_interior | 3 | 0.081413 | 0.100785 | 0.976384 | 0.977860 | 11804.000000 | 14950.000000 | 0.415244 | 0.422690 |
| 2016 | chronological | 3 | 0.020366 | 0.028776 | 0.756906 | 0.955801 | 5516.000000 | 6590.000000 | 0.069005 | 0.264775 |
| 2016 | shuffled_interior | 3 | 0.021698 | 0.023874 | 0.944751 | 1.000000 | 7237.000000 | 7710.000000 | 0.144580 | 0.183704 |
| 2017 | chronological | 3 | 0.055427 | 0.112004 | 0.936759 | 0.948617 | 1879.000000 | 4090.000000 | 0.471590 | 0.695391 |
| 2017 | shuffled_interior | 3 | 0.079147 | 0.109240 | 0.865613 | 0.948617 | 1851.000000 | 2571.000000 | 0.606622 | 0.664757 |
| 2018 | chronological | 3 | 0.000000 | 0.000000 | undefined | undefined | 349.000000 | 712.000000 | undefined | undefined |
| 2018 | shuffled_interior | 3 | 0.000000 | 0.000000 | undefined | undefined | 695.000000 | 1090.000000 | undefined | undefined |
| 2022 | chronological | 3 | 0.008295 | 0.032575 | 0.961995 | 1.000000 | 12028.000000 | 50335.000000 | 0.099633 | 0.169201 |
| 2022 | shuffled_interior | 3 | 0.008295 | 0.021327 | 1.000000 | 1.000000 | 19319.000000 | 50335.000000 | 0.102346 | 0.168853 |
| 2023 | chronological | 3 | 0.042828 | 0.057343 | 0.898848 | 0.921895 | 11836.000000 | 15868.000000 | 0.148781 | 0.164079 |
| 2023 | shuffled_interior | 3 | 0.039973 | 0.053755 | 0.896287 | 0.919334 | 12322.000000 | 17244.000000 | 0.101110 | 0.191521 |


Tanısal sonuç için her tohumun yalnızca kalibrasyonda seçilmiş kendi eşiği vardır. Min/max
aralıkları üç eğitim arasındaki betimsel değişkenliktir; güven aralığı veya tohum ortalaması
modelinin aralığı değildir. En iyi tohum veya avantajlı yıl seçilmez. Tam Brier/log-loss
tohum aralıkları seed_spread.csv içindedir.

## Karar ve tamamlanma yolu

Mevcut kayıt, kullanılan modeli değiştirmeyi desteklemiyor. Sabit yıllık deney, zayıf yıllar
ve eksik dönemler açıkça korunarak tamamlanmalıdır. Önceki hata analizi sorunları yerelleştirir;
devam eden eğitim düzenini değiştirmeyi gerekçelendirmez. Gelecekteki hibrit/statik-özet
kontrolü, bu karşılaştırmadan sonra yeni sabit protokol gerektiren hipotez olarak kalır.
Raporlama aracı bu kaydın üzerine yazmadan son değerlendirme modunu destekler.

```sh
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/evaluate_temporal_snapshot.py --require-complete --output artifacts/temporal_evaluation_20261106_r1
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/report_temporal_evaluation.py --source artifacts/temporal_evaluation_20261106_r1 --name temporal-evaluation-final-20261106
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pytest -q
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/publish_reports.py --output artifacts/bilingual_reports_temporal-evaluation-final-20261106
```

Tekrarlarda yeni çıktı/rapor adı kullanın. Son karşılaştırma için açık --years listesini
--require-complete ile değiştirip yeni çıktı dizini seçin; deney eksikken komut çalışmayı
reddeder. Yeni çift dilli belge sürümü yayımlayın; iki incelenmiş sürümü/kaynak hash değerini
docs/reports.json ile docs/reports.md içine kaydedin. Önceki kayıt sürümleri korunur. Yerel
CSV, PNG, tahmin ve model dosyaları Git dışında kalır. Mevcut kayıt raporunda her kaynak
bölümün ve kodun hash değerleri bulunur; ayrılmış test açılmaz ve yerel app.py marka
düzenlemeleri commit edilmez.

| source | sha256 |
| --- | --- |
| artifacts/temporal_evaluation_20261106_r1/report.json | 0d6e1310fbb19bc4af6491d8b1371fe3b07d42c267d19f91afa4b69399524245 |
| config/temporal-evaluation-report-v1.json | f9633dc5cf8b99000d9fa5ca948872632c08e5ad2053539f6fbfa5aa17260b0d |
| config/temporal-sequence-v2.json | 76db8b565b8ad2ba9f0f322458dd30eb18f9d2c87d34c66ebffb76d055c7cdd0 |


