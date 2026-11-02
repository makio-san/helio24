# Zamansal modelin yanlış alarmları: tamamlanan yılların incelenmesi

**Bulgu:** 2016 TCN gerilemesi, kalıcı bölgesel alarm dizilerinde ve yüksek ölçüm düzeyi
gruplarında yoğunlaşıyor. Ek alarmları yalnızca eksik değerler açıklamıyor. Örüntü yıla
göre değişiyor; kronolojik sıra, karıştırılmış kontrolüne karşı tutarlı üstünlük göstermedi.
Sabit deney sürdürülmeli; bu denetim modeli değiştirmeyi, eşiği ayarlamayı veya devam eden
eğitim düzenini değiştirmeyi gerekçelendirmiyor.

## Kapsam ve çalışma noktaları

Bu, tamamlanmış 2014–2016 geliştirme bölümlerinin sabit kaydıdır. Sonraki bölümler hâlâ
eğitiliyor; raporlama sırasında bitseler bile dışarıda kalır. Sabit bölüm/çıktı hash
ve özgün özellik parçası hash değerleri, tahmin anahtarları, etiketler ve yıllık bölüm
denetimleri doğrulanır. Alarm sayıları ve precision/recall sabit metrikleri yeniden
üretmelidir. 2024–2025 testine ve ham sonuç meta verisine erişilmez. Yeni eğitim yapılmaz.

Plan, genel sonuçlar görüldükten sonra ama ayrıntılı denetimden önce yazıldı. Bu uyarlamalı,
betimsel incelemedir; bağımsız ileriye dönük değerlendirme değildir. Aday ve kontrol kendi
önceki yıl kalibrasyon eşiklerini korur; recall farklı olduğu için karşılaştırma eşit
recall'da yapılmaz. Oransal skorlar 0–1 ölçeğindedir. Sayılar bağımsız patlamaları veya
bildirimleri değil, örtüşen tahmin pencerelerini ifade eder.

| year | candidate | candidate_precision | control_precision | candidate_recall | control_recall | candidate_fp | control_fp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | chronological | 0.100078 | 0.135905 | 0.945455 | 0.945455 | 19639 | 13886 |
| 2014 | shuffled_interior | 0.091195 | 0.135905 | 0.940260 | 0.945455 | 21645 | 13886 |
| 2015 | chronological | 0.105677 | 0.105164 | 0.971218 | 0.993358 | 11137 | 11453 |
| 2015 | shuffled_interior | 0.097865 | 0.105164 | 0.974170 | 0.993358 | 12168 | 11453 |
| 2016 | chronological | 0.026380 | 0.071400 | 0.955801 | 0.972376 | 6385 | 2289 |
| 2016 | shuffled_interior | 0.026896 | 0.071400 | 0.983425 | 0.972376 | 6440 | 2289 |


2015'in küçük precision artışına daha düşük recall eşlik eder. 2016'da kronolojik TCN
recall 0.955801, referans 0.972376 iken TCN 4096 daha fazla yanlış pozitif (FP) pencere
üretir. 2014'te toplam recall aynıdır, FP daha fazladır. Net FP tek başına tam başarı
koşulu değildir; kazanılan ve kaybedilen pozitif pencereler de belirlenmelidir.

## Eşleştirilmiş eklemeler ve önlenen hatalar

| year | candidate | control | extra_fp | removed_fp | shared_fp | net_fp | extra_tp | removed_tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | chronological | baseline | 6773 | 1020 | 12866 | 5753 | 53 | 53 |
| 2014 | shuffled_interior | baseline | 8503 | 744 | 13142 | 7759 | 52 | 64 |
| 2014 | chronological | shuffled_interior | 1122 | 3128 | 18517 | -2006 | 24 | 12 |
| 2015 | chronological | baseline | 2541 | 2857 | 8596 | -316 | 1 | 31 |
| 2015 | shuffled_interior | baseline | 3014 | 2299 | 9154 | 715 | 2 | 28 |
| 2015 | chronological | shuffled_interior | 1280 | 2311 | 9857 | -1031 | 4 | 8 |
| 2016 | chronological | baseline | 4446 | 350 | 1939 | 4096 | 1 | 4 |
| 2016 | shuffled_interior | baseline | 4462 | 311 | 1978 | 4151 | 4 | 2 |
| 2016 | chronological | shuffled_interior | 1285 | 1340 | 5100 | -55 | 0 | 5 |


