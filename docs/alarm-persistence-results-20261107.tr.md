# Alarm kalıcılığı sonuçları: yanlış alarm azalıyor, ama recall dondurulmuş sınırın altına düşüyor

## Karar ve kapsam

[Dondurulmuş protokol](alarm-persistence-protocol-20261107.tr.md), tamamlanan yedi yıllık
karşılaştırmanın dondurulmuş yıllık tahminleri ve eşikleri üzerinde bir kez çalıştırıldı (kaynak rapor
SHA256 `e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`). İki kural değerlendirildi:
alarmı yalnızca 3 (`persist_3h`) veya 6 (`persist_6h`) ardışık eşik aşımından sonra vermek;
karşılaştırma değiştirilmemiş kontrole yapıldı. Model eğitilmedi, eşik ve etiket değişmedi, ayrılmış
2024–2025 testi kapalı kaldı.

Karar: hiçbir kural, hiçbir yılda ve iki kolda da kabul kurallarını karşılamıyor. İkisi de yanlış
alarmı ve dönemleri azaltıyor ve dönem precision'ını yükseltiyor; ama ikisi de her pozitif yılda
dondurulmuş 0,02 sınırından fazla pencere recall'ı kaybediyor. Kalıcılık benimsenmedi; bu
sonuçlara bakarak başka k değeri, bekleme süresi veya birleştirme kuralı eklenmez; bu yeni bir
protokol olur.

Açıklama: ilk çalıştırma 2018'de (pozitif pencere yok, recall tanımsız) hata vererek çıktı yazmadan
durdu. Protokolün 2018 için söylediği gibi, kontrol recall'ı tanımsızsa recall koşulu uygulanmaz
yapıldı ve analiz yeniden çalıştırıldı. Bu düzeltmeden önce hiçbir sonuç görülmemişti. Kontrol,
alarm dönemi incelemesini her yılda ve her kolda birebir yeniden üretiyor.

## Kabul sonucu

| arm | candidate | k | years_met | required_years | all_year_primary |
| --- | --- | --- | --- | --- | --- |
| baseline | persist_3h | 3 | 0 | 6 | no |
| baseline | persist_6h | 6 | 0 | 6 | no |
| chronological | persist_3h | 3 | 0 | 6 | no |
| chronological | persist_6h | 6 | 0 | 6 | no |

Bir aday, aynı k için altı pozitif yılın hepsinde dört yıllık koşulun tamamını sağlamalıdır.

| year | candidate | episode_precision_higher | fp_lower | positive_runs_alarmed_not_below | recall_drop_ok | primary_met |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | persist_3h | yes | yes | no | no | no |
| 2014 | persist_6h | yes | yes | no | no | no |
| 2015 | persist_3h | yes | yes | no | no | no |
| 2015 | persist_6h | yes | yes | no | no | no |
| 2016 | persist_3h | yes | yes | yes | no | no |
| 2016 | persist_6h | yes | yes | yes | no | no |
| 2017 | persist_3h | yes | yes | yes | no | no |
| 2017 | persist_6h | yes | yes | yes | no | no |
| 2018 | persist_3h | no | yes | yes | yes | no |
| 2018 | persist_6h | no | yes | yes | yes | no |
| 2022 | persist_3h | yes | yes | yes | no | no |
| 2022 | persist_6h | yes | yes | yes | no | no |
| 2023 | persist_3h | yes | yes | yes | no | no |
| 2023 | persist_6h | yes | yes | no | no | no |

`recall_drop_ok` iki k için de altı pozitif yılın tamamında başarısız. `positive_runs_alarmed_not_below`
ayrıca iki k için 2014 ve 2015'te, 6 saat için 2023'te başarısız. 2018'de pozitif pencere yoktur ve
kapıya tabi değildir; bayraklar bütünlük için gösterilir. Betimleyici olarak raporlanan chronological
kol da altı yılın 0'ını karşılıyor.

## Baseline kolu için yıllık sonuçlar

