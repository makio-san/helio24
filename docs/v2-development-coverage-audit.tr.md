# SWAN-SF-V2 geliştirme kapsamı denetimi

Denetim tarihi: 2026-10-25. Karar: **2024 öncesi ölçüm kapsamı sayısallaştırıldı,
ancak etiket tamlığı ve geliştirme kapsamı kapısı hâlâ bekliyor**. Bu denetim
model eğitmedi, tahmin metriği hesaplamadı ve ayrılmış 2024–2025 satırlarını
okumadı.

## Kapsam ve kontroller

Dört sabitlenmiş V2 arşivi sırayla geçici yerel dosyalara indirildi. Her tam
sıkıştırılmış dosya, herhangi bir Parquet üyesi incelenmeden önce dondurulmuş
`Content-Length`, ETag ve SHA-256 değeriyle eşleşti. Geçici arşiv ve üye dosyaları
işlemden sonra silindi. Mantıksal Parquet taraması, test sınırının dondurulmuş
TAI karşılığı olan `obs_start < 2024-01-01T00:00:37 TAI` yüklemini uyguladı;
24 ağırlıksız manyetik ölçümle ilişkilendirilmiş olay denetimi için gereken
alanları yansıttı.

Tarama dondurulmuş 12 saatlik gözlem, 24 saatlik tahmin, beş satırlık adım,
UTC rol sınırı, HARP sahipliği ve sonlu değer kalite kurallarını kullandı. Bir
pencere, herhangi bir ölçümün 60 gözlemi içinde 12'den fazla eksik veya sonlu
olmayan konum varsa kaliteyi geçemez. Sonuç alanları yalnızca etiket kapsamı
kontrollerinde kullanıldı ve hiçbir zaman model girdisi olmadı.

Dört arşivin, 20 Parquet üyesinin ve 5,010,828,973 sıkıştırılmış baytın tümü
sabitlenmiş özetlerini geçti. Tarama 4,183,021 birleşik satır, 4,182,825 benzersiz
HARP/zaman gözlemi ve 5,983 HARP buldu. Sıklık nedeniyle pencere çıkarılmadı.
Rol sınırları 1,085, artık saniye geçişleri 215 pencere çıkardı.

## Ölçüm kapsamı

Aşağıdaki sayılar rol sınırlarından ve en erken rol HARP sahipliğinden sonradır.
Tutulan eksik oranının paydası tüm
`tutulan pencere × 60 satır × 24 alan` ölçüm konumlarıdır.

| Rol | Aday pencere | Kaliteden geçen | Kaliteden geçemeyen | Tutma oranı | Tutulan konumlardaki eksik oranı |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 573,509 | 506,493 | 67,016 | 88.31% | 1.4940% |
| calibration | 80,187 | 69,933 | 10,254 | 87.21% | 1.6681% |
| validation | 114,190 | 100,882 | 13,308 | 88.35% | 1.5805% |
| **Toplam** | **767,886** | **677,308** | **90,578** | **88.20%** | **1.5249%** |