`extra_fp`, adayın alarm verdiği ama belirtilen kontrolün vermediği negatif pencere;
`removed_fp`, bunun tersidir. `shared_fp`, ikisinin de alarm verdiği penceredir. Net
fark, eklenen eksi önlenendir ve eşitlik her grupta kontrol edilir. `extra_tp` ve
`removed_tp` aynı geçişleri pozitif pencerelerde gösterir. Bunlar pencere sayılarıdır,
benzersiz patlama sayısı değildir. 2016'da 4446 eklenen eksi 350 önlenen FP, net 4096
ek FP verir. Bir yeni TP'ye karşı dört TP kaybedilir. 2015'te 2541 eklenen eksi 2857
önlenen FP, net 316 azalma verir; bir TP kazanılırken 31 TP kaybedilir.

## Bölgesel yoğunlaşma ve kalıcılık

| year | top10_extra_fp | top10_extra_fp_share | top10_negative_share | complete_measurement_extra_fp | zero_positive_region_extra_fp | extra_fp_in_runs_ge6 | max_extra_run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 1473 | 0.217481 | 0.038111 | 5052 | 6110 | 5695 | 110 |
| 2015 | 777 | 0.305785 | 0.041426 | 1892 | 2473 | 1852 | 70 |
| 2016 | 1557 | 0.350202 | 0.064080 | 3072 | 4233 | 3946 | 107 |


En fazla ek FP üreten on HARP her karşılaştırmada sonradan ayrı seçilir. Ek FP payları,
negatif pencere gözlem paylarıyla birlikte değerlendirilmelidir. 2016'da bu paylar
0.350202 ve 0.064080'dir. Bunlar dışlama listesi değil, inceleme önceliğidir. Bölge
sıralaması ve sıfır-pozitif durumu gelecekteki değerlendirme sonuçlarını kullanır;
tahmin anında erişilebilir girdi gibi ele alınamaz.

Her yılın en fazla ek FP üreten üç bölgesi:

| year | harp | positives | negatives | extra_fp | removed_fp | net_fp |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 3601 | 0 | 309 | 177 | 3 | 174 |
| 2014 | 3620 | 0 | 314 | 177 | 0 | 177 |
| 2014 | 4888 | 0 | 276 | 171 | 0 | 171 |
| 2015 | 5831 | 0 | 308 | 143 | 26 | 117 |
| 2015 | 5724 | 0 | 261 | 103 | 4 | 99 |
| 2015 | 5022 | 0 | 321 | 98 | 6 | 92 |
| 2016 | 6789 | 0 | 272 | 229 | 0 | 229 |
| 2016 | 6289 | 0 | 286 | 181 | 0 | 181 |
| 2016 | 6515 | 0 | 267 | 174 | 0 | 174 |


2016'da HARP 6789, 272 negatif pencerede 229 ek FP ve sıfır önlenen FP içerir. O yılki
4446 ek FP'nin 3946'sı en az altı saatlik pencere dizilerine aittir; en uzun dizi 107
penceredir. Diziler aynı HARP'ta tam bir saatlik komşuluk gerektirir; eksik/dışlanmış
zaman veya eşleşmeyen pencere diziyi keser. Saatlik tahminler 12 saatlik gözlemi ve
24 saatlik hedefi örtüştürür; bunlar bağımsız tekrarlı hatalar değildir. Bildirimleri
tekilleştirmek sunumu iyileştirir, pencere precision'ını değil.

## Eksik ölçümler

