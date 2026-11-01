# Çalışma ortamının kurtarılması ve zamansal eğitime devam

Eğitim, bulut tarafından yönetilen Masaüstü dışındaki yerel Python ortamıyla yeniden
başlatıldı. Mevcut deney ve sabit çalıştırma protokolü korundu. Bu belge operasyonel
kurtarma durumunun kaydıdır; yeni precision, recall veya yıllık karşılaştırma bildirmez.

## Gözlenen hata ve kurtarma

İşçi, 2015/chronological/seed42 eğitiminden önce Python site modülünü içe aktarırken ve
sanal ortam yapılandırmasını okurken durdu. Hata `TimeoutError: [Errno 60] Operation timed out`
idi. macOS `.venv/pyvenv.cfg` ve `.git/config` dosyalarını `dataless` işaretlemişti;
File Provider yapılandırmanın indirilmediğini bildiriyordu. İlk taramada sanal ortamda
2136 dataless dosya bulundu. Keep Downloaded etkinleştirilip indirme istekleri gönderilince
kritik yapılandırma yerelleşti ve Python açıldı; ancak 2097 ortam dosyası erişilemez kaldı,
bilimsel paketleri içe aktarma hâlâ zaman aşımına uğradı. Keep Downloaded ayarının açık
olduğu doğrulandı. Kalan bulut indirmelerinin neden takıldığı belirlenmedi; RAM yetersizliği
veya diskin tamamen dolu olduğu kanıtlanmadı.

Yeni ortam
`/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101`
konumunda oluşturuldu. Python 3.14.3 olarak kaldı; 87 dağıtımın tamamının sürümleri eski
kurulumun dist-info dizin adlarından sabitlendi. Yeni kurulumun paket meta verisi tüm
sabit sürümlerle karşılaştırıldı ve sürüm uyuşmazlığı bulunmadı. Mevcut sanal ortam
dosyaları, deney girdileri, checkpoint'ler ve sabit raporlar korundu.

| field | value |
| --- | --- |
| original_python | 3.14.3 |
| replacement_python | 3.14.3 |
| pinned_packages | 87 |
| package_version_mismatches | 0 |
| tests_passed | 6 |
| completed_fits_retained | 7 |
| planned_fits | 42 |
| resumed_year | 2015 |
| resumed_arm | chronological |
| resumed_seed | 42 |
| completed_epochs_current_fit | 1 |
| prediction_files_identical | 2 |
| cloud_venv_dataless_before_rebuild | 2097 |


Epoch sayısı kayıt oluşturulduğu andaki durumdur; canlı sayaç değildir. Korunan yedi
eğitim, 2014 için altı ve 2015 için bir eğitimden oluşur. Devam işlemi
2015/chronological/seed42 ile ilerler. Özgün yürütücü kod, protokol, girdi/önbellek hash
ve tamamlanmış çıktı hash değerlerini doğrular; tamamlanmış yıllık değerlendirmeleri ve
eğitimleri atlar. Yeni başlatıcı `artifacts/runtime_recovery_20261101_r1/launcher.json`
içindedir; ilk deney başlatıcısı tarihsel kayıt olarak kalır. Özgün hata bu kurtarma
dizinine kopyalandı. Etkin deneydeki eski failure.json önceki durmayı kaydeder; yeniden
başlatılan çalışmayı mevcut süreç, işçi ilerlemesi ve günlüklerden değerlendirin.

## Doğrulama ve sınırlar

Odaklı altı test geçti: üç zaman serisi ön işleme/önbellek testi, bir ayrı süreçte işçi
kesinti/devam testi ve iki yıllık değerlendirme testi. Bu kurtarma için tüm test takımının
geçtiği iddia edilmez. Ayrıca tamamlanmış 2014/chronological/seed24 checkpoint'i ayrı bir
yeniden üretim dizinine kopyalandı. Değişmeyen işçi, son epoch durumunu yükleyerek yeniden
eğitim yapmadan kalibrasyon ve değerlendirme tahminlerini üretti. İki `.npy` dosyasının
SHA-256 değeri de özgün çıktılarla tam aynıydı. Kanıtlar kurtarma dizinindeki
`verification.json` ve `replay/result.json` içindedir.

