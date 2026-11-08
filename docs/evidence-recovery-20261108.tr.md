# Yerel dosya tahliyesi sonrası kanıt kurtarma: envanterler ve geliştirme shard'ları doğrulandı

## Özet

2026-11-08'de, Masaüstü klasörünün bulut senkronunun birçok proje dosyasını yerel diskten tahliye ettiği görüldü
(`dataless` işaretli, içerik yalnızca bulutta). Bu dosyaların okunması takıldı ve zaman aşımına uğradı. Git geçmişi
güvendeydi, çünkü `1ad1f24`'e kadar her commit zaten uzak depodaydı. Git'in yok saydığı kanıtlar, resmi
kaynaklardan yeniden üretilerek veya geri kopyalanarak kurtarıldı ve her öğe, kayıptan önce dondurulmuş bir hash ile
karşılaştırıldı. Baseline kolunun ihtiyaç duyduğu geliştirme özellik shard'ları yeniden üretildi ve 20'sinin hepsi
donmuş SHA256 değerleriyle eşleşti. Bu kurtarmada hiçbir model, eşik, etiket veya önceki raporların hiçbir sonucu
değişmedi. Ayrılmış 2024–2025 testine erişilmedi.

## Ne kurtarıldı ve nasıl kontrol edildi

| öğe | miktar | kontrol | sonuç |
| --- | --- | --- | --- |
| HEK büyük olay envanteri | 164 aylık yanıt (116 sağlam, 48 yeniden çekildi) | events.csv SHA256 donmuş değere eşit | eşleşti |
| V2 etiket envanteri dosyaları | 3 | SHA256, uzlaştırma sayıları ve arşiv SHA256 donmuş değerlere eşit | 3 / 3 |
| Geliştirme özellik shard'ları | 20 | SHA256 donmuş shard raporuna eşit | 20 / 20 |
| temporal_years_20261101_r1 | 429 dosya | listelenen artifact hash'leri | 292 / 292 |
| sequences_20261101_r2 | 5494 dosya | donmuş hash kaynağı yok | doğrulanmadı |

HEK envanterinde 1356 olay vardır ve `events.csv` SHA256 değeri
`f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f`'dir. Etiket uzlaştırmasında 723 tam pik
sınıfı eşleşmesi, 0 çelişki ve 622 dış atanmamış pik sınıfı vardır; atanmamış olay envanterinin SHA256 değeri
`e584b58fbea9f1e03f025df75edae9312303f0dafd82db04347a5ba7fc71be8f`'dir. `sequences_20261101_r2` dosyaları
diskte mevcuttur, ama bunlar için hash listesi bulunamadı, bu yüzden doğrulanmış sayılmamalıdır.

## Yeniden üretilen geliştirme shard'ları

| rol | satır | pozitif |
| --- | --- | --- |
| train | 484549 | 8698 |
| calibration | 50756 | 421 |
| validation | 60366 | 781 |

Yeniden üretilen raporda 5983 HARP ve 595671 tutulan satır vardır; bu sayılar donmuş shard raporuyla aynıdır.
Tamamlanma zamanı, girdi yolları ve `helio24/v2_archive.py` hash'i donmuş rapordan farklıdır. Shard başına
hash'ler farklı değildir, yani kod farkı çıktıyı değiştirmemiştir. Donmuş shard raporunun SHA256 değeri
`62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82`, yeniden üretilen raporun SHA256 değeri
`36e8484a1496f6f1d7e117143766bfa9a15c306f4ac3984be4de321d2b5f7086`'dır. Doğrulanmış shard'lar sonra donmuş
dizine yerleştirildi ve orada yeniden kontrol edildi: 20 / 20 eşleşti.

## İndirmeler

Resmi SWAN-SF arşivleri iki kez akıtılıp doğrulandı: bir kez etiket envanteri için, bir kez shard yeniden
üretimi için.

| bölüm | geçiş başına sıkıştırılmış bayt |
| --- | --- |
| 1 | 1177434736 |
| 2 | 1284717836 |
| 3 | 1246106315 |
| 4 | 1302570086 |
| bir geçişin toplamı | 5010828973 |
| iki geçişin toplamı | 10021657946 |

Daha önceki iki shard denemesi çıkış koduyla 0 verip hiçbir çıktı veya günlük yazmadan bitti ve nedeni bilinmiyor.
Ne kadar veri aktardıkları belirlenemez; bu yüzden gerçek toplam tablodan yüksek olabilir. 48 HEK ayı küçük
sorgularla yeniden çekildi.

## Sınırlar ve belirsizlik

- Çalışma durduğunda özgün Masaüstü klasöründe yaklaşık 18400 dosya hâlâ tahliye edilmiş durumdaydı; çoğu Git
  nesneleri ve yeniden üretilebilir rapor çıktılarıydı. Kurtarmada kullanılan çalışma kopyası, uzak depodan alınmış
  yeni bir klondur ve senkronize klasörün dışındadır.
- Sessiz çıkışların nedeni belirlenmedi. Tahliye edilmiş dosyalar ve başarısız bulut indirmeleri en olası
  açıklamadır, ama kanıtlanmadı.
- Hash'ler, yeniden üretilen dosyaların donmuş dosyalara eşit olduğunu kanıtlar. Donmuş dosyaların kendilerinin
  doğru olduğunu göstermez; bu kurtarmanın kapsamı dışındadır.
- `sequences_20261101_r2` shard'ları doğrulanmamıştır.

## Yeniden üretim

Aşağıdaki komutlar, yeniden üretilen üç artifact'ı yeniden oluşturur. Yer tutucuyu, sağlam ham HEK yanıtlarının
dizini ile değiştirin. İndirme adımları her biri yaklaşık 5 GB çeker.

```sh
python scripts/rebuild_hek_inventory.py --source <surviving raw response directory> --output artifacts/hek_major_inventory_recovery_20261108_r1 --expected-events-sha256 f0431c27d11abf7b2908f588634eccd61d960d5c1e67b1b4ffcfd2a5416afb0f
python scripts/audit_v2_label_inventory.py --inventory artifacts/hek_major_inventory_recovery_20261108_r1 --output artifacts/v2_label_inventory_recovery_20261108_r1
python scripts/materialize_v2_development.py --output artifacts/v2_development_features_recovery_20261108_r1 --inventory-audit artifacts/v2_label_inventory_recovery_20261108_r1
```

Herhangi bir shard'ı kullanmadan önce yeni `report.json` içindeki her `shards[].sha256` değerini, donmuş
`artifacts/v2_development_features_20261025_r2/report.json` ile karşılaştırın.
