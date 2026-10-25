# SWAN-SF-V2 geliştirme yerleşimi denetimi

Denetim tarihi: 2026-10-25. Durum: **tanımlayıcı yerleşimi doğrulandı; ölçüm
ve sonuç kapsamı hâlâ bekliyor**. Bu denetim model performansı sonucu üretmedi
ve ayrılmış 2024–2025 nihai test sütunlarını açmadı.

## Soru ve sınır

Denetim, doğrulanmış V2 arşivlerinin dondurulmuş eğitim, kalibrasyon ve
doğrulama rolleri için kronolojik olarak ayrılmış HARP pencereleri sağlayıp
sağlayamadığını sorar. Parquet okuyucusu yalnızca `harp_number` ve `obs_start`
sütunlarını yansıttı; depolama taraması sınırında
`obs_start < 2024-01-01T00:00:37 TAI` uygulandı. Kesim, dondurulmuş 37 saniyelik
fark altında `2024-01-01T00:00:00 UTC` zamanının TAI karşılığıdır. Sonuç, ölçüm,
kalite ve model sütunları okunmadı.

Her aday 12 dakikalık sıklıkta 60 gözlem kullanır; bu, ilk gözlemden tahmin
zamanına kadar 12 saatlik bir aralık verir. Aday başlangıçları beşer satır
ilerler. Bir pencere yalnızca gözlem ve 24 saatlik hedef aralıklarının tamamı
dondurulmuş bir UTC rolüne sığıyorsa tutulur. Bir HARP birden fazla rolde
göründüğünde ona en erken rol sahip olur ve sonraki rol pencereleri dışlanır.

## Doğrulanmış arşiv taraması

Dört HTTPS yanıtının tümü, sonuçları kabul edilmeden önce sabitlenmiş
`Content-Length`, ETag ve sıkıştırılmış dosyanın tam SHA-256 değeriyle eşleşti.
Yirmi Parquet üyesi incelendi. Spark `_SUCCESS` işaretçilerine yalnızca sıfır
baytlık normal dosyalar olarak izin verildi. Hiçbir arşiv gövdesi veya çıkarılan
Parquet üyesi saklanmadı.

| Bölüm | Üye | Sıkıştırılmış bayt | SHA-256 |
| ---: | ---: | ---: | --- |
| 1 | 5 | 1,177,434,736 | `26fbe84600dcbd2600bced76eeff9df097b5de2bc78328160342869827b1dd3b` |
| 2 | 5 | 1,284,717,836 | `1fc49bff4e61ea2ac608d1c08dd45f335463f8b31e828afc60eaa283e8d50692` |
| 3 | 5 | 1,246,106,315 | `c829699b0afecb88b5cc1743e620096a21565a5127ea76be9fb9cfa6be69783f` |
| 4 | 5 | 1,302,570,086 | `35e86b7e27b52bfba83f6bdf3d39b1b15bc03fa0b52552a590472a4ceed0bf72` |
| **Toplam** | **20** | **5,010,828,973** | — |

## Bulgular

| Kontrol | Sonuç |
| --- | ---: |
| Üye içi anahtar tekilleştirmeden önce birleşik satırlar | 4,183,021 |
| Üyeler içinde benzersiz `harp_number` / `obs_start` satırları | 4,182,825 |
| Üye içi anahtar tekilleştirmesiyle çıkarılan fark | 196 |
| HARP tanımlayıcıları | 5,983 |
| Birden fazla arşiv üyesine yayılan HARP'lar | 0 |
| Her tekilleştirilmiş HARP serisi içindeki 12 dakikalık sıklık kesintileri | 0 |
| Rol sınırlarında veya rollerin dışında olduğu için çıkarılan pencereler | 1,085 |
| 12 saatlik aralığı artık saniye farkını geçtiği için çıkarılan pencereler | 215 |
| Önceki rolün HARP sahipliği nedeniyle çıkarılan kalibrasyon pencereleri | 183 |
| Önceki rolün HARP sahipliği nedeniyle çıkarılan doğrulama pencereleri | 1,174 |

Tanımlayıcı yerleşimi ölçüm taraması ön koşulunu geçti: hiçbir HARP arşiv
üyeleri arasında bölünmedi, her tekilleştirilmiş seri kesintisiz 12 dakikalık
sıklığa sahipti ve üç geliştirme rolünün tamamında aday pencereler vardı.

