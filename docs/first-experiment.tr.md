# İlk deney

Çalıştırma tarihi: 2026-10-12. Gerçek SWAN-SF kayıtları kullanıldı; sentetik eğitim veya değerlendirme verisi yoktur.

## Veri

Resmî 1, 3 ve 5 numaralı arşivler yayımlanmış MD5 özetleriyle doğrulandı.
Sınıf etiketlerine bakılmadan belirlenen, tekrarlanabilir %10 örneklem 19,088
pencere içeriyor. Eksik veya güvenilmeyen ölçüm oranı fazla olan 19 pencere
çıkarıldı. Kalan etiketli patlama zirvelerinin tamamı katalog–pencere kontrolünü geçti.

| Bölüm | Veri bölümü | Pencereler | M/X pencereleri | HARP bölgeleri |
| --- | --- | ---: | ---: | ---: |
| Eğitim | 1 | 7,254 | 129 | 640 |
| Doğrulama | 3 | 4,278 | 131 | 358 |
| Test | 5 | 7,537 | 97 | 669 |

Kesin tarihler ve bölge sayıları notebook ve yerel `artifacts/report.json`
içinde üretilir. Bu örneklemde bölüm sınırındaki örtüşme veya ortak HARP
nedeniyle kayıt çıkarmak gerekmedi. Bölüm 2 ve 4 kullanılmadı.

## Sonuçlar

Model ayarları testten önce sabitlendi. XGBoost, doğrulama average precision
değerine göre seçildi: lojistik regresyonda 0.3778, XGBoost'ta 0.4023.
Yaklaşık %1.437 alarm eşiği doğrulama TSS değerini en yükseğe çıkarır.
Seçilen model ve eşikler test tahminleri değerlendirilmeden önce kaydedildi.

| Model | Test yakalama oranı | Test alarm doğruluğu | Yanlış alarmlar | Kaçırmalar | Average precision | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sabit referans | 0.00% | 0.00% | 0 | 97 | 0.0129 | 0.01273 |
| Lojistik regresyon | 96.91% | 12.11% | 682 | 3 | 0.3588 | 0.01036 |
| XGBoost | 95.88% | 14.98% | 528 | 4 | 0.4520 | 0.00896 |

XGBoost 97 pozitif pencerenin 93'ünü yakaladı ve 621 alarm üretti.
Alarmların yaklaşık %85'i yanlıştı; negatif pencerelerde yanlış pozitif
oranı %7.10 idi. Eşik bilinçli olarak yakalamaya öncelik verir.
Bu bir araştırma başlangıcıdır; operasyonel kullanıma hazır olunduğunun kanıtı değildir.

Referans yöntem her zaman eğitimdeki pozitif oranını (%1.7783) tahmin eder.
TSS her eşikte sıfır olduğundan eşitlik kuralı hiç alarm vermeyen seçeneği seçer.
Alarm verilmediğinde precision sıfır olarak kaydedilmiştir; bu gösterim
kuralıyla yorumlanmalıdır.

## Yorumlama sınırları

- Sonuçlar SWAN-SF'nin tamamına değil %10 örneklemine aittir.
- Sayılar tahmin pencereleridir; aynı patlama birden fazla örtüşen pencereyi etiketleyebilir.
- Bağımsız olay yakalama oranı veya güven aralığı iddia edilmez.
- Kalibrasyon grupları ve Brier ölçülmüştür; kalibrasyon modeli eğitilmemiştir.
- Geçmişi oynatma, kesinleştirilmiş arşiv ölçümlerini kullanır; geçmişte gerçekten kullanılabilir bir canlı akış doğrulanmış değildir.
- Ayrılmış test artık incelenmiştir. Yeni ayarlamalar yeni bir değerlendirme tasarımı gerektirir.

Veri sözleşmesi ve notebook kaynak bağlantılarını ve kesin işleme kurallarını içerir.
Ortam: Python 3.14.3, pandas 3.0.6, NumPy 2.5.4, scikit-learn 1.9.1,
XGBoost 3.4.1. Model rastgelelik tohumları 24'tür.
