# Eşik ve kalıcılık protokolü: sonuçlardan önce dondurulmuştur

## Karar ve kapsam

[Kalıcılık sonuçları](alarm-persistence-results-20261107.tr.md), 3 veya 6 ardışık aşım istemenin yanlış alarmı
azalttığını, ama dondurulmuş 0,02 sınırından fazla pencere recall'ı kaybettirdiğini gösterdi. Kalıcılığı, alarm
eşiğini yükseltmekle karşılaştırmadı; eşik yükseltmek de recall'ı daha az yanlış alarma değiş tokuş eder. Bu
protokol, aynı dondurulmuş yıllık tahmin ve eşikler üzerinde bu karşılaştırmayı dondurur (kaynak rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`; kalıcılık raporu SHA256
`242b78592fb9c64d1a20809be5179874783bde54a7bc4731fc960fa43841f175`). Herhangi bir eşik sonucu hesaplanmadan
yazıldı. Hiçbir şey çalıştırılmadı. Eğitim, yeniden etiketleme veya ayrılmış 2024–2025 testine erişim
kapsamında değildir.

Açıklama: kalıcılık sonuçları zaten biliniyordu. Üç çarpan bunları gördükten sonra, kalıcılıkla
karşılaştırılabilir veya daha büyük yanlış alarm azalmalarını kapsayacak şekilde seçildi. Hiçbir eşik
sonucuna göre ayarlanmadılar.

## Soru

Kalıcılık, eşiği yükseltmekten daha iyi bir precision ve recall ödünleşimi midir? İki okuma gerekir: etiket
kullanmayan sabit bir eşik kuralının ne sağladığı ve kalıcılıkla aynı recall'da mümkün en iyi eşiğin ne
sağlayacağı.

## Uygulanabilir adaylar

Olasılık, değiştirilmemiş dondurulmuş yıllık eşiğin m katına eşit veya üstündeyse alarm verilir; üst sınır 1'dir.
m'yi hiçbir etiket veya sonuç belirlemez. Çarpanlar 1,25, 1,5 ve 2,0'dır; başka değer yasaktır. Her biri,
kalıcılık protokolünün yıllık koşullarıyla değiştirilmemiş kontrole karşı değerlendirilir: daha yüksek dönem
precision'ı, daha az yanlış alarm penceresi, alarmlı pozitif seri sayısında azalma olmaması ve en fazla 0,02
pencere recall düşüşü. Bir çarpan yalnızca altı pozitif yılın hepsinde sağlarsa geçer. Kontrole göre farklar,
eşleştirilmiş tam-HARP bootstrap aralıklarıyla verilir (1000 çekiliş, tohum 24); aralıklar dondurulmuş tahmin ve
eşiklere koşulludur ve çoklu karşılaştırma düzeltmesi içermez.

## Oracle referanslar

Bu bölümdeki eşikler değerlendirme etiketleri kullanılarak seçilir. Tanısal referanslardır; uygulanabilir kural
değildir, belirsizlik aralığı yoktur ve benimsenemez. Izgara, yılın değerlendirme pencerelerinin farklı
olasılıklarıdır; olasılık t'ye eşit veya üstündeyse alarm verilir.

- Eşleşen recall: her kalıcılık adayı ve yıl için, pencere recall'ı en az kalıcılık recall'ı kadar olan en büyük
  t. Ulaşılan recall raporlanır ve eşitlikte eşik lehine karar verilir.
- Tolerans referansı: pencere recall'ı en az kontrol recall'ı eksi 0,02 olan en büyük t. Dondurulmuş recall
  toleransı içine ne kadar yanlış alarm azalmasının sığdığını gösterir.

Her referans için t, recall, precision, yanlış alarm pencereleri, dönemler, isabetli dönemler, dönem
precision'ı ve alarmlı pozitif seriler raporlanır.

## Adaylar ve bütçe

| candidate | rule | budget |
| --- | --- | --- |
| mult_1.25 | threshold times 1.25 | 1 |
| mult_1.5 | threshold times 1.5 | 1 |
| mult_2.0 | threshold times 2.0 | 1 |
| matched_3h | oracle threshold matching persist_3h recall | 0 |
| matched_6h | oracle threshold matching persist_6h recall | 0 |
| tolerance_ref | oracle threshold at control recall minus 0.02 | 0 |

Birincil kol `baseline`'dır; `chronological` ikincil betimleyici koldur. Yıllar: 2014, 2015, 2016, 2017, 2018,
2022 ve 2023. Pozitif pencereli altı yıl kapıya tabidir. 2018'de recall tabanlı kurallar tanımsız olduğu için
yalnızca uygulanabilir adaylar için yanlış alarm pencereleri ve dönemler raporlanır. Model eğitimi: 0.

## Karar kuralları

Aynı k için kalıcılık, yalnızca altı pozitif yılın hepsinde eşleşen recall'daki eşikten hem daha az yanlış alarm
penceresi hem de daha az dönem üretirse değer katar. Altı pozitif yılın hepsinde eşiğin yanlış alarm
pencereleri kalıcılıktan az veya eşitse eşik en az o kadar iyidir. Geri kalan her durum karışıktır ve tek bir karar
verilmeden yıllık kazanç ve kayıplarla raporlanır. Hiçbir karar uyarıları, eşikleri veya modelleri değiştirmez.

## Yorum sınırları

Sonuç, daha önce incelenmiş yıllarda uyarlamalı geliştirme kanıtıdır, bağımsız test değildir. Sayılar örtüşen
tahmin pencereleri ve bunların gruplamasıdır; fiziksel patlama değildir. Oracle referanslar değerlendirme
etiketlerini kullandığı için eşik lehinedir; orada bir eşik üstünlüğü, eşiğin önceden seçilebileceğini
göstermez. Uygulanabilir bir çarpanın geçmesi yalnızca ayrı bir ileriye dönük protokolü gerekçelendirir.
AP, Brier ve log loss iki kural ailesiyle de değişmez.

## Sonraki adım ve yeniden üretim

Gözden geçirmeden sonra testleriyle birlikte `scripts/audit_threshold_tradeoff.py` yazılır, yeni bir çıktı
dizinine bir kez çalıştırılır ve sonuç iki dilde raporlanır. Dondurulmuş config sonradan düzenlenmez; revizyon
yeni sürüm gerektirir. Dondurulmuş dosya şöyle incelenebilir:

```sh
cat config/threshold-tradeoff-v1.json
```
