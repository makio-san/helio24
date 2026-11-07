# Patlama geçmişi kaynak zamanları ön incelemesi ve kurtarma güncellemesi

## Karar ve kapsam

Model eğitimine değil, kaynak kökeni incelemesine devam ediyoruz. HTTPS üzerinden yedi
küçük NOAA Güneş olayı raporu alındı: uygun geliştirme yıllarının her birinden 3 Eylül.
Bu, mevcut 2014 örneğinden hareketle seçilmiş sabit tarihli tanısal bir örneklemdir;
rastgele örneklem, tam yıl kapsama denetimi veya tipik yayın gecikmesi tahmini değildir.
Ayrılmış 2024–2025 verilerine erişilmedi, etiketler değiştirilmedi, yeni metrik üretilmedi.

Arşivdeki `:Created:` başlığı, incelenen her dosyada rapor tarihinden sonradır. Aşağıdaki
süre, rapor gününün başlangıcındaki gece yarısından hesaplanır; tekil patlamadan veya
ilk yayın anından itibaren geçen süre değildir.

| year | report_date | created_utc | hours_after_report_day_start |
| --- | --- | --- | --- |
| 2014 | 2014-09-03 | 2014-09-05T03:57:00+00:00 | 51.95 |
| 2015 | 2015-09-03 | 2015-09-04T15:27:00+00:00 | 39.45 |
| 2016 | 2016-09-03 | 2016-09-06T03:57:00+00:00 | 75.95 |
| 2017 | 2017-09-03 | 2017-09-05T03:57:00+00:00 | 51.95 |
| 2018 | 2018-09-03 | 2018-09-05T03:57:00+00:00 | 51.95 |
| 2022 | 2022-09-03 | 2022-09-06T03:57:00+00:00 | 75.95 |
| 2023 | 2023-09-03 | 2023-09-06T03:57:00+00:00 | 75.95 |

Resmî girdiler: [2014](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/09/20140903events.txt),
[2015](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2015/09/20150903events.txt),
[2016](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2016/09/20160903events.txt),
[2017](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2017/09/20170903events.txt),
[2018](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2018/09/20180903events.txt),
[2022](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2022/09/20220903events.txt),
[2023](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2023/09/20230903events.txt).

## Bulguların gösterdiği ve göstermediği

Bu belge sürümleri, daha önceki tüm olay anlarında mevcutmuş gibi kullanılamaz.
`:Created:`, belge üretimi hakkında kanıttır; ilk kamuya açılma veya değişmez sürüm
geçmişinin kanıtı değildir. Daha erken operasyonel sürümler bulunmuş olabilir.
[SWPC kullanım kılavuzu](https://www.swpc.noaa.gov/sites/default/files/images/u2/Usr_guide.pdf),
olay listelerinin tahmincilerce düzenlenmesini ve ardından haftalık incelemeyi anlatır;
son arşivi indirmek, tarihsel tahminlerde erişilebilir tüm sürümleri geri getirmez.

Keyfî sabit gecikme eklemek veya indirme zamanını kullanmak kaynak kökeni açığını
kapatmaz. `:Created:` zamanını uygunluk sınırı yapmak bile, içeriğin ve bölge eşleştirmesinin
o anda mevcut olduğuna ilişkin kanıt gerektirir. Yedi denetim satırında da
`availability_verified=false`; `training_ready=false` açıkça korunuyor. Sonraki kaynak
gereksinimi, sürümlenmiş yayın zamanı kanıtı ve o anda bilinen bölge eşleştirmeleri;
ardından tüm eğitim/kalibrasyon/değerlendirme dönemlerinin kapsanmasıdır. Mevcut nedensel
geçmiş hipotezi koşullu olmaya devam ediyor, doğrulanmış değil.

`scripts/audit_history_publication.py`, indirilen kaynakların hash değerlerini denetler
ve UTC rapor başlıklarını ayrıştırır. Eksik/desteklenmeyen başlıklar ve rapor gününden
önceki oluşturulma tarihleri reddedilir. Üç test; yayın iddiası olmadan geç oluşturulmayı,
eksik zaman bilgisini ve tutarsız tarihleri kapsar. `scripts/fetch_history_probe.py`
aynı yedi tarihi sabitler, mevcut çıktı dizinlerini korur ve indirmeyi HTTPS ile sınırlar.

## Dosya kurtarma durumu

Yetkilendirilmiş iCloud oturumu artık Drive'ı açıyor. Son Silinenler inceleme sırasında
yükleniyor göstergesinde kaldı. Ayrı Veri Kurtarma yolu tekrar “Bu içerik yüklenirken
bir sorun oluştu.” hatasını verdi. Tarihsel
`calibration_windows_20261030_r1/2019/predictions.parquet` yerelde hâlâ yok.
Uzak dosya listesi alınamadı ve hiçbir geri yükleme tamamlanmadı; bu, uzak kopyanın
yok olduğunu kanıtlamaz. İlgisiz dosyalar kurtarılmadı ve Tümünü Kurtar kullanılmadı.
Tamamlanan yıllık değerlendirme bu tarihsel kontrol dosyası olmadan kullanılabilir.
Doğrulanmış yerel yedek iCloud'dan ayrı kalmaya devam ediyor.

## Yeniden üretim

İncelenen kaynak kopyası `data/history_source_probe_20261107_r1`; manifesti özgün
URL'leri ve SHA256 değerlerini kaydeder. Sonuçlar
`artifacts/history_publication_audit_20261107_r1/report.json` içinde korunur.
İndirilen kaynaklar ve üretilen sonuçlar Git dışında kalır. Yeni indirme ve denetim
için yeni dizinler kullanın:

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261107
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" scripts/fetch_history_probe.py --output data/history_source_probe_20261107_r2
"$PY" scripts/audit_history_publication.py --source data/history_source_probe_20261107_r2 --output artifacts/history_publication_audit_20261107_r2
"$PY" -m pytest tests/test_history_publication.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261107_r1
```

Sonraki indirme farklı arşiv baytları getirebilir. Farkı koda bağlamadan önce manifestleri
karşılaştırın; özgün kaynak kopyasını koruyun ve kanıtı sessizce değiştirmeyin.
