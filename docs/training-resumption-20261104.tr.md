# Doğrulanmış eğitim devamı, 2026-11-04

## Sonuç ve kapsam

Mevcut `2018/shuffled_interior_seed97` işi için eğitim yeniden başladı.
2026-11-04 00:51:50 +03:00 anında ilk epoch ve yeni checkpoint kaydedilmişti.
İşçi sürecinin CPU kullandığı ayrıca gözlendi. İlk epoch
201.77095866699892 saniye sürdü; bu, tamamlanma süresi tahmini değildir.

Girdiler geri yüklendikten sonra hazırlık ve tamamlanmış çıktılara ait beyan
edilmiş 220 dosyanın hashleri doğrulandı. 42 eğitimin 29'u tamamlanmış durumda;
2014, 2015, 2016 ve 2017 yıllarının değerlendirmeleri tamamlanmış. Bitmemiş
13 eğitimin biri şu anda çalışıyor; diğer 12 eğitim başlamadı. Bu sayılar,
çalışan eğitimin veya ait olduğu yıllık değerlendirmenin tamamlandığını söylemez.

Yeni precision, recall, yanlış alarm veya kalibrasyon sonucu yok. Eğitim
kaybı optimizasyonu anlatır, tahmin kalitesini değil. Ayrılmış 2024–2025 test
verisi kapalı kaldı. Dondurulmuş mimari, seed değerleri, epoch bütçesi, eşik
politikası ve bilimsel kaynak kodu değiştirilmedi.

## Girdilerin kurtarılması

İlk dizin taraması toplam 6,806,451 baytlık 118 bulut yer tutucusu buldu.
Yalnızca metadata incelemesi iki eksik dosyayı kaçırdı. Yeni kontrol,
erişilebilir manifestleri okuyup beyan edilen yolları açıkça kontrol ediyor;
böylece üst dizinlerin var olması silinmiş girdileri gizleyemiyor.

Dört girdi yeniden üretildi; yerlerine konmadan önce özgün hazırlık
manifestindeki SHA256 değerleriyle bayt düzeyinde birebir eşleşmeleri doğrulandı:

| Deney dizinine göre yol | SHA256 |
| --- | --- |
| `2014/target.npy` | `95126a1a894ab59d85c755e74e40744da7874b3b5cb38b4fbeafbb83f91c373b` |
| `2017/evaluation.npy` | `643ad2b28997439e1b44d07321d9ff0e9dcc412cacb04ea1dd7abb9fc8ef5a3c` |
| `2018/calibration.npy` | `643ad2b28997439e1b44d07321d9ff0e9dcc412cacb04ea1dd7abb9fc8ef5a3c` |
| `2018/evaluation-metadata.parquet` | `a96e46105e28417aaff2e3a573d3c4d49cca9dd9d91cd7c10f86cf26e5bf68e2` |

2014 eğitim hedefleri, doğrulanmış 2018 eğitim dizilerindeki aynı indeksli
pencerelerden alındı. İndeks dizileri tahmin anahtarlarıyla kaydedilmiş metadata
eşleştirilerek yeniden oluşturuldu. 2018 değerlendirme metadata dosyası, özgün
referans modelin tahmin tablosundan aynı sütun sırası ve serileştirmeyle çıkarıldı.
Metadata kurtarması değerlendirme etiketlerini sinir ağı işçisine göndermedi.
Her geri yüklemenin kabulünü yaklaşık sayısal benzerlik değil, özgün içerik
hashleri belirledi.

## Çalıştırma ve otomatik geçiş

`scripts/resume_temporal_job.py`, mevcut işi hazırlanmış dönem ve protokolle
karşılaştırır; dondurulmuş bilimsel kaynak hashlerini, direction/base/smoke
referanslarını, bütün zaman serisi önbelleğini ve bu eğitimin girdi hashlerini
doğrular; ardından değişmemiş yalıtılmış işçiyi başlatır. Yıllık koordinatörle
aynı deney kilidini tutar ve koordinatörü kapanmış bir işçi hâlâ çalışıyorsa
yeni işi reddeder. Tamamlanmış işlerde özgün kimlik, epoch sayısı ve üç çıktı
dosyasının tamamı aranır. Yılları değerlendirmez ve yeni model seçmez.

