# Üç tartışmalı patlama ilişkisinin birincil kaynak incelemesi

Ayrı indirilen NOAA kayıtları, üç SWAN-SF olayının X-ışını sınıfını ve
başlangıç, zirve, bitiş zamanlarını aynen doğruluyor. Bölge ilişkilerinin
güvenilirliği ise aynı değil. 9529 için HARP 4941 daha güçlü destekleniyor;
8765 ve 8864 çözümlenmedi. Özgün etiketler ve model sonuçları değişmedi.

[Kaynak inceleme protokolü](source-review-protocol.md) izlendi.
Bu keşifsel çalışmada NOAA, SWAN-SF'nin üst kaynaklarından biridir; ayrı
indirme kaynak izleme kontrolüdür, üç yeni bağımsız doğrulama olayı değildir.

## Kaynak bulguları

| SWAN-SF kimliği | Tarih ve zirve UTC | Sınıf | NOAA günlük olay kimliği | Kaynak bulguları | İnceleme kararı |
| --- | --- | --- | --- | --- | --- |
| 8765 | 2014-08-21 13:31 | M3.4 | 9490 | NOAA bölgesi 12149, optik konum N06E38; HARP 4466 NOAA metadata eksik | Çözülmemiş konum/bölge uyuşmazlığı |
| 8864 | 2014-09-03 13:54 | M2.5 | 3300 | XRA 12155, optik/radyo 12152 atıyor; HARP 4502 NOAA metadata eksik | Açık kaynak çelişkisi |
| 9529 | 2014-12-18 21:58 | M6.9 | 550 | NOAA satırları 12241 üzerinde aynı; JSOC HARP 4920 yerine HARP 4941 ile bağlıyor | HARP 4941 kaynak destekli aday; yeniden etiketleme yok |

NOAA günlük olay kimlikleri ve SWAN-SF katalog kimlikleri farklıdır.
Bu 2014 NOAA dosyalarının dört haneli bölge numaralarına 10000 eklendi.
Bu, bütün güneş döngüleri için genel dönüşüm kuralı değildir.

### 8765: numara uyumu konumu çözmez

[21 Ağustos NOAA raporu][aug-events], M3.4 olayını 13:19–13:42 UTC,
zirve 13:31, bölge 2149 olarak verir. 13:29–13:36 optik raporu aynı bölge
numarasıyla N06E38 konumunu bildirir. Ancak 21/2400 UTC için geçerli
[ertesi gün bölge özeti][aug-srs], 2149'u N12E77, 2148'i N05E27 gösterir.

**Yorum:** optik konum ile adlandırılan bölgeyi günlük konumlarla uzlaştırmak
zordur. 2148 görüntüyle araştırılacak adaydır, düzeltilmiş etiket değildir.
Günlük konumlar patlamadan sonradır; zirveye taşınmamıştır.

13:00–13:48 TAI arasındaki beş resmî HARP-4466 kaydında NOAA_AR=0,
NOAA_NUM=0, NOAA_ARS=MISSING. İndirilen güncel tüm-HARP tablosunda da
4466 yok. Eksik metadata kimliği çözmez. SWAN-SF konum anotasyonu geometrik
ilişki kanıtıdır, doğrulanmış NOAA ataması değildir.

### 8864: uyuşmazlık NOAA raporunun içinde

[3 Eylül NOAA raporu][sep-events], M2.5 XRA kaydını (13:20–14:23 UTC,
zirve 13:54) 2155 bölgesine atar. Aynı günlük olay kimliği 3300 altında
dört radyo kaydı ve optik rapor 2152'yi gösterir. 14:07–14:20 optik raporunun
konumu S14W18. Bu zamanlar X-ışını zirvesinden sonra; eşzamanlı görüntü değildir.

03/2400 UTC için geçerli [ertesi gün özeti][sep-srs], 2152'yi S15W26,
2155'i S20E75 gösterir. **Yorum:** optik konum 12152'nin araştırılmasını
destekler; XRA bölgesi 12155'i otomatik değiştirmeyi veya 3300 altındaki her
kaydı aynı fiziksel kaynağın kesin kanıtı saymayı gerekçelendirmez.

Beş HARP-4502 kaydının NOAA ilişkileri eksik. 13:48 TAI'de yerel boylam
sınırları 8.314208–30.087482, enlem sınırları −24.940029–−11.550781;
birleşik katalogdaki (18, −14) ile sayısal olarak tutarlı.
Sınır kutusu ve eksik NOAA metadata'sı uyuşmazlığı çözmez.
Çelişkili on tahmin etiketi korundu.

### 9529: HARP 4941 daha güçlü kaynak desteğine sahip

[18 Aralık NOAA raporu][dec-events], M6.9 olayını (21:41–22:25 UTC,
zirve 21:58) ve radyo/optik kayıtlarını 2241 bölgesine atar.
Optik konum S11E15. Başlangıç **B2217**, tam 22:17 değil 22:17'den önce
demektir; ayrıştırıcı bu niteleyiciyi korur.

