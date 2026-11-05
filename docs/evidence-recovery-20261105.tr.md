# Tamamlanan eğitimler ve referans kanıtların kurtarılması

## 2026-11-05 tarihindeki durum

Planlanan 42 sinir ağı eğitiminin tamamı bitti. Kuyruk tamamlanmayı
2026-11-05T04:14:24.549819+00:00 zamanında kaydetti. 2014, 2015,
2016 ve 2017 yıllarının değerlendirmeleri mevcut; 2018, 2022 ve 2023
değerlendirmeleri bekliyor. Eğitimin bitmesi precision artışını kanıtlamaz.
Yeni nihai metrikler henüz yok ve ayrılmış 2024–2025 testi kapalı tutuluyor.

## Referans deneyin birebir kurtarılması

Geçmiş referans raporu; kaydedilmiş tahminler, güvenilir yerel eğitilmiş
modeller, hazırlanmış bölüm denetimleri ve özgün metrik fonksiyonlarıyla
yeniden oluşturuldu. 63,294 baytlık içerik, dondurulmuş raporun SHA256
değeriyle birebir eşleşiyor:
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`.

Eksik veya yalnızca bulutta bulunan 26 referans dosyası, toplam 184,785 bayt,
geri yüklendi. Geri yüklenen her dosya özgün rapor manifestindeki hash ile;
raporun kendisi de dondurulmuş protokolle eşleşiyor. Okunabilir dosyaların
üzerine yazılmadı, içerikleri doğrulandı. Bulut yer tutucuları değiştirilmeden
önce kurtarma yedeğine taşındı. Hiçbir model yeniden eğitilmedi ve hiçbir eşik
değiştirilmedi. Yerel geri yükleme envanteri:
`artifacts/runtime_recovery_20261105_r1/baseline-restoration.json`.

## Devam eden depolama kısıtı

Yıllık değerlendirme koordinatörünün erişemediği referans girdiler sekizden
dörde indi: kısa kalibrasyon kontrolünün `report.json` dosyası ile 2018,
2022 ve 2023 `thresholds.json` dosyaları. Bu raporu bağımsız olarak yeniden
oluşturma girişimi, yalnızca bulutta görünen `2019/predictions.parquet`
dosyasında duruyor. Bu dosya geçmiş raporu yeniden üretmek için gerekiyor;
yeni bir yıllık değerlendirme veya eğitim eklemek için değil.

macOS, proje ve bu tahmin dosyası için `isKeepDownloaded=1` bildiriyor,
ancak dosya indirilmiş değil. Sağlayıcı metaverisinde yükleme hatası
`NSFileProviderErrorDomain -1005`, altta yatan
`open error: 45 (Operation not supported)` ve “Dosya yok.” mesajı bulunuyor.
Bu bilgi, kullanılabilir bir uzak kopyanın varlığını kanıtlamaz. Projenin ve
belirli dosyaların indirilmesi istendi, `fileproviderd` ve `bird` yeniden
başlatıldı, kritik dosyalar tekrar istendi. Bu durum kaydında dosyalar hâlâ
yer tutucu. Genel Mac Saklama Alanını Optimize Et ayarı başarıyla
değiştirilemedi veya doğrulanamadı. İndirilenleri Tut bir saklama talebidir;
kurtarmanın gerçekleştiğini göstermez.

Mevcut gözetici, özgün yıllık koordinatörü çağırmadan önce doğrulanmış yerel
girdileri beklemeye devam ediyor. Dondurulmuş hash kontrolleri atlanmamalı veya
eksik olasılıklar uydurulmamalı. Özgün float64 özellik özetleriyle float32
zaman serisi önbelleğinden yeniden hesaplanan özetlerin aynı olduğu
varsayılamaz. Deneyin nihai olarak tamamlandığı veya modelin kabul edildiği
iddia edilmiyor.

## Yeniden üretim

Kurtarılmış Python ortamını ve yeni bir hazırlık dizinini kullanın:

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261105
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/reconstruct_baseline_evidence.py --output /tmp/helio24-baseline-review-new
"$PY" scripts/check_temporal_storage.py --run artifacts/temporal_years_20261101_r1 --cache artifacts/sequence_cache_20261101_r1 --protocol config/temporal-sequence-v2.json
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261105_r2
```

Yeniden oluşturma komutu yalnızca yeni bir aday dizin yazar ve raporun hash
değeri dondurulmuş değerden farklıysa hata verir. Güvenilir yerel joblib
modellerini yükler ve kaydedilmiş tahminleri gerektirir; dosyaları otomatik
geri yüklemez. Girdiler erişilemezken depolama kontrolü başarısız çıkış kodu
verir. Sonraki yayınlarda yeni bir çıktı dizini kullanın. Üretilen kanıtlar,
modeller ve veri setleri Git dışında tutulur.

Doğrulama: commit kapsamındaki yeniden oluşturma komutu yeni bir dizinde
dondurulmuş rapor hash değerini birebir üretti. İki dilde rapor ve depolama
kontrollerinde 13 test geçti. Harici Python önbelleği, yalnızca bulutta bulunan
bayt kodu dosyalarına takılmayı önler; model girdilerini veya metrikleri değiştirmez.
