# 8765 ve 8864 olaylarının uzamsal incelemesi

Tarih: 2026-10-23. **Yeni görüntüler iki olayda da doğu kenarındaki kaynağı
destekliyor; ancak düzeltilmiş HARP etiketi belirlemiyor.** Referans etiket,
model, eşik veya performans sonucu değiştirilmedi.

## Kanıt ve kapsam

Helioviewer'dan doğrulanmış HTTPS ile altı tam disk SDO/AIA 131 görüntüsü
alındı: her olay için katalog başlangıcından beş dakika önce, katalog
zirvesinde ve bitişinde. Kaynak kimliği 9, servisin kaynak listesinden
doğrulandı. En yakın görüntü toleransı 60 saniye; altı görüntünün tamamı
istenen zamana 15 saniye içinde.

Asistan altı özgün PNG'yi ve zaman filigranlarını görsel olarak inceledi.
Bu nitel, model destekli kaynak incelemesidir; uzman kararı, kalibre fotometri
veya otomatik patlama konumlandırma sonucu değildir. Filigran zamanları
ayrı indirilen görüntü metadata'sıyla eşleşiyor.

| Olay | Aşama | İstenen UTC | Görüntü UTC | Mutlak fark, saniye |
| --- | --- | --- | --- | ---: |
| 8765 | önce | 2014-08-21 13:14:00 | 2014-08-21 13:13:45 | 15 |
| 8765 | zirve | 2014-08-21 13:31:00 | 2014-08-21 13:31:00 | 0 |
| 8765 | bitiş | 2014-08-21 13:42:00 | 2014-08-21 13:41:48 | 12 |
| 8864 | önce | 2014-09-03 13:15:00 | 2014-09-03 13:14:45 | 15 |
| 8864 | zirve | 2014-09-03 13:54:00 | 2014-09-03 13:54:12 | 12 |
| 8864 | bitiş | 2014-09-03 14:23:00 | 2014-09-03 14:23:09 | 9 |

Özgün görüntüler: 8765 [önce](../data/spatial_review/8765_before.png),
[zirve](../data/spatial_review/8765_peak.png), [bitiş](../data/spatial_review/8765_end.png);
8864 [önce](../data/spatial_review/8864_before.png),
[zirve](../data/spatial_review/8864_peak.png), [bitiş](../data/spatial_review/8864_end.png).
Yerel bağlantılar indirilen veriyi gerektirir; bu dosyalar commitlenmez.

## Bulgular ve güncellenen yorum

**8765** zirve görüntüsünde kuzeydoğu kenarında belirgin, doygun bir parlama
var; parlak yapı bitişte de görülüyor. Bu, kataloğun yaklaşık (-930, 176)
yay-saniyedeki SSW konumuyla nitel olarak tutarlı. GOES/Hinode konumları
yaklaşık x=-580 yay-saniyede, diskin daha iç kesiminde. İç aktif bölgeler
de görülüyor; üç görüntü onların etkin olmadığını kanıtlamıyor.

**8864** zirve görüntüsünde güneydoğu kenarında belirgin parlama var ve
bitişte sürüyor. Bu, yaklaşık (-917, -250) yay-saniyedeki SSW ile nitel
olarak tutarlı. GOES/Hinode konumları yaklaşık x=+285 yay-saniyede, diskin
diğer tarafında. Başka parlak bölgeler de görünür; eşzamanlı olaylar dışlanamaz.

Önceki [birincil kaynak incelemesi](event-source-review.tr.md), optik konumlar
ve daha sonraki günlük bölge konumları üzerinden 12148 ve 12152'nin
araştırılmasını öneriyordu. Yeni görüntü bağlamı, baskın zirve parlamasının
açıklaması olarak bu adayları zayıflatıp doğu kenarındaki NOAA/SSW adayları
12149 ve 12155'i güçlendiriyor. Bu, keşifsel yorumun güncellenmesidir;
çelişkili optik/radyo kanıtını silmez veya aynı NOAA olay kimliği altında
gruplanan her kaydın tek fiziksel kaynağı olduğunu kesinleştirmez.

| Olay | Güçlenen NOAA adayı | Tartışmalı arşiv HARP | Düzeltilmiş HARP belirlendi | Etiket değişikliğine izin |
| --- | ---: | ---: | --- | --- |
| 8765 | 12149 | 4466 | Hayır | Hayır |
| 8864 | 12155 | 4502 | Hayır | Hayır |

Görüntü düzlemi konumu NOAA veya HARP kimliği değildir. FITS/WCS hizalaması,
zamana bağlı heliografik dönüşüm veya HARP sınırlarının izdüşümü yapılmadı.
4466/4502 için eksik NOAA metadata'sı çözümlenmedi. Bu nedenle
containing/location kuralındaki özgün 19 ve 10 negatif etiket çelişkisi
burada onarılmadı veya model hatası olarak yeniden sınıflandırılmadı.

## Sınırlamalar ve sonraki koşul

Görüntü sunumu, pozlama değişimi, doygunluk ve taşma nedeniyle PNG parlaklığı
kalibre akı karşılaştırması olarak kullanılamaz. Üç zaman noktası tam film
değildir. Helioviewer metadata ve görüntü üretimi ayrı isteklerdir; incelenen
zamanların eşleşmesi için filigranlar kontrol edildi. Olay sonrası kanıt
yalnızca etiket araştırması içindir, tahmin girdisi değildir. Bölge seçmek
için model olasılıkları kullanılmadı.

Sonraki adım, kalibre ve zaman damgalı uzamsal gözlemleri açık koordinat
çerçeveleri ve UTC/TAI işleyişiyle kesinleştirilmiş HARP sınırlarına hizalamak.
Kimlik böyle doğrulanana kadar vakalar çözümlenmemiş ilişki inceleme kuyruğunda
kalmalı. İleride kabul edilen düzeltmeler ayrı sürümlü etiket kümesi ve
eğitimden önce sabitlenmiş dahil etme politikası gerektirir. Özgün etiketler
ve ayrılan 2024–2025 değerlendirme dönemi korundu.

## Yeniden üretim ve koruma

```sh
python scripts/fetch_spatial_review.py
python scripts/review_spatial_evidence.py
python scripts/publish_reports.py --output artifacts/bilingual_reports_spatial
```

Komutlar mevcut çıktı dizinlerini korur. `data/spatial_review/` özgün PNG'leri,
metadata'yı ve URL, UTC indirme zamanı, SHA-256 özetlerini içeren manifesti
tutar. `artifacts/spatial_review/` içinde `frames.csv`, `case_dispositions.csv`
ve `report.json` bulunur; görsel inceleme durumu ve otomatik etiket değişikliği
yasağı açıkça kayıtlıdır. Önceki kaynak raporu ve bütün görüntü özetleri
doğrulanır. Önceki eksik SolarSoft arşiv indirmesi kanıt olarak kullanılmadı.

API kaynakları: [görüntü metadata'sı](https://api.helioviewer.org/docs/v2/api/api_groups/official_clients.html)
ve [görüntü üretimi](https://api.helioviewer.org/docs/v2/api/api_groups/screenshots.html).
Yukarıdaki nitel bulgular incelenen altı görüntü ve önceden dondurulmuş
NOAA/SWAN-SF kayıtlarından gelir; yeni performans değerlendirmesi değildir.
