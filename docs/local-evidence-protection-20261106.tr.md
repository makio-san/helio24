# Yerel kanıtların kurtarılması ve korunması

## Doğrulanan durum

Yıllık koordinatör 2026-11-06T08:19:14.767968+00:00 zamanında
(Europe/Istanbul saatine göre 11:19) başarıyla tamamlandı. 42 eğitimin ve uygun
yedi yıllık değerlendirmenin tamamı bitti. İki referans raporu da dondurulmuş
protokoldeki hash değerleriyle eşleşiyor. Son karşılaştırma, tamamlanmış deneyin
manifestini bağımsız doğruladı ve metrikleri yeniden hesapladı.
[Tam değerlendirmeye bakın](temporal-evaluation-final-20261106.tr.md).
Yeni model kabul edilmedi ve ayrılmış 2024–2025 testi kapalı tutuldu.

Kronolojik TCN, pozitif olay içeren altı yılın yalnızca birinde referans precision
değerini geçiyor. Referansa karşı tam karşılaştırma koşulunu sıfır yılda sağlıyor.
Bu sonuç, yeni hipotez olmadan daha fazla epoch çalıştırmayı değil, planlanan
bu deneyi kapatmayı destekliyor.

## Kurtarma ve kalan eksik

Koordinatörün daha önce erişemediği dört girdi artık yerel. Gözetici otomatik
olarak devam etti; bu inceleme hangi indirme işleminin erişimi sağladığını
belirlemiyor. Kısa kontrol deneyinin eksik `metrics.csv` dosyası dondurulmuş
rapordan yeniden oluşturuldu ve yalnızca SHA256 birebir eşleştikten sonra
geri yüklendi:
`73fb4536374c125ee1e611a84ecb8d6207539d70ae6ab744042c7550e2314340`.

Bir tarihsel dosya hâlâ yok:
`artifacts/calibration_windows_20261030_r1/2019/predictions.parquet`.
Aranan proje, geçici kurtarma dizinleri, harici çalışma ortamı/kod dizinleri ve
Finder Çöp Sepeti içinde eşleşen kopya bulunamadı. macOS, Terminal'in Çöp Sepeti
erişimini reddetti; Finder incelemesi başarılı oldu. Uzak bir kurtarma kopyası
henüz doğrulanmadı. Toplu metrikler özgün satır olasılıklarını yeniden oluşturamaz.
Dosya, tamamlanan yedi yıllık TCN değerlendirmesi için gerekli değil; ancak yokluğu,
tarihsel kontrol deneyinin bütünüyle kurtarıldığını söylememizi engelliyor.

## Uygulanan koruma

Masaüstü, Belgeler ve iCloud Drive dışında yeni bir anlık kopya oluşturuldu:
`/Users/esma/Library/Application Support/Helio24/backups/evidence-20261106-r1`.
503 doğrulanmış dosya içeriyor: zaman serisi deneyi, zaman serisi önbelleği,
referans deney, mevcut kısa kontrol kanıtları, son karşılaştırma ve yapılandırma.
Her dosyanın hash değeri hesaplandı, varsa dondurulmuş manifestle karşılaştırıldı,
APFS klon desteğiyle kopyalandı, tekrar doğrulandı ve salt okunur yapıldı.
Yedek manifesti eksik tarihsel tahmin dosyasını açıkça kaydediyor; `complete`
değeri false. Tamamlanan zaman serisi deneyinin kendi manifestinde eksik dosya yok.

`scripts/snapshot_evidence.py`; mevcut çıktı dizinini, bulut tarafından yönetilen
hedefleri, geçersiz kaynak dizinlerini ve değiştirilmiş dondurulmuş dosyaları
reddediyor. Eksik veya yalnızca bulutta bulunan dosyaları yedeklenmiş gibi göstermek
yerine kaydediyor. Üç odaklı test; içeriğin korunmasını, eksik dosya bildirimini,
üzerine yazmayı reddetmeyi, hash uyuşmazlığını ve hedef/kaynak reddini kapsıyor.
Üretilen dosyalar Git dışında tutuluyor.

Bu, aynı diskte ayrı bir dizindir; bağımsız fiziksel yedek değildir. Mevcut
kopyaları Masaüstü iCloud yer boşaltmasından ve kaynak dosyanın silinmesinden
korur; disk arızasından veya yedeğin bilerek silinmesinden korumaz. Salt okunur
dosyalar silinemez değildir. Genel iCloud ayarının değiştirildiği iddia edilmiyor
ve gelecekteki çıktılar otomatik eklenmiyor. Her tamamlanan deneyden sonra yeni
anlık kopya alın; donanım arızasına karşı ayrı disk veya sürümlü uzak yedek ekleyin.

## Yeniden üretim ve kalan işler

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261106
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/snapshot_evidence.py --folder artifacts/temporal_years_20261101_r1 --folder artifacts/sequence_cache_20261101_r1 --folder artifacts/walk_forward_20261028_r1 --folder artifacts/calibration_windows_20261030_r1 --folder artifacts/temporal_evaluation_20261106_r1 --folder config --output '/Users/esma/Library/Application Support/Helio24/backups/evidence-20261106-r2'
"$PY" -m pytest tests/test_snapshot_evidence.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261106_r1
```

Tekrarlarda yeni çıktı adları kullanın. Kalan öncelikler; varsa gerçek bir yedekten
tek tarihsel dosyayı kurtarmak, bağımsız fiziksel yedek oluşturmak ve nihai çok yıllı
hata analizinden sonraki araştırma hipotezini seçmek. Son karşılaştırmanın dashboard
gösterimi bunun ardından gelebilir. Yeni eğitim için yeni dondurulmuş deney planı
gerekiyor; mevcut deney tamamlandı.
