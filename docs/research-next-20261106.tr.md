# Sonraki araştırma yönü ve teslim durumu

## Tamamlanan ürün çalışması

Experiment progress sekmesine son yıllık karşılaştırma, yıl seçimi, precision/recall/
yanlış alarm ve olasılık metrikleri, precision eğilimi, kabul sayımları, tüm metriklerin
CSV indirmesi ve iki tam rapor sürümü eklendi. Son raporun SHA256 değeri
`config/dashboard-comparison-v1.json` içinde sabitlendi; metrik ve karşılaştırma
dosyaları gösterilmeden önce doğrulanıyor. Eksik veya değişmiş kanıtta doğrulanmamış
puanlar yerine erişilemiyor mesajı gösteriliyor. Pozitif olay içermeyen 2018 döneminde
recall/AP'nin tanımsız olduğu açıkça belirtiliyor. Geçmişi tekrar oynatma değişmedi;
bu bir geliştirme karşılaştırmasıdır, canlı tahmin modeli veya bağımsız nihai test değildir.

Tamamlanan kronolojik TCN, altı pozitif yılın yalnızca birinde referans precision
sonucunu geçiyor; tam karşılaştırmayı sıfır yılda sağlıyor. AP altı pozitif yılın tümünde,
Brier ve log loss uygun yedi yılın tümünde daha kötü. 2015'teki küçük precision
kazancının eşleştirilmiş belirsizlik aralığı sıfırı kapsıyor. Yeni model kabul edilmiyor.
Mevcut yanlış alarm analizi 2014–2016'da kalıcı bölgesel hataları yerelleştirmişti;
bu bulgu tüm yılların nedensel açıklaması olarak sunulmamalı.

## Seçilen yön

`config/research-direction-v2.json`, sabit özet özellikli topluluğa nedensel bölgesel
patlama geçmişi eklenmesini, önce kaynak uygunluğunu denetleyerek araştırmayı seçiyor.
Hipotez: tahmin anından önce bilinen aktivite, sürekli yüksek manyetik ölçümlerle
yaklaşan güçlü patlamaları ayırmaya yardımcı olabilir. Bu kanıtlanmadı; toplu metrik
başarısızlıkları, sebebin bu eksik özellikler olduğunu göstermez. Eski zaman serisi
yönü ve tüm dondurulmuş deneyler korunuyor.

Aday özellik kimlikleri: `count_C_24h`, `count_MX_24h`, `count_C_72h`,
`count_MX_72h`, `hours_since_C_capped_72`, `hours_since_MX_capped_72`,
`history_coverage_24h` ve `history_coverage_72h`. Olay bitişi, yayın ve bölge
eşleştirmesinin erişilebilirlik zamanlarının tümü tahminden kesinlikle önce olmalı.
Bilinmeyen geçmiş sessiz değil, eksik sayılmalı. Gelecekteki bölge sonuçları, sonradan
belirlenen bölge sıralamaları, geriye dönük eşleştirmeler ve erişilebilirlik kanıtı
olmayan revize kataloglar girdilere alınmıyor. Kapsama özellikleri tahmin anındaki
bilgi erişimini açıklamalı.

İlk geçiş koşulu, tüm gerekli yıllarda kaynak sürümleri, yayın zamanları ve o anda
bilinen bölge eşleştirmeleridir. `data/flare_catalog.csv` üzerinde yalnızca başlık
kontrolü yapıldı: olay zamanları ve bölge bilgisi mevcut, fakat yayın veya eşleştirme
erişilebilirlik zamanları yok. Alan adı dönüşümleri olay kimliğini, bitişi ve bölgeyi
eşleyebilir; erişilebilirlik kanıtı üretemez. Yerel denetim:
`artifacts/research_direction_20261106_r1/source-preflight.json`.
Bu başlık kontrolünde katalog satırları veya ayrılmış test okunmadı. Eğitime hazır değil.

