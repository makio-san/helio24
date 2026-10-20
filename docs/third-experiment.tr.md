# Deney 3: zamansal özelliklerle ayırt etme sonuçları

Sabit zamansal özellik adayı, önceden kaydedilen geliştirme kuralını geçemedi.
%90 ampirik recall seviyesinde üç ilerleyen-zaman katının ikisinde yanlış
alarmları azalttı, fakat average precision üçünde de düştü.
Dashboard modeli değiştirilmedi.

## Veri ve tasarım

Beş zamansal tablo, kabul edilen 328,901 tahmin penceresi için mevcut tam veri
tablolarıyla bire bir eşleşti. 24 manyetik parametrenin her biri için son
1, 3 ve 6 saatteki eğim, değişim ve ardışık değişim standart sapmaları
eklendi: 96 özellikli kontrole 216 ek özellik. Hepsi tahmin anından önce biter.

[Protokol](third-experiment-protocol.md), tablolar veya sonuçlar üretilmeden önce
commitlendi. Geliştirme karşılaştırması şu katları kullandı:

| Kat | Eğitim bölümleri | Değerlendirme | Eğitim pencereleri | Değerlendirme pencereleri |
| --- | --- | --- | ---: | ---: |
| A | 1 | 2 | 72,613 | 86,546 |
| B | 1–2 | 3 | 159,247 | 42,452 |
| C | 1–3 | 4 | 201,485 | 51,160 |

Sınırı aşan tahmin aralıkları sırasıyla 856, 768 ve 982 eğitim penceresinin
çıkarılmasına yol açtı. Temizlenen sınırları geçen HARP kimliği yoktu.
İki model aynı kayıtları ve deney 2'nin sabit XGBoost ayarlarını kullandı;
yalnızca aday yeni zamansal özellikleri aldı.

## Geliştirme karşılaştırması

Her katın %90 ampirik recall noktasında:

| Kat | Model | Recall | Precision | Yanlış alarmlar | Kaçırmalar | Average precision | Brier |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | Kontrol | 90.01% | 11.18% | 10,021 | 140 | 0.3424 | 0.01283 |
| A | Zamansal | 90.01% | 11.95% | 9,288 | 140 | 0.3390 | 0.01300 |
| B | Kontrol | 90.03% | 23.70% | 4,128 | 142 | 0.4788 | 0.02323 |
| B | Zamansal | 90.03% | 23.86% | 4,090 | 142 | 0.4763 | 0.02314 |
| C | Kontrol | 90.04% | 19.57% | 4,311 | 116 | 0.5237 | 0.01501 |
| C | Zamansal | 90.04% | 18.90% | 4,502 | 116 | 0.5121 | 0.01529 |

Zamansal model toplam 17,880; kontrol 18,460 yanlış alarm verdi: 580 (%3.14)
azalma. A ve B'de azalma, C'de 191 artış oldu. AP üç katta da düştü.
Kural, toplam yanlış alarmın azalmasını, en az iki katta yanlış alarm
avantajını ve en az iki katta AP'nin düşmemesini gerektiriyordu.
Son koşul sağlanmadığından aday kabul edilmedi.

Bu sonuç “zaman serisi bilgisi yararsızdır” anlamına gelmez. Seçilmeden eklenen
bu sabit 216 özetin, daha basit özellik kümesini değiştirmeyi gerekçelendirecek
kadar tutarlı sıralama iyileşmesi sağlamadığını gösterir.

## Hata incelemesi

Deney 2'nin kalibre modeli bölüm 4 doğrulama kayıtlarında dondurulmuş %4.7999
eşikle incelendi. 50,631 pencerede 969 doğru alarm, 107 kaçırma, 4,264 yanlış
alarm ve 45,291 doğru sessiz tahmin üretti.

Hatalar bölgelerde yoğunlaştı: en çok hatalı on HARP, kaçırma ve yanlış
alarmların %36.01'ini içeriyordu. Yanlış pozitif oranı 2014 Q3'te en yüksek,
%12.24 idi. Küçük 2014 Q2 pozitif örnekleminde kaçırma oranı %45.61
(57 pozitiften 26 kaçırma), diğer çeyreklerde %7.05–11.96 oldu.
Paydaları farklı bu betimsel oranlar nedensel mevsim etkisi kanıtı değildir.

Her doğrulama penceresinde mevcut kalite tanımına göre %1'den fazla maskelenmiş
ölçüm vardı. Maskelenmiş oranı %5'i aşanlarda kaçırma %14.67, %1–5 grubunda
%8.12 idi. Yanlış pozitif oranları benzerdi (%8.73 ve %8.55).
Eksiklik zor bölgeler veya dönemlerle birlikte görülebilir; inceleme nedenselliği göstermez.

## Daha önce incelenen dönemde kararlılık kontrolü

Geliştirme kararı yazıldıktan sonra modeller bölüm 1–4 ile yeniden eğitildi
ve C katının eşikleriyle bölüm 5'te değerlendirildi:

| Model | Recall | Precision | Yanlış alarmlar | Kaçırmalar | Average precision | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kontrol | 89.80% | 18.00% | 4,050 | 101 | 0.4716 | 0.00912 |
| Zamansal | 91.82% | 17.59% | 4,258 | 81 | 0.4905 | 0.00898 |

Bölüm 5 önceki deneylerde incelendiğinden bu, geriye dönük kararlılık
betimlemesidir; dokunulmamış test değildir. Sabit eşikler farklı recall verdi;
yanlış alarm sayıları eşit recall karşılaştırması değildir. Olumlu AP sonucu
geliştirme kararını geçersiz kılmaz.

## Yeniden üretim ve sonraki karar

Komutlar [README](../README.md#experiment-3-temporal-discrimination) içindedir.
Yerel `artifacts/experiment3/report.html` tam raporu içerir. Makinece okunabilir
çıktılarda bütün recall hedefleri, tahminler, çıkarılan kayıtlar, hata tabloları,
modeller, kaynak özetleri, arşiv sağlama toplamları, paket sürümleri ve protokol
özeti bulunur.

Sonraki deney bölgesel hata yoğunlaşmasından başlamalıdır. Tekrarlanan pencere
alarmlarının sürekliliği ve olay gruplaması ölçülebilir; ardından yeni sabit
ilerleyen-zaman protokolüyle daha küçük gerekçeli özellik kümesi veya dizi
modeli sınanabilir. Nihai performans iddiası geliştirmeyi etkilememiş sonraki
dönem verisini gerektirir.
