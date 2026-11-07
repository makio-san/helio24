# Eşik seçimi protokolü: sonuçlardan önce dondurulmuştur

## Karar ve kapsam

[Eşik ve kalıcılık sonuçları](threshold-tradeoff-results-20261107.tr.md), bir oracle eşiğin dondurulmuş recall
toleransı içinde büyük yanlış alarm payı bıraktığını, ama dondurulmuş eşiğin sabit çarpanlarının 2016 ve
2023'te recall'ı bozduğunu gösterdi. Açık sorun, böyle bir eşiği değerlendirme etiketleri olmadan seçmektir. Bu
protokol, yalnızca önceki yılın kalibrasyon pencerelerini kullanan dört seçim kuralını dondurur. Herhangi bir
seçim kuralı sonucu hesaplanmadan yazıldı. Hiçbir şey çalıştırılmadı. Eğitim, yeniden kalibrasyon, yeniden
etiketleme veya ayrılmış 2024–2025 testine erişim kapsamında değildir.

Kanıt: dondurulmuş yıllık tahmin ve eşikler (kaynak rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`), eşik ödünleşim raporu (SHA256
`e0cf54967cf89e68865ee13843b24383f5d1fa2106ab33a574ba3cfdd351f14c`) ve baseline walk-forward raporu (SHA256
`6f11b3208dcad94ae5c5898ad02aa976b8ea3e351b01f2bf1fe2a0745597a69c`).

Açıklama: 0,93 ve 0,90 hedefleri ile seri düzeyi temel, ödünleşim sonuçları görüldükten sonra seçildi.
Hiçbir seçim kuralı sonucuna göre ayarlanmadılar.

## Soru

Yalnızca önceki yılın kalibrasyon pencerelerinden, önceden sabitlenmiş bir kuralla seçilen bir eşik, dondurulmuş
0,02 recall toleransını aşmadan, 0,95 pencere recall'lı mevcut kuraldan daha iyi bir precision ve recall
ödünleşimine ulaşabilir mi?

## Veri kuralı

Her kural yalnızca değerlendirme yılından bir önceki yılın kalibrasyon pencerelerini (özgün yıllık katın
kalibrasyon rolü) ve etiketlerini görür. Önceki yıllar aynı modellerin eğitim verisiydi ve örneklem içidir;
bu yüzden kullanılmaz. Değerlendirme pencereleri ve etiketleri, her kuralın eşikleri diske yazılıp hash'lenene
kadar okunmaz. Hiçbir seçim kuralı değerlendirme etiketlerini veya sonuçlarını kullanmaz.

## Kurallar ve bütçe

| rule | basis | target | budget |
| --- | --- | --- | --- |
| control_w95 | window recall | 0.95 | 0 |
| w93 | window recall | 0.93 | 1 |
| w90 | window recall | 0.90 | 1 |
| run95 | positive-run recall | 0.95 | 1 |
| run90 | positive-run recall | 0.90 | 1 |

Pencere kuralları, kalibre edilmiş kalibrasyon olasılıklarında mevcut `recall_threshold` fonksiyonunu kullanır.
Seri kuralları aynı ızgarayı ve eşitlik sırasını kullanır: pozitif seri recall'ı hedefin üstünde veya eşit olan
farklı kalibre kalibrasyon olasılıkları arasından en az kalibrasyon yanlış alarm penceresi, sonra daha büyük
eşik seçilir. Pozitif seri, bir HARP'ın ardışık saatlik pozitif etiketli pencerelerinden oluşur ve
pencerelerinden biri eşikte veya üstündeyse alarmlı sayılır. Kontrol, saklanan eşikleri birebir yeniden
üretmelidir. Sonuçları gördükten sonra başka hedef, temel, çarpan, kalıcılık veya birleşik kural eklenemez.
Model eğitimi: 0.

## Kollar ve uygulanabilirlik kapısı

Birincil kol `baseline`'dır. Kalibrasyon olasılıkları saklanmadığından, saklanan dondurulmuş modellerle çıkarım
yapılarak yeniden hesaplanır ve her yılda `control_w95` altında saklanan baseline eşiğini yeniden
üretmelidir. Herhangi bir yıl başarısız olursa baseline kolu dışlanır ve değerlendirilemez olarak raporlanır;
birincil kol `chronological` olur. Yeniden eğitim yasaktır. `chronological` ve `shuffled_interior` kolları
saklanan tohum başına kalibrasyon skorlarını ve kalibratörleri kullanır ve onlar da saklanan eşikleri yeniden
üretmelidir. Yıllar: 2014, 2015, 2016, 2017, 2018, 2022 ve 2023. Pozitif pencereli altı yıl kapıya tabidir;
2018 yalnızca eşik, yanlış alarm pencereleri ve dönemleri raporlar.

## Kabul kuralları

Bir kural, kontrole karşı dört koşulun tamamını sağlarsa o yılda sayılır; tanımlar kalıcılık protokolündeki
gibidir: daha yüksek dönem precision'ı, daha az yanlış alarm penceresi, alarmlı pozitif seri sayısında azalma
olmaması ve en fazla 0,02 pencere recall düşüşü. Tüm yıllar geçişi, aynı kural için altı pozitif yılın
hepsini gerektirir. Bunlar evrensel aralıklar değil, proje karşılaştırma kurallarıdır. Geçiş yalnızca ayrı bir
ileriye dönük protokolü gerekçelendirir; uyarıları, eşikleri veya modelleri değiştirmez. AP, Brier ve log loss
eşik seçiminden etkilenmez.

## Kararlılık raporlaması

Her kural ve yıl için kalibrasyon pozitif pencere ve pozitif seri sayıları, seçilen eşik, kontrol eşiğine oranı,
kalibrasyon recall'ı, değerlendirme recall'ı ve aralarındaki fark raporlanır. Fark, kalibrasyon yılının
değerlendirme yılını ne kadar iyi öngördüğünü gösterir.

## Belirsizlik

Kontrole göre dönem precision'ı ve yanlış alarm pencere farkları için eşleştirilmiş tam-HARP bootstrap
aralıkları (1000 çekiliş, tohum 24), dondurulmuş seçilen eşiklere koşulludur. Eşik seçiminin kendi
belirsizliğini ve yeniden eğitim belirsizliğini içermez ve çoklu karşılaştırma için düzeltilmemiştir.

## Yorum sınırları

Sonuç, daha önce incelenmiş yıllarda uyarlamalı geliştirme kanıtıdır, bağımsız test değildir. Sayılar örtüşen
tahmin pencereleri ve bunların gruplamasıdır; fiziksel patlama değildir. Bazı kalibrasyon yıllarında az sayıda
pozitif seri vardır; seçilen eşikler gürültülü olabilir. Başarısızlık, bu kayıtta önceki yılın recall
hedefinin güvenilmez bir kılavuz olduğunu gösterir; daha iyi bir eşiğin var olmadığını göstermez.

## Sonraki adım ve yeniden üretim

Gözden geçirmeden sonra testleriyle birlikte `scripts/audit_threshold_selection.py` yazılır, yeni bir çıktı
dizinine bir kez çalıştırılır ve sonuç iki dilde raporlanır. Dondurulmuş config sonradan düzenlenmez; revizyon
yeni sürüm gerektirir. Dondurulmuş dosya şöyle incelenebilir:

```sh
cat config/threshold-selection-v1.json
```
