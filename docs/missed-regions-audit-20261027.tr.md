# HARP 9152 ve 9584: etiket, ölçüm ve uyarı zamanı denetimi

Denetim tarihi: 2026-10-27. **Mevcut kanıtlar etiket veya özellik düzeltmesini
gerektirmiyor.** Tutulan 257 pencerenin tamamı, etiketleri ve 24672 özellik
değeri doğrulanmış ham V2 gözlemlerinden yeniden üretildi. 768 sonlu USFLUX
çiftinin tamamı 1e-5 göreli toleransla JSOC başlıklarına uydu. Kaçırılan 34
pozitif pencerenin tamamında eksik oranı sıfır. Bunlar 34 bağımsız kaçırılan
patlama değil: ilişkilendirilmiş üç M sınıfı olay var ve her biri öncesinde en
az bir alarm bulunuyor. Bu geçmişe dönük alt küme sonucu genel olay recall'unu kanıtlamaz.

## Kaynaklar ve kapsam

İki tam sıkıştırılmış arşivin SHA-256, ETag ve bayt uzunluğu dondurulmuş kayıtla
doğrulandı; mantıksal Parquet okumaları yalnızca HARP 9152/9584 ve 2024 öncesi
gözlem zamanlarını seçti. İndirilen arşivlerde başka dönemler de bulunur, ancak
ayrılmış test kayıtları mantıksal olarak okunmadı veya skorlanmadı. Tahminler,
0.00931081050648097 eşikli dondurulmuş 2023 ensemble modeline aittir. Yeniden
eğitim veya yeniden etiketleme yapılmadı.

HEK/SWPC aylık yanıtları kayıtlı hash'leriyle doğrulandı. Üç sınırlı definitive
SHARP başlık sorgusu NOAA ilişkilerini, zamanları, QUALITY bayraklarını ve
USFLUX değerlerini sağladı. JSOC HTTPS sertifika doğrulaması başarısız oldu;
mevcut salt okunur HTTP alternatifi başlıkları sağladı. Bu nedenle aktarım
kimliği doğrulanmamıştır; yanıt hash'leri ve denemeler saklandı. TLS kontrolleri
kapatılmadı. Bu karşılaştırma ayrı alınmış metaveriyi denetler; JSOC ve V2 aynı
temel gözlemleri paylaşır, bağımsız cihazlar değildir.

## Pencere yeniden üretimi ve eksiklik

| harp | raw_rows | retained_windows | positive_windows | tp | fn | fp | cadence_gaps | raw_rows_nonfinite | zero_flux_rows | missed_windows_without_missing_values | reproduced_feature_values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9152 | 1363 | 106 | 24 | 2 | 22 | 14 | 0 | 25 | 8 | 22 | 10176 |
| 9584 | 1365 | 151 | 48 | 36 | 12 | 88 | 0 | 20 | 12 | 12 | 14496 |

1363 ve 1365 ham gözlem satırı var; 12 dakikalık aralıktan farklı adım yok.
Bu bölge yaşamlarının başka kısımlarında sonlu olmayan satırlar ve sıfır akı
değerleri bulunuyor. Buna karşın kaçırılan 34 pozitif pencerenin tamamındaki
girdiler sonlu; eksik değer doldurma bu kaçırmaları doğrudan açıklamıyor.
Sonlu değerler temiz QUALITY bayrağını veya fiziksel ölçüm güvenilirliğini garanti etmez.

Ham kalite politikası etiket dışlamalarından önce 261 ve 262 aday pencereyi
tutuyor; dondurulmuş değerlendirme popülasyonunda yalnızca 106 ve 151 kalıyor.
Dolayısıyla tahmin saçılım grafiklerindeki boşluklar ham gözlem eksikliğinin
kanıtı değil. Denetim dışlanan değerlendirme pencerelerini geri eklemiyor.
Bu iki bölge mevcut modelin 8577 yanlış pozitif penceresinin 102'sini oluşturuyor;
bu denetim tek başına tüm precision sorununu açıklamıyor.

## Olay ilişkisi ve zaman kontrolleri

