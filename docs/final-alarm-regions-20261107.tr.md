# Son yıllık yanlış alarmların bölgesel incelemesi

## Kapsam ve karar

Bu çalışma bölgesel hata incelemesini tamamlanan yedi yıllık dönemin tamamına genişletir.
Kronolojik TCN ile dondurulmuş referansı, her birinin değişmemiş önceki yıl kalibrasyon
eşiğinde karşılaştırır. Recall eşitlenmiş bir karşılaştırma değildir. Eğitim, eşik ayarı,
yeniden etiketleme, model kabulü veya ayrılmış 2024–2025 testine erişim yapılmadı.
Sayımlar örtüşen tahmin pencereleridir; bağımsız patlama veya bildirim sayısı değildir.

Kaynak raporun SHA256 değeri:
`e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2`.
Dahil edilen her tahmin, eşik ve tamamlanma kaydı bu manifestle doğrulandı. On dört
model/yıl FP toplamı da bağımsız dondurulmuş son karşılaştırmayla eşleşiyor.

Tekil kazançlara dayanarak bu TCN yöntemini daha fazla epoch ile uzatmayın. Yeni yıllar
da ciddi yanlış alarm maliyetini doğruluyor. Nedensel geçmiş yönü, kaynak erişilebilirliği
koşulu henüz sağlanmamış, sınanmamış bir hipotez olarak kalıyor.

## Eşleştirilmiş eklemeler ve çıkarmalar

| year | extra_fp | removed_fp | shared_fp | extra_tp | removed_tp | candidate_fp | baseline_fp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 6773 | 1020 | 12866.000000 | 53 | 53 | 19639 | 13886 |
| 2015 | 2541 | 2857 | 8596.000000 | 1 | 31 | 11137 | 11453 |
| 2016 | 4446 | 350 | 1939.000000 | 1 | 4 | 6385 | 2289 |
| 2017 | 565 | 314 | 973.000000 | 0 | 0 | 1538 | 1287 |
| 2018 | 221 | 62 | 297.000000 | 0 | 0 | 518 | 359 |
| 2022 | 4034 | 1135 | 8937.000000 | 0 | 13 | 12971 | 10072 |
| 2023 | 6678 | 187 | 5805.000000 | 42 | 16 | 12483 | 5992 |

`extra_fp` yalnızca TCN'nin alarm verdiği negatif pencereleri; `removed_fp` yalnızca
referansın alarm verdiklerini; `shared_fp` ikisinin alarm verdiklerini sayar. TP sütunları
aynı geçişleri pozitif pencerelerde ölçer. Her yılda ek FP eksi kaldırılan FP, aday FP
eksi referans FP'ye eşittir. Özgün 2014–2016 eşleştirilmiş sayımları yeniden üretildi.

2022'de net 2899 ek yanlış alarm, yeni yakalanan sıfır pozitif pencere ve kaybedilen
13 pozitif pencere var. 2023'te net 6491 ek yanlış alarm ve net 26 ek pozitif pencere
var (42 kazanım, 16 kayıp). Bunlar operasyonel uyarının değerine ilişkin tahmin değil,
betimleyici ödünleşimlerdir. 2018'de pozitif pencere yok: net 159 ek yanlış alarm
ölçülebilir kalırken recall değerlendirilemez.

## Bölgesel yoğunlaşma

| year | top10_extra_fp | top10_extra_fp_share | top10_negative_share | zero_positive_region_extra_fp |
| --- | --- | --- | --- | --- |
| 2014 | 1473 | 0.217481 | 0.038111 | 6110 |
| 2015 | 777 | 0.305785 | 0.041426 | 2473 |
| 2016 | 1557 | 0.350202 | 0.064080 | 4233 |
| 2017 | 469 | 0.830088 | 0.137373 | 562 |
| 2018 | 211 | 0.954751 | 0.254392 | 221 |
| 2022 | 1141 | 0.282846 | 0.047839 | 3939 |
| 2023 | 1439 | 0.215484 | 0.038617 | 6006 |

On bölge, her yılın ek FP değerleri görüldükten sonra seçildi; eşitlikte HARP kimliği
kullanıldı. Paylar 0–1 ölçeğindedir. Ek FP payını eşit bölge varsayımıyla değil, negatif
pencere payıyla karşılaştırın. 2022'de ilk on bölge ek FP'nin 0.282846'sını ve negatif
pencerelerin 0.047839'unu oluşturuyor; 2023'te paylar 0.215484 ve 0.038617.
Yoğunlaşma yıllara göre değişiyor ve 2016 ile sınırlı değil. 2018'deki yüksek yoğunlaşma,
pozitif olayları yararlı biçimde ayırt edebildiğimizi göstermez.

`zero_positive_region_extra_fp`, değerlendirme döneminin tamamının sonuçlarını kullanır;
bölgenin geçmişte hiç patlama üretmediği anlamına gelmez. Bu geriye dönük gruplar ve
sıralamalar tahmin anı özelliklerine veya dışlama listesine dönüştürülmemeli. Bu inceleme,
patlama geçmişi özelliklerinin yardımcı olacağını gösteremez. Sonradan seçilen bu paylara
yeni belirsizlik aralığı veya anlamlılık testi eklenmedi. Mevcut eşleştirilmiş metrik
aralıkları [son değerlendirmede](temporal-evaluation-final-20261106.tr.md) korunuyor.
Bölgesel veriler yerel `regions.csv` içinde tutuluyor; dönem farkları genel ortalamayla
gizlenmiyor.

## Kaynak erişilebilirliği ve kurtarma

NOAA'nın [tarihsel rapor belgesi](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/docs/SolarEventReport.pdf),
önceki günlük listelerin revize edildiğini açıkça anlatıyor. Bu tarihsel bir belgedir;
güncel yenileme sıklığının kanıtı değildir. İncelenen [Eylül 2023 dizini](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2023/09/)
günlük dosyaları listeler; gün içi sürüm geçmişi sağlamaz. İki gözlem de başka bir yerde
sürüm arşivi bulunmadığını kanıtlamaz. İlk yayın, içeriğin kesin erişilebilirliği ve o
anda bilinen HARP eşleştirmesi doğrulanmadı; seçilen protokol kapsamında zamanları
varsaymak yerine eğitim engeli korunuyor.

Eksik tarihsel `2019/predictions.parquet` hâlâ yoktu. iCloud Veri Kurtarma bu denemede
yükleniyor göstergesi sundu; sonraki erişilebilirlik okuması Safari penceresine ulaşamadı.
Dosya listesi veya başarılı geri yükleme doğrulanmadı. Bu, kalıcı kaybı kanıtlamaz.
Tamamlanan deney ve mevcut yerel yedeği kullanılabilir; bu inceleme eksik tarihsel
kontrol dosyasına bağlı değildir.

## Yeniden üretim

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/audit_final_alarm_regions.py --source artifacts/temporal_years_20261101_r1 --source-sha256 e85c7d9eec4a82e2c472f8f17f1a060cd426babe04894ce82425b32e849dc5a2 --output artifacts/final_alarm_regions_20261107_r2
"$PY" -m pytest tests/test_final_alarm_regions.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r2
```

Yeni çıktı adları kullanın. Özgün sonuçlar
`artifacts/final_alarm_regions_20261107_r1` içinde; üretilen dosyalar Git dışında kalır.
İki dildeki sürümler aynı bulguları ve sınırları kapsar. Bu analiz, sonraki modelin
bağımsız testi değil, uyarlamalı geliştirme kanıtıdır.
