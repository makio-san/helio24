# SWAN-SF-V2 büyük patlama etiket envanteri denetimi

Denetim tarihi: 2026-10-25. Karar: **dondurulmuş HEK/SWPC envanteri, kapalı-hata
yöntemiyle 2024 öncesi V2 etiketleri üretmek için tamdır**. V2'deki 723 farklı
ilişkilendirilmiş GOES M/X zirve/sınıf olayının tamamı envanterle birebir
eşleşir; yalnızca V2'de bulunan olay ve zirve zamanı sınıf çelişkisi yoktur. Bu
denetim model eğitmedi, tahmin eşiğini değiştirmedi ve ayrılmış 2024–2025
satırlarını okumadı.

## Kapsam ve yöntem

Dış envanter, sınıfı `>= M1` ve zirve zamanı
`[2010-05-01, 2024-01-01)` aralığında olan GOES patlamalarını kapsar. Resmî HEK
uç noktasından birbiriyle örtüşmeyen 164 aylık sorguyla; `event_type=FL`,
`OBS_Observatory=GOES` ve `FL_GOESCls>=M1` koşulları kullanılarak alındı. Her
yanıt `overmax=false` bildirdi. Ham yanıtlar ve normalleştirilmiş olaylar yeni,
Git tarafından yok sayılan bir artifact dizinine yazıldı ve uzlaşmadan önce
özetlendi.

V2 tarafı dört sabitlenmiş arşivi
`obs_start < 2024-01-01T00:00:37 TAI` koşuluyla taradı. Her tam arşiv, beş
Parquet üyesi okunmadan önce dondurulmuş `Content-Length`, ETag ve SHA-256
değeriyle eşleşti. İlişkilendirilmiş olay satırları ayrı ayrı doğrulandı.
Geçerli GOES M/X olayları dış envanterle normalleştirilmiş
`(peak_time, goes_class)` kimliği üzerinden birebir karşılaştırıldı. Kaynak olay
kimlikleri korundu; yinelenen HEK kayıtları sessizce atılmadı.

## Dondurulmuş HEK envanteri

| Nicelik | Sonuç |
| --- | ---: |
| Aylık yanıt | 164 |
| Kaynak olay satırı | 1,356 |
| Farklı zirve/sınıf olayı | 1,345 |
| M satırı | 1,285 |
| X satırı | 71 |
| Yinelenen zirve/sınıf anahtarı | 11 |
| Yinelenen anahtarlardaki satır | 22 |

1,356 kaynak satırı; 1,352 `SWPC`, iki `SEC standard`, bir `SWPC standard` ve
bir `SEC nonstandard` sağlayıcı kaydından oluşur. Yinelenen 11 zirve/sınıf
anahtarı birden fazla kaynak kimliğini veya revizyonu temsil eder. Etiket
eşleştirmesi bunların 1,345 farklı zirve/sınıf kimliğini kullanırken dondurulmuş
envanter her kaynak satırını korur.

## Uzlaşma sonuçları

| Nicelik | Sonuç |
| --- | ---: |
| V2 ilişkilendirilmiş bağlantıları | 723 |
| V2 farklı zirve/sınıf olayları | 723 |
| Birebir zirve/sınıf eşleşmesi | 723 |
| Yalnızca V2'deki zirve/sınıf olayları | 0 |
| V2'ye atanmamış HEK olayları | 622 |
| Zirve zamanı sınıf çelişkileri | 0 |
| Dışlanan geçersiz ilişkilendirilmiş olay satırları | 23 |

V2'de ilişkilendirilmiş tüm GOES M/X olayları dış envanterde temsil edilir.
V2'nin ilişkilendirilmiş olay kümesinde bulunmayan 622 farklı HEK olayı,
atanmamış büyük patlamaların sıradan negatifler gibi ele alınmasını önlemek için
gereklidir. Sonraki etiket üreticisi dondurulmuş HARP ilişkilendirme politikasını
uygulamalıdır: kabul edilen ilişkilendirilmiş olaylar pozitif üretebilir,
`very_low` veya başka şekilde belirsiz atamalar dışlanmalıdır ve atanmamış
olaylar bir bölgeye atanmak yerine etkilenen tahmin pencerelerini dışlamalıdır.

