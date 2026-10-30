# Ortak sınıflandırıcı eğitimiyle bir ve iki yıllık kalibrasyon

İki yıllık kol, pozitif değerlendirme yıllarının 6 tanesinden 4 tanesinde
recall >=0.95 sağladı. Tüm yıllar için kabul kontrolü `False` oldu. Dashboard modeli
ve alarm kuralı değiştirilmedi. Ayrılmış 2024–2025 testi kapalı kaldı. Aşağıdaki kontrol
karşılaştırmaları olmadan tek yıllık kazanımlar tutarlı iyileşme olarak sunulmamalıdır.

## Sabit soru ve kontrol kolları

Önceki denetim, az sayıda pozitif bölge desteği ve eşik duyarlılığı buldu. Bu deney,
temel sınıflandırıcı eğitimi aynıyken sabit iki yıllık kalibrasyon penceresinin sabit
bir yıllık pencereye göre dönemler arası aktarımı iyileştirip iyileştirmediğini sorar.
Tasarım `config/calibration-windows-v1.json` ile sabittir; süre ızgarası veya sonradan
bölme tarihi ayarlaması yoktur.

Y değerlendirme yılında iki yeni kol, Y-2 yılının 1 Ocak tarihinden önce eğitilmiş aynı
lojistik ve XGBoost sınıflandırıcılarını paylaşır. Tahmin pencereleri o tarihe kadar
bitmelidir. İki kolda aynı 96 özellik, özgün hiperparametreler ve 0.45/0.55 birleşimi
korunur. `shared_train_two_year`, Y-2 ve Y-1'de; `shared_train_one_year`, yalnızca Y-1
alt kümesinde kalibre edilir. Eğitim HARP'ları kalibrasyondan çıkarılır, gözlem/tahmin
aralıkları takvim sınırları içinde kalmalıdır. Her kol kendi kalibrasyon penceresinde
sigmoid kalibrasyonunu öğrenir, recall >=0.95 eşiğini seçip sabitler, ardından değerlendirme
yılını tahmin eder. Olasılık öğrenimi ve eşik seçimi aynı kalibrasyon satırlarını tekrar
kullanır; bu açıkça belirtilmiştir.

`original_baseline`, mevcutsa sınıflandırıcı eğitiminde bir yıl daha kullanan sabit
özgün yıllık modeldir. İki yeni kolun karşılaştırılması, ortak eğitim altında kalibrasyon
süresini ayırır. Bunlardan herhangi birini özgün referansla karşılaştırmak sınıflandırıcı
eğitim geçmişini de değiştirir; yalnızca kalibrasyon süresi karşılaştırması değildir.

Özgün yıllık değerlendirme topluluğu kullanılır; yeni eğitim veya iki yıllık havuzla
ortak ek HARP varsa çıkarılır, aynı kalan satırlar tüm kollara uygulanır. Çıkarılan
satırlar raporlanır. Özgün etiket/kalite dışlamaları korunur. Kaynak modeller, tahminler
ve girdi kayıtları özetleriyle doğrulanır; referans anahtarları ve etiketleri eşleşmelidir.

## Sayılar, bölge çeşitliliği ve kullanılabilirlik