| harp | peak_utc | goes_class | confidence | harp_vote | max_pair_distance_deg | hek_noaa | jsoc_noaa | noaa_matches | header_offset_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9152 | 2023-03-04T07:10:00+00:00 | M1.0 | very_high | 3-0 | 1.414214 | 13243 | 13243 | True | 83.000000 |
| 9584 | 2023-05-24T18:00:00+00:00 | M1.0 | low | 2-1 | 54.203321 | 13315 | 13315 | True | 37.000000 |
| 9584 | 2023-05-30T13:38:00+00:00 | M1.4 | high | 3-0 | 5.099020 | 13315 | 13315 | True | 157.000000 |

SWPC GOES sınıfları ve UTC tepe zamanları üç V2 olayıyla tam eşleşiyor.
JSOC NOAA_ARS, HARP 9152'yi NOAA 13243'e, HARP 9584'ü NOAA 13315'e bağlıyor;
bunlar SWPC ile eşleşiyor. Arşiv gözlem zamanları, bu tarihlerde geçerli
37 saniyelik farkla TAI'den UTC'ye çevrildi; bütün dondurulmuş etiketler
[forecast_time, forecast_time + 24h) yarı açık hedef aralığıyla yeniden üretildi.

24 Mayıs ilişkisi hâlâ sınırlama: V2 güveni `low`, oyu `2-1`, kaynaklar arası
maksimum ikili ayrım 54.203321 derece. SWPC/JSOC NOAA numarasının eşleşmesi
atamayı destekliyor; ancak kaynak konum uyuşmazlığını çözmüyor veya kesin
uzamsal kökeni kanıtlamıyor. Etiket değiştirilmiyor. Diğer ilişkiler `very_high`
ve `high`; bunlar kaynak metaverisi, yeni bağımsız güven tahminleri değil.
En yakın başlığın zaman farkı tabloda açıkça veriliyor.

## Pencere recall'u ve olay öncesi uyarı

| harp | peak_utc | eligible_windows | alarm_windows | first_alarm_utc | lead_to_peak_hours | lead_to_start_hours |
| --- | --- | --- | --- | --- | --- | --- |
| 9152 | 2023-03-04T07:10:00+00:00 | 24 | 2 | 2023-03-04T05:35:23+00:00 | 1.576944 | 1.510278 |
| 9584 | 2023-05-24T18:00:00+00:00 | 24 | 12 | 2023-05-24T06:47:23+00:00 | 11.210278 | 11.093611 |
| 9584 | 2023-05-30T13:38:00+00:00 | 24 | 24 | 2023-05-29T13:47:23+00:00 | 23.843611 | 23.810278 |

Seçilen bu üç olayda ilk uygun tutulan alarm, bildirilen olay başlangıcından
1.510278, 11.093611 ve 23.810278 saat önceydi. HARP 9152, patlamadan önce
uyarmasına rağmen 24 pozitif pencerenin yalnızca 2'sinde alarm veriyor.
HARP 9584 için oranlar 12/24 ve 24/24. Bu nedenle pozitif pencerelerde %95
recall istemek, her patlamadan önce en az bir uyarı istemekten farklıdır.

Bu, hataları nedeniyle seçilen bölgelerin sonradan yapılan denetimidir;
bağımsız bir 3/3 olay yakalama ölçütü değildir. Dışlanan pencereler ön uyarı
süresi tahminlerini sınırlar. Kullanıcı hedefi ve resmî metrikler değişmedi:
özgün doğrulama popülasyonunda precision 0.079622, recall 0.950064.

## Manyetik değişim ve kalite kanıtı

| harp | stage | forecast_utc | last_observation_utc | USFLUX | TOTUSJH |
| --- | --- | --- | --- | --- | --- |
| 9152 | first_positive_forecast | 2023-03-03T07:35:23+00:00 | 2023-03-03T07:23:23+00:00 | 2.66823332e+21 | 189.603973 |
| 9152 | first_alarm | 2023-03-04T05:35:23+00:00 | 2023-03-04T05:23:23+00:00 | 7.79794053e+21 | 642.218201 |
| 9584 | first_positive_forecast | 2023-05-23T18:47:23+00:00 | 2023-05-23T18:35:23+00:00 | 3.01531448e+21 | 200.157425 |
| 9584 | first_alarm | 2023-05-24T06:47:23+00:00 | 2023-05-24T06:35:23+00:00 | 7.96035666e+21 | 808.570312 |

