# V2 ölçüm uyumluluğu: kaynak izleme raporu

Tarih: 20 Ekim 2026. Karar: **V2 henüz mevcut modele doğrudan bağlanamaz.**
Bu çalışma eğitim deneyi değildir; model metrikleri değişmedi.

## İncelenen veri

Önceki denetimin seçtiği beş 2011 penceresi aynen korundu: HARP 334, 344,
356, 359 ve 372. Toplam 300 zaman noktası, her değişken için 296 sonlu çift
var. Eski kalite kurallarını geçen alt kümede 282 nokta var. Sadece HARP,
gözlem zamanı ve 24 ağırlıksız manyetik ölçüm okundu; V2 sonuç etiketleri
ve 2024–2025 dönemi açılmadı. Kaynak dosyalarının SHA-256 değerleri doğrulandı.

## Kuvvet sütunlarındaki farklar

Aşağıdaki sabit katsayılar tanısal hipotez olarak sınandı. Veriden regresyonla
katsayı öğrenilmedi. Eşleşme toleransı rtol=1e-5, atol=1e-8; bilimsel
eşdeğerlik standardı olarak yorumlanmamalıdır.

| V2 ölçümü | Sınanan V1 dönüşümü | Sonlu çiftlerde eşleşme |
| --- | --- | ---: |
| TOTFX | V1 TOTFX / (4π) | 296 / 296 |
| TOTFY | −V1 TOTFY / (4π) | 296 / 296 |
| TOTFZ | V1 TOTFZ / (8π) | 296 / 296 |

Kalite filtresini geçen alt kümede de üç ilişki 282/282 eşleşiyor. Bu örneklemde
ölçek ve işaret farkı sistematik. Hesaplama kodunun veri üretimindeki kesin
sürümü belirlenmeden bu ilişkiler üretim dönüşümü olarak kullanılmamalıdır.

V2 içinde EPSX=TOTFX/TOTBSQ, EPSY=TOTFY/TOTBSQ ve EPSZ=TOTFZ/TOTBSQ
ilişkileri de ayrı ayrı 296/296 eşleşiyor. Eski EPS sütunlarıyla doğrudan
eşleşme ise sıfır. Örneğin ilk HARP 334 kaydında V1 EPSX=0.265604,
V2 EPSX yaklaşık −2.806969e13. Bu iç tutarlılık, EPS alanlarının eski
normalizasyonla aynı anlama geldiğini kanıtlamaz; büyük farkı gizleyen otomatik
ölçekleme veya sütun değişimi yapılmadı.

## JSOC kaynak kayıtları

Her pencerenin ilk zaman noktası için `hmi.sharp_cea_720s` başlıkları alındı.
Sorguda kayıtlı saat dizgesi TAI olarak yorumlandı; bu açık bir eşleştirme
hipotezidir. Beş başlık bütün zaman serisinin doğrulaması değildir.

| Ölçüm | V1–JSOC eşleşmesi | V2–JSOC eşleşmesi |
| --- | ---: | ---: |
| USFLUX | 5 / 5 | 5 / 5 |
| MEANPOT | 0 / 5 | 5 / 5 |
| TOTPOT | 0 / 5 | 5 / 5 |
| MEANSHR | 0 / 5 | 2 / 5 |
| SHRGT45 | 3 / 5 | 4 / 5 |

Eşleşmeler aynı sayısal toleransla hesaplandı. Başlıkların yazdırma hassasiyeti
özellikle son iki ölçümde değerlendirmeyi sınırlar. MEANPOT/TOTPOT bulgusu,
bu beş noktada V2 değerlerini kaynak başlıkların desteklediğini gösterir;
tüm V1 verisinin hatalı olduğu veya bütün V2 ölçümlerinin doğrulandığı sonucu çıkmaz.

Kaynak indirmelerinde HTTPS sertifika doğrulaması başarısız oldu; yayınlanan
HTTP uç noktasına geçildi. TLS denetimi kapatılmadı. HTTP içerikleri taşıma
katmanında doğrulanmış değildir; deneme bilgileri ve indirilen içerik özetleri
manifestte tutuldu. Bağımsız doğrulama için bu sınırlama korunmalıdır.

## Kalite ve zaman

HARP 372, 2011-02-10 18:24 kaydının JSOC QUALITY değeri `0x00010400`;
diğer dört başlıkta sıfır. V2 bu noktada sonlu manyetik değerler içeriyor.
Bu nedenle “V2 içinde sayı varsa kalite kontrolünden geçmiştir” varsayımı
geçerli değil. Mevcut uygulamanın QUALITY=0 ve IS_TMFI kuralları yeniden
kurulmadan eski ön işleme ile eşdeğerlik iddia edilemez.

Beş sorguda T_REC kayıtlı saatle eşleşiyor, T_OBS ise 7–8 saniye daha erken.
T_REC ve T_OBS ayrı kavramlar; bu sonuç UTC/TAI dönüşümünü veya V2 zaman
üretim adımını doğrulamıyor. Gözlem zamanı, veri kullanılabilirliği ve tahmin
verilme zamanı ayrı tutulmalıdır.

## Dokümantasyonla ilişki

[V2 makalesinin 2.2.1 bölümü](https://arxiv.org/html/2610.04591v1#S2.SS2.SSS1),
eski GPU hesaplamalarından yeni CPU kütüphanesine geçildiğini anlatıyor.
Bu, sayısal değişiklikleri araştırmak için gerekçe; yukarıdaki katsayıların
nedensel kanıtı değil. [Kütüphanenin LorentzForceCalculator belgesi](https://dmlab.cs.gsu.edu/docs/spaceweather_toolkit/magparam.html)
kuvvetleri dynes, TOTBSQ alanını Gauss², EPS alanlarını normalize kuvvet olarak
tanımlıyor. İndirilen EPS değerleriyle bu açıklamanın ilişkisi hesaplama
kodu ve veri üretim sürümü üzerinden ayrıca doğrulanmalı.

## Yeniden üretim ve sonraki adım

```sh
python scripts/fetch_measurement_sources.py
python scripts/trace_measurement_differences.py
```

Komutlar mevcut çıktının üzerine yazmaz. Yerel `data/measurement_sources/`
başlıkları ve indirme manifestini; `artifacts/measurement_trace/` değişken
bazında tanıları, kaynak karşılaştırmasını ve SHA-256 özetlerini tutar.
Veriler Git'e eklenmez. Eksik değerler sonlu eşleşme sayılarına dahil edilmez.

Sonraki görev, veri üretiminde kullanılan hesaplama sürümünü ve EPS
normalizasyonunu izlemek, ardından kalite alanlarını eski dönem için geri
kazanıp maske etkisini ölçmek. Zaman ölçeği ve etiket dahil etme kuralları
doğrulandıktan sonra ayrı bir V2 ön işleme sürümü ve eğitim protokolü dondurulabilir.
Kullanıcının ana hedefi **recall ≥ %95 ve daha az yanlış alarm** olarak kalır.
