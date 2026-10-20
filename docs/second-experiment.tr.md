# Deney 2: tam veri ve kalibrasyon incelemesi

Tam veri deneyi tamamlandı. Kalibrasyon olasılık skorlarını biraz iyileştirdi;
ancak eşleştirilmiş belirsizlik aralığı belirgin bir kazanımı doğrulamıyor.
Yanlış alarmlar önemli bir sınırlama olmaya devam ediyor. Dashboard modeli değiştirilmedi.

## Protokol ve kapsam

[Protokol](second-experiment-protocol.md) sonuçlar incelenmeden önce commitlendi.
Beş resmî arşivin tamamı yayımlanmış MD5 değerleriyle kontrol edildi.
331,185 pencerenin 2,284'ü mevcut ölçüm kalitesi kuralını geçemedi.
Zaman sınırlarında ayrıca 2,279 pencere çıkarıldı. Bundan sonra ortak HARP
veya yinelenen kayıt çıkarmak gerekmedi.

| Rol | Bölümler | Kalan pencereler | M/X pencereleri | HARPs |
| --- | --- | ---: | ---: | ---: |
| Eğitim | 1, 2 | 159,247 | 2,522 | 1,569 |
| Kalibrasyon | 3 | 41,470 | 1,322 | 384 |
| Eşik doğrulama | 4 | 50,631 | 1,076 | 470 |
| Geriye dönük inceleme | 5 | 75,274 | 990 | 753 |

Bölüm 5 ilk deneyde incelenmişti. Bu sonuçlar geriye dönük incelemedir;
**yeni, dokunulmamış bir final test değildir**. Sabit XGBoost ayarları
yeniden kullanıldı. Kalibrasyon yalnızca bölüm 3'te, log odds üzerine pozitif
eğimli sigmoid uydurur. Bölüm 4 olasılık sürümünü ve çalışma eşiklerini seçer.
Kararlar bölüm 5 tahminleri üretilmeden önce kaydedildi.

## Olasılık kalibrasyonu

| Model | Doğrulama Brier | İnceleme Brier | İnceleme log loss |
| --- | ---: | ---: | ---: |
| Dondurulmuş örneklem modeli | 0.015489 | 0.009569 | 0.034322 |
| Tam veri ham model | 0.014855 | 0.009450 | 0.033363 |
| Tam veri kalibre model | 0.014832 | 0.009337 | 0.033344 |

Doğrulama Brier skoru kalibre olasılıkları seçti. İnceleme döneminde kalibre
eksi ham Brier farkı **−0.000113**; %95 HARP kümeli bootstrap aralığı
**[−0.000628, +0.000332]** oldu. Aralık sıfırı geçtiği için küçük nokta
iyileşmesi güvenilir bir kazanım olarak sunulmamalıdır.

Brier kalibrasyon, ayırt etme ve sonuç belirsizliğini birlikte yansıtır;
saf kalibrasyon ölçüsü değildir. Yerel rapor güvenilirlik grafikleri ve grup
sayılarını içerir. Yüksek olasılık gruplarında az gözlem olduğundan yorum sınırlıdır.

## Yakalama ve yanlış alarmlar

Aşağıdaki hedefler doğrulama verisinde seçildi; inceleme döneminin recall
değerinin hedefe eşit olması garanti değildir. Eşikler kalibre olasılıklara aittir.

| Doğrulama recall hedefi | Eşik | İnceleme recall | İnceleme precision | Yanlış alarmlar | Kaçırmalar |
| --- | ---: | ---: | ---: | ---: | ---: |
| 80% | 6.8845% | 87.17% | 22.59% | 2,958 | 127 |
| 90% | 4.7999% | 90.61% | 19.00% | 3,824 | 93 |
| 95% | 3.4028% | 91.82% | 16.27% | 4,678 | 81 |

%90 hedefinde özgün dondurulmuş model %89.60 recall ve 3,933 yanlış alarm,
tam veri modeli %90.61 recall ve 3,824 yanlış alarm verdi.
Bu betimsel karşılaştırma genel iyileşmeyi kanıtlamaz. %95 hedefinde özgün
modelin recall'ı daha yüksek (%93.84), yanlış alarmı da daha fazlaydı (5,738).
Her koşulda üstün bir çalışma noktası yoktur.

Ham ve kalibre tam veri modelleri karşılık gelen recall hedeflerinde aynı
alarmları üretti. Monoton dönüşüm olasılıkların yorumunu değiştirir,
pencerelerin sıralamasını değiştirmez.

%90 hedefinde bütün HARP'ları örnekleyen %95 aralıklar:

- Recall: **%80.09–96.65**.
- Precision: **%11.86–27.30**.
- Yanlış pozitif oranı: **%3.66–6.82**.

Bu noktada alarmların yaklaşık %81'i yanlıştı. Sistem araştırma prototipidir;
bu inceleme canlı uyarıları açmayı gerekçelendirmez.

## Yeniden üretim ve sınırlamalar

Komutlar [README](../README.md#experiment-2-full-data-calibration) içindedir.
Git dışında tutulan `artifacts/experiment2/report.html` grafikler, tüm metrikler,
kalibrasyon grup sayıları ve bootstrap aralıklarını içerir. CSV/JSON çıktıları
girdi özetlerini, arşiv sağlama toplamlarını, kalibrasyon parametrelerini,
eşikleri, paket sürümlerini ve kaynak kod özetlerini saklar.
İlk deney dosyaları dondurulmuş kopyayla bayt düzeyinde aynıdır.

Bootstrap bütün HARP bölgelerini 24 tohumu ile 1,000 kez yeniden örnekler.
Aralıklar eğitilmiş model ve sabit eşik koşulundadır; eğitim belirsizliğini,
bölgeler arası bağımlılığı veya gelecek güneş döngüsü değişimlerini kapsamaz.
Sayılar benzersiz patlamalar değil tahmin pencereleridir. Tam veri eğitimi
eğitim dönemini de uzatır; örneklem büyüklüğünün etkisini tek başına ayırmaz.

Sonraki modelleme deneyi, eğitimden önce sabitlenmiş tasarımla ayırt etme
başarısını hedeflemelidir. Bu inceleme dönemine tekrar tekrar ayar yapmak,
yeni bir final değerlendirme iddiasını geçersiz kılar. Böyle bir iddia için
incelenmemiş daha sonraki dönem verisi gerekir.
