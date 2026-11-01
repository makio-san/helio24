# Yıllık zamansal deney: bütünleştirme ve başlatma

Zaman serisi okuyucusu, yalnızca eğitimden öğrenilen ön işleme, ayrı süreçte sinir ağı
işçisi ve yıllık değerlendirme yürütücüsü uygulandı. Uygun yedi yıllık bölümün tamamı,
özgün birleşim ve kısa eğitim kontrolüyle tam örnek eşleşmesi kontrollerini geçti.
Gerçek deney başlatıldı. Bu belge başlangıç durumunun sabit bir kaydıdır;
precision artışı veya tamamlanmış yıllık sonuç bildirmez.

## Hazırlanmış örneklemler

| year | preparation | train_rows | train_positives | calibration_rows | calibration_positives | evaluation_rows | evaluation_positives |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | ready | 148508 | 2959 | 74149 | 1287 | 75228 | 2310 |
| 2015 | ready | 223647 | 4246 | 75228 | 2310 | 69138 | 1355 |
| 2016 | ready | 299785 | 6633 | 69138 | 1355 | 42987 | 181 |
| 2017 | ready | 370351 | 8036 | 42987 | 181 | 19529 | 253 |
| 2018 | ready | 413604 | 8241 | 19529 | 253 | 7799 | 0 |
| 2019 | skipped | 433399 | 8494 | 7799 | 0 | 4919 | 0 |
| 2020 | skipped | 441344 | 8494 | 4919 | 0 | 9813 | 0 |
| 2021 | skipped | 446303 | 8494 | 9813 | 0 | 28125 | 204 |
| 2022 | ready | 456126 | 8494 | 28125 | 204 | 50756 | 421 |
| 2023 | ready | 484549 | 8698 | 50756 | 421 | 60366 | 781 |

`ready`, girdi hazırlığının geçtiğini belirtir; eğitim veya değerlendirmenin bittiğini
belirtmez. On takvim yılından yedisi uygundur. Pozitif örneği olmayan 2018 değerlendirmesi
tanımsız recall ile korunur; 2019–2021 özgün referans kurallarıyla atlanır. Her bölüm özgün
sınır temizliğini ve HARP ayrımını kullanır. Tam önbellek 595671 tahmin anahtarını, anahtar
başına 60 adımı ve 24 manyetik değeri korur. Disk tabanlı diziler, her bölümü tamamen
bellekte bir tensöre dönüştürmeden indeksli erişim sağlar.

Ölçekleme, yalnızca eğitim pencerelerinden işaretli log1p ve float64 kanal istatistikleri
kullanır. Tekrarlanan gözlemler bu pencerelerde göründükleri kadar sayılır. Eksik değerler
ölçekleme sonrasında sıfırla doldurulur ve ayrı maskeler taşır; sonlu ölçeklenmiş değerler
[-8,8] aralığına kırpılır. Her bölümde iki girdi kolu ve üç tohum ortak ölçekleyici kullanır.
Girdi karıştırması tohum/HARP/UTC tahmin anahtarından deterministik üretilir, ilk/son adımı
korur ve ölçüm/maske kanallarını birlikte taşır. Batch sırası pencerenin karıştırmasını
değiştiremez.

## Sabit deney ve mevcut durum

| field | value |
| --- | --- |
| year | 2014 |
| arm | chronological |
| seed | 24 |
| completed_epochs_current_fit | 1 |
| completed_annual_evaluations | 0 |

v2 çalıştırma protokolü v1'in modelini, optimizasyon yöntemini, 10 epoch'u, 128 örneklik
batch boyutunu, 24/42/97 tohumlarını, kronolojik/karıştırılmış kolları ve yıllık bölümleri
korur: toplam 42 sinir ağı eğitimi. CPU eğitimi her eğitim için yeni Python exec sürecinde
dört iş parçacığı kullanır. Sinir ağı işçileri sklearn veya XGBoost içe aktarmaz. Önceden
görülen yerel çalışma zamanı çökmesi süreç ayrımıyla ele alınır; alttaki kesin neden
henüz çözülmemiştir.

Değerlendirme etiketleri hazırlıkta yalnızca sabit örneklem denetimleri için okunur;
sinir ağı işçilerine hiç verilmez. İşçiler eğitim etiketlerini ve etiketsiz kalibrasyon/
değerlendirme indekslerini alır. Ana süreç üç ham sigmoid olasılığının eşit ortalamasını
kalibre eder; değerlendirme metriklerinden önce recall >=0.95 eşiğini önceki kalibrasyon
yılında seçip kaydeder. Tohumlar ayrı raporlanır, aralarından seçim yapılmaz. Özgün ve kısa
eğitim referanslarının değerlendirme anahtarları aynı olmalıdır; farklı eğitim geçmişleri
açıkça belirtilir. Eşleştirilmiş HARP bootstrap ve kronolojik/karıştırılmış karşılaştırması,
bir yılın altı eğitimi bittikten sonra yapılır.