Resmî [HARP/NOAA tablosu][harp-table] ve HARP başına beş SHARP kaydı:

| HARP | NOAA_ARS | Sorgulanan kayıtlarda NOAA_AR |
| --- | --- | --- |
| 4941 | 12241 | 12241 |
| 4920 | 12235, 12237, 12238, 12242 | 12242 |

18/2400 UTC için geçerli [19 Aralık özeti][dec-srs], 2241'i (S09E04)
2242'den (S18W16) ayırır. Bunlar bağlam konumlarıdır, zirve koordinatları değildir.

Çift konum ilişkisinin olası geometrik açıklaması da var. Birleşik katalog
bu olayda fl_lon, fl_lat için (−5.1917867, −9), goes_location için (0, 0)
kullanıyor. 21:48 TAI'de JSOC kutuları:

| HARP | Boylam sınırları | Enlem sınırları | Katalog noktası sınırların içinde |
| --- | --- | --- | --- |
| 4920 | −6.855653 to 60.014801 | −32.148258 to −2.606695 | Evet |
| 4941 | −19.317751 to 1.365474 | −15.254949 to −5.500595 | Evet |

**Yorum:** örtüşen kutular iki fiziksel kaynak gerektirmeden iki-HARP
ilişkisini açıklayabilir. Bölge numarası HARP 4941'i destekliyor.
Bu hâlâ aday ilişkidir; elle doğrulanmış uzamsal kimlik değildir.
Duyarlılık çalışmasının belirsizlik dışlaması ve özgün etiketler değiştirilmedi.

## Kaynak sınırlamaları ve koruma

NOAA [olay biçimi belgesi][event-format], bunları hata veya eksiklik
içerebilen düzenlenmiş ön raporlar olarak tanımlar. Optik bölge numaraları
gözlemevinden, X-ışını atamaları SWPC personelinden gelir. Ortak günlük olay
numarası tahmincinin gruplamasıdır; bağımsız fiziksel kaynak garantisi değildir.

12 küçük kaynak dosyası 2026-10-15 UTC'de (İstanbul'da 16 Ekim) indirildi:
üç olay listesi, üç bölge özeti, NOAA biçim belgesi, HARP tablosu ve dört JSOC
yanıtı. NOAA doğrulanmış HTTPS kullanır. JSOC HTTPS sertifika doğrulaması
başarısız oldu; yayınlanan HTTP uç noktası metadata sağladı. Bu sınırlama
manifestte kayıtlı. TLS kontrolleri kapatılmadı; HTTP yanıtlarının taşıma
katmanında doğrulandığı söylenemez. SHA-256 baytları korur, yayıncıyı doğrulamaz.

HARP tablosu güncel yaşam boyu ilişki özetidir, tarihsel anlık kopya değildir.
JSOC zamanları açıkça TAI, NOAA zamanları UTC. Eşzamanlı karşılaştırma,
TAI–UTC dönüşümü veya koordinat taşıması yapılmadı. SDO/AIA görüntü incelemesi
henüz olayları karara bağlamadı. Makine raporu kararı çözümsüz bırakır;
9529'un daha güçlü aday desteği bu belgenin yorumudur.

## Kanıt incelemesini yeniden üretme

```sh
python scripts/fetch_source_review.py
python scripts/review_event_sources.py
```

İndirme istek başına 1 MB ve 25 saniye ile sınırlıdır; URL, indirme zamanı,
özet, taşıma ve hatalar `data/source_review/manifest.json` içine kaydedilir.
İki komut mevcut dizinin üzerine yazmaz. İnceleme kaynak/duyarlılık raporları
ve indirilen özetleri doğrular; üç vaka özetini, NOAA satır ve konumlarını,
JSOC anahtarlarını, özgün anotasyonları ve protokolü `artifacts/source_review/`
içine yazar. Ham veri ve üretilen çıktılar Git dışında kalır.

Mevcut benchmark korunmalı, vakalar ilişkilendirme belirsizliği olarak
raporlanmalıdır. Yeni eğitim etiketlerinden önce açık koordinat çerçevesi ve
zaman ölçekleriyle uzamsal kanıt incelenmeli; kabul edilen kararlar ayrı
sürümlü etiket kümesi oluşturmalıdır. Yalnızca bu inceleme yeniden eğitimi gerektirmez.

[aug-events]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/08/20140821events.txt
[sep-events]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/09/20140903events.txt
[dec-events]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2014/12/20141218events.txt
[aug-srs]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries/2014/08/20140822SRS.txt
[sep-srs]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries/2014/09/20140904SRS.txt
[dec-srs]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries/2014/12/20141219SRS.txt
[harp-table]: http://jsoc.stanford.edu/doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt
[event-format]: https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/docs/SolarEventReport.pdf
