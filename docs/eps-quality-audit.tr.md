# EPS ve kalite uyumluluğu incelemesi

Tarih: 2026-10-23. **Karar: V2 model bağlantısı için henüz hazır değil.**
EPS uygulaması artık belirlendi; kalite kapsamı beş tekil başlıktan aynı beş
2011 penceresinin 300 zaman noktasına genişledi. Eğitim, etiket değişikliği
veya gelecek dönem değerlendirmesi yapılmadı.

## Sabitlenen kaynak ve EPS mekanizması

[Resmî kurulum belgesi](https://dmlab.cs.gsu.edu/docs/spaceweather_toolkit/TEST_BUILD.html)
[kütüphane deposuna](https://bitbucket.org/gsudmlab/spaceweather_toolkit/) bağlanıyor.
2026-10-07 tarihli `9f6e805d19077ab44d0ed8d2b546f207a8f155f7` commit'inin
`py_src/swdatatoolkit/magparam/_lorentz_calculator.py` dosyası incelendi.
Gerçek sınıf adı `LorentzCalculator`; önceki rapordaki `LorentzForceCalculator`
adı ayrı bir uygulama değil, adlandırma hatası olarak okunmalıdır.

Kod kuvvet toplamlarını piksel alanı `dA` ile çarpıyor; `TOTBSQ` ise bu alan
çarpanı olmadan alan bileşenlerinin kareleri toplamı. Ardından
`EPSX=TOTFX/TOTBSQ` ve Y/Z karşılıklarını hesaplıyor. Dolayısıyla alan
çarpanı EPS içinde kalıyor. Bu, önceki örtüşme incelemesinin kuvvet/TOTBSQ
ilişkileriyle tutarlı; fakat indirilen V2 arşivini bu commit'in ürettiğini
kanıtlamaz. Paket metadata'sındaki `0.0.1` tek başına üretim sürümünü belirleyemez.

Tanı deneyi, paketi kurmadan yalnızca incelenmiş modülü çağırıyor. Tek piksellik
`(3, 4, 5)` alanı ve sıfır belirsizlikleri sabit tutarak piksel ölçeğini
`0.5` değerinden `1.0` değerine çıkarıyor. Sentetik hesap yalnızca yazılım
davranışını sınar; Güneş eğitimi veya değerlendirme verisi değildir.

| Büyüklük | Piksel ölçeği iki katına çıkınca oran |
| --- | ---: |
| TOTBSQ | 1 |
| TOTFX | 4 |
| TOTFY | 4 |
| EPSX | 4 |
| EPSY | 4 |

Bu özel alanda EPSZ sıfırdır; oranı tanımsız olduğundan kanıt olarak
kullanılmadı. Bu uygulamanın EPS değeri alana bağlıdır; eski boyutsuz EPS
gibi sessizce kullanılamaz. Kaynak veriye, özellik tablolarına, modellere
veya üst kaynak koduna dönüşüm veya düzeltme uygulanmadı.

## Kalite kapsamı ve etkisi

Yeni bölgeler seçmek yerine aynı beş sabit 12 saatlik pencere sorgulandı.
V2 okuması yalnızca kimlik, zaman ve 24 ağırlıksız manyetik girdiyi, 2019
öncesi filtresiyle açıyor. Tarihsel kaynak özetleri doğrulanıyor.

| HARP | Beklenen | JSOC kalite kaydı | Eşit bilinen eski kalite | Eski kalite + IS_TMFI geçen | JSOC QUALITY=0 | V2 tamamı sonlu | V2 sonlu ama JSOC kalitesi reddedilen |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 334 | 60 | 60 | 60 | 56 | 56 | 60 | 4 |
| 344 | 60 | 60 | 56 | 55 | 58 | 56 | 1 |
| 356 | 60 | 60 | 60 | 58 | 58 | 60 | 2 |
| 359 | 60 | 60 | 60 | 56 | 56 | 60 | 4 |
| 372 | 60 | 60 | 60 | 57 | 57 | 60 | 3 |
| Toplam | 300 | 300 | 296 | 282 | 285 | 296 | 14 |

Bilinen 296 eski QUALITY değerinin tamamı JSOC ile aynı. Diğer dört değer
çelişkili bayrak değil, eksik değer. HARP 344'te 2011-01-13 05:24, 05:36,
05:48 ve 06:00 zamanlarına aitler. İki veri sürümünde de manyetik değerler
eksik; JSOC şimdi üç sıfır kalite bayrağı ve bir `65536` sağlıyor.
İndirme zamanı/kaynak işleme farkları mümkün, fakat neden belirlenmedi.
Eksik eski alanlar otomatik doldurulmadı.

Yalnızca güncel JSOC QUALITY=0 kuralı 285 zaman noktasını kabul ediyor;
özgün QUALITY/IS_TMFI kuralında 282. Sonlu V2 ölçümleri de istenirse bu
örneklemde 282 kalıyor; bu örtüşme IS_TMFI'yi yeniden kurmaz veya başka
yerlerde eşdeğerliği kanıtlamaz. Sonlu 14 V2 satırı hem kaynak kalite
kuralını hem eski kuralı geçemiyor. Dolayısıyla sonluluk kalite maskesi değildir.
Manyetik hesap içindeki piksel maskesi de kayıt düzeyindeki QUALITY ve
veri setinin IS_TMFI bayrağından farklıdır.

## Zaman ve aktarım sınırlamaları

300 kayıtlı saat dizgesinin tamamı, açıkça TAI olarak sorgulandığında JSOC
T_REC ile eşleşiyor. T_REC eksi T_OBS 6–8 saniye. Ayrıştırma TAI yorumunu
hipotez olarak koruyor; UTC dönüşümü yapmıyor. Saat dilimi olmayan V2 zamanı
hâlâ zaman ölçeğini veya gözlemin kullanılabilirliğini belgelemez. Bu incelemeye
dayanarak geçmiş tahmin zamanları kaydırılmadı.

Bu çalıştırmada HTTPS istekleri zaman aşımına uğradı; yayınlanan HTTP uç
noktası kayıtları döndürdü. TLS doğrulaması kapatılmadı. HTTP doğrulanmış
taşıma değildir; özetler indirilen baytları korur, yayıncı kimliğini doğrulamaz.
İstek URL'leri, zamanları, başarısızlıkları ve özetleri yerelde saklandı.

## Yeniden üretim ve kalan koşullar

```sh
git clone https://bitbucket.org/gsudmlab/spaceweather_toolkit.git data/toolkit_source
git -C data/toolkit_source checkout 9f6e805d19077ab44d0ed8d2b546f207a8f155f7
python scripts/fetch_quality_sources.py
python scripts/audit_eps_quality.py
python scripts/publish_reports.py --output artifacts/bilingual_reports_eps_quality
```

Mevcut kaynak/çıktı dizinleri korunur. Denetim farklı üst kaynak commit'ini
veya yerelde değiştirilmiş hesaplayıcıyı reddeder. `artifacts/eps_quality_audit/`
içinde `report.json`, `summary.csv` ve 300 hizalanmış kalite satırını içeren
`aligned_quality.csv` bulunur. Ham başlıklar ve kaynak kopyası Git dışında
`data/` altında kalır; manifest kaynak/kod/çıktı özetlerini kaydeder.

Kalan işler: gerçek V2 üretim commit'ini ve EPS tanımını doğrulamak, üretimdeki
zaman dönüşümünü belgelemek, IS_TMFI'yi yeniden kurmak veya ayrı sürümlü bir
kalite politikasını tanımlayıp değerlendirmek. Yeni eğitimden önce etiket
dahil etme ve zaman bölümleme kuralları da sabitlenmelidir. 2024–2025 ayrılmış
test dönemi açılmadı; recall hedefi en az %95 olarak kalıyor.