Bu, paket sürümü uyumunu ve bir checkpoint için tahminin yeniden üretimini doğrular;
gelecekteki tüm eğitimlerin ortam kurulum ayrıntılarından etkilenmeyeceğini kanıtlamaz.
Çalışma ortamı dosyaları bulut tarafından yönetilen proje dışındadır; kaynak ve veri yolları
hâlâ Masaüstü projesini kullanır. Keep Downloaded ve kaynak erişilebilirliği önemini korur.
Başlatmadan sonra süreç ve işçinin CPU kullanımı kontrol edildi. Tamamlanma hâlâ takip
gerektirir. Mimari, optimizasyon yöntemi, tohum, bölüm, eşik kuralı veya ayrılmış teste
erişim değişmedi. Model uygulamaya alınmadı.

## Yeniden üretim ve takip

```sh
/opt/homebrew/bin/python3.14 -m venv "/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101"
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pip install -r requirements-runtime-recovery-20261101.txt
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pytest tests/test_sequence_training.py tests/test_temporal_worker.py tests/test_temporal_evaluation.py -q
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -u scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/publish_reports.py --output artifacts/bilingual_reports_runtime-recovery-20261101
```

Bağımsız yeni kurtarmada yeni çalışma ortamı ve kanıt dizini kullanın. Yukarıdaki eğitim
komutu mevcut deneye devam eder; etkin yürütücüyle eşzamanlı başlatmayın. Mevcut kilitler
çift yürütücüyü engeller. Seçilen yorumlayıcıyı ve paket sürümlerini kaydedin. Tahmin
kontrolünü yinelemek için tamamlanmış job.json ve checkpoint.pt dosyalarını yeni yeniden
üretim dizinine kopyalayın, scripts/temporal_worker.py betiğini bu işle çağırın; ardından
calibration.npy ve evaluation.npy SHA-256 değerlerini özgünlerle karşılaştırın. Özgün
tamamlanmış iş dosyalarını değiştirmeyin. Eksik eğitime devamda checkpoint'ler değişmeyen
protokolde belirtildiği gibi optimizer ve rastgele üreteç durumlarını geri yükler.

`artifacts/temporal_years_20261101_r1/progress.json` ve
`2015/chronological_seed42/progress.json` ile worker.log dosyasını inceleyin. Süreç kimliği
ve gerçek komut yeni kurtarma başlatıcısındadır. Özgün hatayı tarihsel kanıt olarak koruyun;
sonraki hata etkin deneyin failure.json dosyasını güncelleyebilir. Yeni rapor yayını yeni
çıktı dizini kullanmalıdır. İki tam belge sürümü çift dilli indeks üzerinden kaydedilir.
Gereksinimler ve belgeler commit edilir; ortamlar, veri, yeniden üretim çıktıları ve
checkpoint'ler Git dışında kalır. Yerel app.py değişiklikleri commit edilmez.

| source | sha256 |
| --- | --- |
| config/temporal-sequence-v2.json | 76db8b565b8ad2ba9f0f322458dd30eb18f9d2c87d34c66ebffb76d055c7cdd0 |
| requirements-runtime-recovery-20261101.txt | 1b719da8aee31b78fd0bc511007132957247813e6a2533b72dcfe649f95aca87 |
| artifacts/runtime_recovery_20261101_r1/verification.json | 65d7e3d63ca0296ea547b0e7bd7758168723cea81ba4d085a786e3f3c2a0d118 |
| artifacts/runtime_recovery_20261101_r1/launcher.json | e9956651da33f1b30c6c81d9cbfebe311b69b0dbe3f2e873f60185082074068b |
| artifacts/runtime_recovery_20261101_r1/original_failure.json | 4490acb68df9684270293aed0d3040c7f98c8395925a3b69fadbd0066e1df8db |
| artifacts/runtime_recovery_20261101_r1/recovery_report.json | 718e7539b964d66b0b166a966913e39ca6353935cafe179dfef5f1daad0c2091 |

