# Alarm dönemleri: pencereleri gruplamak precision'ı yükseltir mi?

## Kapsam ve karar

Alarmlar örtüşen saatlik tahmin pencereleri olarak sayıldığında precision düşüktür. Bu inceleme,
ardışık saatlik alarmların tek alarm dönemi olarak sayılmasının tabloyu değiştirip değiştirmediğini
sorar. Tamamlanan yedi yıllık karşılaştırmanın dondurulmuş yıllık tahminleri ve eşikleri yeniden
okundu (kaynak rapor SHA256 `e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`).
Eğitim, eşik değişikliği, yeniden etiketleme, model kabulü veya ayrılmış 2024–2025 testine erişim
yapılmadı. Analiz sonradan yapılmış, betimleyici bir incelemedir.

Dönem sayımının precision'ı yükselteceği hipotezi desteklenmedi. Pozitif pencere olan her yılda ve raporlanan
her iki kolda dönem precision'ı pencere precision'ından düşüktür. Operasyonel yük, birkaç uzun
alarm değil, çok sayıda kısa ve tamamen negatif alarm dönemidir.

## Tanımlar

Alarm dönemi, bir HARP'ın olasılığı dondurulmuş eşikte veya üstünde olan ardışık saatlik
pencerelerinden oluşan dizidir. İsabetli dönem en az bir pozitif etiketli pencere içerir; tamamen
negatif dönem hiç içermez. Dönem precision'ı, isabetli dönemlerin dönemlere oranıdır. Pozitif seri,
bir HARP'ın ardışık pozitif etiketli pencerelerinden oluşan dizidir; pencerelerinden biri alarm
içindeyse alarmlı sayılır. Bunlar örtüşen pencerelerin gruplamasıdır; fiziksel patlama, bağımsız
olay veya katalog eşleştirmesi değildir. Saatlik kayıttaki boşluklar bir dönemi böler; CSV kayıt
sınırına değen dönemleri sayar.

## Sonuçlar

Baseline ve chronological kolları, değiştirilmemiş kalibrasyon eşiklerinde. Dört kolun tamamı ve
daha fazla alan yerel `episodes.csv` içindedir.

| year | arm | positive_runs | positive_runs_alarmed | window_precision | episodes | hit_episodes | episode_precision | all_negative_episodes | median_all_negative_hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | baseline | 83 | 80 | 0.135905 | 686 | 67 | 0.097668 | 619 | 5 |
| 2014 | chronological | 83 | 79 | 0.100078 | 801 | 65 | 0.081149 | 736 | 7 |
| 2015 | baseline | 51 | 51 | 0.105164 | 568 | 38 | 0.066901 | 530 | 3 |
| 2015 | chronological | 51 | 50 | 0.105677 | 578 | 38 | 0.065744 | 540 | 4 |
| 2016 | baseline | 7 | 7 | 0.071400 | 204 | 4 | 0.019608 | 200 | 3 |
| 2016 | chronological | 7 | 7 | 0.026380 | 385 | 5 | 0.012987 | 380 | 6 |
| 2017 | baseline | 6 | 5 | 0.155512 | 85 | 5 | 0.058824 | 80 | 3.5 |
| 2017 | chronological | 6 | 5 | 0.133521 | 140 | 5 | 0.035714 | 135 | 3 |
| 2018 | baseline | 0 | 0 | 0.000000 | 30 | 0 | 0.000000 | 30 | 2 |
| 2018 | chronological | 0 | 0 | 0.000000 | 49 | 0 | 0.000000 | 49 | 3 |
| 2022 | baseline | 16 | 16 | 0.039573 | 622 | 16 | 0.025723 | 606 | 5 |
| 2022 | chronological | 16 | 16 | 0.030061 | 809 | 16 | 0.019778 | 793 | 4 |
| 2023 | baseline | 38 | 36 | 0.103397 | 475 | 40 | 0.084211 | 435 | 5 |
| 2023 | chronological | 38 | 37 | 0.054318 | 796 | 37 | 0.046482 | 759 | 5 |

Pencere precision'ı mevcut yıllık değerlendirmeyle aynıdır. Recall kollar veya yıllar arasında
eşitlenmemiştir. İsabetli dönem sayısı alarmlı pozitif seri sayısını aşabilir; çünkü bir pozitif seri
birden çok alarm dönemiyle örtüşebilir.

## Yorum

- Dönem precision'ı pencere precision'ının altındadır. 2014'te baseline için 0.097668,
  pencere için 0.135905; 2023'te 0.084211 ve 0.103397. Pozitif pencereler az sayıda seride
  kümelenir, yanlış alarmlar ise çok sayıda ayrı kısa dönem olarak gelir.
- Alarm dönemlerinin neredeyse tamamı tamamen negatiftir: baseline 2022'de 622 dönemin 606'sı,
  2014'te 686'nın 619'u. Tamamen negatif dönemin medyan süresi 2 ile 7 saat arasındadır; yük
  uzun süren alarmlardan çok alarm başlangıçlarının sayısıdır.
- Pozitif seriler neredeyse her zaman alarmlıdır (baseline için 2014'te 83'ün 80'i, 2015'te
  51'in 51'i); 2017 ve 2023'te kaçırmalar vardır (6'nın 5'i ve 38'in 36'sı). 2016'daki 7 gibi küçük
  seri sayıları oranları çok belirsiz kılar; aralık hesaplanmadı.
- Chronological kol her yılda baseline'dan daha çok dönem üretir; bu nedenle önceki TCN
  karşılaştırması dönem düzeyinde de geçerlidir.
- 2018'de pozitif pencere yoktur. Orada yalnızca 30 ve 49 tamamen negatif dönem ölçülebilir.

## Sınırlamalar

Dönem tanımı ardışık saat kuralına ve kayıt boşluklarına bağlıdır. Pozitif seri recall'ı etiketli
pencereleri anlatır; fiziksel patlama tespitini değil. Sayılar tekrar tekrar incelenmiş uyarlamalı
geçmiş kanıtıdır, bağımsız test değildir; farklı bir gruplama veya bastırma kuralının yardımcı
olacağını gösteremez. Alarm bekleme süresi veya dönem birleştirme eklemek, sonuçlara bakmadan
dondurulmuş bir kuralla yeni bir protokol gerektirir.

## Yeniden üretim

```sh
export PYTHONPATH=. PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_alarm_episodes.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/alarm_episodes_20261107_r2
"$PY" -m pytest tests/test_alarm_episodes_audit.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r4
```

Üretilen `report.json` kaynak hash değeri: `9d6b5c02d370f0b08ecc0dc3083d2df88d65a39469907077192666b143306788`. Tekrarlarda yeni çıktı adı kullanın.
Üretilen dosyalar Git dışında kalır. İngilizce sürüm aynı bulguları ve sınırları kapsar.
