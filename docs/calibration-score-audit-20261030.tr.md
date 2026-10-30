# Kalibrasyon skor dağılımları ve bölgesel eşik duyarlılığı

Denetim, eşik duyarlılığı için iki somut bulgu ortaya koyuyor: pozitif pencereler çok az
HARP'ta yoğunlaşabiliyor ve pozitif skorların alt kuyruğu yılın yarıları arasında belirgin
değişebiliyor. Bu betimsel kanıttır; fiziksel nedenin veya yeni model iyileşmesinin kanıtı
değildir. Model, etiket, uygulama eşiği ve değerlendirme topluluğu değiştirilmedi;
ayrılmış 2024–2025 testi kapalı kaldı.

## Kapsam ve yöntem

`artifacts/walk_forward_20261028_r1` içindeki sabit yıllık modeller özetleriyle doğrulanır.
Tamamlanan her değerlendirme yılı için önceki kalibrasyon yılının tamamı, erken yarısı
ve geç yarısı incelenir. Temmuz sınırı, önceki deneyde olduğu gibi sınırı aşan gözlem/tahmin
pencerelerini temizler; erken yarıyla ortak HARP'ları geç yarıdan çıkarır. Bu işlem yarım
yıllık bileşimi değiştirir; tam yıllık topluluk, temizlenmiş yarıların toplamına eşit
olmak zorunda değildir. Önceki 2019–2021 dış tur atlamaları korunur.

Üç dönem de o yılın aynı sabit tam yıllık sigmoid kalibratörleri ve 0.45 lojistik/0.55
XGBoost birleşimiyle puanlanır. Böylece yarıları karşılaştırırken skor dönüşümü değişmez;
ancak tam yıllık kalibratörler o yılın etiketlerini gördüğünden erken yarı için ileriye
dönük tahmin üretilmiş olmaz. Temel sınıflandırıcılar daha önce eğitilse de skorlar
kalibrasyon açısından örneklem içidir. Yeni sınıflandırıcı veya kalibratör öğrenilmez;
bu denetimde değerlendirme yılı tahmin sonuçları kullanılmaz.

## Her dönemi kaç pozitif bölge destekliyor?

| evaluation_year | calibration_year | period | rows | positives | positive_regions | top1_positive_share | top3_positive_share | concentration_equivalent_regions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 2013 | full | 74149 | 1287 | 31 | 0.107226 | 0.253302 | 21.683344 |
| 2014 | 2013 | early | 33718 | 406 | 14 | 0.160099 | 0.354680 | 11.851884 |
| 2014 | 2013 | late | 39614 | 881 | 17 | 0.156640 | 0.370034 | 12.422352 |
| 2015 | 2014 | full | 75228 | 2310 | 44 | 0.130736 | 0.282684 | 20.992730 |
| 2015 | 2014 | early | 36445 | 1215 | 27 | 0.179424 | 0.362140 | 14.148624 |
| 2015 | 2014 | late | 37472 | 1054 | 16 | 0.286528 | 0.519924 | 7.497577 |
| 2016 | 2015 | full | 69138 | 1355 | 24 | 0.118081 | 0.346125 | 15.251277 |
| 2016 | 2015 | early | 38615 | 692 | 13 | 0.228324 | 0.510116 | 8.401418 |
| 2016 | 2015 | late | 29912 | 663 | 11 | 0.241327 | 0.553544 | 6.934687 |
| 2017 | 2016 | full | 42987 | 181 | 4 | 0.480663 | 0.878453 | 2.996524 |
| 2017 | 2016 | early | 26232 | 111 | 2 | 0.783784 | 1.000000 | 1.512707 |
| 2017 | 2016 | late | 16505 | 70 | 2 | 0.685714 | 1.000000 | 1.757532 |
| 2018 | 2017 | full | 19529 | 253 | 3 | 0.573123 | 1.000000 | 2.362043 |
| 2018 | 2017 | early | 10352 | 65 | 1 | 1.000000 | 1.000000 | 1.000000 |
| 2018 | 2017 | late | 9078 | 188 | 2 | 0.771277 | 1.000000 | 1.545160 |
| 2022 | 2021 | full | 28125 | 204 | 9 | 0.205882 | 0.495098 | 7.468772 |
| 2022 | 2021 | early | 9997 | 75 | 3 | 0.560000 | 1.000000 | 2.323420 |
| 2022 | 2021 | late | 17462 | 129 | 6 | 0.271318 | 0.643411 | 5.281181 |
| 2023 | 2022 | full | 50756 | 421 | 12 | 0.175772 | 0.441805 | 9.559409 |
| 2023 | 2022 | early | 24198 | 192 | 5 | 0.375000 | 0.750000 | 4.114286 |
| 2023 | 2022 | late | 25733 | 229 | 7 | 0.323144 | 0.580786 | 5.473437 |