Kaynak kökeni ve kapsama doğrulandıktan sonra yürütme protokolü tek bir genişletilmiş
topluluk yöntemini sabitleyecek; hiperparametre araması yapılmayacak. Bütçe: yedi
yıllık topluluk eğitimi, on dört bileşen kestirici eğitimi. Aynı tahmin anahtarları
üzerinde dondurulmuş 96 özellikli toplulukla karşılaştırılacak. Yıllık HARP ayrımı,
sınır örtüşmelerinin temizlenmesi, önceki yıl kalibrasyonunda recall >=0.95 hedefi,
pozitifsiz 2018 dahil uygun yedi yıl ve eşleştirilmiş HARP belirsizliği korunacak.
Altı pozitif yılın her birinde recall >=0.95 ile precision ve FP iyileşmeli; AP
düşmemeli, Brier/log loss artmamalı. Bunlar evrensel aralıklar değil, proje karşılaştırma
kurallarıdır. Önceden incelenen yıllar uyarlamalı geliştirme olarak kalır; ayrılmış
2024–2025 testi kapalı tutulur. Güvenilir kaynak erişilebilirliği belirlenemezse
tarihsel bilgiyi varsaymak yerine bu yön uygulanamaz olarak durdurulur. Daha fazla TCN
epoch'u, geniş model taramaları ve küçük ağırlık/kalibrasyon aramaları beklemede kalır.
Alarm bastırma, pencere precision iyileşmesi değildir.

## Kurtarma ve bağımsız yedek: bekleyen bağımlılıklar

Tarihsel `calibration_windows_20261030_r1/2019/predictions.parquet` henüz kurtarılmadı.
Time Machine yedeği veya yerel anlık görüntü listelenmedi. Safari'de
https://www.icloud.com/recovery/ açıldı, fakat sayfa otomasyonu içeriği okuyamadı:
Apple Events JavaScript kapalı ve erişilebilirlik sorgusu içerik döndürmedi. Tarayıcı
güvenlik ayarı değiştirilmedi; uzak dosya listesinin incelendiği iddia edilmiyor.
Kullanıcıdan Dosyaları Geri Yükle bölümünü kontrol edip yalnızca eşleşen tarihsel
dosyayı geri yüklemesi istendi. Kurtarılan her aday özgün kontrol raporundaki dosya
hash'iyle eşleşmeli. Apple, uygun silinmiş dosyalar için 30 gün içinde kurtarmayı
belgeliyor; bu, söz konusu dosyanın mevcut olduğunun kanıtı değil.
[Apple kurtarma talimatları](https://support.apple.com/en-asia/guide/icloud/mmae56ea1ca5/icloud).

Harici fiziksel disk listelenmedi; `/Volumes` yalnızca Macintosh HD içeriyordu.
503 dosyalık doğrulanmış yerel kopya mevcut, ancak aynı diskte.
`scripts/copy_evidence_backup.py` ikinci kopya adımını hazırlıyor: bağlı harici disk
zorunlu, kaynak ve kopya hash'leri doğrulanıyor, mevcut hedef reddediliyor, boş alan
kontrol ediliyor ve eksik dosya envanteri korunuyor. Harici yedek henüz oluşturulmadı.
Bağlı disk gerekiyor; ikinci bir dahili klasör bu adımı karşılamaz. Salt okunur yedek
dosyaları hâlâ silinebilir ve disk arızasına karşı koruma sağlamaz.

## Yeniden üretim

```sh
export PYTHONPYCACHEPREFIX=/tmp/helio24-pycache-20261106
PY='/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python'
"$PY" -m pytest tests/test_final_comparison.py tests/test_experiment_views.py tests/test_copy_evidence_backup.py tests/test_bilingual_reports.py -q -p no:cacheprovider
"$PY" scripts/publish_reports.py --output artifacts/bilingual_reports_20261106_r2
"$PY" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Gerçek harici disk bağlandıktan sonra aşağıdaki komutta gerçek disk adını ve yeni
bir hedefi kullanın. Komut diski biçimlendirmez veya silmez:

```sh
"$PY" scripts/copy_evidence_backup.py --source '/Users/esma/Library/Application Support/Helio24/backups/evidence-20261106-r1' --output '/Volumes/EXTERNAL_DISK/Helio24/evidence-20261106-r1'
```

İki rapor sürümünü gözden geçirin, katalogdaki kaynak hash'ini güncelleyin ve yeni
dizine yayımlayın. Veri setleri, modeller ve üretilen kanıtlar Git dışında kalır;
`app.py` içindeki yerel marka düzenlemeleri commit edilmez. Yeni eğitim veya metrik
kazancı iddia edilmiyor.
