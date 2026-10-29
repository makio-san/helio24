# Yanlış alarmların yoğunlaşması ve sonraki model seçimi

Bu denetim, dondurulmuş yıllık geliştirme tahminlerini karşılaştırır ve kontrollü bir
zor negatif ağırlıklı XGBoost deneyi seçer. **Yeni model henüz eğitilmedi; precision
iyileşmesi iddia edilmez.** Etiketler, tahminler, dashboard modeli ve ayrılmış 2024–2025
testi değişmedi. Tasarım `config/hard-negative-v1.json` dosyasındadır; açıkça
`design_frozen_not_executed` olarak işaretlenmiştir.

## Kanıt ve kapsam

Girdiler, `artifacts/walk_forward_20261028_r1` dizininin tamamlanmış 2014–2018, 2022 ve
2023 turlarıdır. Kaydedilmiş her artifact özeti kontrol edilir; alarmlar her dondurulmuş
kalibrasyon eşiğinden yeniden hesaplanır ve birleşik modelin FP toplamları özgün metriklerle
eşleşmek zorundadır. 2019–2021 yıllarında, önceki kalibrasyon topluluklarında pozitif örnek
olmadığından tamamlanmış tur yoktur. Korunan 2018 değerlendirme verisinde pozitif yoktur;
yanlış alarmlar ölçülebilir, recall tanımsızdır.

Bunlar uyarlamalı, geçmişe dönük geliştirme incelemeleridir; yeni modelin bağımsız
doğrulaması değildir. Sayılar bağımsız Güneş patlamalarını, bildirimleri veya uydu
etkilerini değil, örtüşen tahmin pencerelerini anlatır. Tüm oranlar 0–1 ölçeğindedir.

## Gözlem sayısıyla karşılaştırılan bölgesel yoğunlaşma

| year | negatives | fp | fpr | top10_fp | top10_fp_share | top10_negative_share |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 72918 | 13886 | 0.190433 | 2729 | 0.196529 | 0.040923 |
| 2015 | 67783 | 11453 | 0.168966 | 2696 | 0.235397 | 0.042120 |
| 2016 | 42806 | 2289 | 0.053474 | 1478 | 0.645697 | 0.060763 |
| 2017 | 19276 | 1287 | 0.066767 | 1198 | 0.930847 | 0.123055 |
| 2018 | 7799 | 359 | 0.046032 | 358 | 0.997214 | 0.237338 |
| 2022 | 50335 | 10072 | 0.200099 | 2430 | 0.241263 | 0.052210 |
| 2023 | 59585 | 5992 | 0.100562 | 1836 | 0.306409 | 0.039238 |

`fpr`, FP sayısının negatif pencere sayısına bölümüdür. En yüksek katkılı on HARP, her
yılda FP sayısıyla sonradan seçilir. FP payları, bölgelerin eşit büyüklükte olduğu
varsayımıyla değil, negatif pencere paylarıyla karşılaştırılmalıdır. 2023'te bu bölgeler
FP'nin 0.306409'unu, negatif pencerelerin yalnızca 0.039238'ini oluşturur. 2017'de karşılıkları
0.930847 ve 0.123055'tir. Dolayısıyla yoğunlaşma yalnızca bu bölgelerde daha fazla negatif
pencere gözlenmesiyle açıklanmaz. Bu, fiziksel nedeni belirlemez.

Yıl başına en fazla katkı yapan üç bölge:

| year | harp | rows | positives | negatives | fp | fpr | mean_missing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 4851 | 300 | 0 | 300 | 291 | 0.970000 | 0.011481 |
| 2014 | 4000 | 337 | 24 | 313 | 290 | 0.926518 | 0.004014 |
| 2014 | 4296 | 321 | 0 | 321 | 284 | 0.884735 | 0.006557 |
| 2015 | 5039 | 330 | 0 | 330 | 326 | 0.987879 | 0.002635 |
| 2015 | 6178 | 300 | 0 | 300 | 296 | 0.986667 | 0.009708 |
| 2015 | 6027 | 291 | 0 | 291 | 287 | 0.986254 | 0.003866 |
| 2016 | 6558 | 309 | 0 | 309 | 267 | 0.864078 | 0.005753 |
| 2016 | 6483 | 290 | 24 | 266 | 257 | 0.966165 | 0.004701 |
| 2016 | 6327 | 320 | 87 | 233 | 210 | 0.901288 | 0.004622 |
| 2017 | 6975 | 278 | 0 | 278 | 240 | 0.863309 | 0.004701 |
| 2017 | 7075 | 279 | 43 | 236 | 225 | 0.953390 | 0.005376 |
| 2017 | 7107 | 264 | 0 | 264 | 213 | 0.806818 | 0.067030 |
| 2018 | 7237 | 295 | 0 | 295 | 177 | 0.600000 | 0.049675 |
| 2018 | 7275 | 183 | 0 | 183 | 105 | 0.573770 | 0.001184 |
| 2018 | 7269 | 301 | 0 | 301 | 31 | 0.102990 | 0.002224 |
| 2022 | 8737 | 299 | 0 | 299 | 284 | 0.949833 | 0.002174 |
| 2022 | 8724 | 307 | 0 | 307 | 276 | 0.899023 | 0.002242 |
| 2022 | 8844 | 265 | 0 | 265 | 265 | 1.000000 | 0.009670 |
| 2023 | 9250 | 263 | 0 | 263 | 242 | 0.920152 | 0.004188 |
| 2023 | 10413 | 278 | 0 | 278 | 229 | 0.823741 | 0.003864 |
| 2023 | 10430 | 228 | 0 | 228 | 216 | 0.947368 | 0.004389 |