`positives`, bağımsız patlamaları değil, örtüşen pencereleri sayar. `positive_regions`,
en az bir korunan pozitif penceresi olan HARP sayısıdır. En yüksek paylar pozitif
pencerelerin yoğunlaşmasını gösterir. `concentration_equivalent_regions`, p_h her
bölgenin pozitif payı olmak üzere 1/sum(p_h**2) değeridir. Eşit büyüklükte bölgeler
cinsinden ifade edilen yoğunlaşma endeksidir; bağımsız örnek sayısı tahmini veya fiziksel
patlama sayısı değildir.

2017 değerlendirmesi için 2016 kalibrasyonunun geç yarısında 70 pozitif pencere yalnızca
2 HARP'tan gelir; en büyük pay 0.685714'tür. 2018 değerlendirmesi için 2017 kalibrasyonunun
erken yarısındaki 65 pozitif pencere tek HARP'tandır. 2023 değerlendirmesi için 2022
kalibrasyonunun geç yarısında 7 HARP'tan 229 pozitif pencere vardır; ilk üç bölgenin payı
0.580786'dır. Dolayısıyla yüzlerce pencere geniş bölge çeşitliliği sağlamayabilir.

## Ortak dönüşüm üzerindeki skor dağılımları

| evaluation_year | period | positive_q05 | positive_q50 | positive_q95 | negative_q05 | negative_q50 | negative_q95 | threshold | negative_alarm_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | full | 0.011580 | 0.167211 | 0.586696 | 0.000077 | 0.000430 | 0.070068 | 0.011475 | 0.174096 |
| 2014 | early | 0.004390 | 0.095331 | 0.539138 | 0.000078 | 0.000535 | 0.072008 | 0.004389 | 0.289655 |
| 2014 | late | 0.037206 | 0.224362 | 0.592614 | 0.000077 | 0.000359 | 0.069333 | 0.037206 | 0.081094 |
| 2015 | full | 0.018840 | 0.273278 | 0.770197 | 0.000269 | 0.001158 | 0.117030 | 0.018839 | 0.218739 |
| 2015 | early | 0.010665 | 0.173029 | 0.772194 | 0.000270 | 0.001083 | 0.113298 | 0.010411 | 0.298098 |
| 2015 | late | 0.048547 | 0.369536 | 0.769026 | 0.000267 | 0.001171 | 0.114980 | 0.048456 | 0.107776 |
| 2016 | full | 0.030884 | 0.272912 | 0.823479 | 0.000042 | 0.000194 | 0.062607 | 0.030831 | 0.083398 |
| 2016 | early | 0.038605 | 0.232619 | 0.804585 | 0.000042 | 0.000169 | 0.068693 | 0.038226 | 0.076840 |
| 2016 | late | 0.029660 | 0.319682 | 0.831958 | 0.000043 | 0.000221 | 0.051984 | 0.029657 | 0.076379 |
| 2017 | full | 0.012000 | 0.156537 | 0.508341 | 0.000001 | 0.000011 | 0.009410 | 0.012000 | 0.042728 |
| 2017 | early | 0.033673 | 0.314764 | 0.522029 | 0.000001 | 0.000011 | 0.009871 | 0.027813 | 0.025573 |
| 2017 | late | 0.006642 | 0.094330 | 0.249638 | 0.000001 | 0.000010 | 0.009149 | 0.006265 | 0.067721 |
| 2018 | full | 0.005685 | 0.643340 | 0.977143 | 0.000001 | 0.000010 | 0.020389 | 0.004351 | 0.086273 |
| 2018 | early | 0.001537 | 0.438571 | 0.896121 | 0.000001 | 0.000018 | 0.010618 | 0.001514 | 0.121610 |
| 2018 | late | 0.059476 | 0.833817 | 0.978899 | 0.000000 | 0.000004 | 0.032197 | 0.058659 | 0.038695 |
| 2022 | full | 0.009002 | 0.053421 | 0.166537 | 0.000133 | 0.000543 | 0.031512 | 0.008994 | 0.133161 |
| 2022 | early | 0.008219 | 0.020485 | 0.053921 | 0.000132 | 0.000475 | 0.018915 | 0.008212 | 0.115299 |
| 2022 | late | 0.024713 | 0.095064 | 0.171570 | 0.000134 | 0.000582 | 0.044298 | 0.023981 | 0.073790 |
| 2023 | full | 0.018203 | 0.077292 | 0.605342 | 0.000022 | 0.000212 | 0.032203 | 0.018203 | 0.079706 |
| 2023 | early | 0.030897 | 0.077042 | 0.414994 | 0.000022 | 0.000206 | 0.030738 | 0.030397 | 0.050821 |
| 2023 | late | 0.006854 | 0.080588 | 0.640864 | 0.000023 | 0.000234 | 0.033747 | 0.006393 | 0.180011 |

