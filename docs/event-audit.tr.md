# Alarm dönemleri ve kapsanan katalog olayları

Sonraki [kaynak incelemesi](event-provenance.tr.md), 8864 için NOAA/konum
geçmişi uyuşmazlığını ve aralık başlangıcı zamanlama örüntüsünü belirledi.
Aşağıdaki sonuçlar özgün ihtiyatlı kuralları korur.

Olay incelemesi tamamlandı. Uzun alarm süreleri yüksek olay yakalama ile çok
sayıda yanlış pencere alarmının birlikte görülmesini açıklıyor. Ayrıca
kurtarılan bir katalog olayı ile on negatif referans pencere arasında uyuşmazlık bulundu.

[Protokol](event-audit-protocol.md) toplu sonuçlardan önce commitlendi.
Deney 2'nin bölüm 4'teki 50,631 doğrulama kaydı, 470 HARP, tam kalibre
model ve %4.7999 sabit eşik kullanıldı. Model eğitilmedi veya seçilmedi.
Bölüm 5 kullanılmadı.

## Alarm yükü

| Ölçüt | Sonuç |
| --- | ---: |
| İzlenen bölge-saat | 50,631 |
| Alarm bölge-saat | 5,233 |
| Referansa göre yanlış alarm bölge-saat | 4,264 |
| İzlenen bölge-saat içinde yanlış alarm payı | 8.42% |
| Alarm dönemleri | 333 |
| Tamamen negatif etiketli dönemler | 280 |
| Veri sınırına veya boşluğa değen dönemler | 130 |
| En uzun tamamen negatif etiketli dönem | 127 saat |
| Yanlış saatlerde ilk on bölgenin payı | 36.59% |

Son tahmin dahil her kullanılabilir tahmin en fazla bir saat alarm durumu
katkısı yapar. Ardışık alarmlar yalnızca tam bir saat aralıkla birleştirilir.
Sessiz tahminler ve boşluklar dönemleri böler. Bu saatlik durum tanımı,
ölçülmüş kesintisiz kullanıcı uyarısı değildir; 24 saat tahmin ufku 24 saat
alarm maruziyeti sayılmaz. Bölge-saat bölgeler üzerinden toplanır; tek
gözlemcinin duvar saati değildir. Sınırda kesilen dönemler boşlukta sürebilir.

Tamamen negatif dönem yalnızca hedef-sıfır pencereler içerir. Karma dönemlerde
doğru ve yanlış saatler birlikte olabilir. Dolayısıyla 280 negatif dönem,
4,264 yanlış saatin yerine geçmez. Eksik olay eşlemesi nedeniyle tamamen
negatif etiketler fiziksel patlama yokluğunu kanıtlamaz.

| HARP | Yanlış saat / izlenen saat | En uzun negatif dönem |
| --- | ---: | ---: |
| 4851 | 181 / 208 | 113 saat |
| 4321 | 169 / 203 | 87 saat |
| 4315 | 167 / 190 | 116 saat |
| 4225 | 153 / 214 | 127 saat |

HARP 4225'in 127 saatlik negatif dönemi, önceki eşlenmiş M1.0 zirvesinden
yaklaşık 23.58 saat sonra başlar. Bu betimseldir; önceki patlama bu gelecek
tahmin pencerelerinde değildir. Zaman çizgisi olasılığın düşük çalışma
eşiğinin üzerinde kaldığını gösterir.

## Olay kimliği, zaman ve kapsam

HARP ve NOAA kimlikleri eşitlenmedi. Doğrulanmış bölüm 4 arşivi 105 benzersiz
HARP/patlama ilişkisi sağladı: 44'ü dosya adı ve konum geçmişiyle, 42'si yalnız
dosya adıyla, 19'u yalnız geçmişle desteklendi. Kabul edilen hiçbir olay
birden çok HARP'a eşlenmedi. Son 19 ilişki, en güçlü patlama etiketlerinin
atladığı bilgiyi açığa çıkarır.

Model özelliklerinden çıkarılanlar dahil 51,261 pencere ilişki kanıtı için
tarandı. Model/girdiler değişmedi. Katalog kimliği veya büyüklük uyuşmazlığı
kanıtı reddeder; geçmiş zirveleri anotasyona altı dakika içinde olmalıdır.

45 zaman ilişkisi reddedildi, bir ilişki doğrulanmadı. Anotasyonlar zirveden
7–11 dakika önceydi. Makale en yakın 12 dakikalık örneği anlatıyor; bu kayıtlar
kurala uymuyor. İhtiyatlı filtre korunuyor; farklar yuvarlanmak yerine
incelemeye aktarılıyor. Geçmişi reddedilen olay dosya adıyla yine desteklenebilir.

Tahmin dönemi içindeki tüm-Güneş M/X kataloğu:

| Durum | Benzersiz olaylar |
| --- | ---: |
| Tekil eşlenmiş, en az bir uygun tahmini olan | 87 |
| Eşlenmiş ama uygun tahmin kapsamı yok | 1 |
| Bu arşivde kabul edilmiş eşleme yok | 62 |