| year | missing_bin | negatives | extra_fp | removed_fp | net_fp | candidate_fpr | control_fpr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | zero | 54389 | 5052 | 719 | 4333 | 0.253470 | 0.173804 |
| 2014 | (0,0.01] | 2758 | 279 | 88 | 191 | 0.731690 | 0.662437 |
| 2014 | (0.01,0.05] | 8852 | 923 | 94 | 829 | 0.271577 | 0.177926 |
| 2014 | (0.05,1] | 6919 | 519 | 119 | 400 | 0.206822 | 0.149010 |
| 2015 | zero | 51224 | 1892 | 2080 | -188 | 0.152370 | 0.156040 |
| 2015 | (0,0.01] | 3093 | 136 | 353 | -217 | 0.499838 | 0.569997 |
| 2015 | (0.01,0.05] | 6375 | 290 | 246 | 44 | 0.158588 | 0.151686 |
| 2015 | (0.05,1] | 7091 | 223 | 178 | 45 | 0.109293 | 0.102947 |
| 2016 | zero | 32227 | 3072 | 271 | 2801 | 0.136842 | 0.049927 |
| 2016 | (0,0.01] | 1653 | 402 | 16 | 386 | 0.388385 | 0.154870 |
| 2016 | (0.01,0.05] | 4056 | 447 | 28 | 419 | 0.149901 | 0.046598 |
| 2016 | (0.05,1] | 4870 | 525 | 35 | 490 | 0.148871 | 0.048255 |


Beş sabit eksiklik kategorisi erişilemeyen grubunu da içerir; bu grup CSV'de korunur,
boş olduğunda yukarıda gösterilmez. FPR aynı gruptaki FP'nin negatif pencere sayısına
oranıdır. 2016'da küçük eksiklik grubu (0,0.01] için FPR 0.388385, referansta 0.154870'dir.
Göreli risk yüksektir; ancak eksiksiz pencereler 4446 ek FP'nin 3072'sini ve 4096 net ek
FP'nin 2801'ini üretir. 2014 ve 2015'te de ek FP'nin çoğu eksiksiz pencerelerdedir.
Dolayısıyla yalnızca eksik değer doldurmayı iyileştirmek ana çözüm olarak gösterilemez.
Eksiklik ilişkisi bölge bileşimi ve ölçüm düzeyiyle karışabilir; hiçbir eksiklik grubu
veya bölge dışlanmaz, yeniden etiketlenmez.

## Yalnızca eğitimden seçilen sınırlarla ölçüm koşulları

Sekiz alan sabitlendi: USFLUX, TOTUSJH, R_VALUE ve MEANSHR için last ve delta. Her yılın
özgün eğitim verisinin sonlu değerlerinden yüzde 25/50/75 kesimleri çıkarılır; tekrar eden
kesimler kaldırılır. Değerlendirme etiketi ve skoru kesim seçmez. Gruplar sağdan kapalı
aralık kullanır; erişilemeyen değerler korunur. Değerlendirme gözlem sayısı gruplarda eşit
olmak zorunda değildir. Tam sınırlar measurement_cutpoints.csv içindedir. Bu verilerde
son değer için en yüksek grup bin4'tür:

| year | field | negatives | extra_fp | removed_fp | net_fp | candidate_fpr | control_fpr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | USFLUX__last | 18235 | 2765 | 680 | 2085 | 0.783603 | 0.669262 |
| 2014 | TOTUSJH__last | 18618 | 2852 | 746 | 2106 | 0.794070 | 0.680954 |
| 2014 | R_VALUE__last | 15521 | 2081 | 667 | 1414 | 0.842729 | 0.751627 |
| 2014 | MEANSHR__last | 16661 | 4059 | 341 | 3718 | 0.753556 | 0.530400 |
| 2015 | USFLUX__last | 12927 | 548 | 1957 | -1409 | 0.607566 | 0.716562 |
| 2015 | TOTUSJH__last | 12839 | 631 | 2002 | -1371 | 0.646779 | 0.753563 |
| 2015 | R_VALUE__last | 11460 | 497 | 2069 | -1572 | 0.702705 | 0.839878 |
| 2015 | MEANSHR__last | 10097 | 1393 | 1008 | 385 | 0.649203 | 0.611073 |
| 2016 | USFLUX__last | 6397 | 2434 | 199 | 2235 | 0.645928 | 0.296545 |
| 2016 | TOTUSJH__last | 6088 | 2394 | 244 | 2150 | 0.685611 | 0.332457 |
| 2016 | R_VALUE__last | 7008 | 2505 | 328 | 2177 | 0.623288 | 0.312643 |
| 2016 | MEANSHR__last | 8833 | 2465 | 294 | 2171 | 0.442545 | 0.196762 |