Yüzdelikler, pozitif ve negatif pencereler için ayrı hesaplanan 5., 50. ve 95. yüzdeliklerdir.
Eşik, mevcut kesin eşik seçimi yordamının o dönemde recall >=0.95 için seçtiği değerdir;
ara değerlemeli 5. yüzdeliğe eşit olmak zorunda değildir. `negative_alarm_rate`, o dönemin
eşiğinde veya üzerindeki negatif pencere oranıdır. Bunlar yeni değerlendirme metrikleri
değil, kalibrasyon incelemeleridir. Tüm skorlar ve paylar 0–1 ölçeğindedir.

2023 değerlendirmesinde erken/geç eşikler 0.030397 ve 0.006393'tür. Pozitif 5. yüzdelikler
0.030897'den 0.006854'e düşerken negatif 95. yüzdelikler 0.030738 ve 0.033747'dir.
Pozitif alt kuyruk, bu negatif kuyruk özetinden çok daha fazla değişir. Bu nedenle geç
yarı pozitiflerinin %95'ini yakalamak için daha düşük eşik gerekir. 2022 değerlendirmesinde
yön tersinedir: erken/geç eşikler 0.008212 ve 0.023981'dir. Bu yıllar arasında yıl içi
değişimin yönü sabit değildir. Bölge bileşimi, etkinlik ve korunan etiket farkları katkı
yapabilir; denetim nedenleri birbirinden ayırmaz.

## Her pozitif bölgeyi sırayla dışarıda bırakma duyarlılığı