Eşlenmeyen 62 olay otomatik bölgesel kaçırma değildir: başka bölgelerde veya
kullanılabilir kapsam dışında olabilir. Bu ilişkiler ve kapsanan alt küme
eksiksiz Güneş veya HARP-olay kapsamı oluşturmaz.

Kapsanan 87 olayın 86'sında uygun 24 saat tahmininde en az bir alarm var:
**%98.85 koşullu olay recall'u**. 86'sında da katalog başlangıcından kesin
olarak önce alarm var. Değerlendirilen 14 olay yalnız geçmiş ilişkilerinden
geliyor. Önceki 24 saatin tamamı saatlik tahmin durumlarıyla kapsanan alt
kümedeki 47 olayın tamamı yakalandı.

Kaçırılan olay M2.2, katalog 9053, HARP 4678; zirvesi 2014-10-14 21:21 UTC.
Önceki 24 saatin yalnızca 10.15 saati kapsanıyor. Kapsam eksikliği model
kaçırmalarından ayrı raporlanır.

Yakalananlarda zirveye medyan ön süre 23.35, başlangıca 22.99 saat.
Bunlar 24 saat ufku içindeki en erken uygun tahminlerdir; yeni alarm dönemi
başlangıcı olmak zorunda değildir. Sürekli alarmlar tek tek olayları kesin
öngörmeden yaklaşık 24 saat ön süre üretebilir. Yüksek koşullu recall düşük
alarm yükünün kanıtı değildir.

## Etiket uyuşmazlığı

8864, zirvesi 2014-09-03 13:54 UTC olan M2.5 olayıdır. Doğrulanmış konum
geçmişi HARP 4502'ye bağlar. 2014-09-02 21:24–2014-09-03 06:24 UTC arasında
verilen on hedef-sıfır tahmin, zirveyi gelecek aralığında içerir.

İki kaynak korunur: yanlış alarm saatleri özgün referans etiketlerini,
olay eşlemesi kabul edilen katalog ilişkilerini kullanır. Referans tanımları
tam tutarlı değildir. Etiket onarımı veya yeniden eğitim yapılmadı.
On çelişki dışa aktarıldı ve dashboard uyarısında gösteriliyor. Tam olay
benchmark'ı iddiasından veya olayların model seçiminde kullanımından önce
kaynak uyuşmazlığı çözülmelidir.

## Ölçüm örüntüleri

| Pencere sonucu | Son USFLUX medyanı | Son R_VALUE medyanı | Son TOTUSJH medyanı |
| --- | ---: | ---: | ---: |
| Doğru sessiz | 1.530 × 10²¹ | 0.000 | 97.86 |
| Yanlış alarm | 2.920 × 10²² | 4.524 | 1,929.42 |
| Yakalama | 4.813 × 10²² | 4.836 | 3,647.69 |
| Kaçırma | 2.728 × 10²² | 4.359 | 1,585.13 |

Yanlış alarm pencerelerinin manyetik özetleri genellikle doğru sessiz
pencerelerden büyük. Dört grupta da maskelenmiş ölçüm medyanı %3.33;
bu özet eksikliği tek başına açıklama olarak belirlemiyor.
Örtüşen pencere dağılımları betimseldir; bölge ve zamanla karışır,
fiziksel neden veya istatistiksel anlamlılık göstermez.

## Yeniden üretim ve arayüz

```sh
python scripts/prepare_event_mapping.py
python scripts/run_event_audit.py
python scripts/report_event_audit.py
```

Çalıştırıcı deney 2 çıktılarını gerektirir; sabit kararları, kaynak özellikleri,
eşleme kanıtını ve katalog kimliğini kontrol eder. Mevcut analiz dizinlerinin
üzerine yazmaz. Eşleme hazırlığı sağlama toplamı doğrulanmış önbelleği kullanabilir.

`artifacts/event_audit/report.html` örnek zaman çizgilerini, sayıları,
çelişkileri, değerlendirilen olayları ve protokolü içerir. CSV/Parquet çıktıları
dönemleri, bölgeleri, katalog kapsamını, olay/dönem bağlantılarını ve özetleri
korur. Ham veri, modeller ve üretilen raporlar Git dışında kalır.

Dashboard'un **Alarm & event audit** sekmesi bu geliştirme analizini ilk
deneyden ayrı gösterir. Bölgeler yanlış saat veya en uzun negatif döneme göre
sıralanabilir; manyetik değişken seçilebilir, eşlenmiş zirveler açılabilir ve
tablolar indirilebilir. Eğriler tahmin boşluklarında kesilir; eksik manyetik
değerler boşluk olarak kalır. Bölge değiştirmek sonuçları yeniden gizler.

Kaynak: [SWAN-SF özgün makalesi](https://pmc.ncbi.nlm.nih.gov/articles/PMC7351763/),
patlama bütünleştirme ve dilimleme bölümleri. Makale HARP/NOAA ayrımını ve
pencerenin en büyük patlama etiketini gerekçelendirir; bu denetimin ölçülmüş
sonuçları ve kanıtları gerçek arşiv/katalogdan gelir.