| year | role | rows | positives | regions | positive_regions |
| --- | --- | --- | --- | --- | --- |
| 2014 | train | 82507 | 1633 | 628 | 34 |
| 2014 | one_year | 74853 | 1287 | 593 | 31 |
| 2014 | two_year | 140149 | 2596 | 1128 | 57 |
| 2014 | evaluation | 75228 | 2310 | 629 | 44 |
| 2015 | train | 148508 | 2959 | 1168 | 60 |
| 2015 | one_year | 75790 | 2341 | 636 | 45 |
| 2015 | two_year | 150287 | 3674 | 1217 | 75 |
| 2015 | evaluation | 69138 | 1355 | 599 | 24 |
| 2016 | train | 223647 | 4246 | 1756 | 91 |
| 2016 | one_year | 70117 | 1403 | 608 | 25 |
| 2016 | two_year | 145794 | 3713 | 1228 | 69 |
| 2016 | evaluation | 42987 | 181 | 357 | 4 |
| 2017 | train | 299785 | 6633 | 2385 | 135 |
| 2017 | one_year | 43122 | 193 | 360 | 5 |
| 2017 | two_year | 112391 | 1560 | 956 | 28 |
| 2017 | evaluation | 19529 | 253 | 163 | 3 |
| 2018 | train | 370351 | 8036 | 2984 | 160 |
| 2018 | one_year | 19698 | 253 | 166 | 3 |
| 2018 | two_year | 62782 | 434 | 520 | 7 |
| 2018 | evaluation | 7799 | 0 | 74 | 0 |
| 2019 | train | 413604 | 8241 | 3341 | 164 |
| 2019 | one_year | 7880 | 0 | 75 | 0 |
| 2019 | two_year | 27474 | 253 | 237 | 3 |
| 2019 | evaluation | 4919 | 0 | 44 | 0 |
| 2020 | train | 433399 | 8494 | 3504 | 167 |
| 2020 | one_year | 4919 | 0 | 44 | 0 |
| 2020 | two_year | 12758 | 0 | 118 | 0 |
| 2020 | evaluation | 9813 | 0 | 77 | 0 |
| 2021 | train | 441344 | 8494 | 3578 | 167 |
| 2021 | one_year | 9813 | 0 | 77 | 0 |
| 2021 | two_year | 14742 | 0 | 121 | 0 |
| 2021 | evaluation | 28125 | 204 | 255 | 9 |
| 2022 | train | 446303 | 8494 | 3622 | 167 |
| 2022 | one_year | 28318 | 204 | 258 | 9 |
| 2022 | two_year | 38236 | 204 | 332 | 9 |
| 2022 | evaluation | 50756 | 421 | 528 | 12 |
| 2023 | train | 456126 | 8494 | 3699 | 167 |
| 2023 | one_year | 50756 | 421 | 528 | 12 |
| 2023 | two_year | 78881 | 625 | 783 | 21 |
| 2023 | evaluation | 60366 | 781 | 703 | 27 |

`positive_regions`, bağımsız patlamaları değil, korunan pozitif penceresi olan HARP'ları
sayar. Daha fazla pencere otomatik olarak daha fazla pozitif bölge çeşitliliği demek
değildir; bir ve iki yıllık sayılar birlikte incelenmelidir. Sayılar temizlenmiş topluluklara aittir.

| year | status | additional_evaluation_rows_removed | unavailable | passes_gate |
| --- | --- | --- | --- | --- |
| 2014 | complete | 0 | {} | False |
| 2015 | complete | 0 | {} | False |
| 2016 | complete | 0 | {} | False |
| 2017 | complete | 0 | {} | False |
| 2018 | complete | 0 | {} | undefined |
| 2019 | complete | 0 | {"original_baseline": "Training/calibration lacks both classes: ['calibration']", "shared_train_one_year": "Training or calibration lacks both classes"} | undefined |
| 2020 | skipped | 0 | {"original_baseline": "Training/calibration lacks both classes: ['calibration']", "shared_train_one_year": "Training or calibration lacks both classes", "shared_train_two_year": "Training or calibration lacks both classes"} | undefined |
| 2021 | skipped | 0 | {"original_baseline": "Training/calibration lacks both classes: ['calibration']", "shared_train_one_year": "Training or calibration lacks both classes", "shared_train_two_year": "Training or calibration lacks both classes"} | undefined |
| 2022 | complete | 0 | {} | True |
| 2023 | complete | 0 | {} | False |

Her kol bağımsız olarak eğitim ve kalibrasyonda iki sınıfı ve boş olmayan değerlendirmeyi
gerektirir. Kullanılamayan kollar referansla doldurulmaz. Özgün referans yalnızca önceki
tamamlanmış turlarında vardır. İki yıllık kol, özgün referansı olmayan bir yılda kullanılabilir
olabilir; böyle sonuçlar ölçülmüş iyileşme değil, eşleşmemiş kanıttır. Pozitif olmayan
değerlendirme yıllarında FP/FPR korunur, recall/AP tanımsızdır. Hiç alarm yoksa precision
da tanımsızdır. `undefined` sıfır değildir.

## Yıllık precision, recall ve yanlış pozitif pencereler