İki bölgenin ilk olaylarında, ilk tutulan pozitif tahmin ile ilk alarm arasında
işaretsiz akı ve toplam işaretsiz akım helisitesi artıyor. Model olasılığı da
yükseliyor. Bu, değişime duyarlı özellikleri sınamayı destekler; modelin erken
pencereleri neden kaçırdığını veya manyetik ortaya çıkışın patlamaya neden
olduğunu kanıtlamaz. Değerler veri setinin yerel birimleriyle raporlanır.

| harp | matched_header_times | finite_flux_pairs | flux_matches_rtol_1e5 | header_rows | nonzero_quality | noaa_ars | transport |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9152 | 300 | 300 | 300 | 300 | 9 | 13243 | http |
| 9584 | 468 | 468 | 468 | 477 | 20 | 13315 | http |

Sorgulanan aralıklarda HARP 9152 için 9, HARP 9584 için 20 sıfır olmayan QUALITY
başlığı bulunuyor. Denetim bitleri kaydeder; bunları genel bir geçersizlik kuralı
olarak yorumlamaz. Zamanları eşleşen 300 ve 468 sonlu USFLUX çiftinin tamamı
JSOC ile uyumlu; kalan başlıkların seçilen ham zamanlarda karşılığı yok.
USFLUX uyumu 24 parametrenin tümünü veya fiziksel birimlerini doğrulamaz.

## Grafikler

[HARP 9152 — Türkçe grafik](../artifacts/missed_regions_20261027_r2/harp_9152.tr.png)

[HARP 9584 — Türkçe grafik](../artifacts/missed_regions_20261027_r2/harp_9584.tr.png)

Her grafik dondurulmuş olasılıkları, ham USFLUX, ham TOTUSJH, pencere eksikliğini
ve sıfır olmayan QUALITY işaretlerini içerir. Kırmızı noktalar pozitif pencereler,
kırmızı dik çizgiler patlama tepeleri, kesikli çizgi dondurulmuş eşiktir.
Ölçüm eksenleri simetrik logaritmik ölçek kullanır. Son paneldeki -2 işaretleri
negatif eksikliği değil, QUALITY bayraklarını gösterir. Gelecekteki olay
işaretleri geçmişe dönük açıklamadır; model girdisi değildir.

## Karar ve sonraki deney

Etiketler, popülasyon, model ve eşik korunsun. Sonraki en yararlı deney, ham
gözlemlerden 24/48 saatlik değişim özellikleri; yalnızca eğitimde öğrenilen
ön işleme ve kronolojik karşılaştırmadır. Geçmiş yalnızca etiketle filtrelenmiş
pencerelerden oluşturulmamalı. Herhangi bir düzeltme önermeden önce düşük güvenli
24 Mayıs uzamsal ilişkisi bağımsız incelenmeli. En fazla yanlış pozitif üreten
bölgeler de incelenmeli; iki bölgede geç uyarıları azaltmak tek başına precision
artışının kanıtı değildir.

Ayrı bir olay düzeyi değerlendirmesi, olay eşleştirme ve alarm birleştirme
kuralları değerlendirmeden önce sabitlenerek, mevcut pencere metriklerinin
yanında ön uyarı süresini ve alarm olaylarını raporlamalı. Özgün recall hedefini
değiştirmemeli veya bu seçilmiş alt kümeyi yeni bir başarı metriği olarak sunmamalı.

## Yeniden üretim ve kanıt

```sh
.venv/bin/python scripts/extract_region_audit.py --output data/region_audit_20261027_r2
.venv/bin/python scripts/fetch_region_headers.py
.venv/bin/python scripts/audit_missed_regions.py --raw data/region_audit_20261027_r2 --output artifacts/missed_regions_20261027_r2
.venv/bin/python scripts/report_missed_regions.py
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_missed_regions_20261027
```