2016'da üst USFLUX__last grubu 6397 negatif pencerede 2235 net ek FP üretir;
FPR 0.645928, referansta 0.296545'tir. Üst TOTUSJH__last ve R_VALUE__last grupları
2150 ve 2177 net ek FP üretir. Üst son-değer grupları 2014'te de geriler; 2015'te üst
USFLUX/TOTUSJH/R_VALUE grupları iyileşirken üst MEANSHR yine kötüleşir. Bu, yüksek
değerleri reddeden evrensel ve kararlı bir kural değildir.

Kısa inceleme için aşağıdaki tablo 2016'da her alanın en fazla net FP üreten sonlu
grubunu seçer. Bu seçim sonradandır; tüm gruplar measurement_bins.csv içinde kalır:

| field | measurement_bin | negatives | extra_fp | removed_fp | net_fp | candidate_fpr | control_fpr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MEANSHR__delta | bin1 | 10822 | 1323 | 63 | 1260 | 0.173073 | 0.056644 |
| MEANSHR__last | bin4 | 8833 | 2465 | 294 | 2171 | 0.442545 | 0.196762 |
| R_VALUE__delta | bin1 | 9339 | 1877 | 88 | 1789 | 0.257951 | 0.066388 |
| R_VALUE__last | bin4 | 7008 | 2505 | 328 | 2177 | 0.623288 | 0.312643 |
| TOTUSJH__delta | bin4 | 8672 | 1788 | 222 | 1566 | 0.327837 | 0.147256 |
| TOTUSJH__last | bin4 | 6088 | 2394 | 244 | 2150 | 0.685611 | 0.332457 |
| USFLUX__delta | bin4 | 8370 | 1825 | 236 | 1589 | 0.353286 | 0.163441 |
| USFLUX__last | bin4 | 6397 | 2434 | 199 | 2235 | 0.645928 | 0.296545 |


Alan görünümleri örtüşür: aynı pencere birden fazla alanda yer alabilir. Sayılar bağımsız
katkılar gibi toplanmamalıdır. Delta son eksi ilk değerdir; eğim veya tam zaman serisi
örüntüsü değildir. Yüksek değer ve değişim ilişkileri fiziksel neden, etiket hatası veya
tek bir model mekanizması kanıtlamaz. Kaba etkinlik düzeyine dayalı olası kestirme,
sonraki bileşen deneyleri için hipotezdir; gösterilmiş nedensel açıklama değildir.

## Sıralama, olasılık skorları ve belirsizlik

| year | candidate_average_precision | control_average_precision | candidate_brier | control_brier | candidate_log_loss | control_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.421566 | 0.507930 | 0.022812 | 0.020661 | 0.089042 | 0.076538 |
| 2015 | 0.461100 | 0.492441 | 0.014098 | 0.013564 | 0.052287 | 0.047847 |
| 2016 | 0.146877 | 0.366443 | 0.004133 | 0.003263 | 0.019767 | 0.014523 |


Üç yılda da kronolojik TCN'nin AP'si daha düşük, Brier/log loss'u referanstan daha yüksektir.
AP alarm eşiğine bağlı değildir; bu nedenle görülen sıralama açığını yalnızca eşik sorunu
ile açıklamak yeterli değildir. Temsil, optimizasyon, sınıf ağırlığı ve dağılım değişimi
arasından nedeni ayırmaz. Kronolojik sıra, 2014 ve 2015'te karıştırılmış AP'den daha iyi;
2016'da daha kötüdür (0.146877 ve 0.187088). Sıra hipotezi tutarlı desteklenmiyor.