| year | candidate | recall | recall_drop | precision | fp | episodes | hit_episodes | episode_precision | positive_runs | positive_runs_alarmed | median_alarm_delay_hours | max_alarm_delay_hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 0.945455 | 0.000000 | 0.135905 | 13886 | 686 | 67 | 0.097668 | 83 | 80 | 0.0 | 15.0 |
| 2014 | persist_3h | 0.913853 | 0.031602 | 0.142193 | 12735 | 453 | 63 | 0.139073 | 83 | 78 | 0.0 | 17.0 |
| 2014 | persist_6h | 0.871429 | 0.074026 | 0.147830 | 11604 | 355 | 60 | 0.169014 | 83 | 75 | 0.0 | 20.0 |
| 2015 | control | 0.993358 | 0.000000 | 0.105164 | 11453 | 568 | 38 | 0.066901 | 51 | 51 | 0.0 | 7.0 |
| 2015 | persist_3h | 0.967528 | 0.025830 | 0.110951 | 10505 | 339 | 36 | 0.106195 | 51 | 49 | 0.0 | 9.0 |
| 2015 | persist_6h | 0.927675 | 0.065683 | 0.115353 | 9640 | 256 | 35 | 0.136719 | 51 | 48 | 0.0 | 12.0 |
| 2016 | control | 0.972376 | 0.000000 | 0.071400 | 2289 | 204 | 4 | 0.019608 | 7 | 7 | 0.0 | 5.0 |
| 2016 | persist_3h | 0.950276 | 0.022099 | 0.081324 | 1943 | 118 | 4 | 0.033898 | 7 | 7 | 0.0 | 7.0 |
| 2016 | persist_6h | 0.917127 | 0.055249 | 0.091865 | 1641 | 84 | 4 | 0.047619 | 7 | 7 | 0.0 | 10.0 |
| 2017 | control | 0.936759 | 0.000000 | 0.155512 | 1287 | 85 | 5 | 0.058824 | 6 | 5 | 0.0 | 13.0 |
| 2017 | persist_3h | 0.905138 | 0.031621 | 0.165942 | 1151 | 50 | 5 | 0.100000 | 6 | 5 | 2.0 | 15.0 |
| 2017 | persist_6h | 0.857708 | 0.079051 | 0.174157 | 1029 | 35 | 5 | 0.142857 | 6 | 5 | 5.0 | 18.0 |
| 2018 | control | undefined | undefined | 0.000000 | 359 | 30 | 0 | 0.000000 | 0 | 0 | undefined | undefined |
| 2018 | persist_3h | undefined | undefined | 0.000000 | 307 | 14 | 0 | 0.000000 | 0 | 0 | undefined | undefined |
| 2018 | persist_6h | undefined | undefined | 0.000000 | 276 | 6 | 0 | 0.000000 | 0 | 0 | undefined | undefined |
| 2022 | control | 0.985748 | 0.000000 | 0.039573 | 10072 | 622 | 16 | 0.025723 | 16 | 16 | 0.0 | 0.0 |
| 2022 | persist_3h | 0.928741 | 0.057007 | 0.041622 | 9003 | 391 | 16 | 0.040921 | 16 | 16 | 2.0 | 2.0 |
| 2022 | persist_6h | 0.843230 | 0.142518 | 0.042673 | 7964 | 306 | 16 | 0.052288 | 16 | 16 | 5.0 | 5.0 |
| 2023 | control | 0.884763 | 0.000000 | 0.103397 | 5992 | 475 | 40 | 0.084211 | 38 | 36 | 0.0 | 13.0 |
| 2023 | persist_3h | 0.788732 | 0.096031 | 0.105842 | 5204 | 328 | 38 | 0.115854 | 38 | 36 | 2.0 | 15.0 |
| 2023 | persist_6h | 0.650448 | 0.234315 | 0.102834 | 4432 | 243 | 33 | 0.135802 | 38 | 33 | 5.0 | 18.0 |

`recall_drop`, kontrol recall'ı eksi aday recall'ıdır. Alarm gecikmesi, alarmlı bir pozitif serinin ilk
pozitif etiketli penceresinden ölçülür; raporlanır, kapı koşulu değildir. Recall kayıpları k ile artar
ve en çok 2022 ve 2023'te görülür.

## Belirsizlik

Adayın kontrolden farkı için eşleştirilmiş tam-HARP bootstrap aralıkları (1000 çekiliş, tohum 24):

| year | candidate | metric | lower | upper | valid_draws | undefined_draws |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | persist_3h | episode_precision_diff | 0.025754 | 0.056382 | 1000 | 0 |
| 2014 | persist_3h | fp_diff | -1374.025000 | -950.975000 | 1000 | 0 |
| 2014 | persist_6h | episode_precision_diff | 0.049742 | 0.092547 | 1000 | 0 |
| 2014 | persist_6h | fp_diff | -2739.150000 | -1877.975000 | 1000 | 0 |
| 2015 | persist_3h | episode_precision_diff | 0.020060 | 0.063789 | 1000 | 0 |
| 2015 | persist_3h | fp_diff | -1164.050000 | -754.850000 | 1000 | 0 |
| 2015 | persist_6h | episode_precision_diff | 0.039940 | 0.102681 | 1000 | 0 |
| 2015 | persist_6h | fp_diff | -2223.075000 | -1455.850000 | 1000 | 0 |
| 2016 | persist_3h | episode_precision_diff | 0.002824 | 0.031001 | 1000 | 0 |
| 2016 | persist_3h | fp_diff | -484.125000 | -233.000000 | 1000 | 0 |
| 2016 | persist_6h | episode_precision_diff | 0.005690 | 0.060274 | 1000 | 0 |
| 2016 | persist_6h | fp_diff | -907.050000 | -435.975000 | 1000 | 0 |
| 2017 | persist_3h | episode_precision_diff | 0.000000 | 0.108293 | 1000 | 0 |
| 2017 | persist_3h | fp_diff | -216.000000 | -70.000000 | 1000 | 0 |
| 2017 | persist_6h | episode_precision_diff | 0.000000 | 0.218805 | 1000 | 0 |
| 2017 | persist_6h | fp_diff | -423.000000 | -126.925000 | 1000 | 0 |
| 2018 | persist_3h | episode_precision_diff | 0.000000 | 0.000000 | 1000 | 0 |
| 2018 | persist_3h | fp_diff | -95.000000 | -19.975000 | 1000 | 0 |
| 2018 | persist_6h | episode_precision_diff | 0.000000 | 0.000000 | 981 | 19 |
| 2018 | persist_6h | fp_diff | -158.025000 | -30.000000 | 1000 | 0 |
| 2022 | persist_3h | episode_precision_diff | 0.006766 | 0.024970 | 1000 | 0 |
| 2022 | persist_3h | fp_diff | -1288.025000 | -870.900000 | 1000 | 0 |
| 2022 | persist_6h | episode_precision_diff | 0.011648 | 0.044252 | 1000 | 0 |
| 2022 | persist_6h | fp_diff | -2558.275000 | -1709.950000 | 1000 | 0 |
| 2023 | persist_3h | episode_precision_diff | 0.016722 | 0.049083 | 1000 | 0 |
| 2023 | persist_3h | fp_diff | -967.000000 | -613.000000 | 1000 | 0 |
| 2023 | persist_6h | episode_precision_diff | 0.026213 | 0.079862 | 1000 | 0 |
| 2023 | persist_6h | fp_diff | -1921.025000 | -1212.925000 | 1000 | 0 |

