# Uzun geçmişli precision deneyi: hazırlık ve depolama engeli

## Durum

Yeni model henüz eğitilmedi. Doğrulama precision değeri **%7.9622**, recall değeri **%95.0064** olarak kaldı: 60366 pencerede 742 doğru pozitif, 8577 yanlış pozitif, 39 yanlış negatif ve 51008 doğru negatif. Bunlar dondurulmuş mevcut modelin sonuçlarıdır; yeni özelliklerin sonuçları değildir. Recall >= %95 korunurken precision artırılması, garanti edilmiş bir sonuç değil, araştırma hedefidir.

## Uygulanan değişiklik

Yeni özellik çıkarıcı, sonuç etiketlerine göre filtrelemeden bağımsız olarak her tahminden önceki ham manyetik gözlemleri kullanır. Mevcut 96 özelliğe 196 özellik ekler: 24 ölçümün hem 24 hem 48 saatlik ortalaması, popülasyon standart sapması, uç noktalar arasındaki değişimi ve normalize edilmiş değişimi; ayrıca kullanılabilirlik ve eksik değer oranı göstergeleri. Tam geçmiş, 12 dakika aralıklı 120 veya 240 gözlem gerektirir. Normalize edilmiş değişim, uç noktalar arasındaki farkı mutlak ortalama ile standart sapmanın toplamına böler ve [-100, 100] aralığına kırpar. Payda sıfırsa sonuç eksik değerdir.

Tahmin anındaki ve sonrasındaki gözlemler dışlanır. Veri bölümünün başlangıç sınırını, gözlem aralığı boşluğunu veya artık saniye geçişini aşan geçmişler kullanılamaz. Her ölçüm için en az %80 sonlu değer gerekir; aksi durumda istatistikleri eksik bırakılır. Kullanılabilirlik, zamansal kapsamı belirtir; cihaz kalitesinin garantisi değildir. Eksik geçmişi olan tahmin satırları, eksik özellikler ve kullanılabilirlik göstergesiyle korunur. Böylece yalnızca zor tahminleri çıkararak precision artırılması önlenir.

## Yerel doğrulama

Önceki denetimin özet değerleri doğrulanmış veri kopyaları kullanıldı. Uygun her USFLUX ortalaması doğrudan ham zaman aralığı hesabıyla karşılaştırıldı; hedef etiketlerini değiştirmek özellikleri değiştirmedi.

| HARP | Korunan pencereler | Kullanılabilir 24 saatlik geçmişler | Kullanılabilir 48 saatlik geçmişler |
| --- | ---: | ---: | ---: |
| 9152 | 106 | 106 | 86 |
| 9584 | 151 | 144 | 127 |
| Toplam | 257 | 250 | 213 |

Bu, önceden seçilmiş iki bölge üzerinde bir uygulama kontrolüdür; temsili bir performans tahmini değildir. Eklenen özelliklerin precision artırdığını göstermez. Girdi ve kod özetleri dahil kanıtlar yerel `artifacts/long_history_readiness_20261028/report.json` dosyasında tutulur. Kontroller, HARP 9584 için önceki olay ilişkilendirmesi belirsizliğini çözmez.

## Tam veri engeli ve sonraki deney

İlk tam veri hazırlığı girişimi, `artifacts/long_history_20261028_r1`, arşiv indirilirken `ENOSPC` hatasıyla durdu. Geçici indirmeler temizlendi; mevcut veri setleri ve deney kanıtları korundu. Hazırlık kaydı, ihtiyatlı gereksinim olan 5368709120 bayta (5 GiB) karşılık 215805952 bayt boş alan gösterdi. İndirmeler artık varsayılan olarak sırayla çalışıyor, başlamadan boş alanı kontrol ediyor ve disk doluluğu hatalarında tekrar denemiyor. Alan tahminleri ön kontroldür; sonraki her eğitim adımının sığacağına dair garanti değildir.

Hedeflenen 595671 geliştirme penceresinin tam özellik hazırlığı **tamamlanmadı**. Depolama alanı sağlandığında yeni bir çıktı dizini kullanılmalı ve tahmin anahtarlarının birebir eşleştiği doğrulanmalıdır. Eğitimden önce gerçek geçmiş raporu özetiyle yeni protokol sürümü dondurulmalıdır; `config/precision-long-history-v1.json` dosyasının özeti bilinçli olarak beklemededir ve dosya çalıştırılmaya hazır değildir.

Dondurulmuş arama bütçesi üç aday (`history_logistic`, `history_xgboost`, `history_hist`) ve dört yeni model karışım ağırlığı (0.25, 0.5, 0.75, 1.0) içerir. Seçim, recall >= 0.95 koşulunda kalibrasyon precision değerini; eşitlik durumunda AP değerini kullanır. Yeni modelin kabulü için recall >= 0.95 koşulunda doğrulama precision değerinin artması, AP değerinin düşmemesi ve Brier skoru ile log loss değerlerinin artmaması gerekir. Ayrılmış 2024–2025 testi kullanılmaz. Tekrarlanan geliştirme karşılaştırmaları doğrulama verisine aşırı uyum sağlayabilir; başarılı bir geliştirme karşılaştırması tek başına genellenebilirliği kanıtlamaz.

## Yeniden üretim

Depo kökünde, mevcut özet değerleri doğrulanmış denetim verileri ve Python ortamıyla:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_long_history_readiness.py
# After freeing at least 5 GiB:
.venv/bin/python scripts/materialize_long_history.py --output artifacts/long_history_20261028_r2 --workers 1
```

Hazırlık kontrol betiği mevcut çıktının üzerine yazmayı reddeder. Yeni çalıştırmada özgün kanıtı koruyarak betikteki çıktı yolunu yeni bir sürüme değiştirin; bunun sonucunda kod özeti de değişir. Tam veri hazırlığı komutu, tamamlanmış bir sonuç değil, bekleyen sonraki adımdır. Doğrulanmış hazırlık özeti yeni protokol sürümünde dondurulana kadar eğitim komutu verilmez. Üretilen çıktılar ve ham veriler Git dışında kalır.