Bu kayıtta yıllık metrik karşılaştırması henüz tamamlanmamıştır. İlerleme dosyalarında
bulunan eğitim kaybı optimizasyon tanısıdır; precision, recall veya daha iyi olasılık
kanıtı değildir. Önceki sentetik CPU tahmini yaklaşık 18.31 hesaplama saatiydi; yükleme,
ön işleme, çıkarım ve değerlendirmeyi içermez. Bu bir bitiş zamanı sözü değildir.
Ayrılmış 2024–2025 testi kapalıdır.

## Kesintiden devam ve doğrulama

Tamamlanan her epoch; model parametrelerini, AdamW durumunu, torch rastgele üreteç durumunu,
NumPy batch rastgele üreteç durumunu ve epoch geçmişini atomik kaydeder. Ara checkpoint'ler
yalnızca kesintiden devam içindir; sadece son epoch değerlendirilir. Sentetik test eğitimi
zorla keser, devam ettirir ve kesintisiz eğitimle tahminlerin tam eşitliğini kontrol eder.
Son checkpoint'in yeniden kullanımı da tahminleri üretir; değişen girdi hash değerleri
çalışmayı durdurur. Ek testler yalnızca eğitimden ölçeklemeyi, eksiklikleri, anahtara bağlı
sabit karıştırmayı, anahtar eşleşmesini ve önbellek bozulmasının saptanmasını doğrular.
Toplu kontrolde 140 test geçti; güçlendirilmiş kesinti testi bu çalıştırmadan sonra ayrıca
geçti.

Devam işlemi protokolü, yürütücü kodunu, hazırlanmış girdileri, önbelleği ve tamamlanmış
işleri doğrular. Yürütücü kilidi çift çalıştırmayı engeller. İşçi hatası ana süreci
durdurur ve failure.json'a kaydedilir; tamamlanmış yıllık çıktılar yeniden kullanılmadan
önce doğrulanır. Tamamlanmış deneyin üzerine yazılmaz. Sürecin çalışması ve sonunda
bitmesi yine takip gerektirir.

## Yeniden üretim ve takip

```sh
.venv/bin/python -m pip install -r requirements-sequence.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1 --prepare-only
.venv/bin/python scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1
.venv/bin/python scripts/report_temporal_execution.py --source artifacts/temporal_years_20261101_r1 --output artifacts/temporal_execution_start_20261101_r1 --name temporal-execution-20261101
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_temporal-execution-20261101
```

Ön planda çalıştırma komutu, kesilmiş deneye tamamlanan son epoch'tan devam etmek için de
kullanılır. Mevcut yürütücü kilidi tutarken ikinci yürütücüyü başlatmayın.
`artifacts/temporal_years_20261101_r1/progress.json`, `run.log` ve her
`year/arm_seed/worker.log` ile `progress.json` dosyasını inceleyin; süreç çıkarsa
`failure.json` dosyasına bakın. Tamamlanan yıllık sonuçlar `year/finished.json` içinde;
son report.json ve metrics.csv ise uygun tüm yıllar bittikten sonra üretilir. Etkin
başlatma, launcher.json'da kayıtlı ayrılmış yerel süreçtir. Bu kayıt canlı izleyici değildir.

Bağımsız tekrarlarda yeni çıktı/önbellek dizinleri kullanın. Tasarım veya hash ile bağlı
yürütücü kodu değişirse yeni protokol sürümü sabitleyin. Yeni durum kaydı dizinleri/belge
adları kullanın; iki incelenmiş sürümü docs/reports.json ve docs/reports.md içine kaydedip
çift dilli HTML yayımlayın. Veri, önbellek, checkpoint, tahmin ve üretilmiş HTML Git dışında
kalır. Yerel app.py marka değişiklikleri commit edilmez.

| source | sha256 |
| --- | --- |
| config/temporal-sequence-v2.json | 76db8b565b8ad2ba9f0f322458dd30eb18f9d2c87d34c66ebffb76d055c7cdd0 |
| artifacts/temporal_years_20261101_r1/prepared.json | 35b38dba22048b32e82a1e6068d136d553c10a4cd486204fef71770e99e62711 |
| artifacts/temporal_execution_start_20261101_r1/report.json | ef9a2c845e8d067d2cefbdd1f442235407ea186de48dfa518e4bb393738279a1 |

