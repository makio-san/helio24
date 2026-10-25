# SWAN-SF-V2 veri sözleşmesi denetimi

Tarih: 2026-10-25. Karar: **UTC dönüşümü, V2 kalite politikası ve GOES
etiket politikası sabitlendi; diğer üç koşul eğitimi engellemeye devam
ediyor.** Bu bir geliştirme verisi denetimidir, model deneyi değildir. Yeni
tahmin skoru içermez; 2024-2025 satırlarını veya sonuçlarını incelemez.

## Kapsam ve kaynak kimliği

Sınırlı yerel kaynak, ham arşiv bölüm 1'den daha önce sabitlenen ilk Parquet
üyesidir. Yalnız `obs_start < 2019-01-01` satırları izdüşürüldü. Taramada
131,290 birleştirilmiş satır, 131,284 ayrı gözlem satırı ve 186 HARP vardır.
Olay sütunları yalnız bu geliştirme veri sözleşmesi denetimi için okundu;
model girdisi olarak kullanılmaları yasaktır.

Dört ham arşivin kimliği 2026-10-25 tarihinde doğrulanmış HTTPS üzerinden
kontrol edildi:

| Bölüm | İçerik uzunluğu (bayt) | ETag | Son değişiklik (UTC) | SHA-256 |
| ---: | ---: | --- | --- | --- |
| 1 | 1,177,434,736 | 462e3a70-65ccb14823788 | 2026-10-01 17:52:32 | 26fbe84600dcbd2600bced76eeff9df097b5de2bc78328160342869827b1dd3b |
| 2 | 1,284,717,836 | 4c933d0c-65ccb20b27a70 | 2026-10-01 17:55:56 | 1fc49bff4e61ea2ac608d1c08dd45f335463f8b31e828afc60eaa283e8d50692 |
| 3 | 1,246,106,315 | 4a4612cb-65ccb20d79562 | 2026-10-01 17:55:59 | c829699b0afecb88b5cc1743e620096a21565a5127ea76be9fb9cfa6be69783f |
| 4 | 1,302,570,086 | 4da3a466-65ccb2236ed31 | 2026-10-01 17:56:22 | 35e86b7e27b52bfba83f6bdf3d39b1b15bc03fa0b52552a590472a4ceed0bf72 |
| Toplam | 5,010,828,973 | — | — | verified |

ETag, uzunluk ve tarihler, 5,010,828,973 baytın tamamı SHA-256 akışından
geçirilmeden önce kontrol edildi. Arşiv gövdeleri kaydedilmedi. Dört tam özet
artık bayt kimliğini sabitliyor; bu nedenle `versioned_dataset_manifest`
verified durumundadır. V2 makalesi hâlâ ön baskı v1'dir ve final Dataverse
DOI'sinin hakem değerlendirmesinden sonra geleceğini söyler. Arşivleri üreten
kesin toolkit commit'i belirlenmediği için `measurement_semantics` pending
kalır. Doğrulanmış kaynak envanteri `config/swan_sf_v2_sources.verified.json`
dosyasındadır; önceki bekleyen envanter korunur.

## Gözlem saati dönüşümü

Sabit toolkit dokümantasyonu, JSOC `*_TAI` dizgelerinden ayrıştırılan HARP
saatlerinin zaman dilimsiz döndürüldüğünü ve UTC gerektiğinde dönüştürülmesi
gerektiğini belirtir. Helio24 artık `obs_start` değerini TAI olarak yorumlar,
tarihsel TAI-UTC farkını uygular ve zaman dilimi açık UTC üretir. IERS/USNO
kaydı bu veri dönemi için 2012-07-01'den önce 34 saniye, 2015-07-01'den önce
35, 2017-01-01'den önce 36 ve sonrasında 37 saniyeyi destekler.

| TAI-UTC farkı (saniye) | Ayrı gözlem satırı |
| ---: | ---: |
| 34 | 35,342 |
| 35 | 68,223 |
| 36 | 17,558 |
| 37 | 10,161 |
| Toplam | 131,284 |

Sözleşme TAI alanındaki zaman dilimli girdiyi, 2010-2025 dışındaki zamanları
ve pandas'ın gösteremediği artık saniye anını reddeder. Ayrıca artık saniye
geçişini kesen 12 saatlik gözlem penceresini, süresini sessizce değiştirmek
yerine dışlar. Böylece belirli bir UTC tahmin zamanı üretilir.

V2 patlama saatleri, zaman dilimsiz kaynak katalog UTC'si olarak yorumlanır.
Ekli 501 GOES olay satırının 496'sı sabit V1 birleşik kataloğunda zirve zamanı
ve sınıf bakımından tam eşleşir. M/X GOES satırlarının 49/49'u tam eşleşir;
eşleşmeyen beş satır B sınıfıdır. Bu, olay saati yorumu için güçlü eski dönem
kanıtıdır; tam V2 yayını için eksiksizlik iddiası değildir.

## Sürümlü V2 kalite politikası

V2'de kayıt düzeyinde `QUALITY` veya `IS_TMFI` alanı yoktur. Bu nedenle
Helio24 tarihsel maskeyi yeniden ürettiğini iddia etmek yerine ayrı bir politika
sabitler:

1. Bir HARP'tan benzersiz 12 dakikalık TAI sıklığında tam 60 satır iste.
2. Sayısal olmayan ve sonsuz değerleri eksik say.
3. 24 ağırlıksız manyetik parametreden herhangi biri %20'den fazla eksikse
   pencereyi reddet.
4. Ortalama, popülasyon standart sapması, son değer ve değişimi yalnız sonlu
   değerlerden hesapla. Sonraki model doldurma ve eksiklik göstergeleri yalnız
   eğitimde öğrenilir.
