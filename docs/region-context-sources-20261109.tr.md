# Bölgesel bağlam kaynakları: edinme, kaynak kanıtı ve kapsam

## Karar ve kapsam

İki açık kaynak, [donmuş kaynak dosyası](../config/region-context-sources-v1.json) altında edinildi ve
denetlendi; amaç, nedensel bölgesel bağlamın daha sonra erişilebilirlik varsaymadan HARP tahmin pencerelerine
eklenebilmesi. Hiçbir özellik oluşturulmadı, hiçbir model eğitilmedi, hiçbir etiket değişmedi ve ayrılmış
2024–2025 dönemine dokunulmadı. Bu rapor kaynakların ne olduğunu, erişilebilirlik hakkında neyi kanıtladıklarını
ve geliştirme verisinin ne kadarını kapsadıklarını söyler. Herhangi bir metriği iyileştirdiklerini söylemez.

Kararlar:

1. NOAA SWPC Güneş Bölge Özeti (SRS), her üründe kendi yayın zamanını taşır. Nedensel olarak kullanılabilir: t
   anındaki bir tahmin, t eksi 30 dakikalık payda veya öncesinde yayımlanan en son SRS'yi okuyabilir.
2. JSOC HARP–NOAA ilişkisinin (`NOAA_ARS`) belirtilmiş bir erişilebilirlik zamanı yoktur. Yalnızca NOAA
   numarasının tahmin anında mevcut SRS'te de geçtiği günlerde kullanılır; bu, erişilebilirliği SRS ile sınırlar.
3. Kapsam önemli yerde yüksektir: pozitif geliştirme pencerelerinin %97,5'i NOAA numaralı bir HARP'a aittir ve
   %90,8'inde bu numara tahmin anında mevcut SRS'te geçer; tüm pencereler için bu oranlar %59,1 ve %43,5'tir.
   Numaralı bölge durumu tek başına yanlış alarmları azaltmaz, çünkü donmuş baseline numarasız HARP'larda zaten
   nadiren alarm verir (aşağıdaki tanıya bakın). Kazanç varsa SRS içeriğinden gelmelidir.

## Kaynaklar

| kaynak | dosya | alınan | bayt | yayın zamanı üründe |
| --- | --- | --- | --- | --- |
| SRS | 4993 | 4989 | 3703125 | evet |
| JSOC NOAA_ARS | 164 | 164 | 2150086 | hayır |

SRS dosyaları yalnızca HTTPS ile `ngdc.noaa.gov` adresinden alındı. Dört gün arşivde yoktu (2016-07-19,
2019-04-27, 2019-08-02, 2022-12-17) ve iki arşiv dosyası boş (2019-08-04, 2019-08-07); bu yüzden 4993 günün
4987'sinde ayrıştırılabilir yayın zamanı var. Yayın zamanı dosyaların %99,4'ünde 00:30 UTC'dir; kalanlar aynı
gün içinde daha geç, en geç 22:00 UTC'dir. JSOC sorguları 164 ayın hepsinde HTTP yedeğini kullandı, çünkü sunucu
kendinden imzalı sertifika sunuyor; manifest bunu sorgu başına kaydeder. Dönem boyunca SRS manyetik sınıf
dağarcığı Alpha, Beta, Beta-Delta, Beta-Gamma, Beta-Gamma-Delta ve Gamma'dır; 17283 bölge satırı ayrıştırıldı.
1960 HARP en az bir NOAA numarası taşır.

## Geliştirme verisinin kapsamı

Bir pencere, HARP'ının o tarihteki NOAA numaralarından biri, tahmin zamanı eksi 30 dakika veya öncesinde
yayımlanan en son SRS'te geçiyorsa "mevcut SRS'te" sayılır.

