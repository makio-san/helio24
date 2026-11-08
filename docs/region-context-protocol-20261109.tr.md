# Bölgesel bağlam protokolü: yıllık yeniden eğitimle yayımlanmış SRS özellikleri, hiçbir sonuçtan önce dondurulmuştur

## Karar ve kapsam

[Kaynak denetimi](region-context-sources-20261109.tr.md), NOAA Güneş Bölge Özeti'nin (SRS) kendi yayın
zamanını taşıdığını ve tahmin anında pozitif geliştirme pencerelerinin %90,8'ini kapsadığını gösterdi. Bu
protokol tek bir sınırlı deneyi dondurur: sabit 96 manyetik özet artı nedensel SRS bağlamı, donmuş baseline ile
aynı yıllık katlarda, değiştirilmemiş walk-forward reçeteleriyle yeniden eğitilir. Hiçbir aday sonucu
hesaplanmadan önce yazılmıştır. Hiçbir şey çalıştırılmadı. Hiçbir etiket değişmez ve ayrılmış 2024–2025 testi
kapalı kalır. Tek adımın recall 0,95'te 0,30 kesinlik proje hedefine ulaşması beklenmez; mesafe raporlanır.

Kanıt: donmuş yıllık tahminler (kaynak rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), baseline walk-forward raporu (SHA256
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`), donmuş shard raporu (SHA256
`62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82`) ve manifestleriyle edinilen SRS ve
HARP–NOAA kaynakları.

## Bu deney neden

Donmuş baseline'da yanlış-alarm pencerelerinin %80 ile %97'si yayımlanmış SRS'te bulunan numaralı bölgelere
düşer; yani bölgenin varlığı onları ayırmaz, içeriği ayırabilir. Manyetik sınıf (Beta-Gamma, Beta-Delta,
Beta-Gamma-Delta), McIntosh sınıfı, alan, leke sayısı ve bölge yaşı literatürde yerleşik patlama göstergeleridir
ve 96 SHARP özeti tarafından taşınmaz. Bu kayıtta o özetlerin üzerine bilgi ekleyip eklemedikleri sorudur.

## Erişilebilirlik kuralı

t tahmin zamanındaki bir pencere, yayın zamanı t eksi 30 dakika veya öncesinde olan en son SRS'yi ve yalnızca
NOAA numarası HARP'ın tahmin tarihindeki `NOAA_ARS` değerinde bulunan SRS satırlarını kullanır. Böyle satırı
olmayan bir HARP'ta `srs_available` 0'dır ve diğer tüm bağlam değerleri eksiktir. Eksik değerler, eksiklik
göstergesiyle mevcut medyan doldurucudan geçer; böylece model bağlamın yokluğunu görür. Yokluk asla sakin olarak
kodlanmaz.

## Bağlam özellikleri

| özellik | tanım |
| --- | --- |
| srs_available | en az bir SRS satırı eşleştiyse 1, yoksa 0 |
| hours_since_issue | t eksi kullanılan SRS'nin yayın zamanı, saat |
| n_regions | eşleşen SRS satırı sayısı |
| mag_rank | satırlar üzerinde en büyük: Alpha 0, Beta 1, Gamma 2, Beta-Gamma 2, Beta-Delta 3, Beta-Gamma-Delta 4 |
| has_delta | eşleşen herhangi bir manyetik sınıf Delta içeriyorsa 1 |
| has_gamma | eşleşen herhangi bir manyetik sınıf Gamma içeriyorsa 1 |
| zurich_rank | satırlar üzerinde en büyük değiştirilmiş Zürih harfi: A 0, B 1, H 1, C 2, D 3, E 4, F 5 |
| penumbra_rank | satırlar üzerinde en büyük ikinci McIntosh harfi: x 0, r 1, s 2, a 3, h 4, k 5 |
| compact_rank | satırlar üzerinde en büyük üçüncü McIntosh harfi: x 0, o 1, i 2, c 3 |
| area_log | log(1 + eşleşen alanların toplamı) |
| spots_log | log(1 + eşleşen leke sayılarının toplamı) |
| extent_max | eşleşen en büyük boylam genişliği, derece |
| srs_history_days | satırlar üzerinde en büyük: kullanılandan kesinlikle önce yayımlanmış ve aynı NOAA numarasını listeleyen SRS ürünü sayısı |

## Adaylar ve bütçe

| aday | tanım | eğitim |
| --- | --- | --- |
| control | donmuş baseline topluluk tahminleri ve önceki yıl eşikleri, aynı değerlendirme anahtarları | 0 |
| flag | yalnızca 96 özet artı srs_available ve hours_since_issue üzerinde yeniden eğitim | yılda 2 |
| context | 96 özet artı 13 bağlam özelliğinin tümü üzerinde yeniden eğitim | yılda 2 |

Eğitim, donmuş geliştirme shard'larının yıllık katlarını kullanır; her katın denetimi donmuş baseline kat
denetimine eşit olmalıdır. Modeller, hiperparametreler, doldurucu, ölçekleyici, kalibrasyon yılındaki sigmoid
kalibrasyon ve 0,45/0,55 topluluk ağırlığı `config/walk-forward-v1.json` dosyasındakilerdir, değiştirilmemiştir.
Eşikler kalibrasyon yılı olasılıkları üzerinde pencere recall 0,95'te seçilir ve herhangi bir değerlendirme
etiketi okunmadan önce diske yazılıp hash'lenir. Bütçe: 2 aday reçete, 7 yıl, 28 bileşen eğitimi, hiperparametre
araması yok, sonuçlardan sonra eklenen özellik kümesi yok. `flag` adayı, yeniden eğitim veya erişilebilirlik tek
başına kazanç üretirse bunun içeriğe atfedilememesi için vardır.

## Kabul kuralları

Bir aday, kontrole karşı dört koşulun hepsini sağlarsa o yıl için sayılır; tanımlar kalıcılık protokolündekiyle
aynıdır: daha yüksek dönem kesinliği, daha az yanlış-alarm penceresi, alarm verilen pozitif serilerde azalma
olmaması ve en fazla 0,02 pencere recall düşüşü. Tüm yıllar için geçiş, aynı adayın altı pozitif yılın hepsinde
geçmesini gerektirir. `context`'in `flag` ile paylaşmadığı bir geçiş SRS içeriğine atfedilir. 2018'de pozitif
pencere yoktur; yalnızca eşikleri, yanlış-alarm pencerelerini ve dönemleri raporlar. Rapor ayrıca yıl ve aday
başına recall 0,95'e ulaşılıp ulaşılmadığını, AP, Brier, log loss değerlerini ve ulaşılan doğru pozitiflerde 0,30
kesinlik verecek en büyük sayının üzerindeki yanlış-alarm penceresi sayısını verir. Geçiş yalnızca ayrı bir
ileriye dönük protokolü haklı çıkarır ve uyarıları, eşikleri veya modelleri asla değiştirmez.

## Belirsizlik

Kontrole karşı dönem kesinliği ve yanlış-alarm penceresi farkları için eşleştirilmiş tam-HARP bootstrap
aralıkları (1000 çekim, seed 24), donmuş eşiklere koşulludur. Yeniden eğitim ve eşik seçimi belirsizliğini
dışarıda bırakır ve çoklu karşılaştırma için düzeltilmemiştir.

## Açıklama ve sınırlar

Özellik listesi ve sıralı kodlamalar, SRS dağarcığından ve aynı yılların donmuş baseline'ında yanlış alarmların
nerede yoğunlaştığından sabitlendi; bu uyarlanabilirdir. Yapılandırma dondurulduğunda hiçbir aday sonucu
hesaplanmamıştı. Sonuç, zaten incelenmiş yıllar üzerinde uyarlanabilir geliştirme kanıtıdır, bağımsız bir test
değildir. Sayılar örtüşen tahmin pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir. SRS yayın
zamanı yayımlanmayı kanıtlar, alınmayı değil; 30 dakikalık pay proje kuralıdır.

## Sonraki adım ve yeniden üretim

İncelemeden sonra `scripts/audit_region_context_features.py` testleriyle eklenir, yeni bir çıktı dizinine bir
kez çalıştırılır ve sonuç iki dilde raporlanır. Donmuş yapılandırma sonradan düzenlenmez; bir revizyon yeni sürüm
gerektirir. Donmuş dosya şununla incelenebilir:

```sh
cat config/region-context-v1.json
```
