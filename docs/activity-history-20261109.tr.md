# Yayımlanmış SGAS patlama geçmişi bağlamı: kaynak ve sonuçlar (2026-11-09)

## Karar

Olumsuz sonuç. Yayımlanmış NOAA SGAS ürünlerinden gelen nedensel patlama geçmişini 96 manyetik özete eklemek,
proje çalışma noktasında (önceki yıl eşiği, pencere recall 0,90) precision'ı yükseltmiyor. `history` adayı birincil
kabulü 6 yılın 0 tanesinde, `flag` adayı 1 tanesinde karşılıyor. Hiçbir model terfi ettirilmedi, hiçbir
uyarı veya eşik değişmedi. Ayrılmış 2024–2025 testine erişilmedi. Protokol
[`config/activity-history-v1.json`](../config/activity-history-v1.json) herhangi bir aday sonucundan önce
donduruldu ve commit edildi.

## Neden bu kaynak

Patlama geçmişi engelliydi, çünkü güneş olay raporları yalnızca arşiv `:Created:` zamanı taşıyor
([inceleme](history-publication-probe-20261107.tr.md)). Joint USAF/NOAA Solar and Geophysical Activity Summary
(SGAS) her üründe bir `:Issued:` zamanı taşır ve önceki UT gününün enerjik olaylarını NOAA bölge numarası ve
X-ışını sınıfıyla, ayrıca X-ışını arka planını listeler.

| kalem | değer |
| --- | --- |
| arşiv | `https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_geophysical_activity_summaries/` |
| dönem | 2010-05-01 – 2023-12-31 |
| alınan / beklenen dosya | 4980 / 4993 |
| bayt | 6020323 |
| yayın zamanı ayrıştırılan rapor | 4979 |
| ayrıştırılan olay satırı | 12286 |
| ayrıştırılamayan olay satırı | 0 |

Dosyası olmayan tarihler: 2015-02-26, 2015-11-07, 2017-07-07, 2019-04-27, 2019-08-02, 2019-08-27, 2021-08-04, 2021-09-28, 2022-01-01, 2022-01-02, 2022-01-03, 2022-04-08, 2022-12-17. Alınan bir dosyada ayrıştırılabilir yayın zamanı yoktur ve kullanılmaz.
Ayrıştırılan raporların 4937'si 0245 UTC'de yayımlanmıştır. SGAS enerjik olayları listeler, her C sınıfı patlamayı
değil.

## Yöntem

Tahmin zamanı t olan bir pencere yalnızca t eksi 30 dakikada veya öncesinde yayımlanmış ürünleri kullanır.
Bölgesel olaylar, NOAA numarası tahmin tarihinde HARP'ın `NOAA_ARS` alanında bulunanlardır. NOAA numarası
olmayan veya önceki 75 saatte ürünü bulunmayan bir HARP için `history_available` = 0 olur ve bölgesel değerler
eksik kalır. On beş özellik: `history_available`, `reports_3d`, `hours_since_issue`, `reg_c_1d`, `reg_mx_1d`,
`reg_c_3d`, `reg_mx_3d`, `reg_events_3d`, `reg_max_logflux_3d`, `reg_mx_life`, `reg_max_logflux_life`,
`disk_mx_1d`, `disk_mx_3d`, `disk_max_logflux_1d`, `xray_background_log`. `flag` değişmemiş tarifleri yalnızca ilk
üçüyle yeniden uydurur; `history` on beşini de kullanır. Hiperparametre araması yok; 24 bileşen uydurması.

Değerlendirme yılı kapsamı:

| yıl | history_available payı | reg_mx_3d > 0 payı |
| --- | --- | --- |
| 2014 | 0.5203 | 0.0454 |
| 2015 | 0.5482 | 0.0405 |
| 2016 | 0.5499 | 0.0066 |
| 2017 | 0.6040 | 0.0198 |
| 2022 | 0.6178 | 0.0514 |
| 2023 | 0.5388 | 0.0736 |

## Sonuçlar

