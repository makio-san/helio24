# Eşik seçimi protokolü v2: baseline kolu, hiçbir sonuçtan önce dondurulmuştur

## Karar ve kapsam

[Eşik seçimi sonuçları](threshold-selection-results-20261108.tr.md), 20 donmuş geliştirme özellik shard'ının
tamamı eksik olduğu için baseline kolunu değerlendiremedi. Shard'lar sonradan doğrulanmış resmi arşivlerden
yeniden üretildi ve 20'sinin hepsi donmuş SHA256 değerleriyle eşleşti. Bu protokol yalnızca baseline kolu için
yeni bir sürüm ekler. Sürüm 1 donmuş kalır ve raporlanan sonuçları değişmez. Bu dosya, hiçbir baseline
seçim kuralı sonucu hesaplanmadan önce yazılmıştır. Hiçbir şey çalıştırılmadı. Eğitim, yeniden kalibrasyon,
yeniden etiketleme veya ayrılmış 2024–2025 testine erişim bunun parçası değildir.

Kanıt: donmuş yıllık tahminler ve eşikler (kaynak rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), sürüm 1 sonuç raporu (SHA256
`dae49d81c516a8a3bc512ccf5ef10081cc252fa162b8d0274fba97e4ff54a6b1`), baseline walk-forward raporu (SHA256
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`), donmuş shard raporu (SHA256
`62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82`) ve yeniden üretilen shard raporu
(SHA256 `36e8484a1496f6f1d7e117143766bfa9a15c306f4ac3984be4de321d2b5f7086`).

## Soru

Shard'lar geri yüklenip doğrulandığında baseline kolu uygulanabilirlik kapısını geçiyor mu? Geçiyorsa, yalnızca
önceki yılın kalibrasyon pencerelerinden, sürüm 1'de sabitlenen kurallarla seçilen bir eşik, donmuş 0,02 recall
toleransını aşmadan, 0,95'teki mevcut pencere-recall kuralından daha iyi bir kesinlik ve recall dengesine
ulaşabilir mi?

## Kol tanımı

Baseline kolu, özgün 96 özet özellikli topluluk modelidir. Walk-forward çıktısında her yıl `ensemble` olarak
saklanır: kalibre edilmiş lojistik ve XGBoost olasılıklarının saklanan topluluk ağırlığıyla birleşimi.
Walk-forward'daki `baseline` adayı değildir; o, eğitim prevalansı sabitidir. chronological ve
shuffled_interior kolları yeniden hesaplanmaz. Sürüm 1 sonuçları zaten görülmüştür ve raporlandığı gibi kalır.

## Veri kuralı

Her kural yalnızca değerlendirme yılından önceki yılın kalibrasyon pencerelerini, yani özgün yıllık katın
kalibrasyon rolünü, ve etiketlerini görür. Daha önceki yıllar aynı modellerin eğitim verisiydi ve örneklem
içidir, bu yüzden kullanılmaz. Her kuralın eşiği diske yazılıp hash'lenene kadar değerlendirme pencereleri ve
etiketleri okunmaz. Hiçbir seçim kuralı değerlendirme etiketlerini veya sonuçlarını kullanmaz.

## Kurallar ve bütçe

| kural | temel | hedef | bütçe |
| --- | --- | --- | --- |
| control_w95 | pencere recall | 0.95 | 0 |
| w93 | pencere recall | 0.93 | 1 |
| w90 | pencere recall | 0.90 | 1 |
| run95 | pozitif-seri recall | 0.95 | 1 |
| run90 | pozitif-seri recall | 0.90 | 1 |

Kurallar, hedefler ve seçim yöntemi sürüm 1 ile aynıdır. Pencere kuralları, kalibre edilmiş kalibrasyon
olasılıkları üzerinde mevcut `recall_threshold` fonksiyonunu kullanır. Seri kuralları, pozitif-seri recall'u
hedefin üzerinde veya eşit olan ayrık kalibre edilmiş kalibrasyon olasılıkları arasından en az kalibrasyon
yanlış-alarm penceresini, eşitlikte büyük eşiği seçer. Pozitif seri, tek bir HARP'ın ardışık saatlik pozitif
etiketli pencerelerinin dizisidir ve pencerelerinden herhangi biri eşikte veya üzerindeyse alarm verilmiş sayılır.
Sonuçları gördükten sonra başka hedef, temel, çarpan, kalıcılık veya birleşik kural eklenemez. Model eğitimi: 0.

## Uygulanabilirlik kapısı

Kapı dört adımdır ve herhangi bir seçim kuralı değerlendirilmeden önce hesaplanıp diske yazılır.

| adım | kontrol |
| --- | --- |
| G1 | Yeniden üretilen her shard'ın hash'i donmuş SHA256 değerine eşittir. 20'sinin hepsi gereklidir. |
| G2 | Değerlendirilen her yılın saklanan `models.joblib` dosyası, donmuş walk-forward raporundaki SHA256 ile eşleşir. |
| G3 | Çıkarımla yeniden hesaplanan kalibrasyon olasılıkları, `control_w95` altında her yılda saklanan baseline eşiğine eşit bir eşik verir (bağıl tolerans 1e-12). |
| G4 | Etiketsiz kimlik kontrolü: yeniden hesaplanan değerlendirme olasılıkları, (harp, forecast_time) anahtarında donmuş tahminlerin `baseline` kolonuna eşittir; anahtar kümeleri aynıdır ve en büyük mutlak fark en fazla 1e-6'dır. |

Herhangi bir yılda herhangi bir adım başarısız olursa baseline kolu, başarısız olan adım ve yılla birlikte
değerlendirilemez olarak raporlanır ve onun için hiçbir seçim kuralı değerlendirilmez. Başka bir aday modele
geri dönüş, yeniden eğitim, yeniden kalibrasyon ve kural değişikliği yoktur. Yıllar: 2014, 2015, 2016, 2017,
2018, 2022 ve 2023. Pozitif pencereli altı yıl kapıya tabidir; 2018 yalnızca eşikleri, yanlış-alarm pencerelerini
ve dönemleri raporlar.

## Kabul kuralları

Bir kural, kontrole karşı dört koşulun hepsini sağlarsa o yıl için sayılır; tanımlar kalıcılık protokolündekiyle
aynıdır: daha yüksek dönem kesinliği, daha az yanlış-alarm penceresi, alarm verilen pozitif serilerde azalma
olmaması ve en fazla 0,02 pencere recall düşüşü. Tüm yıllar için geçiş, aynı kuralın altı pozitif yılın hepsinde
geçmesini gerektirir. Bunlar evrensel aralıklar değil, proje karşılaştırma kurallarıdır. Geçiş yalnızca ayrı bir
ileriye dönük protokolü haklı çıkarır ve uyarıları, eşikleri veya modelleri asla değiştirmez. AP, Brier ve log
loss eşik seçiminden etkilenmez.

## Kararlılık raporlaması

Her kural ve yıl için rapor; kalibrasyon pozitif pencere ve pozitif seri sayısını, seçilen eşiği, kontrol eşiğine
oranını, kalibrasyon recall'unu, değerlendirme recall'unu ve aralarındaki farkı verir. Fark, kalibrasyon yılının
değerlendirme yılını ne kadar iyi öngördüğünü gösterir.

## Belirsizlik

Kontrole karşı dönem kesinliği ve yanlış-alarm penceresi farkları için eşleştirilmiş tam-HARP bootstrap
aralıkları (1000 çekim, seed 24), donmuş seçilen eşiklere koşulludur. Eşik seçiminin kendi belirsizliğini ve
yeniden eğitim belirsizliğini içermez ve çoklu karşılaştırma için düzeltilmemiştir.

## Açıklama

Kurallar, hedefler ve kabul koşulları sürüm 1 ile aynıdır ve baseline kolu için ayarlanmamıştır. Eşik takas
sonuçları görüldükten sonra seçilmişlerdir ve sürüm 1'de chronological ve shuffled_interior kolları için dört
kuralın hiçbiri geçmemiştir. Bu, bu protokolden önce bilinmektedir ve ayarlama kanıtı değil, olumsuz bir sonuç
beklemek için bir nedendir. Bu dosya dondurulduğunda hiçbir baseline seçim kuralı sonucu hesaplanmamıştı.
Yeniden üretilen shard raporu, donmuş shard raporundan tamamlanma zamanı, girdi yolları ve
`helio24/v2_archive.py` hash'i bakımından farklıdır. Shard başına hash'ler, satır sayıları, pozitif sayıları ve
HARP sayısı aynıdır.

## Yorum sınırları

Sonuç, zaten incelenmiş yıllar üzerinde uyarlanabilir geliştirme kanıtıdır, bağımsız bir test değildir. Sayılar
örtüşen tahmin pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir. Bazı kalibrasyon yıllarında
az sayıda pozitif seri vardır, bu yüzden seçilen eşikler gürültülü olabilir; bir başarısızlık, bu kayıtta önceki
yıl recall hedefinin güvenilmez bir rehber olduğunu gösterir, daha iyi bir eşiğin var olmadığını değil.

## Sonraki adım ve yeniden üretim

İncelemeden sonra baseline değerlendirmesi, testleriyle birlikte `scripts/audit_threshold_selection.py` dosyasına
(veya yeni bir betiğe) eklenir, yeni bir çıktı dizinine bir kez çalıştırılır ve sonuç iki dilde raporlanır.
Donmuş yapılandırma sonradan düzenlenmez; bir revizyon yeni sürüm gerektirir. Donmuş dosya şununla incelenebilir:

```sh
cat config/threshold-selection-v2.json
```
