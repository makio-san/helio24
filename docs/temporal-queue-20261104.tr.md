# Kalan zaman serisi eğitimleri, 2026-11-04

## Doğrulanmış durum

Önceki `2018/shuffled_interior_seed97` işi 10 epoch'un tamamını bitirdi ve
kaydedilmiş çıktıları doğrulamadan geçti. Böylece deneyde 42 eğitimin 30'u
tamamlandı. Yıllık koordinatör, başarısız bir sinir ağı eğitimi nedeniyle değil,
sekiz tarihsel referans dosyası nedeniyle beklemeye devam etti.

Artık 2022 ve 2023 için önceden belirlenmiş kalan 12 eğitim sıralı bir kuyrukta
çalışıyor. 2026-11-04 22:22:14 +03:00 anında `2022/chronological_seed24`,
10 epoch'un 1'ini ve yeni checkpoint'i kaydetmişti; işçi süreci ayrıca
doğrulandı. Dashboard görüntüsü `queue_running`, 30/42 tamamlanmış eğitim
ve kayıt uyarısı olmadığını gösterdi. Bu görüntüden sonraki ilerleme canlı
kontrol edilmelidir.

Yeni yıllık precision, recall, yanlış alarm veya kalibrasyon sonucu yok.
Yalnızca 2014, 2015, 2016 ve 2017 yıllarının değerlendirmeleri tamamlandı.
2018 eğitimlerinin tamamı kaydedilmiş olsa da yıllık değerlendirmesi bekliyor.
Model eğitiminin tamamlanması, yıllık değerlendirmenin tamamlanması veya
precision iyileşmesi olarak raporlanmamalıdır. Ayrılmış 2024–2025 test verisi
kapalı kaldı.

## Kuyruk sözleşmesi ve kontroller

`scripts/resume_temporal_queue.py`, mevcut hazırlanmış dönemleri, özgün
kol/seed sırasını ve özgün iş serileştirmesini kullanır. Hazırlık manifesti
SHA256 değeri
`35b38dba22048b32e82a1e6068d136d553c10a4cd486204fef71770e99e62711`
ile eşleşmelidir. Kuyruk ilerlemeden önce protokolü, kaynak hashlerini ve eğitim
bütçesini kontrol eder. Tamamlanmış yıllık çıktıları doğrular, mevcut iş
kimliklerini korur; her eğitimin önbelleğini, girdilerini ve tamamlanmış
çıktılarını mevcut devam doğrulayıcısına kontrol ettirir. Bitmemiş her eğitim
için değişmemiş işçi yeni bir alt süreçte çalışır. Ortak deney kilidi bütün
kuyruk boyunca tutulur; koordinatörünü kaybetmiş aktif işçiler reddedilir ve
bir hata sonraki işleri durdurur.

Çalıştırma düzenindeki değişiklik, bağımsız ve zaten belirlenmiş eğitimler
sürerken yıllık değerlendirmeyi erteler. Mimariyi, optimizasyon yöntemini,
seed değerlerini, epoch sayısını, örnek kümelerini, olasılık kalibrasyonunu veya
alarm eşiği kurallarını değiştirmez. Dondurulmuş bütçenin üzerine yeni model
adayları veya sinir ağı eğitimleri eklemez. Değerlendirme etiketleri işçiye
gönderilmez. Kurtarma sonrasında özgün yıllık koordinatör bütün deneyi yine
doğrulamalı ve özgün kalibrasyon ile değerlendirmeyi yürütmelidir.

Bütün eğitimler bittiğinde kuyruk
`fits_complete_awaiting_annual_evaluation` kaydeder; `report.json` oluşturmaz
ve bilimsel deneyi tamamlandı olarak işaretlemez. Kurtarma yeniden
başlatıldığında mevcut tamamlanmış eğitimler doğrulanıp atlanır.

## Kalan bağımlılık ve izleme

Toplam 104,401 baytlık sekiz tarihsel dosya hâlâ bulut yer tutucusudur:
referans model ve kısa eğitim kontrolünün `report.json` dosyaları ile 2018,
2022 ve 2023 `thresholds.json` dosyaları. Kuyruk, bağımsız sinir ağı eğitimleri
için bu dosyalara ihtiyaç duymaz. Nihai karşılaştırmalar için hâlâ gerekliler.