| yıl | aday | TP | FP | FN | recall | precision | accuracy | hep-negatif accuracy | epizot precision | alarm verilen pozitif seri | AP | Brier | log loss | birincil kabul |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2007 | 7634 | 303 | 0.8688 | 0.2082 | 0.8945 | 0.9693 | 0.1636 | 77/83 | 0.5079 | 0.0207 | 0.0765 |  |
| 2014 | flag | 1988 | 7411 | 322 | 0.8606 | 0.2115 | 0.8972 | 0.9693 | 0.1688 | 76/83 | 0.5089 | 0.0207 | 0.0766 | hayır |
| 2014 | history | 2042 | 8134 | 268 | 0.8840 | 0.2007 | 0.8883 | 0.9693 | 0.1335 | 77/83 | 0.5176 | 0.0206 | 0.0765 | hayır |
| 2015 | control | 1308 | 6294 | 47 | 0.9653 | 0.1721 | 0.9083 | 0.9804 | 0.1138 | 51/51 | 0.4924 | 0.0136 | 0.0478 |  |
| 2015 | flag | 1319 | 6536 | 36 | 0.9734 | 0.1679 | 0.9049 | 0.9804 | 0.1132 | 51/51 | 0.4937 | 0.0135 | 0.0479 | hayır |
| 2015 | history | 1296 | 6423 | 59 | 0.9565 | 0.1679 | 0.9062 | 0.9804 | 0.1000 | 50/51 | 0.4725 | 0.0139 | 0.0487 | hayır |
| 2016 | control | 162 | 1303 | 19 | 0.8950 | 0.1106 | 0.9692 | 0.9958 | 0.0347 | 7/7 | 0.3664 | 0.0033 | 0.0145 |  |
| 2016 | flag | 162 | 1313 | 19 | 0.8950 | 0.1098 | 0.9690 | 0.9958 | 0.0355 | 7/7 | 0.3612 | 0.0033 | 0.0146 | hayır |
| 2016 | history | 158 | 942 | 23 | 0.8729 | 0.1436 | 0.9776 | 0.9958 | 0.0556 | 7/7 | 0.4356 | 0.0030 | 0.0133 | hayır |
| 2017 | control | 235 | 1035 | 18 | 0.9289 | 0.1850 | 0.9461 | 0.9870 | 0.0781 | 5/6 | 0.8117 | 0.0049 | 0.0205 |  |
| 2017 | flag | 235 | 1015 | 18 | 0.9289 | 0.1880 | 0.9471 | 0.9870 | 0.0758 | 5/6 | 0.8135 | 0.0049 | 0.0204 | hayır |
| 2017 | history | 234 | 1123 | 19 | 0.9249 | 0.1724 | 0.9415 | 0.9870 | 0.0556 | 5/6 | 0.7735 | 0.0053 | 0.0227 | hayır |
| 2022 | control | 414 | 8949 | 7 | 0.9834 | 0.0442 | 0.8235 | 0.9917 | 0.0316 | 16/16 | 0.2800 | 0.0071 | 0.0292 |  |
| 2022 | flag | 414 | 8996 | 7 | 0.9834 | 0.0440 | 0.8226 | 0.9917 | 0.0311 | 16/16 | 0.2808 | 0.0071 | 0.0292 | hayır |
| 2022 | history | 416 | 12238 | 5 | 0.9881 | 0.0329 | 0.7588 | 0.9917 | 0.0231 | 16/16 | 0.3094 | 0.0071 | 0.0310 | hayır |
| 2023 | control | 653 | 4852 | 128 | 0.8361 | 0.1186 | 0.9175 | 0.9871 | 0.0905 | 35/38 | 0.2206 | 0.0112 | 0.0440 |  |
| 2023 | flag | 653 | 4818 | 128 | 0.8361 | 0.1194 | 0.9181 | 0.9871 | 0.0928 | 35/38 | 0.2209 | 0.0112 | 0.0440 | evet |
| 2023 | history | 719 | 6343 | 62 | 0.9206 | 0.1018 | 0.8939 | 0.9871 | 0.0745 | 38/38 | 0.2342 | 0.0110 | 0.0422 | hayır |

Yıl başına birincil kabul: epizot precision'ı daha yüksek, FP pencereleri daha az, alarm verilen pozitif seriler
daha az değil, pencere recall düşüşü en fazla 0,02; hepsi kontrole göre.

- Precision: `history` yalnızca 2016'da kontrolün üstünde (0.1436'ya karşı 0.1106), diğer beş yılda altında.
- Accuracy her adayda ve her yılda hep-negatif accuracy değerinin altında kalıyor. Bunu aşmak TP'nin FP'den büyük
  olmasını, yani precision'ın 0,50'nin üstünde olmasını gerektirir.
- AP: `history` 2014, 2016, 2022 ve 2023'te kontrolün üstünde, 2015 ve 2017'de altında. Sıralama kazançları önceki
  yıl eşiğine taşınmadı: `history` eşiği her yıl kontrolden düşük ve 2014, 2015, 2017, 2022 ve 2023'te daha fazla
  yanlış alarm kabul ediyor.
- `flag` kontrolden yalnızca yeniden uydurma gürültüsü kadar ayrılır; 2023'teki tek geçişi içeriğe atfedilmez.

Eşleştirilmiş tüm-HARP bootstrap aralıkları (1000 çekiliş, tohum 24) `intervals.csv` içindedir.

## Sınırlar

Zaten incelenmiş yıllar: uyarlanabilir geliştirme kanıtı, bağımsız test değil. Sayılar örtüşen tahmin pencereleri
ve bunların gruplamalarıdır, fiziksel patlamalar değildir. Arşivlenmiş SGAS metni ilk yayımlanan baytlardan farklı
olabilir. `NOAA_ARS`, kesin JSOC ilişkilendirmesidir. Bölgesel geçmiş, değerlendirme pencerelerinin yalnızca
yaklaşık %52–62'sinde mevcuttur.

## Yeniden üretim

```sh
python -m scripts.fetch_activity_summaries --output data/activity_summaries_20261109_r1
python -m scripts.audit_activity_history --output artifacts/activity_history_20261109_r1
```

Config sha256 `f8797376e56bf6be386181fd160f3fde21e8fa9797efe5274316b577cf195d40`; eşik sha256 `a9bfefa4fe76ed6b4644e2fb2da6277c74bc1b159d8fcf925656b6a29b34f533`. Yeni çıktı dizinleri kullanın; var olan çıktının üzerine yazılmaz.
