# Helio24 — Güncel metrik raporu

Rapor tarihi: 16 Ekim 2026. Bu belge kayıtlı deney sonuçlarını bir araya getirir;
yeni model eğitimi veya yeni test sonucu içermez. Son kaynak incelemeleri
etiketleri ve performans sayılarını değiştirmedi.

## Ana sonuçlar

| Metrik | Dashboard modeli: ilk test | Tam veri: doğrulama | Tam veri: sonraki dönem incelemesi |
| --- | ---: | ---: | ---: |
| Accuracy | %92,94 | %91,37 | %94,80 |
| Recall | %95,88 | %90,06 | %90,61 |
| Precision | %14,98 | %18,52 | %19,00 |
| F1 | 0,2591 | 0,3072 | 0,3141 |
| Balanced accuracy | %94,39 | %90,73 | %92,73 |
| False positive rate | %7,10 | %8,60 | %5,15 |
| False alarm ratio | %85,02 | %81,48 | %81,00 |
| TSS | 0,8878 | 0,8145 | 0,8546 |
| Average precision (AP) | 0,4520 | 0,4720 | 0,4340 |
| Brier skoru | 0,008956 | 0,014832 | 0,009337 |
| Log loss | 0,030966 | 0,052204 | 0,033344 |
| Alarm eşiği | %1,437 | %4,800 | %4,800 |
| Pencere sayısı | 7.537 | 50.631 | 75.274 |
| Pozitif pencere | 97 | 1.076 | 990 |
| TP: doğru alarm | 93 | 969 | 897 |
| FP: yanlış alarm | 528 | 4.264 | 3.824 |
| FN: kaçırılan pozitif | 4 | 107 | 93 |
| TN: doğru negatif | 6.912 | 45.291 | 70.460 |
| Toplam alarm | 621 | 5.233 | 4.721 |

Dashboard modeli ilk deneydeki XGBoost'tur. Diğer iki sütun, ikinci deneydeki
tam veriyle eğitilmiş ve sigmoid kalibrasyon uygulanmış XGBoost'a aittir.
Accuracy, F1 ve balanced accuracy kayıtlı karışıklık matrisinden hesaplandı.

İlk test ile tam veri incelemesi farklı örnek kapsamları kullanır. Doğrulama,
eşik ve model seçiminde kullanılmıştır. Sonraki dönem beşinci bölümdür ve daha
önce incelenmiştir; bugün dokunulmamış final test olarak adlandırılamaz.
Sayılar fiziksel patlama sayısı değil, örtüşebilen tahmin penceresi sayısıdır.

## Nasıl yorumlanmalı?

Tam veri modelinin sonraki döneminde 897 doğru alarma karşı 3.824 yanlış alarm
vardır. Pozitif pencerelerin yaklaşık %91'i yakalanır, ancak alarmların yaklaşık
%81'i yanlıştır. Öncelikli sorun yanlış alarm yüküdür.

Aynı dönemde sürekli negatif tahmin veren yöntem %98,68 accuracy elde eder,
ancak recall sıfır olur. Bu nedenle başarı hedefi yalnızca accuracy değildir.
Recall ve precision yüksek; yanlış alarm oranları, Brier ve log loss düşük
olmalıdır. AP, precision–recall eğrisini özetler; trapez PR-AUC ile aynı hesap
değildir. Brier tek başına saf kalibrasyon ölçüsü sayılmaz.

## Belirsizlik ve alarm eşiği

Tam veri modelinin %90 doğrulama recall hedefindeki sonraki dönem %95 güven
aralıkları, 1.000 HARP bazlı bootstrap tekrarından elde edilmiştir:

| Metrik | Nokta tahmini | %95 aralık |
| --- | ---: | ---: |
| Recall | %90,61 | %80,09–96,65 |
| Precision | %19,00 | %11,86–27,30 |
| False positive rate | %5,15 | %3,66–6,82 |
| False alarm ratio | %81,00 | %72,70–88,14 |
| Brier | 0,009337 | 0,005959–0,013718 |

Bu aralıklar modelin yeniden eğitilmesinden veya tüm güneş döngüsü
değişimlerinden kaynaklanan belirsizlikleri kapsamaz. Kalibre edilmiş eksi ham
model Brier farkı −0,000113; %95 aralık [−0,000628, 0,000332]. Sıfırı içerdiği
için kalibrasyonun kesin iyileşme sağladığı söylenemez.

| Doğrulamada seçilen recall hedefi | Sabit eşik | Sonraki dönem recall | Precision | Yanlış alarm |
| --- | ---: | ---: | ---: | ---: |
| %80 | %6,884 | %87,17 | %22,59 | 2.958 |
| %90 | %4,800 | %90,61 | %19,00 | 3.824 |
| %95 | %3,403 | %91,82 | %16,27 | 4.678 |

Hedef recall daha sonraki dönemde garanti edilmez. İnceleme sonuçlarına bakarak
yeni eşik seçilmedi.

## Olay bazlı sonuçlar ve üçüncü deney

Geliştirme verisindeki ilk olay eşleştirmesi 86/87 yakalama (%98,85) verdi.
Altı eşleştirme kuralında aynı HARP'a atanan ortak 85 olayın 84'ü yakalandı
(%98,82). Tam 24 saat kapsamı olan ilk alt kümede 47/47 yakalama vardı. Bunlar
eşleştirme ve veri kapsamına koşullu oranlardır; genel final-test başarısı değildir.

333 alarm döneminin 280'i tamamen negatif pencere etiketlerinden oluşuyordu.
Yanlış alarm yükü 4.264 bölge-saat, toplam izlenen bölge-saatin %8,42'siydi.
En uzun tamamen negatif alarm dönemi 127 saatti. Yakalanan olaylarda medyan
başlangıç öncesi uyarı süresi 22,99 saatti. Uzun alarm dönemleri birden çok olayı
kapsayabilir; bu sayı bağımsız ve isabetli erken uyarıların garantisi değildir.

Üçüncü deneydeki zamansal özellik adayının sonraki dönem accuracy'si %94,24,
recall'ı %91,82, precision'ı %17,59, AP'si 0,4905'tir. Aday, geliştirme kabul
kurallarını sağlayamadığı için seçilmedi. Sonraki dönemde görülen olumlu bir
metrik bu kararı geriye dönük değiştirmek için kullanılmadı.

## Tam rapor ve yeniden üretim

```sh
python scripts/report_metrics.py
```

Komut 50 kayıtlı model/eşik sonucunu kontrol ederek `artifacts/metrics_summary/`
altına Türkçe, grafikleri içine gömülü `report.html` ve CSV tabloları yazar.
`all_metrics.csv` bütün deneyleri; `headline_metrics.csv` yukarıdaki üç ana
sonucu; diğer tablolar eşikleri, güven aralıklarını, kalibrasyon gruplarını,
olay analizini ve eşleştirme duyarlılığını içerir. `report.json` kaynak ve çıktı
SHA-256 özetlerini saklar. Mevcut raporun üstüne yazılmaz.

Ham veriler ve üretilen raporlar Git dışında kalır. Bu özet belge, rapor kodu
ve testler sürüm kontrolündedir. Önceki deneylerin dosyaları korunur.

Kaldığımız nokta: [üç olayın kaynak incelemesi](event-source-review.md).
Sonraki aşama: [yeni dönem değerlendirme hazırlığı](next-evaluation-plan.md).
