# Olay etiketlerinin kaynak incelemesi

On olay/pencere çelişkisi resmî bölüm 4 arşivinde yeniden üretilebiliyor.
8864 olayı HARP 4502'nin konuma dayalı geçmişinde var; NOAA numarası
geçmişinde ve arşivdeki pozitif dosya adı etiketlerinde yok.
Bu, 24 saatlik aralık hesabı hatası değil, ilişkilendirme kanalları arasındaki
uyuşmazlıktır. Fiziksel olarak doğru ilişkiyi veya özgün dilimleme kodunu kanıtlamaz.

## Katalog olayı 8864 için kanıtlar

Birleşik katalog M2.5, başlangıç 2014-09-03 13:20 UTC, zirve 13:54 UTC ve
NOAA bölgesi 12155 bildiriyor. 13:48 UTC'de HARP 4502'nin
`MFLARE_LABEL_LOC` alanında `M2.5@8864:Primary` var; `MFLARE_LABEL` boş.
Arşivde başka HARP bu olaya geçmiş kanıtı sağlamıyor; pozitif dosya adı yok.

Katalog konumu boylam 18°, enlem −14°. HARP kutusu 13:48 UTC'de boylam
8.314°–30.087°, enlem −24.940°–−11.551° aralığında; konum kutunun içinde.
Satırda QUALITY=0 ve IS_TMFI=True. Bu ölçüm bayrakları patlamanın fiziksel
kaynağını karara bağlamaz.

2014-09-02 21:24 ile 2014-09-03 06:24 UTC arasında saatlik verilen on
HARP-4502 tahmini, gelecek 24 saatinde zirveyi içeriyor; tüm dosya adları FQ.
Zirve sınırdan uzakta. Altı dakika önceki anotasyon aşağıdaki iki zaman
kuralına da uyuyor; bu on negatif etiket ayrık zamanlamayla açıklanamaz.

Katalogdaki GOES konumu (18, −14), saklanan NOAA merkezi yaklaşık
(−80.84, −20). SSW ilişkisi doğrulanmamış, Hinode ilişkisi doğrulanmış.
Kaynak incelemesi gerekiyor; yalnızca koordinatlara bakarak NOAA kimliğini
değiştirmek veya pencereleri yeniden etiketlemek gerekçelendirilemez.

## Anotasyon zamanları

Arşivdeki 214 ayrı doğrulanmış M/X geçmiş kaydının tamamı
`annotation_time <= peak_time < annotation_time + 12 minutes` koşulunu sağlıyor.
Anotasyon zirveden 0–11 dakika önce. Yalnızca 125 kayıt
`abs(annotation_time - peak_time) <= 6 minutes` koşulunu sağlıyor.

| Geçmiş kanalı | Doğrulanmış kayıtlar | Altı dakika içinde | Kapsayan 12 dakikalık aralık |
| --- | ---: | ---: | ---: |
| NOAA M | 96 | 57 | 96 |
| Konum M | 98 | 58 | 98 |
| NOAA X | 10 | 5 | 10 |
| Konum X | 10 | 5 | 10 |

Kayıtlar HARP, zaman, kanal ve patlama kimliğiyle tekilleştirildi; 214 bağımsız
patlama değildir. Önceki incelemede zaman nedeniyle dışlanan 45 konum kaydının
tamamı kapsayan-aralık kuralına uyuyor. Dışlanmaları kimliklerinin yanlış
olduğunu göstermez. Örüntü, bu sürümde makaledeki en yakın örnek yerine
aralık başlangıcına yerleştirmeyi destekler; bütün sürüm veya sınıflara genellenmez.

## İlişkilendirme yöntemleri arasındaki fark

Altı dakika kısıtı olmadan doğrulanmış geçmişler kullanıldığında iki yöntemin
desteklediği 105 HARP/olay çifti, yalnızca konumdan gelen üç ve yalnızca
NOAA'dan gelen bir çift var:

| Katalog olayı | HARP | Geçmiş desteği |
| --- | --- | --- |
| 8765 | 4466 | Yalnız konum |
| 8864 | 4502 | Yalnız konum |
| 9053 | 4678 | Yalnız NOAA numarası |
| 9529 | 4920 | Yalnız konum |

9053 için konum geçmişi yokken dosya adı HARP 4678'i destekliyor.
9529 için dosya adları HARP 4941'i gösteriyor. Dosya adlarını konum
geçmişiyle birleştirmek açık bir belirsizlik politikası gerektirir.
Yalnızca zaman filtresini değiştirmek ek ilişkileri görünür yapabilir.

Özgün inceleme dosya adları ve ihtiyatlı filtrelenmiş konum geçmişini kullandı.
86/87 yakalama bu tanıma koşulludur; yöntem uyuşmazlıkları çözülmeden kesin
olay düzeyi performansı değildir.

## Yeniden üretim ve koruma

Olay incelemesinden sonra `python scripts/investigate_event_provenance.py`
çalıştırılır. Resmî arşivin MD5'ini kontrol eder, 51,261 pencereyi tarar,
katalog kimlik ve büyüklüklerini doğrular; geçmişleri, zaman farklarını,
ölçümleri ve dosya adlarını `artifacts/event_provenance/` içine yazar.
Mevcut çıktılar değiştirilmez.

Kaynak ve çıktı özetleri incelemeyi önceki denetime bağlar. Dashboard'daki
isteğe bağlı **Label provenance investigation** bölümü göstermeden önce
özetleri doğrular. Testler zaman kurallarını ayırır, bölgeler arası kanal
uyuşmazlıklarını korur, sentetik arşivi uçtan uca sınar ve değişmiş kanıtı reddeder.

Özgün etiket, model, eşik ve geçmiş çıktılar korundu. Sonraki etiketleme
çalışması kapsayan-aralık kuralını sürümlemeli, NOAA ve konum kanallarını ayrı
tutmalı, çoklu HARP olaylarını dışlamalı veya incelemeli; yeni etiketlerle
eğitimden önce duyarlılığı raporlamalıdır.

Kaynak bağlamı: [SWAN-SF özgün makalesi](https://pmc.ncbi.nlm.nih.gov/articles/PMC7351763/),
patlama bütünleştirme ve dilimleme bölümleri. Sayısal bulgular doğrulanmış
arşiv ve birleşik katalogdan gelir.