Kronolojik eksi referans için mevcut eşleştirilmiş HARP-bootstrap aralıkları aşağıda
yeniden verilir. Sabit model/eşiklerle 1000 çekiliş ve 24 tohumu kullanılır; yeniden
eğitim belirsizliğini içermez, bu denetimin çoklu görünümleri için düzeltme yapılmaz:

| year | metric | lower | upper | valid_draws |
| --- | --- | --- | --- | --- |
| 2014 | precision | -0.050744 | -0.023858 | 1000 |
| 2014 | recall | -0.038392 | 0.036012 | 1000 |
| 2014 | fp | 4488.800000 | 7035.675000 | 1000 |
| 2015 | precision | -0.007348 | 0.008657 | 1000 |
| 2015 | recall | -0.061816 | -0.002144 | 1000 |
| 2015 | fp | -1277.425000 | 554.250000 | 1000 |
| 2016 | precision | -0.082771 | 0.000000 | 1000 |
| 2016 | recall | -0.136364 | 0.000000 | 973 |
| 2016 | fp | 3057.900000 | 5347.175000 | 1000 |


2015 precision aralığı sıfırı kapsar; küçük nokta kazancı güvenilir iyileşme olarak
kurulmuş değildir. 2016'da bazı yeniden örneklemelerde pozitif bulunmaz, 973 geçerli
recall çekilişi kalır; precision aralığı sıfıra ulaşır. Bölge sırası veya seçilmiş ölçüm
gruplarından evrensel nedensel etki ya da bağımsız istatistiksel doğrulama çıkarılmamalıdır.

## Araştırma sonucu ve yeniden üretim

Mevcut model ve devam eden zaman serisi düzeni sabit tutulmalıdır. Yön değiştirmeden önce
yıllık deney tamamlanmalıdır. Örüntü sürerse güçlü özet-özellik referansını koruyarak yüksek
ölçümlü, çoğunlukla negatif gruplar içindeki ayrımı inceleyen bileşen deneyine öncelik
verilebilir; hibrit/statik-özet kontrolü gelecekte sabitlenecek protokol için adaydır.
Bu denetim o deneyi seçmez veya başlatmaz. Yeni eksik değer ayarları ve değerlendirmeye
göre eşik seçimi tek başına yeterli çözüm olarak desteklenmiyor.

```sh
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/audit_temporal_errors.py --plan config/temporal-error-audit-v1.json --output artifacts/temporal_error_audit_20261102_r2
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/report_temporal_errors.py --source artifacts/temporal_error_audit_20261102_r2 --name temporal-errors-20261102
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pytest tests/test_temporal_errors.py tests/test_false_alarm_audit.py tests/test_bilingual_reports.py -q
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/publish_reports.py --output artifacts/bilingual_reports_temporal-errors-20261102
```

Tekrarlarda yeni çıktı/rapor adı kullanın; sabit çıktıları koruyun. İlk denetim sürümü
korundu; r2 sabit sıralama/olasılık bağlamını ve açık grup kapsamı kontrollerini ekler.
İki tam sürümü inceleyip kaynak hash ve dil bağlantılarını docs/reports.json ile
docs/reports.md içine kaydedin; yeni dizine çift dilli HTML yayımlayın. Tam bölge,
eksiklik, dizi ve ölçüm tabloları yerel ve Git dışında CSV çıktılarında kalır. Yalnızca
analiz kodu, plan ve belgeler Git'e girer; yerel app.py marka düzenlemeleri commit edilmez.

| source | sha256 |
| --- | --- |
| artifacts/temporal_error_audit_20261102_r2/report.json | 4a4308bf4f9aa2703039c3679c7f0d26871cf2fbb2b211615939139d162b15f2 |
| config/temporal-error-audit-v1.json | f46c5bf147b1ac8c269128c4702acc12d35d9a7eb95566da45506586eff6d302 |