Önceki bekleyici, komutu doğrulanıp altında koordinatör süreci olmadığı
kontrol edildikten sonra kapatıldı. Yerine geçen bekleyici 172,800 saniyeyle
(48 saat) sınırlıdır; 30 saniyede bir kontrol yaparak hem girdilerin
erişilebilirliğini hem deneyin boş olmasını bekler. Ardından değişmemiş yıllık
koordinatörü çağırır. Bu koşullu bir geçiştir; dosyaların kurtarılacağını veya
48 saatte tamamlanmayı garanti etmez. Kaynak kopyası iCloud dışındadır; deney
ve önbellek Desktop üzerinde kalır ve yeniden erişilemez hâle gelebilir.

Dashboard artık kimliği doğrulanmış kuyruğu, koordinatörünü kaybetmiş işçiden
ve yıllık koordinatörden ayırır. Yeniden kullanılmış PID veya farklı çıktı
yolu reddedilir. Aktif kuyrukta 15 dakika checkpoint hareketi görülmezse eski
ilerleme uyarısı gösterilir; dashboard yalnızca kaydedilmiş JSON'a bakarak
sürecin çalıştığını varsaymaz.

## Doğrulama, kanıtlar ve yeniden üretim

Odaklı 44 testin tamamı geçti. Kapsam; değişmeyen iş serileştirmesini,
tamamlanmış çıktıların korunmasını, hazırlık hashinin reddedilmesini, kuyrukta
hataların sonraki işleri durdurmasını, ortak kilitleri, tek iş doğrulamasını,
manifestteki eksik girdileri, geçiş beklemesini, kuyruk süreç kimliğini,
dashboard çizimini ve iki dilli yayını içeriyor. Bunlar yazılım ve kurtarma
kontrolleridir; model kalitesi skorları değildir.

Kanıtlar `artifacts/runtime_recovery_20261104_r3/` içinde saklanıyor:
`status.json`, `current_job.json`, `confirmation.json`,
`previous_waiter.json` ve `handoff-supervisor.json`. Kuyruk başlatma
argümanları `artifacts/runtime_recovery_20261104_r1/launcher-queue.json`
içindedir. Yeni geçiş durumu `artifacts/runtime_recovery_20261104_r4/`
içindedir. İşçi, checkpoint'ini ve epoch geçmişini özgün
`artifacts/temporal_years_20261101_r1/2022/chronological_seed24/` yoluna yazar.

Salt okuma kontrolleri kurtarılmış Python ortamı ve yerel çalışma kopyasıyla
yeniden üretilebilir. Gerekli referans dosyaları erişilemiyorken depolama
kontrolü 2 çıkış kodu verir; bu, bağımsız eğitim kuyruğunun başarısız olduğu
anlamına gelmez.

```sh
cd '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' scripts/check_temporal_storage.py --root '/Users/esma/Library/Application Support/Helio24/execution-20261103-r1' --protocol '/Users/esma/Desktop/Helio24/config/temporal-sequence-v2.json' --run '/Users/esma/Desktop/Helio24/artifacts/temporal_years_20261101_r1' --cache '/Users/esma/Desktop/Helio24/artifacts/sequence_cache_20261101_r1'
'/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python' -m pytest tests/test_resume_temporal_queue.py tests/test_await_temporal_resume.py tests/test_resume_temporal_job.py tests/test_temporal_storage.py tests/test_storage_preflight.py tests/test_experiment_monitor.py tests/test_experiment_views.py tests/test_bilingual_reports.py -q -p no:cacheprovider
```

Kesinti sonrasında kuyruk kurtarmasını yeniden üretmek için kayıtlı kuyruk
argümanlarını yeni bir `--recovery` dizini ve aynı dondurulmuş hazırlık hashiyle
kullanın. Kaydedilmiş iş kimliklerinin geçerli kalması için özgün protokol,
deney ve önbellek yollarını koruyun. Başka bir kurtarma süreci başlatmadan önce
süreç kimliğini doğrulayın. Önceki kurtarma kanıtlarının veya dondurulmuş deney
çıktılarının üzerine yazmayın.

Sıradaki araştırma çıktısı, 42 eğitimin ve değerlendirilebilir yedi yılın
tamamı doğrulandıktan sonraki eksiksiz iki dilli yıllık karşılaştırma olmaya
devam ediyor. Yalnızca bu çalıştırma ilerlemesi modelin kullanıma alınmasını
gerekçelendirmez.