| yıl | pencere | pozitif | HARP | NOAA numaralı pencere | mevcut SRS'teki pencere | NOAA numaralı pozitif | mevcut SRS'teki pozitif |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2010 | 21176 | 124 | 175 | 63.9% | 43.4% | 100.0% | 75.0% |
| 2011 | 61553 | 1526 | 462 | 65.8% | 49.5% | 99.5% | 94.3% |
| 2012 | 65974 | 1309 | 550 | 58.2% | 43.3% | 97.8% | 92.7% |
| 2013 | 75184 | 1311 | 597 | 63.0% | 47.1% | 100.0% | 93.8% |
| 2014 | 76206 | 2363 | 638 | 52.3% | 41.1% | 92.1% | 86.7% |
| 2015 | 70341 | 1403 | 610 | 55.2% | 40.3% | 98.1% | 93.7% |
| 2016 | 43267 | 205 | 361 | 54.9% | 39.7% | 100.0% | 89.3% |
| 2017 | 19739 | 253 | 167 | 60.1% | 45.8% | 100.0% | 100.0% |
| 2018 | 7932 | 0 | 76 | 63.8% | 40.0% | — | — |
| 2019 | 4941 | 0 | 44 | 62.9% | 39.8% | — | — |
| 2020 | 9867 | 0 | 78 | 73.1% | 44.1% | — | — |
| 2021 | 28369 | 204 | 258 | 65.6% | 45.9% | 100.0% | 89.2% |
| 2022 | 50756 | 421 | 528 | 61.8% | 44.8% | 100.0% | 90.3% |
| 2023 | 60366 | 781 | 703 | 53.9% | 40.5% | 100.0% | 83.9% |

## Donmuş baseline'ın yanlış alarmları nereye düşüyor

Bu tanı, zaten incelenmiş yılların donmuş yıllık baseline tahminlerini okur. Uyarlanabilir ve betimleyicidir;
kaynaklar edinildikten sonra hesaplandı ve sonraki protokole bilgi sağlar.

| yıl | YA pencereleri | mevcut SRS'teki YA | numarasız HARP'taki YA | TP | mevcut SRS'teki TP | pozitif | mevcut SRS'teki pozitif |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 13886 | 11113 | 1734 | 2184 | 1921 | 2310 | 1996 |
| 2015 | 11453 | 10193 | 124 | 1346 | 1257 | 1355 | 1266 |
| 2016 | 2289 | 2060 | 62 | 176 | 159 | 181 | 159 |
| 2017 | 1287 | 1186 | 30 | 237 | 237 | 253 | 253 |
| 2018 | 359 | 347 | 0 | 0 | 0 | 0 | 0 |
| 2022 | 10072 | 8917 | 67 | 415 | 374 | 421 | 380 |
| 2023 | 5992 | 5708 | 2 | 691 | 602 | 781 | 655 |

Yanlış-alarm pencerelerinin %80,0 (2014) ile %96,7 (2018) arası, mevcut SRS'te bulunan bölgelere düşer ve
numarasız HARP'lardaki yanlış alarmlar nadirdir (2023'te 5992'de 2). Bu yüzden "numaralı bölge" bayrağı az
yanlış alarm kaldırır. Yardımcı olabilecek bilgi, numaralı bölgelerin SRS içeriğidir: manyetik sınıf, McIntosh
sınıfı, alan ve leke sayısı. Mevcut SRS dışındaki pozitifler (2023'te %16,1), sonradan numaralanan bölgeler veya
günün SRS'sinden önceki pencerelerdir; bağlamları sakin değil eksik sayılmalıdır.

## Sınırlar

- SRS yayın zamanı ürünün ne zaman yayımlandığını kanıtlar, her tarihsel okuyucunun onu o dakikada aldığını
  değil; 30 dakikalık pay ölçülmüş bir gecikme değil, proje kuralıdır.
- `NOAA_ARS`, HARP işlem hattının atadığı kesin seri ilişkisidir; kendi erişilebilirliği bilinmez ve burada
  yalnızca SRS ile sınırlanır.
- Arşiv sürümleri 2026-11-09'da alındı; sonraki alımlar farklı olabilir. Değişiklikleri koda atfetmeden önce
  manifestleri karşılaştırın.
- Yanlış-alarm tanısı zaten incelenmiş yılların değerlendirme sonuçlarını kullanır ve herhangi bir iyileşmenin
  kanıtı değildir.

## Yeniden üretim

```sh
python scripts/fetch_region_summaries.py --output data/region_summaries_20261109_r1
python scripts/fetch_harp_noaa_mapping.py --output data/harp_noaa_mapping_20261109_r1
python scripts/audit_region_context_sources.py --srs data/region_summaries_20261109_r1 --mapping data/harp_noaa_mapping_20261109_r1 --output artifacts/region_context_sources_20261109_r1
python -m pytest -q tests/test_region_context_sources.py
```