| evaluation_year | period | threshold | loro_min | loro_max | loro_valid | loro_undefined |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | full | 0.011475 | 0.009165 | 0.013358 | 31 | 0 |
| 2014 | early | 0.004389 | 0.003704 | 0.006606 | 14 | 0 |
| 2014 | late | 0.037206 | 0.031652 | 0.049829 | 17 | 0 |
| 2015 | full | 0.018839 | 0.015741 | 0.022836 | 44 | 0 |
| 2015 | early | 0.010411 | 0.006395 | 0.014823 | 27 | 0 |
| 2015 | late | 0.048456 | 0.040604 | 0.055010 | 16 | 0 |
| 2016 | full | 0.030831 | 0.028395 | 0.036676 | 24 | 0 |
| 2016 | early | 0.038226 | 0.027657 | 0.064856 | 13 | 0 |
| 2016 | late | 0.029657 | 0.027115 | 0.036002 | 11 | 0 |
| 2017 | full | 0.012000 | 0.007103 | 0.043831 | 4 | 0 |
| 2017 | early | 0.027813 | 0.016567 | 0.043831 | 2 | 0 |
| 2017 | late | 0.006265 | 0.003033 | 0.077669 | 2 | 0 |
| 2018 | full | 0.004351 | 0.001779 | 0.058659 | 3 | 0 |
| 2018 | early | 0.001514 | undefined | undefined | 0 | 1 |
| 2018 | late | 0.058659 | 0.041224 | 0.299917 | 2 | 0 |
| 2022 | full | 0.008994 | 0.008509 | 0.016213 | 9 | 0 |
| 2022 | early | 0.008212 | 0.007776 | 0.013187 | 3 | 0 |
| 2022 | late | 0.023981 | 0.023561 | 0.033569 | 6 | 0 |
| 2023 | full | 0.018203 | 0.011763 | 0.023175 | 12 | 0 |
| 2023 | early | 0.030397 | 0.029032 | 0.039608 | 5 | 0 |
| 2023 | late | 0.006393 | 0.005466 | 0.020886 | 7 | 0 |

Her pozitif HARP için negatif pencereleri dahil tüm pencereleri geçici olarak dönemden
çıkarılır. Model skorları ve kalibratörler sabitken kalan satırlarda yalnızca recall eşiği
yeniden hesaplanır. Bir sonraki hesapta bölge geri konur. Kalıcı dışlama, kural güncellemesi
veya değerlendirme yılı optimizasyonu yapılmaz. `loro_min` ve `loro_max`, gözlenen değişim
uçlarıdır; güven aralığı değildir. `loro_undefined`, iki hedef sınıfının artık bulunmadığı
durumları sayar.

2017 değerlendirmesinin geç kalibrasyon yarısında tek pozitif HARP'ı çıkarmak, eşiği
0.006265'ten 0.003033–0.077669 aralığındaki değerlere değiştirir. 2023 değerlendirmesinin
geç yarısında karşılık gelen aralık, 0.006393 çevresinde 0.005466–0.020886'dır. 2018
değerlendirmesinin erken yarısında tek pozitif HARP'ı çıkarmak recall eşiği seçimini tanımsız
yapar. Bu örnekler öğrenilmiş skorlar sabitken bölge bileşimine duyarlılığı gösterir;
gelecekteki recall'ı tahmin etmez veya herhangi bir bölgenin yanlış etiketlendiğini kanıtlamaz.

Dönem başına mutlak değerce en büyük eşik değişimi:

| evaluation_year | period | harp | removed_positives | removed_rows | threshold_without_region | threshold_delta |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | early | 2809 | 24 | 181 | 0.006606 | 0.002217 |
| 2014 | full | 3291 | 138 | 232 | 0.009165 | -0.002311 |
| 2014 | late | 3437 | 24 | 289 | 0.049829 | 0.012624 |
| 2015 | early | 3779 | 15 | 212 | 0.014823 | 0.004411 |
| 2015 | full | 4186 | 24 | 240 | 0.022836 | 0.003997 |
| 2015 | late | 4698 | 302 | 331 | 0.040604 | -0.007852 |
| 2016 | early | 5456 | 24 | 241 | 0.064856 | 0.026631 |
| 2016 | full | 5456 | 24 | 241 | 0.036676 | 0.005845 |
| 2016 | late | 6078 | 24 | 276 | 0.036002 | 0.006345 |
| 2017 | early | 6327 | 87 | 320 | 0.043831 | 0.016018 |
| 2017 | full | 6870 | 22 | 261 | 0.043831 | 0.031831 |
| 2017 | late | 6870 | 22 | 261 | 0.077669 | 0.071405 |
| 2018 | early | 6972 | 65 | 253 | undefined | undefined |
| 2018 | full | 6972 | 65 | 253 | 0.058659 | 0.054308 |
| 2018 | late | 7075 | 43 | 279 | 0.299917 | 0.241258 |
| 2022 | early | 7570 | 24 | 279 | 0.013187 | 0.004976 |
| 2022 | full | 7570 | 24 | 279 | 0.016213 | 0.007220 |
| 2022 | late | 7770 | 24 | 277 | 0.033569 | 0.009589 |
| 2023 | early | 8206 | 24 | 190 | 0.039608 | 0.009211 |
| 2023 | full | 8155 | 72 | 196 | 0.011763 | -0.006440 |
| 2023 | late | 8882 | 24 | 100 | 0.020886 | 0.014493 |