| Sınırlar ve HARP sahipliği sonrasındaki rol | Aday pencere |
| --- | ---: |
| train | 573,509 |
| calibration | 80,187 |
| validation | 114,190 |
| **Toplam** | **767,886** |

## Yorum ve karar

Denetim, dondurulmuş kronolojik kuralların tanımlayıcı ve zaman yerleşimine
uygulanabildiğini doğrular. `development_coverage_audit` henüz doğrulanmış olarak
işaretlenmedi. Raporlanan pencereler ölçüm kalite kontrolleri, eksik değer
politikası, etiket oluşturma ve sınıf sayısı kontrollerinden önceki adaylardır.
Bunlar eğitim örnekleri değildir ve sayıları daha iyi kapsam veya performans
kanıtı olarak V1 örnek sayılarıyla karşılaştırılmamalıdır.

Sonraki kontrollü adım, aynı depolama yüklemiyle 2024 öncesi ölçüm ve sonuç
taramasıdır. Her rol için tutulan satırları, eksikliği, sonlu değer kalite
dışlamalarını, etiket belirsizliğini, pozitif/negatif sınıf sayılarını ve tarih
kapsamını raporlamalıdır. Geliştirme kapsamı kapısı ancak bundan sonra gözden
geçirilebilir. Ayrı `measurement_semantics` ve `training_runner_review` kapıları
da beklemektedir; bu yüzden model eğitimi hâlâ engellidir.

## Sınırlamalar ve belirsizlik

- Tarama yalnızca tanımlayıcı ve zaman damgası sütunlarını kontrol etti; özellik
  birimleri, formüller, EPS yorumu, etiket doğruluğu veya sınıf dengesi hakkında
  sonuç vermez.
- Benzersiz satır sayımı her Parquet üyesi içinde yapıldı. Birden fazla üyede
  HARP bulunmaması, gözlenen yerleşimde üyeler arası HARP/zaman tekrarını olanaksız
  kıldı.
- Sıklık sürekliliği ölçüm geçerliliğini göstermez. NaN, sonsuz, sentinelli ve
  kalite alanı dışlamaları nihai topluluğu azaltabilir.
- Sıkıştırılmış arşivlerin tamamı zorunlu olarak akış okuyucusundan geçti, ancak
  Parquet mantıksal taraması ayrılmış dönem sonuçlarını, ölçümlerini veya model
  sütunlarını yansıtmadı. Bu bir iş akışı kontrolüdür; keyfî doğrudan erişime
  karşı güvenlik sınırı değildir.
- Sonuç aşağıdaki manifest ve kod özetlerine bağlıdır. Değişen bir arşiv,
  protokol, zaman dönüşümü veya tarayıcı yeni bir denetim çıktısı gerektirir.

## Yeniden üretim

Ağ erişimiyle depo kökünden çalıştırın:

```sh
.venv/bin/python scripts/audit_v2_layout.py \
  --output artifacts/v2_layout_audit_20261025_r4 --workers 4
```

Komut mevcut bir çıktının üzerine yazmayı reddeder. Kabul edilen makine raporu
`artifacts/v2_layout_audit_20261025_r4/report.json` dosyasıdır ve şunları kaydeder:

| Girdi veya kod | SHA-256 |
| --- | --- |
| `config/swan_sf_v2_sources.verified.json` | `4da23877d22c2676ab76950c69c016bbe8eaacd8049fc806dad078752feafa3d` |
| `config/experiment5-v3.json` | `e447ec51797cd14b0e44b85f0fae4e46ef2c67f3f981c23b2bd7b47f41c09ae4` |
| `helio24/v2_archive.py` | `c43557b531e826e5ec265acec82fee0ad694fd1b0748622b5dd571be0aff36c1` |
| `helio24/v2_contract.py` | `e195bbc33d1afc2aed417229369723194413eca5c5ac461c38bb22916a9ad9cd` |
| `scripts/audit_v2_layout.py` | `84981b6b3225b4b758779640e673f31db3f89f69903ddc280598a4020698dd8d` |

Gözden geçirilmiş dil çiftini yeni bir dizine yayınlayın:

```sh
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_layout_20261025
```