23 geçersiz ilişkilendirilmiş satırda `start_time > peak_time` veya
`peak_time > end_time` vardır. Karantinada kalırlar; onarılmadılar ve uzlaşmada
kullanılmadılar. Dışlanmaları yalnızca V2'de bulunan büyük olay oluşturmaz:
geçerli ilişkilendirilmiş kümede HEK'de bulunmayan olay sayısı yine sıfırdır.

## Kapı ve precision sonuçları

`development_coverage_audit` kapısı
`pending_unassigned_major_event_inventory` durumundan doğrulanmış etiket
envanteri kapsamına ilerleyebilir. Bu, Experiment 5 eğitimine izin vermez:
`measurement_semantics` ve `training_runner_review` hâlâ beklemektedir.

Denetim yeni bir precision değeri raporlamaz. Bilinen bir yanlış negatif etiket
kaynağını ortadan kaldırır: 622 dış büyük olay V2'nin güvenilen
ilişkilendirilmiş olay kümesinde yoktu. Daha önce çözülmemiş tüm pencereleri
negatif kabul etmek, gerçek olayları yanlış alarm sayabilir ve precision'ı
olduğundan düşük gösterebilirdi. Kalan kapılar kapandıktan sonra aday modeller,
dondurulmuş `recall >= 0.95` koşulunu sağlayan eşikler arasından önce en yüksek
precision, ardından en az yanlış pozitif ölçütüyle seçilecektir.

## Sınırlamalar ve belirsizlik

- HEK değişebilen bir hizmettir. Yeniden üretim dondurulmuş ham yanıt özetlerini
  kullanır; daha sonraki canlı bir sorgu revize edilmiş kayıtlar döndürebilir.
- Birebir zirve/sınıf eşleştirmesi, V2'ye bağlı büyük olaylar için envanter
  kapsamını gösterir. Her HEK uzamsal ilişkilendirmesinin veya her V2 HARP
  ilişkilendirmesinin fiziksel olarak doğru olduğunu kanıtlamaz.
- Atanmamış 622 olay bu denetimle bir HARP'a atanamaz. Pozitif bölge etiketi
  değil, kapalı-hata dışlaması sağlarlar.
- Test aralığı dışlandı. Bu karar 2024–2025 performansı, precision veya
  kalibrasyonu hakkında kanıt sunmaz.
- Model eğitilmedi. Önceden kaydedilmiş ve incelenmiş bir eğitim çalışması yeni
  tahminler üretmedikçe mevcut geliştirme metrikleri değişmez.

## Yeniden üretim ve özetler

Depo kökünden, ağ erişimi ve yeterli geçici disk alanıyla çalıştırın. Yeni çıktı
dizinleri kullanın; betikler kanıtların üzerine yazmayı reddeder.

```sh
.venv/bin/python scripts/fetch_hek_major_inventory.py \
  --output artifacts/hek_major_inventory_20261025_r2
.venv/bin/python scripts/audit_v2_label_inventory.py \
  --inventory artifacts/hek_major_inventory_20261025_r2 \
  --output artifacts/v2_label_inventory_20261025_r1 --workers 1
```

| Kanıt | SHA-256 |
| --- | --- |
| HEK ham yanıt kümesi | `37969ae4da798f10e313790b35db9421f657eab18557bdfab8a1904ba0be1d11` |
| HEK normalleştirilmiş olayları | `f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f` |
| Atanmamış büyük olaylar | `e584b58fbea9f1e03f025df75edae9312303f0dafd82db04347a5ba7fc71be8f` |
| Yalnızca V2'deki zirve/sınıf olayları | `804883bb801a590a5ccb80debb2ff274f9bb0dd674cdef33346a1a5505293d6d` |
| Zirve/sınıf çelişkileri | `da7b8c17324642cc2be91a47c800d88d087d705742a9048680e69d6fe515e683` |

Kabul edilen makine raporları
`artifacts/hek_major_inventory_20261025_r2/report.json` ve
`artifacts/v2_label_inventory_20261025_r1/report.json` dosyalarıdır. Gözden
geçirilmiş dil çiftini yeni bir dizine yayınlayın:

```sh
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_labels_20261025
```

Kaynaklar: [HEK API belgesi](https://hekapidocs.readthedocs.io/en/latest/hek_api.html),
[HEK API uç nokta belgesi](https://www.lmsal.com/hek/api.html).