fp_diff aralıkları her yılda sıfırı dışlar; yani yanlış alarm azalması bu dondurulmuş tahminlerin
örnekleme rastlantısı değildir. Dönem precision kazancı da 2014, 2015, 2016, 2022 ve 2023'te sıfırı
dışlar; 2017'de alt sınır sıfırdır ve 2018'de pozitif pencere yoktur. Aralıklar dondurulmuş tahmin ve
eşiklere koşulludur, yeniden eğitim belirsizliğini ve çoklu karşılaştırma düzeltmesini içermez.
Recall başarısızlığını değiştirmezler.

## Birleşik sayımlar

Yedi yılın toplamı; 2018 dönem ve yanlış alarmları dahil.

| arm | candidate | k | tp | fp | fn | tn | episodes | hit_episodes | positive_runs | positive_runs_alarmed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | control | 1 | 5049 | 45338 | 252 | 275164 | 2670 | 170 | 201 | 195 |
| baseline | persist_3h | 3 | 4830 | 40848 | 471 | 279654 | 1693 | 162 | 201 | 191 |
| baseline | persist_6h | 6 | 4516 | 36586 | 785 | 283916 | 1285 | 153 | 201 | 184 |
| chronological | control | 1 | 5029 | 64671 | 272 | 255831 | 3558 | 166 | 201 | 194 |
| chronological | persist_3h | 3 | 4824 | 58563 | 477 | 261939 | 2341 | 159 | 201 | 189 |
| chronological | persist_6h | 6 | 4527 | 52470 | 774 | 268032 | 1798 | 153 | 201 | 184 |

Baseline için 3 saatlik kalıcılık dönemleri 2670'ten 1693'e, yanlış alarm pencerelerini 45338'den
40848'e indirir; fakat doğru alarm pencereleri 5049'dan 4830'a düşer. 6 saatte dönemler 1285'e ve
yanlış alarm pencereleri 36586'ya iner; doğru alarm pencereleri 4516'dır ve 201 pozitif serinin 195'i
yerine 184'ü alarmlıdır.

## Yorum ve sınırlar

- Kalıcılık alarm sayısı üzerinde amaçlandığı gibi çalışır: kısa ve tamamen negatif dönemler kalkar.
- Bedeli, her olayın başındaki kaçan pozitif pencereler, az sayıda kaybedilen pozitif seri ve en az
  k eksi bir saatlik gecikmedir.
- Bu protokol kalıcılığı, alarm eşiğini yükseltmekle karşılaştırmadı; eşik yükseltmek de recall'ı
  daha az yanlış alarma değiş tokuş eder. Sonuç, kalıcılığın daha yüksek bir eşikten daha iyi bir
  ödünleşim olduğunu göstermez.
- Sayılar daha önce incelenmiş yıllarda uyarlamalı geliştirme kanıtıdır, bağımsız test değildir.
  Pencere ve dönem sayıları örtüşen tahmin pencereleridir; fiziksel patlama veya bağımsız olay
  değildir. AP, Brier ve log loss bu kuralla değişmez.
- Yanlış alarm yükü yüksek kalır: en iyi aday bile birleşik baseline'da 201 pozitif seriye karşılık
  1132 tamamen negatif dönem bırakır.

## Yeniden üretim

```sh
export PYTHONPATH=. PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_alarm_persistence.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --episode-audit artifacts/alarm_episodes_20261107_r2 --output artifacts/alarm_persistence_20261107_r1
"$PY" -m pytest tests/test_alarm_persistence_audit.py tests/test_alarm_persistence_protocol.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r6
```

Üretilen `report.json` kaynak hash değeri: `242b78592fb9c64d1a20809be5179874783bde54a7bc4731fc960fa43841f175`. Tekrarlarda yeni çıktı adı kullanın.
Üretilen dosyalar Git dışında kalır. İngilizce sürüm aynı bulguları ve sınırları kapsar.
