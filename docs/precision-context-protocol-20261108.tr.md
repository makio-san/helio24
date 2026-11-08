# Kesinlik bağlamı protokolü: ikinci aşama olarak nedensel bölgesel gidişat, hiçbir sonuçtan önce dondurulmuştur

## Karar ve kapsam

Donmuş baseline'ın pencere kesinliği recall hedefinde 0,10 civarında kalıyor ve proje hedefi recall 0,95'te
0,30. Bu protokol, donmuş baseline topluluğuna küçük bir ikinci aşama olarak nedensel, katalog gerektirmeyen
bölgesel bağlam ekleyen tek bir sınırlı deneyi dondurur. Hiçbir aday sonucu hesaplanmadan önce yazılmıştır.
Hiçbir şey çalıştırılmadı. Hiçbir birinci aşama modeli yeniden eğitilmez, hiçbir etiket değişmez ve ayrılmış
2024–2025 testi kapalı kalır. Tek adımın hedefe ulaşması beklenmez; protokol mesafeyi ölçer.

Kanıt: donmuş yıllık tahminler ve eşikler (kaynak rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), baseline walk-forward raporu (SHA256
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`) ve donmuş shard raporu (SHA256
`62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82`); hepsi
[v2 baseline kapısı](threshold-selection-v2-results-20261108.tr.md) ile doğrulanmıştır.

## Bu deney neden

Donmuş baseline tahminlerinde yanlış-alarm pencerelerinin çoğu, o yıl hiç pozitif penceresi olmayan HARP'lara
düşer ve uzun süre alarmda kalan birkaç bölge bunların büyük bir payını taşır.

| yıl | YA pencereleri | sıfır-pozitif HARP'lardaki YA | pay | en kötü on HARP'taki YA |
| --- | --- | --- | --- | --- |
| 2014 | 13886 | 7646 | 55% | 2729 |
| 2015 | 11453 | 7607 | 66% | 2696 |
| 2016 | 2289 | 1642 | 72% | 1478 |
| 2017 | 1287 | 998 | 78% | 1198 |
| 2022 | 10072 | 8510 | 84% | 2430 |
| 2023 | 5992 | 4576 | 76% | 1836 |

[Araştırma yönü](research-next-20261106.tr.md), aynı hipotez için nedensel patlama geçmişi bağlamını seçti:
sürekli yüksek ölçümler, patlamaya yaklaşan bölgelerden ayırt edilebilir. Ancak durma kuralı, yayın zamanı
kaynağı kanıtlanana kadar eğitimi yasaklar ve [yayın sondası](history-publication-probe-20261107.tr.md)
`availability_verified=false` bıraktı. Bu protokol hipotezi dış katalog gerektirmeyen bağlamla sınar: bölgenin
kendi geçmiş birinci aşama olasılıkları ve kayıttaki yaşı. Sabit alarm kalıcılığı, eşik çarpanları, önceki yıl
recall hedefleri, ham geçmiş özetleri, ağırlıklandırma, havuzlama, spline'lar, Extra Trees ve histogram
boosting daha önce sınandı ve geçmedi.

## Birinci aşama ve bağlam özellikleri

Birinci aşama, saklanan donmuş yıllık topluluktur; yalnızca çıkarım, sıfır eğitim. Kalibrasyon yılı ve
değerlendirme yılı olasılıkları birinci aşama için örneklem dışıdır. Bağlam özellikleri yalnızca aynı HARP'ın,
aynı yıllık kat rolünde, tahmin zamanı mevcut olandan kesinlikle önce olan pencerelerini ve mevcut pencereyi
kullanır. Etiket, olay, gelecek pencere veya başka HARP kullanılmaz.

| özellik | tanım |
| --- | --- |
| logit_p | mevcut birinci aşama olasılığının logit'i |
| age_log_hours | log(1 + bu HARP'ın kayıttaki ilk penceresinden bu yana geçen saat) |
| past24_max_logit, past24_mean_logit | (t−24s, t) aralığındaki pencereler üzerinde |
| past72_max_logit, past72_mean_logit | (t−72s, t) aralığındaki pencereler üzerinde |
| past72_hours_above_control | (t−72s, t) aralığında o yılın donmuş kontrol eşiğinde veya üzerinde olan pencereler |
| slope6 | logit_p eksi (t−6s, t) aralığındaki ortalama logit |
| coverage24, coverage72 | her geriye bakışta bulunan geçmiş pencere sayısı |
| missing_fraction | mevcut pencerenin |

Geçmiş penceresi olmayan bir geriye bakış, coverage 0 verir ve geçmiş istatistikleri mevcut logit'e eşit olur.
Coverage özellikleri, geçmişin yokluğu bilgisini taşır; geçmiş asla sakin varsayılmaz.

## Adaylar ve ikinci aşama

| aday | tanım | bütçe |
| --- | --- | --- |
| control | donmuş önceki yıl eşiğiyle birinci aşama olasılığı; yıllık karşılaştırmanın baseline koluyla aynı | 0 |
| recal | yalnızca logit_p ve missing_fraction üzerinde ikinci aşama | 1 |
| context | tüm bağlam özellikleri üzerinde ikinci aşama | 1 |

İkinci aşama, StandardScaler ve ardından C 1.0, lbfgs, 2000 yineleme, sınıf ağırlığı yok ve seed 24 ile
LogisticRegression'dır; arama yoktur. Yalnızca yıllık katın kalibrasyon yılında eğitilir; eğitim yılları birinci
aşama için örneklem içidir ve kullanılmaz. Kalibrasyon yılında beş HARP-grup katı (kat = HARP kimliğinin sıralı
kalibrasyon HARP'ları arasındaki sırasının 5'e bölümünden kalan), her kalibrasyon penceresine çapraz uyarlanmış
bir ikinci aşama olasılığı verir. Eşik, bu çapraz uyarlanmış olasılıklar üzerinde `recall_threshold` ile 0,95
hedefinde seçilir. Tüm kalibrasyon yılında yeniden eğitilen ikinci aşama modeli değerlendirme yılına
uygulanır. Eğitimler: 7 yıl × 2 aday × 6 = 84 küçük lojistik eğitim. Her yıl için tüm adayların eşikleri,
herhangi bir değerlendirme etiketi okunmadan önce diske yazılır ve hash'lenir.

`recal` adayı tek bir farkı görünür kılmak için vardır: ikinci aşama kalibrasyon yılı etiketlerini eğitmek için
kullanır, kontrol ise yalnızca eşik seçmek için kullanır. `context`'in `recal` ile paylaşmadığı bir geçiş
gidişat bilgisine, ikisinin paylaştığı bir geçiş ise bağlama değil yeniden eğitmeye atfedilir.

## Kabul kuralları

Bir aday, kontrole karşı dört koşulun hepsini sağlarsa o yıl için sayılır; tanımlar kalıcılık protokolündekiyle
aynıdır: daha yüksek dönem kesinliği, daha az yanlış-alarm penceresi, alarm verilen pozitif serilerde azalma
olmaması ve en fazla 0,02 pencere recall düşüşü. Tüm yıllar için geçiş, aynı adayın altı pozitif yılın hepsinde
geçmesini gerektirir. 2018'de pozitif pencere yoktur; yalnızca eşikleri, yanlış-alarm pencerelerini ve dönemleri
raporlar. Her yıl için rapor, pencere kesinliğini ve ulaşılan doğru pozitiflerde 0,30 kesinlik verecek
yanlış-alarm penceresi sayısını verir. Bunlar evrensel aralıklar değil, proje karşılaştırma kurallarıdır. Geçiş
yalnızca ayrı bir ileriye dönük protokolü haklı çıkarır ve uyarıları, eşikleri veya modelleri asla değiştirmez.

## Raporlanan metrikler ve belirsizlik

Yıl ve aday başına: tp, fp, fn, tn, kesinlik, recall, alarm pencereleri, dönemler, dönem kesinliği, pozitif
seriler, alarm verilen pozitif seriler, ortalama kesinlik, Brier ve log loss. Kontrole karşı dönem kesinliği ve
yanlış-alarm penceresi farkları için eşleştirilmiş tam-HARP bootstrap aralıkları (1000 çekim, seed 24), donmuş
eşiklere koşulludur. İkinci aşama eğitiminin veya eşik seçiminin belirsizliğini içermez ve çoklu karşılaştırma
için düzeltilmemiştir.

## Açıklama ve sınırlar

Bağlam özellikleri, aynı yılların donmuş baseline tahminlerinde yanlış alarmların nerede yoğunlaştığı
görüldükten sonra seçildi; bu uyarlanabilirdir. Hiçbir ikinci aşama sonucuna göre seçilmediler; yapılandırma
dondurulduğunda hiçbiri hesaplanmamıştı. Sonuç, zaten incelenmiş yıllar üzerinde uyarlanabilir geliştirme
kanıtıdır, bağımsız bir test değildir. Sayılar örtüşen tahmin pencereleri ve bunların gruplamalarıdır, fiziksel
patlamalar değildir. Bazı katlarda kalibrasyon yılında az pozitif pencere vardır (2017 için 181), bu yüzden
ikinci aşama orada gürültülü olabilir.

## Sonraki adım ve yeniden üretim

İncelemeden sonra `scripts/audit_precision_context.py` testleriyle eklenir, yeni bir çıktı dizinine bir kez
çalıştırılır ve sonuç iki dilde raporlanır. Donmuş yapılandırma sonradan düzenlenmez; bir revizyon yeni sürüm
gerektirir. Donmuş dosya şununla incelenebilir:

```sh
cat config/precision-context-v1.json
```