Mevcut çıktılar korunur. Tekrar için yeni yollar ve tarihli rapor/başlık girdi
yollarının güncellenmesi gerekir. Kabul edilen ham çıkarım r2'dir; ilk çıkarım
ağ adresi çözümleme hatasıyla başarısız oldu. Denetim r1, rapor üretmeden göreli
yol hatasıyla durdu; kabul edilen denetim r2'dir. Veri, ham başlıklar ve
PNG/CSV/JSON/HTML çıktıları Git dışında kalır. Kaynak kod, eşlenmiş Markdown
raporları ve iki dilli katalog sürüm kontrolündedir.

| source | SHA-256 |
| --- | --- |
| artifacts/missed_regions_20261027_r2/report.json | 08822ae3b0c90f1b5175d71dca40c198280d9558ea2f106e4480be78ed1ca6d8 |
| artifacts/experiment5_v2_development_20261026_r2/report.json | b57ce8e12de3d18740872b1504f97ff6a9dee22b272143836bb1a739d155ef03 |
| artifacts/experiment5_v2_development_20261026_r2/validation_predictions.parquet | 44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff |
| data/region_audit_20261027_r2/report.json | a179f054e2951ffb1d37544f9835f2b8af957ed71a7190e3dccc4fdd268a42f7 |
| config/swan_sf_v2_sources.verified.json | 4da23877d22c2676ab76950c69c016bbe8eaacd8049fc806dad078752feafa3d |
| artifacts/v2_development_features_20261025_r2/report.json | 62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82 |
| artifacts/v2_development_features_20261025_r2/shards/partition-1-d917a8a4fd4a.parquet | e526b9b806a8b85b34431b09cc47ac7a97a69f07c69b1ac6a71d91b61d9b1aef |
| artifacts/v2_development_features_20261025_r2/shards/partition-2-05b11f13de93.parquet | eb904ebc6e9370551c9f0f56e8bd43757764ed581992d590bbed32c417543cab |
| artifacts/hek_major_inventory_20261025_r2/report.json | 1d82d652504e162c35138ca19815f9c8dab9312eb18e1848c54123e837c0b4b5 |
| artifacts/hek_major_inventory_20261025_r2/events.csv | f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f |
| artifacts/hek_major_inventory_20261025_r2/raw/2023-03.json | 2e3c7a39c9ae0dde2164cd5df8f2bd1d624500f04b491c56b58817604fc894f3 |
| artifacts/hek_major_inventory_20261025_r2/raw/2023-05.json | 39da653a72b3ca30b9b5cdeaa4e57819460167c7fefd059f0fc5ca2c553a7984 |
| data/region_headers_20261027/manifest.json | 06a998be0e7ff3e6c7d4fa8dc764fb71ac24910ef0cdfd465c712294d7c6d6ae |
| data/region_headers_20261027/harp_9152_2023.03.02.json | d46152e407c8caccce03033621e8eab40baec30e60026dbd86e959090378f4f2 |
| data/region_headers_20261027/harp_9584_2023.05.23.json | a5e09376e15145fd55f2c96a884f0997c210bf547e69e44b5906e46926398b24 |
| data/region_headers_20261027/harp_9584_2023.05.29.json | b952d9e84be1bd7be66ba89b566a8d3610338d6d06c8e556d51666257ab8e9ae |
| artifacts/v2_label_inventory_20261025_r1/unassigned_major_events.csv | e584b58fbea9f1e03f025df75edae9312303f0dafd82db04347a5ba7fc71be8f |
| data/region_audit_20261027_r2/harp_9152.parquet | 4be4e9fac1807c09b5ec69f0b72a47fe5dd5280a53074d45a1b75ab270438aac |
| data/region_audit_20261027_r2/harp_9584.parquet | f50b5202e9aaba476e93b2f81e9ed8b9d73e5d9b3fd59869a0235b41c409ae5e |