| year | arm | n | positives | precision | recall | fp | fn | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | original_baseline | 75228 | 2310 | 0.135905 | 0.945455 | 13886 | 126 | 0.011475 |
| 2014 | shared_train_one_year | 75228 | 2310 | 0.123993 | 0.952381 | 15543 | 110 | 0.010974 |
| 2014 | shared_train_two_year | 75228 | 2310 | 0.130032 | 0.946753 | 14632 | 123 | 0.014190 |
| 2015 | original_baseline | 69138 | 1355 | 0.105164 | 0.993358 | 11453 | 9 | 0.018839 |
| 2015 | shared_train_one_year | 69138 | 1355 | 0.110455 | 0.994096 | 10848 | 8 | 0.020398 |
| 2015 | shared_train_two_year | 69138 | 1355 | 0.114749 | 0.993358 | 10384 | 9 | 0.016427 |
| 2016 | original_baseline | 42987 | 181 | 0.071400 | 0.972376 | 2289 | 5 | 0.030831 |
| 2016 | shared_train_one_year | 42987 | 181 | 0.076092 | 0.972376 | 2137 | 5 | 0.032370 |
| 2016 | shared_train_two_year | 42987 | 181 | 0.044612 | 0.983425 | 3812 | 3 | 0.025267 |
| 2017 | original_baseline | 19529 | 253 | 0.155512 | 0.936759 | 1287 | 16 | 0.012000 |
| 2017 | shared_train_one_year | 19529 | 253 | 0.161814 | 0.944664 | 1238 | 14 | 0.014550 |
| 2017 | shared_train_two_year | 19529 | 253 | 0.149068 | 0.948617 | 1370 | 13 | 0.026176 |
| 2018 | original_baseline | 7799 | 0 | 0.000000 | undefined | 359 | 0 | 0.004351 |
| 2018 | shared_train_one_year | 7799 | 0 | 0.000000 | undefined | 351 | 0 | 0.004511 |
| 2018 | shared_train_two_year | 7799 | 0 | 0.000000 | undefined | 237 | 0 | 0.009588 |
| 2019 | shared_train_two_year | 4919 | 0 | 0.000000 | undefined | 312 | 0 | 0.003541 |
| 2022 | original_baseline | 50756 | 421 | 0.039573 | 0.985748 | 10072 | 6 | 0.008994 |
| 2022 | shared_train_one_year | 50756 | 421 | 0.041375 | 0.983373 | 9592 | 7 | 0.009790 |
| 2022 | shared_train_two_year | 50756 | 421 | 0.041491 | 0.983373 | 9564 | 7 | 0.007402 |
| 2023 | original_baseline | 60366 | 781 | 0.103397 | 0.884763 | 5992 | 90 | 0.018203 |
| 2023 | shared_train_one_year | 60366 | 781 | 0.106350 | 0.889885 | 5840 | 86 | 0.018942 |
| 2023 | shared_train_two_year | 60366 | 781 | 0.060194 | 0.959027 | 11694 | 32 | 0.007094 |

Skorlar 0–1 ölçeğindedir; sayılar bağımsız patlama veya bildirimleri değil, örtüşen
tahmin pencerelerini anlatır. Her kol kendi aktarılmış kalibrasyon eşiğini kullanır.
Recall 0.95 altındayken daha yüksek precision, istenen başarı olarak sayılmamalıdır.

İki yıllık kol eksi kullanılabilir her kontrol:

| year | control | precision_delta | recall_delta | fp_delta |
| --- | --- | --- | --- | --- |
| 2014 | original_baseline | -0.005874 | 0.001299 | 746 |
| 2014 | shared_train_one_year | 0.006039 | -0.005628 | -911 |
| 2015 | original_baseline | 0.009584 | 0.000000 | -1069 |
| 2015 | shared_train_one_year | 0.004293 | -0.000738 | -464 |
| 2016 | original_baseline | -0.026788 | 0.011050 | 1523 |
| 2016 | shared_train_one_year | -0.031480 | 0.011050 | 1675 |
| 2017 | original_baseline | -0.006443 | 0.011858 | 83 |
| 2017 | shared_train_one_year | -0.012746 | 0.003953 | 132 |
| 2018 | original_baseline | 0.000000 | undefined | -122 |
| 2018 | shared_train_one_year | 0.000000 | undefined | -114 |
| 2022 | original_baseline | 0.001918 | -0.002375 | -508 |
| 2022 | shared_train_one_year | 0.000116 | 0.000000 | -28 |
| 2023 | original_baseline | -0.043202 | 0.074264 | 5702 |
| 2023 | shared_train_one_year | -0.046156 | 0.069142 | 5854 |