Bunlar sonradan belirlenen inceleme öncelikleridir; bölge dışlama listesi değildir.
Yıllar arasındaki farklı HARP kimlikleri farklı katalog bölgeleridir; tekrarlanan bulgu
yoğunlaşmadır, aynı fiziksel bölgenin yıllar boyunca tekrarlandığının kanıtı değildir.

## Eksik ölçümler

| missing_bin | rows | negatives | fp | positives | fpr | year |
| --- | --- | --- | --- | --- | --- | --- |
| zero | 55626 | 54389 | 9453 | 1237 | 0.173804 | 2014 |
| (0,0.01] | 3214 | 2758 | 1827 | 456 | 0.662437 | 2014 |
| (0.01,0.05] | 9266 | 8852 | 1575 | 414 | 0.177926 | 2014 |
| (0.05,1] | 7122 | 6919 | 1031 | 203 | 0.149010 | 2014 |
| zero | 52029 | 51224 | 7993 | 805 | 0.156040 | 2015 |
| (0,0.01] | 3351 | 3093 | 1763 | 258 | 0.569997 | 2015 |
| (0.01,0.05] | 6505 | 6375 | 967 | 130 | 0.151686 | 2015 |
| (0.05,1] | 7253 | 7091 | 730 | 162 | 0.102947 | 2015 |
| zero | 32362 | 32227 | 1609 | 135 | 0.049927 | 2016 |
| (0,0.01] | 1699 | 1653 | 256 | 46 | 0.154870 | 2016 |
| (0.01,0.05] | 4056 | 4056 | 189 | 0 | 0.046598 | 2016 |
| (0.05,1] | 4870 | 4870 | 235 | 0 | 0.048255 | 2016 |
| zero | 14970 | 14827 | 823 | 143 | 0.055507 | 2017 |
| (0,0.01] | 644 | 633 | 111 | 11 | 0.175355 | 2017 |
| (0.01,0.05] | 1654 | 1633 | 114 | 21 | 0.069810 | 2017 |
| (0.05,1] | 2261 | 2183 | 239 | 78 | 0.109482 | 2017 |
| zero | 5799 | 5799 | 229 | 0 | 0.039490 | 2018 |
| (0,0.01] | 215 | 215 | 56 | 0 | 0.260465 | 2018 |
| (0.01,0.05] | 755 | 755 | 31 | 0 | 0.041060 | 2018 |
| (0.05,1] | 1030 | 1030 | 43 | 0 | 0.041748 | 2018 |
| zero | 36828 | 36605 | 6411 | 223 | 0.175140 | 2022 |
| (0,0.01] | 3499 | 3351 | 2102 | 148 | 0.627275 | 2022 |
| (0.01,0.05] | 4512 | 4491 | 814 | 21 | 0.181251 | 2022 |
| (0.05,1] | 5917 | 5888 | 745 | 29 | 0.126529 | 2022 |
| zero | 44871 | 44332 | 3708 | 539 | 0.083642 | 2023 |
| (0,0.01] | 4003 | 3891 | 1442 | 112 | 0.370599 | 2023 |
| (0.01,0.05] | 5197 | 5161 | 375 | 36 | 0.072660 | 2023 |
| (0.05,1] | 6295 | 6201 | 467 | 94 | 0.075310 | 2023 |