Yerel çalıştırma kopyası
`/Users/esma/Library/Application Support/Helio24/execution-20261103-r1`
konumundadır. Kurtarılmış Python ortamı
`/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python`
konumundadır. Deney ve önbellek yolları Desktop üzerinde kalır; yalnızca kodun
taşınması bunların ileride yerelde bulunacağını garanti etmez.

`scripts/await_temporal_resume.py`, manifestte beyan edilen girdilerin
erişilebilirliğini, aktif işçi bulunmamasını ve deney kilidinin boş olmasını
30 saniyede bir kontrol eder. Koşullar sağlanınca değişmemiş yıllık koordinatörü
çağırır; koordinatör bütün dondurulmuş doğrulamayı yeniden yapar ve doğrulanmış
tamamlanmış işleri atlar. Bekleme 86,400 saniyeyle sınırlıdır. Girdiler hâlâ
erişilemiyorsa bekleyici `waiting_timeout` kaydeder; eğitimin başladığını
iddia etmez. Başlatma yarışına karşı son koruma özgün koordinatörün kilididir.

Bu durum görüntüsünde toplam 104,401 baytlık sekiz tarihsel referans dosyası
yıllık koordinatörü hâlâ engelliyor: referans model ve kısa eğitim kontrolünün
`report.json` dosyaları ile 2018, 2022 ve 2023 `thresholds.json` dosyaları.
Çalışan eğitim bu dosyalara ihtiyaç duymuyor; yıllık kalibrasyon, karşılaştırma
ve eksiksiz nihai rapor için hâlâ gerekliler. Otomatik geçiş dosyaların
kurtarılmasına bağlıdır; kalan bütün eğitimin tamamlanacağı sözü değildir.

## Kanıtlar, doğrulama ve yeniden üretim

Depolama, manifest taraması, yalıtılmış iş devamı, geçiş beklemesi, süreç izleme,
dashboard ve iki dilli yayını kapsayan odaklı 37 test geçti. Testler beyan
edilmiş eksik girdileri, erişilemeyen manifestleri, değişmiş önbellek/kaynak/dönem
hashlerini, değiştirilmiş iş kimliklerini, mevcut işçileri, deney kilitlerini
ve sınırlı beklemeyi kapsıyor. Model performansını ölçmüyorlar.

Yerel kanıtlar `artifacts/runtime_recovery_20261104_r1/` içindedir:
`restored_inputs.json`, `completed_verification.json`,
`progress_confirmation.json`, `launcher.json`, `status.json` ve
`supervisor.json`. Geçiş durumu ve daha sonra oluşacak koordinatör başlatma
kaydı/günlüğü `artifacts/runtime_recovery_20261104_r2/` içindedir. Kaydedilmiş
PID, sürecin hâlâ aktif olduğunun kanıtı değildir; komutunu ve yeni kaydedilen
ilerlemeyi doğrulayın.

Aşağıdaki kontrolleri yerel çalışma kopyasından çalıştırın. Kurtarmayı elle
başlatmadan önce mevcut işçinin/bekleyicinin bu işi zaten yapmadığını doğrulayın
ve yeni bir durum veya kurtarma çıktı yolu seçin.

```sh
cd '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' scripts/check_temporal_storage.py --root '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1' --protocol '/Users/esma/Desktop/Helio24/config/temporal-sequence-v2.json' --run '/Users/esma/Desktop/Helio24/artifacts/temporal_years_20261101_r1' --cache '/Users/esma/Desktop/Helio24/artifacts/sequence_cache_20261101_r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' -m pytest tests/test_await_temporal_resume.py tests/test_resume_temporal_job.py tests/test_temporal_storage.py tests/test_storage_preflight.py tests/test_experiment_monitor.py tests/test_experiment_views.py tests/test_bilingual_reports.py -q -p no:cacheprovider
```

Tam başlatma argümanları `launcher.json` ve `supervisor.json` içinde korunuyor.
Sıradaki araştırma çıktısı, 42 eğitimin ve değerlendirilebilir yedi dönemin
tamamı doğrulandıktan sonraki eksiksiz eşleştirilmiş yıllık değerlendirmedir.
Kısmi eğitim ilerlemesi veya tek bir seed, modelin kullanıma alınmasını
belirlememelidir.