Pozitif precision/recall farkları iki yıllık kolu destekler; negatif FP farkları daha
az yanlış pozitif pencere demektir. Çok yıllık tek ortalama bu karşılaştırmaların yerine geçmez.

## Tüm metrikler ve kabul

| year | arm | n | positives | threshold | tp | fp | fn | tn | recall | precision | false_positive_rate | false_alarm_ratio | alarms | tss | average_precision | brier | log_loss | accuracy | balanced_accuracy | f1 | always_quiet_accuracy | precision_defined | recall_defined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | original_baseline | 75228 | 2310 | 0.011475 | 2184 | 13886 | 126 | 59032 | 0.945455 | 0.135905 | 0.190433 | 0.864095 | 16070 | 0.755021 | 0.507930 | 0.020661 | 0.076538 | 0.813740 | 0.877511 | 0.237650 | 0.969293 | True | True |
| 2014 | shared_train_one_year | 75228 | 2310 | 0.010974 | 2200 | 15543 | 110 | 57375 | 0.952381 | 0.123993 | 0.213157 | 0.876007 | 17743 | 0.739224 | 0.483201 | 0.020988 | 0.078063 | 0.791926 | 0.869612 | 0.219419 | 0.969293 | True | True |
| 2014 | shared_train_two_year | 75228 | 2310 | 0.014190 | 2187 | 14632 | 123 | 58286 | 0.946753 | 0.130032 | 0.200664 | 0.869968 | 16819 | 0.746089 | 0.486485 | 0.020934 | 0.077733 | 0.803863 | 0.873045 | 0.228658 | 0.969293 | True | True |
| 2015 | original_baseline | 69138 | 1355 | 0.018839 | 1346 | 11453 | 9 | 56330 | 0.993358 | 0.105164 | 0.168966 | 0.894836 | 12799 | 0.824392 | 0.492441 | 0.013564 | 0.047847 | 0.834216 | 0.912196 | 0.190194 | 0.980402 | True | True |
| 2015 | shared_train_one_year | 69138 | 1355 | 0.020398 | 1347 | 10848 | 8 | 56935 | 0.994096 | 0.110455 | 0.160040 | 0.889545 | 12195 | 0.834056 | 0.488445 | 0.013474 | 0.047741 | 0.842981 | 0.917028 | 0.198819 | 0.980402 | True | True |
| 2015 | shared_train_two_year | 69138 | 1355 | 0.016427 | 1346 | 10384 | 9 | 57399 | 0.993358 | 0.114749 | 0.153195 | 0.885251 | 11730 | 0.840163 | 0.488916 | 0.013481 | 0.046870 | 0.849677 | 0.920082 | 0.205732 | 0.980402 | True | True |
| 2016 | original_baseline | 42987 | 181 | 0.030831 | 176 | 2289 | 5 | 40517 | 0.972376 | 0.071400 | 0.053474 | 0.928600 | 2465 | 0.918902 | 0.366443 | 0.003263 | 0.014523 | 0.946635 | 0.959451 | 0.133031 | 0.995789 | True | True |
| 2016 | shared_train_one_year | 42987 | 181 | 0.032370 | 176 | 2137 | 5 | 40669 | 0.972376 | 0.076092 | 0.049923 | 0.923908 | 2313 | 0.922453 | 0.433388 | 0.003128 | 0.013935 | 0.950171 | 0.961226 | 0.141139 | 0.995789 | True | True |
| 2016 | shared_train_two_year | 42987 | 181 | 0.025267 | 178 | 3812 | 3 | 38994 | 0.983425 | 0.044612 | 0.089053 | 0.955388 | 3990 | 0.894372 | 0.434278 | 0.003199 | 0.015885 | 0.911252 | 0.947186 | 0.085351 | 0.995789 | True | True |
| 2017 | original_baseline | 19529 | 253 | 0.012000 | 237 | 1287 | 16 | 17989 | 0.936759 | 0.155512 | 0.066767 | 0.844488 | 1524 | 0.869992 | 0.811694 | 0.004907 | 0.020488 | 0.933279 | 0.934996 | 0.266742 | 0.987045 | True | True |
| 2017 | shared_train_one_year | 19529 | 253 | 0.014550 | 239 | 1238 | 14 | 18038 | 0.944664 | 0.161814 | 0.064225 | 0.838186 | 1477 | 0.880439 | 0.806978 | 0.004954 | 0.020646 | 0.935890 | 0.940220 | 0.276301 | 0.987045 | True | True |
| 2017 | shared_train_two_year | 19529 | 253 | 0.026176 | 240 | 1370 | 13 | 17906 | 0.948617 | 0.149068 | 0.071073 | 0.850932 | 1610 | 0.877544 | 0.807301 | 0.005278 | 0.022802 | 0.929182 | 0.938772 | 0.257649 | 0.987045 | True | True |
| 2018 | original_baseline | 7799 | 0 | 0.004351 | 0 | 359 | 0 | 7440 | undefined | 0.000000 | 0.046032 | 1.000000 | 359 | undefined | undefined | 0.000012 | 0.000791 | 0.953968 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | shared_train_one_year | 7799 | 0 | 0.004511 | 0 | 351 | 0 | 7448 | undefined | 0.000000 | 0.045006 | 1.000000 | 351 | undefined | undefined | 0.000012 | 0.000796 | 0.954994 | undefined | 0.000000 | 1.000000 | True | False |
| 2018 | shared_train_two_year | 7799 | 0 | 0.009588 | 0 | 237 | 0 | 7562 | undefined | 0.000000 | 0.030389 | 1.000000 | 237 | undefined | undefined | 0.000016 | 0.000977 | 0.969611 | undefined | 0.000000 | 1.000000 | True | False |
| 2019 | shared_train_two_year | 4919 | 0 | 0.003541 | 0 | 312 | 0 | 4607 | undefined | 0.000000 | 0.063428 | 1.000000 | 312 | undefined | undefined | 0.000502 | 0.003290 | 0.936572 | undefined | 0.000000 | 1.000000 | True | False |
| 2022 | original_baseline | 50756 | 421 | 0.008994 | 415 | 10072 | 6 | 40263 | 0.985748 | 0.039573 | 0.200099 | 0.960427 | 10487 | 0.785649 | 0.280023 | 0.007064 | 0.029196 | 0.801442 | 0.892824 | 0.076091 | 0.991705 | True | True |
| 2022 | shared_train_one_year | 50756 | 421 | 0.009790 | 414 | 9592 | 7 | 40743 | 0.983373 | 0.041375 | 0.190563 | 0.958625 | 10006 | 0.792810 | 0.284225 | 0.007028 | 0.029089 | 0.810880 | 0.896405 | 0.079409 | 0.991705 | True | True |
| 2022 | shared_train_two_year | 50756 | 421 | 0.007402 | 414 | 9564 | 7 | 40771 | 0.983373 | 0.041491 | 0.190007 | 0.958509 | 9978 | 0.793366 | 0.285019 | 0.006989 | 0.028388 | 0.811431 | 0.896683 | 0.079623 | 0.991705 | True | True |
| 2023 | original_baseline | 60366 | 781 | 0.018203 | 691 | 5992 | 90 | 53593 | 0.884763 | 0.103397 | 0.100562 | 0.896603 | 6683 | 0.784201 | 0.220619 | 0.011195 | 0.043996 | 0.899248 | 0.892100 | 0.185155 | 0.987062 | True | True |
| 2023 | shared_train_one_year | 60366 | 781 | 0.018942 | 695 | 5840 | 86 | 53745 | 0.889885 | 0.106350 | 0.098011 | 0.893650 | 6535 | 0.791874 | 0.229153 | 0.011149 | 0.043730 | 0.901832 | 0.895937 | 0.189995 | 0.987062 | True | True |
| 2023 | shared_train_two_year | 60366 | 781 | 0.007094 | 749 | 11694 | 32 | 47891 | 0.959027 | 0.060194 | 0.196257 | 0.939806 | 12443 | 0.762769 | 0.229548 | 0.011102 | 0.043389 | 0.805752 | 0.881385 | 0.113279 | 0.987062 | True | True |