Tam liste `region_influence.csv` içinde korunur. Tanımlı değişimi olmayan dönemde tablo,
etki değeri uydurmak yerine tanımsız satır gösterir.

## Karar ve sonraki deneyin sınırı

Geçmiş precision daha iyi görünene kadar yarım yıl sınırı tekrar tekrar kaydırılmamalıdır.
Bu denetim, kalibrasyon desteğini pencere sayısının yanında bölge çeşitliliğiyle değerlendirmeyi
gerekçelendirir. Evrensel minimum bölge sayısı veya en uygun kalibrasyon süresini belirlemez.
Sonraki aday, daha erken iç kronolojik bölümlerde sabit çok yıllık kalibrasyon pencerelerini
ve bölge çeşitliliğini karşılaştırmalıdır. Uzatılan her kalibrasyon penceresi, zaman ve
HARP ayrımıyla bütünüyle sınıflandırıcı eğitiminden sonra kalmalıdır. Karşılaştırmalar
değişen eğitim geçmişini kontrol etmeli ve son sabit kuralı aynı dış dönemlerde ölçmelidir.
Burada böyle yeni bir eğitim veya süre araması yapılmadı.

Kalibrasyon desteği yetersizse gelecekte %95 recall sözü vermek yerine açıkça raporlanmalıdır.
Kalibrasyon olasılık yorumunu ve çalışma noktasını ayarlar; zor pozitif ve negatif
örneklerin daha iyi ayrılmasını garanti etmez. Mevcut dashboard modeli korunur. Bu,
bağımsız test değil, uyarlamalı geçmişe dönük geliştirmedir; bağımlı pencereler ve önceki
etiket/kalite dışlamaları çıkarımları sınırlar.

## Yeniden üretim ve kanıt

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/audit_calibration_scores.py \
  --output artifacts/calibration_score_audit_20261030_r1
.venv/bin/python scripts/report_calibration_scores.py --source artifacts/calibration_score_audit_20261030_r1 --report-name calibration-score-audit-20261030
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_calibration-score-audit-20261030
```

Yeni artifact dizinleri ve rapor adları kullanın; tüm sabit çıktıları koruyun. İki tam
sürümü gözden geçirip kaynak özetini ve bağlantıları `docs/reports.json` ve `docs/reports.md`
dosyalarına kaydedin; ardından yeni HTML dizinine yayımlayın. Skor tabloları ve üretilen
HTML yerel, Git dışında çıktılar olarak kalır. Özgün model/eşik özetleri, denetim kodu
özetleri ve sonuç özetleri yeniden üretimi destekler. Nedensel anlamlılık testi iddia edilmez.

| source | SHA-256 |
| --- | --- |
| artifacts/calibration_score_audit_20261030_r1/report.json | 37d4773a865824d034d4701b220686575820918b4461e9c33f7c02ef4e0414dd |
| artifacts/calibration_score_audit_20261030_r1/summary.csv | 72f3d3fd48e4bc5ade803e693bde049a69f064991e0a666fc3cf09cf2b69d24c |
| artifacts/calibration_score_audit_20261030_r1/region_influence.csv | 2607f3e89c9ad2280ead59f0868677b009a1f5f91b9548661dcdefbf38928882 |

