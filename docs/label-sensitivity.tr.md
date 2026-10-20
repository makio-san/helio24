# Etiket ilişkilendirme duyarlılığı sonuçları

Bu, bölüm 4 geliştirme analizidir; deney 2'nin 50,631 kayıtlı tahminini ve
0.0479986873703553 sabit eşiğini kullanır.
[Protokol](label-sensitivity-protocol.md), [kaynak incelemesinden](event-provenance.tr.md)
sonra, karşılaştırmalar hesaplanmadan önce commitlendi.
Model, referans hedefler, katalog zirveleri ve alarm durumları değişmedi.

## Altı sabit karşılaştırma

Her varyant doğrulanmış pozitif dosya adı kanıtını içerir. Geçmiş kanalı NOAA,
konum veya birleşimidir. `nearest`, katalog zirvesinin altı dakika yakınını;
`containing`, anotasyonla başlayan 12 dakikalık aralığa düşen zirveyi kabul eder.
Kurallar kanıtın uygunluğunu değiştirir; olayın katalog zirvesini değiştirmez.

| Zamanlama | Geçmiş kanalı | Yakalanan / değerlendirilen | Koşullu olay recall | Eşlenmemiş | Belirsiz | Tahmin kapsamı yok | Negatif etiket çelişkileri |
| --- | --- | --- | --- | --- | --- | --- | --- |
| En yakın | NOAA | 85 / 86 | 98.84% | 63 | 0 | 1 | 0 |
| En yakın | Konum | 86 / 87 | 98.85% | 62 | 0 | 1 | 10 |
| En yakın | Birleşim | 86 / 87 | 98.85% | 62 | 0 | 1 | 10 |
| Kapsayan | NOAA | 90 / 91 | 98.90% | 57 | 0 | 2 | 0 |
| Kapsayan | Konum | 91 / 92 | 98.91% | 55 | 1 | 2 | 29 |
| Kapsayan | Birleşim | 91 / 92 | 98.91% | 55 | 1 | 2 | 29 |

Her satır tahmin dönemi içindeki aynı 150 tüm-Güneş olayını kapsar.
Recall yalnızca tek HARP'a eşlenmiş, zirvesini kapsayan kullanılabilir tahmini
olan olayları içerir. Diğer durumlar kaçırma sayılmaz. Çelişkiler, hedefi sıfır
olan olay/pencere çiftleridir; benzersiz patlama sayısı değildir.

`nearest_location` referansı önceki incelemenin olay durumu, HARP, yakalama,
başlangıç öncesi uyarı, tahmin sayısı ve kapsamını yeniden üretir.
Önceki 24 saatin tamamı kapsanan alt kümelerde nearest için 47, containing
için 51 olay vardır; hepsi yakalandı. Yakalanan tüm olaylarda katalog
başlangıcından kesin olarak önce bir alarm var. Bu, alt kümeler dışında
eksiksiz izleme anlamına gelmez.

## Sabit olay paydası

**Altı varyantta aynı HARP üzerinde** değerlendirilen tam 85 olay var.
Hepsi aynı 84 olayı yakalıyor: %98.82 koşullu recall.
Tablodaki küçük artışlar daha iyi tahminlerden değil değişen uygunluktan
kaynaklanıyor. Hiçbir kural kazanan olarak seçilmedi.

9053 (M2.2, HARP 4678) bütün varyantlarda tek kaçırılan değerlendirilmiş olay.
Önceki 24 saatte 10.15 saat tahmin durumu kapsamı var.
Yanlış alarm yükü her varyantta 4,264 bölge-saat; varsayımsal yeni etiketlerle
yeniden hesaplanmadı.

## Paydayı değiştiren durumlar

- **8864 / HARP 4502:** konum kanalı değerlendirmeyi mümkün kılıyor;
  yalnız NOAA geçmişinde eşlenmemiş kalıyor. Konum dahilken iki zaman
  kuralında da on negatif etiket çelişkisi var.
- **8765 / HARP 4466:** containing konum anotasyonunu kabul ediyor.
  Yakalanıyor, fakat 19 hedef-sıfır pencereyle örtüşüyor. 8864 ile toplam 29 çelişki.
- **9529:** containing, HARP 4941'in dosya adı/konum kanıtına ek HARP 4920
  konum ilişkisini açığa çıkarıyor. Konum/birleşim varyantları elverişli HARP'ı
  seçmek yerine olayı belirsiz sayıp dışlıyor. Nearest referansı 4941'de değerlendiriyor.
- **9035, 9097, 9150, 9159, 9235:** containing bütün kanallarda bu beş olayı
  değerlendirmeye ekliyor; hepsi yakalanıyor.
- **9225 / HARP 4781:** containing ilişki kuruyor ama uygun tahmin yok;
  recall paydasının dışında kalıyor.

Yalnız NOAA varyantlarında negatif etiket çelişkisi yok. Bu, NOAA geçmişinin
tam veya fiziksel olarak doğru olduğunu kanıtlamaz; ayrıca daha fazla olayı
eşlenmemiş bırakır. Eğitim etiketleri değişmeden bağımsız kaynak incelemesi gerekir.

## Yeniden üretim ve teslim

Olay denetimi ve kaynak incelemesinden sonra
`python scripts/run_label_sensitivity.py` çalıştırılır. Kaynak, üretici kod ve
çıktı özetleri doğrulanır; mevcut deneyin üzerine yazılmaz. Önceki çıktılar
korunur. `artifacts/label_sensitivity/` Git dışında kalır:

- `metrics.csv`: sayılar, koşullu recall, ortak olay ve tam kapsam alt kümeleri.
- `events.csv`, `mappings.csv`: her varyantın eşlemeleri ve kanıtları.
- `transitions.csv`: referansa göre olay durumu/HARP/yakalama değişimleri.
- `conflicts.csv`: yeniden etiketlemeden negatif olay/pencere çelişkileri.
- `report.html`, `report.json`, `protocol.md`: bağımsız rapor ve kaynak bilgisi.

Dashboard'daki **Alarm & event audit → Label association sensitivity** bölümü
çıktıları doğrular, altı karşılaştırmayı ve değişen olayları gösterir; CSV/HTML
indirmeleri sunar. Bu betimsel karşılaştırmadan yeni final-test performansı
iddiası çıkmaz; bağımsız dönem hâlâ gerekir.