5. Artık saniye geçişini kesen gözlem pencerelerini dışla.

Aynı beş sabit 2011 örtüşme penceresi, yerel V2 sonluluğu ve V2 değerlerine
uygulanan eski `QUALITY=0` artı `IS_TMFI` maskesiyle değerlendirildi:

| Büyüklük | Yerel V2 politikası | V2 üzerinde tarihsel maske |
| --- | ---: | ---: |
| Tutulan pencere | 5 | 5 |
| Eksik ölçüm konumu | 96 | 432 |
| Karşılaştırılan özet değer | 480 | 480 |
| Politikalar arasında değişen özet değer | 280 | 280 |

İki politika bu beş pencereyi de tutar fakat 480 özetin 280'i değişir.
Sonuç, bu örnekte tutma kararlarının aynı olmasının özellik eşdeğerliği
olmadığını kanıtlar. Yeni politika V2'ye özgü ayrı bir sürüm olarak kaydedilir
ve böyle raporlanmalıdır. Tam dönem eksiklik ve tutma oranı, bekleyen geliştirme
kapsamı denetiminin parçasıdır.

## GOES etiket dahil etme politikası

Birincil hedef, aynı HARP için yarı açık UTC
`[forecast_time, prediction_end)` aralığında en az bir GOES M/X patlama
zirvesidir. V2 makalesi bu yarı açık aralığı tanımlar; sabit dilimleyici kodu
ise son örnek zamanını dahil eder. Helio24 etiketi olay satırlarından yeniden
üretir ve makaledeki tanımı izler; sağ sınırda `peak_class` değerine güvenmez.

Yalnız `has_goes=True` satırları birincil olaya katkı verir. Yalnız SSW/XRT
satırları ayrı duyarlılık çalışması için korunur. Makale `very_low` ve
`unverified` dışındaki atamaları doğrulanmış saydığı için `very_high`, `high`,
`moderate` ve `low` HARP atamaları kabul edilir. `very_low` M/X satırı, aday
HARP için negatif etiketi engeller. Eksiksiz dış GOES M/X envanteri zorunludur;
güvenilir HARP'ı olmayan her güçlü olay eşzamanlı bütün HARP pencerelerinde
negatif etiketi engeller. Bu envanterin eksiksizliği doğrulanmadan etiket
üretimi çalışmayı reddeder.

| GOES sınıfı | very_high | high | moderate | low | very_low | Toplam |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M | 29 | 14 | 1 | 1 | 0 | 45 |
| X | 1 | 2 | 0 | 1 | 0 | 4 |
| Toplam | 30 | 16 | 1 | 2 | 0 | 49 |

Sınırlı örtüşmedeki 49 M/X GOES satırının tamamı kabul edilen güven politikasını
sağlar. Bu, tam geliştirme döneminde belirsiz veya eşlenmemiş güçlü olay
olmadığını göstermez. Etiketler üretilmeden önce bu eksiksizlik kontrolü gerekir.

## Bu revizyondan sonraki koşul durumu

| Koşul | Durum | Gerekçe |
| --- | --- | --- |
| measurement_semantics | pending | Üretim hesaplama revizyonu ve kesin EPS anlamı çözülmedi |
| quality_policy | verified | Ayrı V2 politikası uygulandı, test edildi ve sınırlı olarak denetlendi |
| utc_conversion | verified | Açık TAI-UTC dönüşümü uygulandı ve test edildi |
| label_inclusion_policy | verified | GOES kaynağı, güven, belirsizlik ve yarı açık sınır kuralları sabitlendi |
| versioned_dataset_manifest | verified | Dört sıkıştırılmış arşivin tam SHA-256 kimliği var |
| development_coverage_audit | pending | 2024 öncesindeki bütün bölümler taranmadı |
| training_runner_review | pending | Deney 5 V2 eğitim çalıştırıcısı yok |

Buradaki verified, kural ve kanıtın bu proje için sabitlendiği anlamına gelir.
V2'nin V1'i yeniden ürettiği, üst kaynak üretiminin bütünüyle tekrarlanabilir
olduğu veya model başarısının bilindiği anlamına gelmez.
`config/experiment5-v3.json`, yalnız gelecekteki yürütme için önceki tasarımların
yerini alır ve hâlâ `design_frozen_data_contract_pending` durumundadır.

## Yeniden üretim

```sh
python scripts/audit_v2_contract.py --output artifacts/v2_contract_audit_20261025_r2
python scripts/check_evaluation_protocol.py \
  --config config/experiment5-v3.json \
  --output artifacts/experiment5_v3_preflight_20261025
python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_contract_20261025
```

Denetim mevcut dizinin üzerine yazmayı reddeder. Hazırlık kontrolü kod 2 ile
çıkmalı ve üç bekleyen koşulu listelemelidir. Ham veri ve üretilen artifact
dosyaları Git dışında kalır. Sırada yalnız 2024 öncesi satırları Parquet tarama
sınırında seçen bir okuyucu kurmak, ardından model eğitiminden önce geliştirme
kapsamını denetlemek vardır.

Kaynaklar: [SWAN-SF-V2 ön baskı v1](https://arxiv.org/html/2610.04591v1),
[Space Weather Toolkit dilimleyici dokümantasyonu](https://dmlab.cs.gsu.edu/docs/spaceweather_toolkit/slicer.html),
[USNO artık saniye bilgisi](https://maia.usno.navy.mil/products/leap-second),
[IERS Bulletin C](https://datacenter.iers.org/data/html/bulletinc-058.html).