Precision alarmlar içindeki pozitifleri, recall yakalanan pozitif pencereleri, accuracy
tüm doğru sınıflandırmaları ölçer. AP sıralamayı ölçer; düşük Brier/log loss daha iyi
olasılıksal puanlamadır. Sabit kontrol, özgün referansla karşılaştırılabilir tüm pozitif
yılların kapsanmasını; her birinde iki kontrole göre recall >=0.95 koşulunda daha yüksek
precision, düşmeyen AP ve artmayan Brier/log loss gerektirir. Kontrol geçilse bile otomatik
dağıtım yoktur. Seyrek veya eksik dönemler görünür tutulur.

## Bu çalıştırmanın bulguları

Yalnızca 2022, iki kontrole göre tüm yıllık kabul koşullarını geçer. O yılda bile ortak
eğitimli bir yıllık kontrole göre precision 0.041375'ten 0.041491'e, yanlış pozitifler
9592'den 9564'e değişir; recall 0.983373 olarak kalır. İki pencerede de 9 pozitif HARP
vardır; süreyi uzatmak o yılda pozitif bölge çeşitliliği eklemez.

2016'da pozitif HARP sayısı 25'ten 69'a çıkarken, ortak eğitimli kontrole göre yanlış
pozitifler 2137'den 3812'ye yükselir ve precision 0.076092'den 0.044612'ye düşer.
2023'te pozitif HARP sayısı 12'den 21'e çıkar; recall 0.889885'ten 0.959027'ye yükselir,
fakat yanlış pozitifler 5840'tan 11694'e çıkar ve precision 0.106350'den 0.060194'e düşer.
Dolayısıyla daha fazla pozitif bölge kapsamı tek başına daha iyi çalışma noktasını
kanıtlamaz. Hiçbir yılda ek değerlendirme satırı çıkarılmadı.

