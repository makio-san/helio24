# Eşik seçimi sonuçları: hiçbir önceki yıl kuralı geçmiyor ve baseline kolu değerlendirilemiyor

## Karar ve kapsam

[Dondurulmuş protokol](threshold-selection-protocol-20261107.tr.md), tamamlanan yedi yıllık karşılaştırmanın
dondurulmuş yıllık tahminleri üzerinde bir kez çalıştırıldı (kaynak rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`). Dört seçim kuralı, eşiği yalnızca her
değerlendirme yılından bir önceki yılın kalibrasyon pencerelerinden seçti; eşikler, herhangi bir değerlendirme
dosyası okunmadan önce diske yazıldı ve hash'lendi. Model eğitilmedi, etiket değişmedi ve ayrılmış 2024–2025
testi kapalı kaldı. Kontrol kuralı, iki TCN kolunda da her yılda saklanan eşikleri birebir yeniden üretti.

Kararlar:

1. Baseline kolu için uygulanabilirlik kapısı başarısız oldu: 20 dondurulmuş geliştirme özellik shard'ının
   hiçbiri yerelde yok; bu yüzden kalibrasyon olasılıkları yeniden hesaplanamıyor ve saklanan eşiği yeniden
   üretilemiyor. Protokolün söylediği gibi baseline kolu dışlanır ve değerlendirilemez olarak raporlanır;
   birincil kol `chronological` olur. Yeniden eğitim yapılmadı.
2. Hiçbir kural altı pozitif yılın hepsinde geçmiyor. En iyi kural `w93`, birincil kolda 6 yılın 4'ünde geçiyor.
3. Hiçbir şey benimsenmedi. Bu kayıtta önceki yılın recall hedefi, eşik için güvenilmez bir kılavuzdur.

Açıklama: baseline kapısının sonucunu bir metrik değil, eksik veri belirledi. Baseline kolunun sonucu, önceki
eşik ve kalıcılık raporlarıyla aynı zeminde karşılaştırılamaz.

## Uygulanabilirlik kapısı

| arm | shards_expected | shards_missing | evaluable |
| --- | --- | --- | --- |
| baseline | 20 | 20 | no |

## Kabul sonucu

| arm | rule | years_met | required_years | all_year_primary |
| --- | --- | --- | --- | --- |
| chronological | w93 | 4 | 6 | no |
| chronological | w90 | 2 | 6 | no |
| chronological | run95 | 1 | 6 | no |
| chronological | run90 | 0 | 6 | no |
| shuffled_interior | w93 | 3 | 6 | no |
| shuffled_interior | w90 | 2 | 6 | no |
| shuffled_interior | run95 | 0 | 6 | no |
| shuffled_interior | run90 | 0 | 6 | no |

Bir kural, altı pozitif yılın hepsinde dört yıllık koşulun tamamını sağlamalıdır. Birincil kol
`chronological`'dır; `shuffled_interior` ikincil betimleyici koldur ve genel olarak başarısızdır.

| year | rule | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | w93 | yes | yes | no | yes | no |
| 2014 | w90 | yes | yes | no | no | no |
| 2014 | run95 | yes | yes | no | no | no |
| 2014 | run90 | yes | yes | no | no | no |
| 2015 | w93 | yes | yes | yes | yes | yes |
| 2015 | w90 | yes | yes | no | no | no |
| 2015 | run95 | yes | yes | no | no | no |
| 2015 | run90 | yes | yes | no | no | no |
| 2016 | w93 | yes | yes | yes | no | no |
| 2016 | w90 | yes | yes | yes | no | no |
| 2016 | run95 | no | yes | no | no | no |
| 2016 | run90 | yes | yes | no | no | no |
| 2017 | w93 | yes | yes | yes | yes | yes |
| 2017 | w90 | yes | yes | yes | yes | yes |
| 2017 | run95 | yes | yes | yes | no | no |
| 2017 | run90 | yes | yes | yes | no | no |
| 2018 | w93 | no | yes | yes | yes | no |
| 2018 | w90 | no | yes | yes | yes | no |
| 2018 | run95 | no | yes | yes | yes | no |
| 2018 | run90 | no | yes | yes | yes | no |
| 2022 | w93 | yes | yes | yes | yes | yes |
| 2022 | w90 | yes | yes | yes | yes | yes |
| 2022 | run95 | yes | yes | yes | no | no |
| 2022 | run90 | yes | yes | yes | no | no |
| 2023 | w93 | yes | yes | yes | yes | yes |
| 2023 | w90 | yes | yes | yes | no | no |
| 2023 | run95 | yes | yes | yes | yes | yes |
| 2023 | run90 | yes | yes | no | no | no |

`w93`, 2014'te bir pozitif seri eksik alarmlı olduğu için (78'e karşı 79) ve 2016'da pencere recall'ı 0.955801'den
0.900552'ye düştüğü için, 0,02 toleransın çok ötesinde, başarısız olur. Daha düşük hedefler daha çok yılda
başarısız olur. Seri recall kuralları 2014, 2015, 2016, 2017 ve 2022'de recall toleransında veya alarmlı pozitif
seri sayısında başarısız olur. 2018'de pozitif pencere yoktur ve kapıya tabi değildir.

## Birincil kol için yıllık sonuçlar

| year | rule | threshold | ratio_to_control | calibration_positive_windows | calibration_positive_runs | calibration_recall | recall | recall_drop | fp | episodes | episode_precision | positive_runs_alarmed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control_w95 | 0.003306 | 1.000000 | 1287 | 46 | 0.950272 | 0.945455 | 0.000000 | 19639 | 801 | 0.081149 | 79 |
| 2014 | w93 | 0.006616 | 2.000983 | 1287 | 46 | 0.930070 | 0.934199 | 0.011255 | 17113 | 782 | 0.085678 | 78 |
| 2014 | w90 | 0.011362 | 3.436211 | 1287 | 46 | 0.900544 | 0.917749 | 0.027706 | 15000 | 686 | 0.097668 | 77 |
| 2014 | run95 | 0.009509 | 2.875808 | 1287 | 46 | 0.911422 | 0.922511 | 0.022944 | 15676 | 725 | 0.091034 | 78 |
| 2014 | run90 | 0.041321 | 12.497127 | 1287 | 46 | 0.815074 | 0.780519 | 0.164935 | 8813 | 566 | 0.114841 | 65 |
| 2015 | control_w95 | 0.014138 | 1.000000 | 2310 | 83 | 0.950216 | 0.971218 | 0.000000 | 11137 | 578 | 0.065744 | 50 |
| 2015 | w93 | 0.021835 | 1.544426 | 2310 | 83 | 0.930303 | 0.957934 | 0.013284 | 9655 | 561 | 0.071301 | 50 |
| 2015 | w90 | 0.030756 | 2.175494 | 2310 | 83 | 0.900000 | 0.941697 | 0.029520 | 8307 | 527 | 0.077799 | 48 |
| 2015 | run95 | 0.039690 | 2.807384 | 2310 | 83 | 0.870996 | 0.904797 | 0.066421 | 7291 | 485 | 0.098969 | 48 |
| 2015 | run90 | 0.050356 | 3.561820 | 2310 | 83 | 0.829870 | 0.859779 | 0.111439 | 6304 | 458 | 0.098253 | 47 |
| 2016 | control_w95 | 0.008422 | 1.000000 | 1355 | 51 | 0.950554 | 0.955801 | 0.000000 | 6385 | 385 | 0.012987 | 7 |
| 2016 | w93 | 0.013940 | 1.655270 | 1355 | 51 | 0.930627 | 0.900552 | 0.055249 | 5441 | 377 | 0.018568 | 7 |
| 2016 | w90 | 0.031056 | 3.687708 | 1355 | 51 | 0.900369 | 0.850829 | 0.104972 | 3861 | 302 | 0.016556 | 7 |
| 2016 | run95 | 0.040602 | 4.821182 | 1355 | 51 | 0.878229 | 0.839779 | 0.116022 | 3209 | 296 | 0.010135 | 6 |
| 2016 | run90 | 0.076402 | 9.072168 | 1355 | 51 | 0.803690 | 0.696133 | 0.259669 | 1672 | 201 | 0.024876 | 6 |
| 2017 | control_w95 | 0.017731 | 1.000000 | 181 | 7 | 0.950276 | 0.936759 | 0.000000 | 1538 | 140 | 0.035714 | 5 |
| 2017 | w93 | 0.018025 | 1.016586 | 181 | 7 | 0.933702 | 0.936759 | 0.000000 | 1527 | 138 | 0.036232 | 5 |
| 2017 | w90 | 0.019112 | 1.077863 | 181 | 7 | 0.900552 | 0.936759 | 0.000000 | 1493 | 136 | 0.036765 | 5 |
| 2017 | run95 | 0.040512 | 2.284788 | 181 | 7 | 0.685083 | 0.901186 | 0.035573 | 891 | 85 | 0.058824 | 5 |
| 2017 | run90 | 0.040512 | 2.284788 | 181 | 7 | 0.685083 | 0.901186 | 0.035573 | 891 | 85 | 0.058824 | 5 |
| 2018 | control_w95 | 0.004784 | 1.000000 | 253 | 6 | 0.952569 | undefined | undefined | 518 | 49 | 0.000000 | 0 |
| 2018 | w93 | 0.009822 | 2.052942 | 253 | 6 | 0.932806 | undefined | undefined | 376 | 31 | 0.000000 | 0 |
| 2018 | w90 | 0.038863 | 8.122870 | 253 | 6 | 0.901186 | undefined | undefined | 123 | 16 | 0.000000 | 0 |
| 2018 | run95 | 0.013937 | 2.913107 | 253 | 6 | 0.924901 | undefined | undefined | 316 | 29 | 0.000000 | 0 |
| 2018 | run90 | 0.013937 | 2.913107 | 253 | 6 | 0.924901 | undefined | undefined | 316 | 29 | 0.000000 | 0 |
| 2022 | control_w95 | 0.006156 | 1.000000 | 204 | 9 | 0.950980 | 0.954869 | 0.000000 | 12971 | 809 | 0.019778 | 16 |
| 2022 | w93 | 0.008209 | 1.333587 | 204 | 9 | 0.931373 | 0.947743 | 0.007126 | 11924 | 767 | 0.020860 | 16 |
| 2022 | w90 | 0.010215 | 1.659541 | 204 | 9 | 0.901961 | 0.938242 | 0.016627 | 11100 | 727 | 0.020633 | 16 |
| 2022 | run95 | 0.019965 | 3.243500 | 204 | 9 | 0.754902 | 0.912114 | 0.042755 | 8248 | 614 | 0.026059 | 16 |
| 2022 | run90 | 0.019965 | 3.243500 | 204 | 9 | 0.754902 | 0.912114 | 0.042755 | 8248 | 614 | 0.026059 | 16 |
| 2023 | control_w95 | 0.004442 | 1.000000 | 421 | 16 | 0.950119 | 0.918054 | 0.000000 | 12483 | 796 | 0.046482 | 37 |
| 2023 | w93 | 0.009016 | 2.029464 | 421 | 16 | 0.931116 | 0.898848 | 0.019206 | 9702 | 705 | 0.056738 | 37 |
| 2023 | w90 | 0.022363 | 5.033956 | 421 | 16 | 0.900238 | 0.790013 | 0.128041 | 5875 | 514 | 0.081712 | 37 |
| 2023 | run95 | 0.007915 | 1.781656 | 421 | 16 | 0.935867 | 0.911652 | 0.006402 | 10273 | 736 | 0.051630 | 37 |
| 2023 | run90 | 0.046271 | 10.415721 | 421 | 16 | 0.617577 | 0.604353 | 0.313700 | 2847 | 296 | 0.141892 | 29 |

`recall_drop`, kontrol recall'ı eksi kural recall'ıdır. Birkaç kuralda eşik, kontrol eşiğinin büyük katlarıdır;
örneğin `run90` için 2014'te 12.4971 kat.

## Kalibrasyon yılının kılavuz olarak kararlılığı

| year | rule | calibration_recall | recall | evaluation_recall_minus_calibration_recall |
| --- | --- | --- | --- | --- |
| 2014 | control_w95 | 0.950272 | 0.945455 | -0.004817 |
| 2014 | w93 | 0.930070 | 0.934199 | 0.004129 |
| 2014 | w90 | 0.900544 | 0.917749 | 0.017205 |
| 2014 | run95 | 0.911422 | 0.922511 | 0.011089 |
| 2014 | run90 | 0.815074 | 0.780519 | -0.034554 |
| 2015 | control_w95 | 0.950216 | 0.971218 | 0.021001 |
| 2015 | w93 | 0.930303 | 0.957934 | 0.027631 |
| 2015 | w90 | 0.900000 | 0.941697 | 0.041697 |
| 2015 | run95 | 0.870996 | 0.904797 | 0.033801 |
| 2015 | run90 | 0.829870 | 0.859779 | 0.029908 |
| 2016 | control_w95 | 0.950554 | 0.955801 | 0.005248 |
| 2016 | w93 | 0.930627 | 0.900552 | -0.030075 |
| 2016 | w90 | 0.900369 | 0.850829 | -0.049540 |
| 2016 | run95 | 0.878229 | 0.839779 | -0.038450 |
| 2016 | run90 | 0.803690 | 0.696133 | -0.107557 |
| 2017 | control_w95 | 0.950276 | 0.936759 | -0.013517 |
| 2017 | w93 | 0.933702 | 0.936759 | 0.003057 |
| 2017 | w90 | 0.900552 | 0.936759 | 0.036206 |
| 2017 | run95 | 0.685083 | 0.901186 | 0.216103 |
| 2017 | run90 | 0.685083 | 0.901186 | 0.216103 |
| 2018 | control_w95 | 0.952569 | undefined | undefined |
| 2018 | w93 | 0.932806 | undefined | undefined |
| 2018 | w90 | 0.901186 | undefined | undefined |
| 2018 | run95 | 0.924901 | undefined | undefined |
| 2018 | run90 | 0.924901 | undefined | undefined |
| 2022 | control_w95 | 0.950980 | 0.954869 | 0.003889 |
| 2022 | w93 | 0.931373 | 0.947743 | 0.016371 |
| 2022 | w90 | 0.901961 | 0.938242 | 0.036281 |
| 2022 | run95 | 0.754902 | 0.912114 | 0.157212 |
| 2022 | run90 | 0.754902 | 0.912114 | 0.157212 |
| 2023 | control_w95 | 0.950119 | 0.918054 | -0.032065 |
| 2023 | w93 | 0.931116 | 0.898848 | -0.032269 |
| 2023 | w90 | 0.900238 | 0.790013 | -0.110225 |
| 2023 | run95 | 0.935867 | 0.911652 | -0.024215 |
| 2023 | run90 | 0.617577 | 0.604353 | -0.013224 |

Değerlendirme recall'ı ile kalibrasyon recall'ı arasındaki fark kontrol için −0.0321 ile 0.0210, `w93` için
−0.0323 ile 0.0276, `w90` için −0.1102 ile 0.0417, `run95` için −0.0384 ile 0.2161 ve `run90` için −0.1076 ile
0.2161 arasındadır. Bazı kalibrasyon yıllarında az pozitif seri vardır: 2017 için 7, 2022 için 9 ve 2018 için 6.
Bu kadar az seriyle seri kuralları kabadır: `run95` ve `run90`, 2017, 2018 ve 2022'de aynı eşiği seçer. Bu
nedenle kalibrasyon yılı, değerlendirme yılı için gürültülü ve bazen yanlı bir kılavuzdur.

## Belirsizlik

Birincil kol için kural eksi kontrol, eşleştirilmiş tam-HARP bootstrap aralıkları (1000 çekiliş, tohum 24):

| year | rule | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | w93 | episode_precision_diff | -0.004148 | 0.015479 | 1000 | 0 |
| 2014 | w93 | fp_diff | -3031.225000 | -2073.875000 | 1000 | 0 |
| 2014 | w90 | episode_precision_diff | 0.006529 | 0.026714 | 1000 | 0 |
| 2014 | w90 | fp_diff | -5503.025000 | -3873.775000 | 1000 | 0 |
| 2014 | run95 | episode_precision_diff | 0.001379 | 0.018309 | 1000 | 0 |
| 2014 | run95 | fp_diff | -4696.475000 | -3277.850000 | 1000 | 0 |
| 2014 | run90 | episode_precision_diff | 0.009788 | 0.061084 | 1000 | 0 |
| 2014 | run90 | fp_diff | -12602.125000 | -9195.975000 | 1000 | 0 |
| 2015 | w93 | episode_precision_diff | -0.002919 | 0.015807 | 1000 | 0 |
| 2015 | w93 | fp_diff | -1855.125000 | -1163.000000 | 1000 | 0 |
| 2015 | w90 | episode_precision_diff | -0.005017 | 0.031072 | 1000 | 0 |
| 2015 | w90 | fp_diff | -3544.025000 | -2211.975000 | 1000 | 0 |
| 2015 | run95 | episode_precision_diff | 0.006457 | 0.061697 | 1000 | 0 |
| 2015 | run95 | fp_diff | -4790.000000 | -3012.800000 | 1000 | 0 |
| 2015 | run90 | episode_precision_diff | 0.008612 | 0.057115 | 1000 | 0 |
| 2015 | run90 | fp_diff | -5989.350000 | -3777.900000 | 1000 | 0 |
| 2016 | w93 | episode_precision_diff | -0.000062 | 0.014137 | 1000 | 0 |
| 2016 | w93 | fp_diff | -1206.025000 | -695.000000 | 1000 | 0 |
| 2016 | w90 | episode_precision_diff | -0.005205 | 0.014080 | 1000 | 0 |
| 2016 | w90 | fp_diff | -3165.125000 | -1925.950000 | 1000 | 0 |
| 2016 | run95 | episode_precision_diff | -0.015991 | 0.005447 | 1000 | 0 |
| 2016 | run95 | fp_diff | -3987.000000 | -2411.800000 | 1000 | 0 |
| 2016 | run90 | episode_precision_diff | -0.011167 | 0.037001 | 1000 | 0 |
| 2016 | run90 | fp_diff | -5943.075000 | -3601.875000 | 1000 | 0 |
| 2017 | w93 | episode_precision_diff | -0.000797 | 0.003685 | 1000 | 0 |
| 2017 | w93 | fp_diff | -18.000000 | -5.000000 | 1000 | 0 |
| 2017 | w90 | episode_precision_diff | -0.001727 | 0.006553 | 1000 | 0 |
| 2017 | w90 | fp_diff | -67.000000 | -26.000000 | 1000 | 0 |
| 2017 | run95 | episode_precision_diff | 0.000000 | 0.071865 | 1000 | 0 |
| 2017 | run95 | fp_diff | -960.025000 | -374.000000 | 1000 | 0 |
| 2017 | run90 | episode_precision_diff | 0.000000 | 0.071865 | 1000 | 0 |
| 2017 | run90 | fp_diff | -960.025000 | -374.000000 | 1000 | 0 |
| 2018 | w93 | episode_precision_diff | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | w93 | fp_diff | -240.025000 | -64.000000 | 1000 | 0 |
| 2018 | w90 | episode_precision_diff | 0.000000 | 0.000000 | 994 | 6 |
| 2018 | w90 | fp_diff | -769.075000 | -131.000000 | 1000 | 0 |
| 2018 | run95 | episode_precision_diff | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | run95 | fp_diff | -346.050000 | -84.975000 | 1000 | 0 |
| 2018 | run90 | episode_precision_diff | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | run90 | fp_diff | -346.050000 | -84.975000 | 1000 | 0 |
| 2022 | w93 | episode_precision_diff | -0.000034 | 0.002485 | 1000 | 0 |
| 2022 | w93 | fp_diff | -1269.100000 | -841.950000 | 1000 | 0 |
| 2022 | w90 | episode_precision_diff | -0.002275 | 0.003378 | 1000 | 0 |
| 2022 | w90 | fp_diff | -2265.150000 | -1513.950000 | 1000 | 0 |
| 2022 | run95 | episode_precision_diff | 0.000911 | 0.012382 | 1000 | 0 |
| 2022 | run95 | fp_diff | -5690.150000 | -3811.950000 | 1000 | 0 |
| 2022 | run90 | episode_precision_diff | 0.000911 | 0.012382 | 1000 | 0 |
| 2022 | run90 | fp_diff | -5690.150000 | -3811.950000 | 1000 | 0 |
| 2023 | w93 | episode_precision_diff | 0.003210 | 0.019414 | 1000 | 0 |
| 2023 | w93 | fp_diff | -3348.025000 | -2231.975000 | 1000 | 0 |
| 2023 | w90 | episode_precision_diff | 0.017828 | 0.059132 | 1000 | 0 |
| 2023 | w90 | fp_diff | -7858.175000 | -5353.950000 | 1000 | 0 |
| 2023 | run95 | episode_precision_diff | 0.000760 | 0.010917 | 1000 | 0 |
| 2023 | run95 | fp_diff | -2665.200000 | -1777.650000 | 1000 | 0 |
| 2023 | run90 | episode_precision_diff | 0.052931 | 0.151780 | 1000 | 0 |
| 2023 | run90 | fp_diff | -11401.225000 | -7817.850000 | 1000 | 0 |

fp_diff aralıkları her kural için her yılda sıfırın altındadır. Dönem precision kazancı `w93` için yalnızca
2023'te, `w90` için 2014 ve 2023'te, `run95` ile `run90` için 2014, 2015, 2022 ve 2023'te sıfırı dışlar; 2016,
2017 ve 2018'de hiçbir kural için dışlamaz. Aralıklar dondurulmuş seçilen eşiklere koşulludur; eşik seçiminin
kendi belirsizliğini, yeniden eğitim belirsizliğini ve çoklu karşılaştırma düzeltmesini içermez. Geçti veya
kaldı sonucunu değiştirmezler.

## Yorum ve sınırlar

- Daha düşük kalibrasyon recall'ı sabitleyen kurallar yanlış alarmı gerçekten azaltır; ama değerlendirme
  yılında vazgeçtikleri recall, kalibrasyon yılı tarafından iyi öngörülemez. Kırılgan yıllar 2016 ve 2023,
  çoğu kural için toleransı bozar.
- `w93`, 6 yılın 4'ü ile kabule yakın tek kuraldır. 2014'te bir pozitif seri, 2016'da büyük bir recall düşüşü
  yüzünden kaybeder. Bu bir geçiş değildir ve bu sonuçlara bakılarak ona doğru ayarlama yapılmamalıdır.
- Recall toleransı içindeki önceki oracle payı gerçektir, ama bu etiketsiz kurallarla erişilemedi. Ona erişmek,
  tek bir önceki yıl recall hedefinden daha iyi bir sinyal gerektirir; bu açık sorundur.
- Önceki raporların asıl konusu olan baseline kolu değerlendirilemedi. Geliştirme özellik shard'ları geri
  yüklenip hash ile doğrulanırsa, baseline kapısı yeni bir protokol sürümüyle yeniden çalıştırılabilir.
- Sayılar daha önce incelenmiş yıllarda uyarlamalı geliştirme kanıtıdır, bağımsız test değildir. Sayımlar
  örtüşen tahmin pencereleri ve bunların gruplamasıdır; fiziksel patlama değildir. AP, Brier ve log loss eşik
  seçiminden etkilenmez. Bu sonuçlara bakılarak başka hedef, temel veya birleşik kural eklenmez.

## Yeniden üretim

```sh
export PYTHONPATH=. PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_threshold_selection.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/threshold_selection_20261108_r1
"$PY" -m pytest tests/test_threshold_selection_audit.py tests/test_threshold_selection_protocol.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261108_r1
```

Üretilen `report.json` kaynak hash değeri: `dae49d81c516a8a3bc512ccf5ef10081cc252fa162b8d0274fba97e4ff54a6b1`. Tekrarlarda yeni çıktı adı kullanın.
Üretilen dosyalar Git dışında kalır. İngilizce sürüm aynı bulguları ve sınırları kapsar.