Eksiklik aralıkları karşılaştırmadan önce sabitlendi: tam sıfır, (0,0.01], (0.01,0.05]
ve (0.05,1]. `missing_fraction`, özgün gözlem penceresindeki eksik girdileri ölçer; tam
bir cihaz kalitesi bayrağı değildir. Her aralığın FP sayısı negatif paydasıyla karşılaştırılmalıdır.
Tamamlanan her yılda en yüksek gözlenen FPR, (0,0.01] aralığındadır; fakat örüntü eksiklik
arttıkça düzenli bir yükseliş değildir. 2023'te bu oran 0.370599, sıfır eksiklikte 0.083642'dir.
Bölge bileşimi, ölçüm zamanlaması ve etiket seçimi ilişkiyi etkileyebilir; denetim nedensellik
kurmaz.

Ayrıca her yılda FP pencerelerinin çoğunda eksiklik sıfırdır. 2023'te 5992 FP penceresinin
3708'inde eksik girdi yoktur. Bu nedenle yalnızca eksik değer doldurmayı iyileştirmenin
temel çözüm olduğu gösterilmemiştir. Daha iyi skor üretmek için az eksiklikli aralık çıkarılmamalıdır.

## Süreklilik ve modellerin ortak hataları

| year | zero_positive_region_fp | complete_measurement_fp | both_models_alarm_fp | fp_windows_in_runs_ge6 | max_fp_run_windows |
| --- | --- | --- | --- | --- | --- |
| 2014 | 7646 | 9453 | 11798 | 13190 | 263 |
| 2015 | 7607 | 7993 | 9728 | 10793 | 325 |
| 2016 | 1642 | 1609 | 1470 | 2041 | 140 |
| 2017 | 998 | 823 | 1064 | 1184 | 178 |
| 2018 | 359 | 229 | 245 | 306 | 129 |
| 2022 | 8510 | 6411 | 8228 | 9429 | 258 |
| 2023 | 4576 | 3708 | 5600 | 5474 | 145 |

`zero_positive_region_fp`, korunan değerlendirme pencerelerinde pozitif olmayan bölgelerdeki
hataları sayar; o bölgelerin hiç patlamadığını kanıtlamaz. `both_models_alarm_fp`, birleşik
modelin yanlış olduğu pencerede iki bileşenin de kendi sabit kalibrasyon eşiğinde alarm
vermesini gerektirir. 2023'te bu, 5992 FP penceresinin 5600'ünde gerçekleşir: yalnızca iki
modelin anlaşmasına güvenmek gözlenen hataların çoğunu ortadan kaldırmaz.

Bir dizi, aynı HARP'ın tam bir saat aralıklı ardışık FP pencerelerini gerektirir. Eksik
veya dışlanmış zaman damgası, FP olmayan pencere veya bölge değişimi diziyi keser. En az
altı koşulu, altı tahmin penceresini sayar; altı bağımsız olay veya altı saatlik fiziksel
süre değildir. 2023'te 5992 FP penceresinin 5474'ü böyle dizilerdedir; en uzunu 145 pencere
içerir. 2018'de en uzun dizi 129 penceredir. Bu, betimsel süreklilik ölçüsüdür; sonradan
uygulanan alarm bastırma kuralı değildir. Tekrarlı bildirimleri azaltmak ayrı bir uygulama
metriğidir ve tek başına pencere düzeyindeki precision'ı iyileştirmez.

## Seçilen model deneyi ve kontroller

Çalışma hipotezi, sürekli patlama benzeri görünen bazı negatif örneklerin mevcut karar
sınırıyla yeterince ayrılamadığıdır. Bu, hata yapısından çıkarımdır; kanıtlanmış neden
değildir. Aynı 96 girdi özelliği ve mevcut hiperparametreler korunarak **yalnızca eğitim
içinde, zaman sıralı zor negatif seçimi**, ardından ağırlıklı XGBoost öğrenci modeli
seçilmiştir. Böylece geniş bir parametre araması yerine farklı öğrenme ağırlığı sınanır.

Her Y değerlendirme yılında dış eğitim yine Y-1 öncesinde biter. Öğretmen XGBoost, Y-3
yılının 1 Ocak tarihinden önce eğitilir; seçim yalnızca dış eğitimin son iki yılında yapılır.
Örtüşen gözlem/tahmin aralıkları temizlenir; öğretmen eğitiminde görülen HARP'lar seçim
bölümünden çıkarılır. Uygun, negatif olduğu bilinen eğitim pencereleri öğretmenin ham
skoruyla sıralanır; tam olarak ceil(0.10 * eligible_count) örnek seçilir. Eşitlikler tahmin
zamanı ve HARP ile belirlenimci çözülür. Değerlendirme yılı skorları, etiketleri veya hata
listeleri seçime girmez. Bu dış eğitim etiketleri son öğrenci eğitilirken erişilebilirdir;
tahmin girdisi değildir.