2019 iki yıllık kolunda 312 yanlış pozitif pencere vardır; pozitif değerlendirme penceresi
yoktur ve o yıl özgün veya bir yıllık kontrol bulunmaz. 2020 ve 2021'de hiçbir kol
kullanılamaz. Bu dönemler gizlenmez veya iyileşme sayılmaz. Denenen iki yıllık kural
benimsenmez; bu çalışma tek başına başka bir süre aramasını gerekçelendirmez.

## Eşleştirilmiş koşullu belirsizlik

| year | control | metric | lower | upper | valid_draws |
| --- | --- | --- | --- | --- | --- |
| 2014 | original_baseline | precision | -0.009523 | -0.002794 | 1000 |
| 2014 | original_baseline | recall | -0.007179 | 0.014346 | 1000 |
| 2014 | original_baseline | fp | 451.950000 | 1053.000000 | 1000 |
| 2014 | shared_train_one_year | precision | 0.003759 | 0.008677 | 1000 |
| 2014 | shared_train_one_year | recall | -0.011853 | -0.001576 | 1000 |
| 2014 | shared_train_one_year | fp | -1106.050000 | -724.975000 | 1000 |
| 2015 | original_baseline | precision | 0.005274 | 0.015383 | 1000 |
| 2015 | original_baseline | recall | 0.000000 | 0.000000 | 1000 |
| 2015 | original_baseline | fp | -1471.350000 | -740.950000 | 1000 |
| 2015 | shared_train_one_year | precision | 0.002570 | 0.006408 | 1000 |
| 2015 | shared_train_one_year | recall | -0.002999 | 0.000000 | 1000 |
| 2015 | shared_train_one_year | fp | -591.000000 | -341.000000 | 1000 |
| 2016 | original_baseline | precision | -0.048811 | 0.000000 | 1000 |
| 2016 | original_baseline | recall | 0.000000 | 0.090909 | 973 |
| 2016 | original_baseline | fp | 1065.925000 | 2050.150000 | 1000 |
| 2016 | shared_train_one_year | precision | -0.056642 | 0.000000 | 1000 |
| 2016 | shared_train_one_year | recall | 0.000000 | 0.090909 | 973 |
| 2016 | shared_train_one_year | fp | 1186.975000 | 2260.075000 | 1000 |
| 2017 | original_baseline | precision | -0.028886 | 0.000336 | 1000 |
| 2017 | original_baseline | recall | 0.000000 | 0.046154 | 949 |
| 2017 | original_baseline | fp | 25.000000 | 160.000000 | 1000 |
| 2017 | shared_train_one_year | precision | -0.035986 | 0.000000 | 1000 |
| 2017 | shared_train_one_year | recall | 0.000000 | 0.015385 | 949 |
| 2017 | shared_train_one_year | fp | 68.975000 | 208.025000 | 1000 |
| 2018 | original_baseline | precision | 0.000000 | 0.000000 | 1000 |
| 2018 | original_baseline | recall | undefined | undefined | 0 |
| 2018 | original_baseline | fp | -249.000000 | -29.000000 | 1000 |
| 2018 | shared_train_one_year | precision | 0.000000 | 0.000000 | 1000 |
| 2018 | shared_train_one_year | recall | undefined | undefined | 0 |
| 2018 | shared_train_one_year | fp | -222.050000 | -29.000000 | 1000 |
| 2022 | original_baseline | precision | 0.000900 | 0.003161 | 1000 |
| 2022 | original_baseline | recall | -0.009180 | 0.000000 | 1000 |
| 2022 | original_baseline | fp | -653.000000 | -383.950000 | 1000 |
| 2022 | shared_train_one_year | precision | 0.000051 | 0.000206 | 1000 |
| 2022 | shared_train_one_year | recall | 0.000000 | 0.000000 | 1000 |
| 2022 | shared_train_one_year | fp | -41.000000 | -16.000000 | 1000 |
| 2023 | original_baseline | precision | -0.063876 | -0.026031 | 1000 |
| 2023 | original_baseline | recall | 0.022419 | 0.136529 | 1000 |
| 2023 | original_baseline | fp | 4503.850000 | 6915.200000 | 1000 |
| 2023 | shared_train_one_year | precision | -0.067960 | -0.028180 | 1000 |
| 2023 | shared_train_one_year | recall | 0.022985 | 0.128646 | 1000 |
| 2023 | shared_train_one_year | fp | 4635.750000 | 7079.675000 | 1000 |