Tutulan pencerelerdeki toplam eksik konum sayısı 975,323,520 içinde
14,872,489'dur. HARP sahipliği ayrıca 183 kalibrasyon adayını (174'ü kaliteyi
geçecekti) ve 1,174 doğrulama adayını (946'sı kaliteyi geçecekti) çıkardı. Daha
erken roldeki HARP'ın sonraki rolünde tutulan pencere olmasa bile bu sonraki rol
pencereleri veriye geri giremez.

| Rol | İlk tutulan tahmin (UTC) | Son tutulan tahmin (UTC) |
| --- | --- | --- |
| train | 2010-05-01 12:59:26 | 2021-12-30 23:35:23 |
| calibration | 2022-01-01 12:23:23 | 2022-12-30 23:59:23 |
| validation | 2023-01-01 12:35:23 | 2023-12-30 23:59:23 |

Her roldeki son tahmin rol sınırından öncedir; çünkü 24 saatlik yarı açık hedef
aralığının tamamı aynı role sığmalıdır.

## İlişkilendirilmiş olay denetimi ve geçici etiketler

Tarama 24,132 geçerli ilişkilendirilmiş olay bağlantısını tuttu. Tekilleştirilmiş
diğer 23 ilişkilendirilmiş olay satırında `start_time > peak_time` veya
`peak_time > end_time` vardı; kapalı-hata doğrulayıcısı 23'ünü de
`Flare start/peak/end order is invalid` nedeniyle dışladı. Bu satırlar onarılmadı
veya etiketlerde kullanılmadı.

723 ilişkilendirilmiş GOES M/X bağlantısı vardır: 678 M ve 45 X. Bunların 722'si
kabul edilen HARP güven düzeyini kullanır; bir M olayı dondurulmuş sözleşme
altında belirsiz olan `very_low` düzeyindedir.

| GOES sınıfı | very_high | high | moderate | low | very_low | Toplam |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M | 380 | 231 | 30 | 36 | 1 | 678 |
| X | 18 | 20 | 4 | 3 | 0 | 45 |
| **Toplam** | **398** | **251** | **34** | **39** | **1** | **723** |

Aşağıdaki bilinen pozitif, kaliteden geçen pencerenin yarı açık 24 saatlik hedef
aralığına en az bir kabul edilmiş, ilişkilendirilmiş GOES M/X zirvesinin düştüğü
anlamına gelir. “Çözülmemiş pozitif olmayan” özellikle negatif anlamına gelmez:
güvenilir HARP'ı bulunmayan M/X olaylarını belirlemek için hâlâ bağımsız envanter
gereklidir.

| Rol | Kaliteden geçen | Bilinen pozitif | Belirsiz HARP | Çözülmemiş pozitif olmayan |
| --- | ---: | ---: | ---: | ---: |
| train | 506,493 | 8,698 | 0 | 497,795 |
| calibration | 69,933 | 421 | 0 | 69,512 |
| validation | 100,882 | 781 | 24 | 100,077 |
| **Toplam** | **677,308** | **9,900** | **24** | **667,384** |

## Kapı kararı

2024 öncesi tam ölçüm taraması başarılıdır ve her geliştirme rolünde boş olmayan,
kaliteden geçmiş kapsam gösterir. Henüz negatif etiketleri doğrulamaz.
`development_coverage_audit` kapısı, tüm geliştirme dönemi için tam, değişmez ve
bağımsız olarak kontrol edilmiş GOES M/X envanteri sabitlenene kadar
`pending_unassigned_major_event_inventory` durumunda kalır. Bu envanter, sınıf
sayıları kesinleşmeden önce ilişkilendirilmiş kabul edilen olayları, belirsiz HARP
atamalarını ve güvenilir HARP'ı olmayan olayları ayırmalıdır.

`measurement_semantics` ve `training_runner_review` de beklemektedir. Bu yüzden
sonuç Experiment 5 eğitimine izin vermez. 9,900 bilinen pozitif pencere örtüşen
tahmin pencereleridir; 9,900 bağımsız Güneş patlaması değildir. Burada accuracy,
recall, precision, yanlış alarm veya kalibrasyon sonucu raporlanmaz.

## Sınırlamalar ve belirsizlik

- Denetim sürümlenmiş V2 sonlu değer politikasını değerlendirir. V1
  `QUALITY`/`IS_TMFI` maskesine eşdeğerliği kanıtlamaz veya ölçüm formülleriyle
  EPS semantiğini çözmez.
- Eksik oranları örtüşen pencereler boyunca tekrarlanan ölçüm konumlarını sayar.
  Benzersiz ham satırlardaki eksik değer oranı değildir.
- İlişkilendirilmiş olay satırları bilinen pozitifleri gösterir, ancak tam
  negatifleri gösteremez. Çözülmemiş grup gerçek negatiflerle güvenilir HARP
  ataması olmayan büyük olayları birlikte içerir.
- Geçersiz olay aralıkları raporlanıp dışlanmıştır. Doğru onarılmış değerleri
  bilinmemektedir ve denetim bunlar hakkında varsayım yapmaz.
- Sayılar kayıtlı kaynak ve kod özetleri için belirlenimlidir. Her kaynak,
  sözleşme, sınır veya tarayıcı değişikliği yeni çıktı dizini ve inceleme gerektirir.

## Yeniden üretim

Yeterli geçici disk alanı ve ağ erişimiyle depo kökünden çalıştırın:

```sh
.venv/bin/python scripts/audit_v2_development_coverage.py \
  --output artifacts/v2_development_coverage_20261025_r3 --workers 1
```

Kabul edilen makine raporu
`artifacts/v2_development_coverage_20261025_r3/report.json` dosyasıdır. Şu kod
özetlerini kaydeder:

| Kod | SHA-256 |
| --- | --- |
| `helio24/v2_archive.py` | `bde85ba5b4659995941cc4ace06c0088a21a67a1048b0c9c623d4f37dd1ce5e0` |
| `helio24/v2_contract.py` | `e195bbc33d1afc2aed417229369723194413eca5c5ac461c38bb22916a9ad9cd` |
| `helio24/v2_coverage.py` | `7ff70591ccf621cc6a8f12403b3f81c08adf5bb88753240a943bd699f4dd733e` |
| `scripts/audit_v2_development_coverage.py` | `cedd5bf40b08dc85431d688c506aa9bec43ea5db2d65fc9f396f24af19aaac25` |

Gözden geçirilmiş dil çiftini yeni bir dizine yayınlayın:

```sh
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_coverage_20261025
```
