# Alarm kalıcılığı protokolü: sonuçlardan önce dondurulmuştur

## Karar ve kapsam

Alarm dönemi incelemesi, yanlış alarmların çok sayıda kısa ve tamamen negatif dönem olarak
geldiğini ve medyan sürenin 2 ile 7 saat olduğunu gösterdi ([inceleme](alarm-episodes-20261107.tr.md)).
Patlama geçmişi yönü, tarihsel olay raporlarının olaylardan günler sonra oluşturulması nedeniyle
engelli kalıyor ([zamanlama incelemesi](history-publication-probe-20261107.tr.md)). Bu protokol
bu yüzden ucuz ve eğitim gerektirmeyen tek bir hipotezi dondurur: alarm vermeden önce ardışık
birkaç eşik aşımı istemek. Bu belge ve `config/alarm-persistence-v1.json`, herhangi bir kalıcılık
sonucu hesaplanmadan yazıldı. Hiçbir şey çalıştırılmadı. Eğitim, eşik değişikliği, yeniden
etiketleme veya ayrılmış 2024–2025 testine erişim bu protokolün parçası değildir.

Açıklama: iki aday değer, betimleyici medyan tamamen negatif dönem sürelerini gördükten sonra
seçildi. Hiçbir kalıcılık sonucuna göre ayarlanmadı.

## Hipotez

k ardışık eşik aşımı istemek kısa ve tamamen negatif dönemleri kaldırır; pozitif serileri
kaybetmeden dönem ve pencere precision'ını yükseltir. Bu kanıtlanmamıştır. Kural recall'ı
düşürebilir ve her alarmı en az k eksi bir saat geciktirir. Alarm bastırma model iyileştirmesi
değildir ve olasılıkları değiştirmez.

## Kural

Bir HARP'ın t saatinde alarm, yalnızca t−k+1 ile t arasındaki pencereler tam birer saat arayla
ardışıksa ve hepsinin olasılığı değiştirilmemiş dondurulmuş yıllık eşikte veya üstündeyse verilir.
Yalnızca mevcut ve geçmiş pencereler kullanılır; kural nedenseldir. Kontrol k=1 mevcut davranıştır.
Dönem, isabetli dönem, pozitif seri ve alarmlı pozitif seri tanımları alarm dönemi incelemesindeki
gibidir. İsabetli dönem pozitif etiketli pencere içerir; bunlar örtüşen pencerelerin gruplamasıdır,
fiziksel patlama değildir.

## Adaylar, veri ve bütçe

| candidate | k | budget |
| --- | --- | --- |
| control | 1 | 0 |
| persist_3h | 3 | 1 |
| persist_6h | 6 | 1 |

Birincil kol, dondurulmuş 96 özellikli topluluk olan `baseline`'dır; `chronological` ikincil
betimleyici kol olarak raporlanır. Kanıt, tamamlanan yedi yıllık karşılaştırmanın dondurulmuş
yıllık tahminleri ve eşikleri (rapor SHA256
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`) ile alarm dönemi incelemesidir
(SHA256 `9d6b5c02d370f0b08ecc0dc3083d2df88d65a39469907077192666b143306788`). Yıllar: 2014, 2015,
2016, 2017, 2018, 2022 ve 2023. Pozitif pencereli altı yıl kapıya tabidir; 2018 yalnızca dönem ve
yanlış alarm raporlar. Sonuçları gördükten sonra başka k değeri, bekleme süresi, birleştirme veya
histerezis eklenemez. Model eğitimi: 0. Eşik değişikliği: 0.

## Raporlanan ölçüler

Yıl, kol ve aday başına: tp, fp, fn, tn, recall, precision, alarm pencereleri, dönemler, isabetli
dönemler, dönem precision'ı, tamamen negatif dönemler, pozitif seriler, alarmlı pozitif seriler,
pozitif seri recall'ı ile alarm gecikmesinin medyanı ve maksimumu. Alarm gecikmesi, alarmlı bir
pozitif serinin ilk pozitif etiketli penceresinden içindeki ilk alarm penceresine kadar geçen saattir.
Raporlanır, kapı koşulu değildir.

## Kabul kuralları

| rule | required value |
| --- | --- |
| episode precision versus control | higher |
| fp windows versus control | lower |
| alarmed positive runs versus control | not below |
| window recall drop versus control | at most 0.02 |
| positive years that must pass for the same k | 6 |

Bunlar evrensel aralıklar değil, proje karşılaştırma kurallarıdır. Tüm yıllar geçişi, aynı k için
her pozitif yılı gerektirir. AP, Brier ve log loss bu kuralla değişmez ve iyileşme olarak
iddia edilmez. 2017 ve 2023 gibi bazı yıllar, kontrol zaten pozitif seri kaçırdığı için başarısız
olabilir.

## Belirsizlik

Yıllık ve birleşik sayımlar raporlanır. Kontrole göre dönem precision'ı ve fp pencere farkları,
tohum 24 ile 1000 eşleştirilmiş tam-HARP bootstrap çekilişi kullanır. Aralıklar dondurulmuş
tahmin ve eşiklere koşulludur, yeniden eğitim belirsizliğini içermez ve çoklu karşılaştırma için
düzeltilmemiştir.

## Yorum sınırları

Sonuç, daha önce incelenmiş yıllarda uyarlamalı geliştirme kanıtıdır, bağımsız test değildir.
Geçiş yalnızca ayrı bir ileriye dönük protokolü gerekçelendirir; uyarıları veya modelleri
otomatik değiştirmez. Başarısızlık da bilgi verir: kısa dönemlerin alarm yükünün kaldırılabilir bir
parçası olmadığını gösterir. Geciken alarmlar, bu pencere düzeyindeki inceleme tarafından
değerlendirilemeyen uyarı süresine mal olabilir.

## Sonraki adım ve yeniden üretim

Bu protokol gözden geçirildikten sonra testleriyle birlikte `scripts/audit_alarm_persistence.py`
yazılır, yeni bir çıktı dizinine bir kez çalıştırılır ve sonuç iki dilde raporlanır. Dondurulmuş
config sonradan düzenlenmez; revizyon yeni config sürümü gerektirir. Dondurulmuş dosya şöyle
incelenebilir:

```sh
cat config/alarm-persistence-v1.json
```