Aralıklar iki yıllık kol eksi belirtilen kontroldür; yıl başına 24 tohumla eşleştirilmiş
bütün HARP'ları örnekleyen 1000 bootstrap tekrarı kullanır. Sınıflandırıcılar, kalibratörler
ve eşikler sabitken iki kolda aynı örneklenmiş bölgeler kullanılır. Öğrenim ve geçmiş
model seçimi belirsizliği dahil değildir. `valid_draws`, tanımsız precision/recall
tekrarlarını izler. Komşu yıllık turlar geçmiş eğitimi paylaşır; bağımsız tekrarlar değildir.
Sıfırı içeren aralık o aralık düzeyinde yönlü değişimi göstermez.

## Yorum sınırları

Bu, önceki incelemelerin yönlendirdiği uyarlamalı geçmişe dönük geliştirmedir; el değmemiş
test değildir. Uzun pencere, yakın tarihli olma özelliğinden ödün verip daha fazla veri
ve olası pozitif bölge çeşitliliği sağlar; bundan otomatik olarak kalibrasyon kararlılığı
veya precision iyileşmesi çıkmaz. Uzun kalibrasyona yer açmak sınıflandırıcı eğitimini
kısalttığından ortak eğitim kontrolü gereklidir. Özgün referansa göre daha güçlü veya
zayıf skorlar yalnızca süreye bağlanamaz.

Çok dönemli kanıt model değiştirmeyi desteklemedikçe mevcut model korunmalıdır. Sonraki
kural daha erken iç kronolojik bölümlerde sabitlenmeli; değerlendirme sonuçlarına bakarak
her yıl için farklı süre seçilmemelidir. Bu raporda canlı tahmin, etiket düzeltmesi,
ek süre araması veya dağıtım kararı yapıldığı iddia edilmez.

## Yeniden üretim

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_calibration_windows.py \
  --protocol config/calibration-windows-v1.json --output artifacts/calibration_windows_20261030_r1
.venv/bin/python scripts/report_calibration_windows.py --source artifacts/calibration_windows_20261030_r1 --report-name calibration-windows-20261030
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_calibration-windows-20261030
```

Yeni çıktı dizinleri ve rapor adları seçin. Sabit kaynak çıktıları ve protokolleri
koruyun. İki tam sürümü gözden geçirip kaynak özetini ve bağlantıları `docs/reports.json`
ve `docs/reports.md` dosyalarına kaydedin; yeni HTML dizinine yayımlayın. Modeller,
kalibratörler, tahminler ve üretilen HTML yerel, Git dışında çıktılar olarak kalır.
Deney kaynak, protokol, kod ve çıktı özetlerini kaydeder.

| source | SHA-256 |
| --- | --- |
| artifacts/calibration_windows_20261030_r1/report.json | 59290a8f2a74c4f993f45539c2f9f3306cb4e5d97046884560333552d5a247ba |
| artifacts/calibration_windows_20261030_r1/metrics.csv | 73fb4536374c125ee1e611a84ecb8d6207539d70ae6ab744042c7550e2314340 |