Aynı yıllık ayrımlarda üç sabit deney kolu karşılaştırılacaktır:

1. Mevcut, ağırlıksız referans model birleşimi.
2. Zor negatif öğrenci: seçilen negatiflerin eğitim ağırlığı 3, diğer tüm eğitim
   pencerelerinin ağırlığı 1 olur. Özgün dış eğitim satırlarının tamamı korunur.
3. Eşleştirilmiş tekdüze negatif kontrol: dış eğitimdeki tüm negatiflerin ağırlığı
   `1 + 2 * hard_negative_count / outer_training_negative_count`, pozitiflerin ağırlığı 1 olur.
   Toplam negatif ağırlığı ikinci kolla aynıdır; hedefli seçimin etkisini yalnızca negatif
   sınıfa daha fazla ağırlık vermekten ayırır.

Lojistik bileşen korunur; sabit 0.45/0.55 birleşiminde yalnızca XGBoost değiştirilir.
Her öğrencinin sigmoid kalibrasyonu aynı dış kalibrasyon yılında yeniden öğrenilir;
birleşim eşiği orada recall >=0.95 koşuluyla seçilip değiştirilmeden aktarılır. Kalibrasyon
düzenini sabit tutmak ağırlıklandırmayı ayrı sınar; olasılık öğrenimiyle eşik öğrenimini
ayırmak farklı ve henüz çalıştırılmamış deney olarak kalır. Öğretmende iki sınıf yoksa
veya uygun negatif yoksa sessizce referansa dönülmez; aday kollar kullanılamıyor olarak
işaretlenir. Özgün dış tur atlama kuralları korunur.

Otomatik model değiştirme yoktur. Sabit tasarım, karşılaştırılabilir her pozitif değerlendirme
yılında daha yüksek precision ve recall >=0.95; referansa göre yıl başına düşmeyen AP ve
artmayan Brier/log loss gerektirir. Pozitif olmayan yılların FP/FPR değerleri dahil tüm
kollar ve başarısız yıllar raporlanır. 24 tohumla eşleştirilmiş bütün HARP'ları örnekleyen
1000 bootstrap tekrarı kullanılır; aralıklar eğitilmiş model ve sabit eşik koşulludur.
Kazancı hedefli seçime bağlamak için eşleştirilmiş tekdüze kontrolden de iyi sonuç gerekir.
Bu sıkı ölçüt adayı reddedebilir. Ağırlıklandırma recall veya kalibrasyonu bozabilir;
başarı garanti değildir. Değerlendirme uyarlamalı geliştirme olarak kalır; tüm kural
dondurulana kadar ayrılmış test kapalı tutulur.

## Yeniden üretim ve sınırlamalar

```sh
.venv/bin/python scripts/audit_false_alarms.py --output artifacts/false_alarm_audit_20261029_r1
.venv/bin/python scripts/report_false_alarm_audit.py --source artifacts/false_alarm_audit_20261029_r1 --report-name false-alarm-audit-20261029
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_false-alarm-audit-20261029
```

Tekrarda dondurulmuş kanıtı koruyarak yeni çıktı dizinleri ve rapor adları kullanın.
Denetim raporu özeti değişirse yeni tasarım sürümü oluşturup rapor betiğindeki tasarım
yolunu güncelleyin; sabit protokolün üzerine yazmayın. İki sürümü gözden geçirip kaynak
özetini ve bağlantıları `docs/reports.json` ile `docs/reports.md` dosyalarına kaydedin,
ardından yeni HTML dizinine yayımlayın. Veri ve üretilen çıktılar Git dışında kalır.
Seçilen tasarım için henüz eğitim komutu yoktur: uygulama ve çalıştırma sonraki görevdir.

Denetim betimseldir; pencereler bağımlıdır, yıllık olay sıklığı değişir ve önceki etiket/kalite
dışlamaları geçerlidir. Eksiklik ilişkisi için güven aralığı veya nedensel etki değil,
gözlenen sayı ve oranları raporlar. Güneş dönüşleri arasında fiziksel bölge kimliğini
doğrulamaz, olay ilişkilerini çözmez ve herhangi bir etiketin yanlış olduğunu kanıtlamaz.

| source | SHA-256 |
| --- | --- |
| artifacts/false_alarm_audit_20261029_r1/report.json | 2da6a2804b33e7c7d0f26d7c43fccd9d00c79e4550221560fc162409d108bb23 |
| config/hard-negative-v1.json | cb016d8ff9d1942d9410332c9e639ba475f1365ca88d301c735d326d189e8730 |

