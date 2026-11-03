# Eğitim depolamasını kurtarma, 2026-11-03

## Durum ve kanıtlar

Kontrol sırasında yıllık TCN deneyinin koordinatörü veya eğitim işçisi
çalışmıyordu. Son doğrulanmış deney görüntüsünde 42 eğitimin 29'u tamamlanmıştı;
2014, 2015, 2016 ve 2017 yıllarının değerlendirmeleri vardı. Sıradaki eğitim
`2018/shuffled_interior_seed97`; kalan eğitim sayısı 13. Bu, her sonucun yeniden
doğrulandığı güncel bir inceleme değil, son doğrulanmış görüntüdür: bazı deney
dosyaları artık bulut yer tutucusudur. Ana `progress.json` dosyasında `training`
yazması sürecin çalıştığını kanıtlamaz. Bu kurtarma çalışmasından yeni model
skorları elde edilmedi.

Önceki hata kaynak dosyası okumasında zaman aşımıydı. Şimdiki inceleme deney
manifestlerinde ve önbellek dosyalarında da bulut yer tutucuları buldu.
3,431,065,088 baytlık `values.npy` başlangıçta bir yer tutucuydu ve sonrasında
yerel hâle geldi. Yalnızca bu dosyanın indirilmesi bütün deneyin kullanılabilir
olduğunu göstermez. macOS indirme isteklerini kabul etti; tamamlanmaları ayrıca
kontrol edilmelidir.

## Geri yüklenen dosyalar ve korunan girdiler

Daha önce geri yüklenen `config/research-direction-v1.json`, dondurulmuş yön
SHA256 değeri `31eda27d68bb1b63e4047027f7c20acf3adfc9b1e9aa4783b758c4ecb59f04cb`
ile eşleşiyor. Eksik sekiz dosya daha yayımlanmış
`a854bf32965518d74086dbde0ecb097be48d620b` commitinden kurtarıldı:

* `config/temporal-sequence-v1.json`
* `docs/temporal-execution-20261101.md`
* `helio24/sequence_training.py`
* `scripts/check_sequence_readiness.py`
* `scripts/consolidate_experiments.py`
* `scripts/materialize_sequences.py`
* `scripts/run_recency_training.py`
* `tests/test_temporal_worker.py`

`/Users/esma/Library/Application Support/Helio24/execution-20261103-r1` konumunda
ayrı bir çalışma kopyası oluşturuldu. Bu kopyadaki 11 `runner_code_hashes`
değerinin tamamı dondurulmuş protokolle eşleşiyor. `artifacts` ve `data`
girdileri özgün Desktop konumlarına bağlanıyor; bu işlem kaynak kodunu iCloud
dışına aldı, deney verilerini taşımadı. Hiçbir checkpoint veya dondurulmuş
sonuç dosyası yeniden yazılmadı. Ayrılmış 2024–2025 test verisi kapalı kaldı.
`app.py` içindeki yerel marka görünümü değişiklikleri commitlenmedi.

## Değişiklikler ve doğrulama

`scripts/check_temporal_storage.py`, yer tutucuların içeriğini açmadan dosya
metadata bilgilerini inceler. Dosyalar eksikse, erişilemiyorsa veya
`SF_DATALESS` işaretliyse çıkış kodu 2; incelenen yollar yerelde erişilebilirse
çıkış kodu 0 olur. Bu, geliştirme dönemi devam girdilerinin dizinlerini kapsayan
ihtiyatlı bir kontroldür; bağımlılık çözümlemesi veya hash doğrulaması değildir.
Erişilebilirlik incelemeden sonra değişebilir; mevcut koordinatör devam etmeden
önce dondurulmuş hashleri ve tamamlanmış çıktıları yine doğrulamalıdır.

Dashboard artık gerekli kayıtlara erişilememesini hiç başlamamış bir deneyden
ayırıyor. Doğrulanamayan tamamlanma sayılarını ve süreç durumunu gizliyor.
İsteğe bağlı yer tutucu JSON kayıtları, beklemeye neden olabilecek okuma
denenmeden atlanıyor. Desktop klasörü dışındaki koordinatör, başlatma kaydındaki
betik yolu ve eşleşen deney çıktı konumuyla tanınıyor; ilgisiz PID reddediliyor.

Depolama, izleme, dashboard ve iki dilli yayın için odaklı 20 testin tamamı geçti. Bu testler
hata yönetimini ve süreç kimliği doğrulamasını sınar; model kalitesini veya
iCloud'un bütün deney dosyalarını indirdiğini kanıtlamaz.

## Yeniden üretim ve kalan işler

Yerel çalışma kopyasında kurtarılmış Python ortamıyla çalıştırın:

```sh
cd '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' scripts/check_temporal_storage.py --root '/Users/esma/Desktop/Helio24' --run '/Users/esma/Desktop/Helio24/artifacts/temporal_years_20261101_r1' --cache '/Users/esma/Desktop/Helio24/artifacts/sequence_cache_20261101_r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' -m pytest tests/test_storage_preflight.py tests/test_experiment_monitor.py tests/test_experiment_views.py tests/test_bilingual_reports.py -q -p no:cacheprovider
```

Gerekli dosyaların yerel hâle gelmesini bekleyin, erişilebilirlik kontrolünü
yeniden çalıştırın; ardından değişmemiş koordinatörün hashleri doğrulayıp
kaydedilmiş işlerden devam etmesini sağlayın. Eğitimin ilerlediğini bildirmeden
önce yeni bir epoch checkpoint'i doğrulayın. 42 eğitimin ve yedi yıllık
değerlendirmenin tamamı doğrulandıktan sonra precision, recall, yanlış alarmlar,
kalibrasyon ve belirsizlik için eksiksiz iki dilli karşılaştırmayı üretin.
Mevcut eksik geliştirme sonuçlarına dayanarak modeli kullanıma almayın.
