# Helio24: V2 precision geliştirme sonuçları

Değerlendirme tarihi: 2026-10-26. Seçilen geliştirme adayı, %45 lojistik
regresyon ve %55 XGBoost olasılıklarının sabit karışımı olan **ensemble**
modelidir. Recall >= 0.95 koşulundaki çalışma noktasında doğrulama precision'ı,
tek başına XGBoost sonucundaki 0.061597 değerinden 0.079622 değerine yükseldi.
Recall 0.950064 düzeyinde kalırken yanlış pozitif pencereler 11.304'ten 8.577'ye
indi.

Bu bir geliştirme sonucudur; bağımsız test sonucu değildir. Ayrılmış 2024–2025
test verisi materyalleştirilmedi, tahmin edilmedi veya incelenmedi.

## Veri ve seçim protokolü

Model 96 nedensel özellik kullanır: tahminden önceki 12 saatte bulunan 24 veri
seti yerel manyetik ölçümünün ortalaması, popülasyon standart sapması, son
değeri ve sondan-başa farkı. Hedef, `[forecast_time, forecast_time + 24h)`
aralığındaki M veya X sınıfı GOES patlama tepe noktasıdır.

| Rol | Dönem | Satır | Pozitif pencere | HARP |
| --- | --- | ---: | ---: | ---: |
| Eğitim | 2010-05-01–2021-12-31 | 484549 | 8698 | 3954 |
| Kalibrasyon | 2022-01-01–2022-12-31 | 50756 | 421 | 528 |
| Doğrulama | 2023-01-01–2023-12-31 | 60366 | 781 | 703 |

Materyalleştirme, bir HARP'a atanamayan büyük bir HEK olayıyla örtüşen 81.613
pencereyi ve 24 belirsiz pencereyi dışladı. Eksik değer doldurma, ölçekleme ve
model eğitimi yalnızca eğitim verisini kullandı. Sigmoid olasılık kalibrasyonu
ve karışım ağırlığı araması kalibrasyon rolünü kullandı. Karışım araması,
lojistik regresyon ağırlıklarını 0.05 adımlarla 0.00–1.00 arasında değerlendirdi
ve recall >= 0.95 düzeyindeki en yüksek precision ile 0.45'i seçti. Son alarm
eşiği, recall >= 0.95 koşulunu sağlayan adaylar arasında önce en yüksek
precision, sonra en az yanlış pozitif kuralıyla doğrulama üzerinde seçildi.

## Doğrulama metrikleri

| Model | Recall | Precision | TP | FP | FN | TN | FPR | FAR | Accuracy | Balanced accuracy | F1 | TSS | AP | Brier | Log loss | Eşik |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 1.000000 | 0.012938 | 781 | 59585 | 0 | 0 | 1.000000 | 0.987062 | 0.012938 | 0.500000 | 0.025545 | 0.000000 | 0.012938 | 0.012795 | 0.069891 | 0.017951 |
| Logistic | 0.950064 | 0.060052 | 742 | 11614 | 39 | 47971 | 0.194915 | 0.939948 | 0.806961 | 0.877575 | 0.112963 | 0.755149 | 0.216153 | 0.011315 | 0.045501 | 0.005988 |
| XGBoost | 0.950064 | 0.061597 | 742 | 11304 | 39 | 48281 | 0.189712 | 0.938403 | 0.812096 | 0.880176 | 0.115693 | 0.760352 | 0.206027 | 0.011386 | 0.045217 | 0.004231 |
| Ensemble | 0.950064 | 0.079622 | 742 | 8577 | 39 | 51008 | 0.143946 | 0.920378 | 0.857271 | 0.903059 | 0.146931 | 0.806118 | 0.220619 | 0.011195 | 0.043996 | 0.009311 |

Ensemble modeli her 100 alarmın yaklaşık 8'inde doğru sonuç üretir. Doğrulama
pencerelerinin yalnızca %1,29'u pozitif olduğu için precision mutlak anlamda
hâlâ düşüktür. Aynı satırlarda ve aynı recall düzeyinde XGBoost ile
karşılaştırıldığında ensemble, precision'ı 0.018025 veya göreli olarak %29,26
artırır ve 2.727 yanlış pozitif pencereyi kaldırır; bu %24,12 azalmadır. AP,
Brier skoru, log loss, F1, TSS ve balanced accuracy de iyileşir.

Önceki V1 geliştirme sonucunda 0.950743 recall düzeyinde precision 0.164840 idi.
Bu yalnızca tarihsel bağlamdır: V1 ve V2 farklı arşivler, etiket kapsamı,
dışlama kuralları, zaman popülasyonları ve özellik hesapları kullanır. V2
ensemble modelinin ölçülmüş belirli bir miktarda gerilediğine kanıt sayılamaz.

## Kriterler ve yorum

| Ölçüm | Geliştirme kriteri | Ensemble sonucu | Karar |
| --- | --- | ---: | --- |
| Recall | >= 0.950000 | 0.950064 | Karşılandı |
| Precision | XGBoost 0.061597 değerinden yüksek | 0.079622 | Karşılandı |
| Yanlış pozitif pencere | <= 10174 (11304 değerinden %10 düşük) | 8577 | Karşılandı |
| AP | >= XGBoost 0.206027 | 0.220619 | Karşılandı |
| Brier | <= XGBoost 0.011386 | 0.011195 | Karşılandı |
| Log loss | <= XGBoost 0.045217 | 0.043996 | Karşılandı |

Precision, alarmların ne kadarının doğru olduğunu gösterir. Recall, pozitif
pencerelerin ne kadarının yakalandığını gösterir. FPR, negatif pencerelerin ne
kadarında alarm verildiğini; FAR ise alarmların ne kadarının yanlış olduğunu
gösterir. AP, sıralama başarısını bütün eşiklerde değerlendirir. Brier skoru ve
log loss olasılık hatasını ölçer; düşük değer daha iyidir. Balanced accuracy,
pozitif ve negatif sınıf recall değerlerinin ortalamasıdır. TSS, recall ile FPR
arasındaki farktır. Normal accuracy raporlanmıştır ancak birincil kriter
değildir: her zaman “patlama yok” diyen bir yöntem bu dengesiz doğrulama
kümesinde 0.987062 accuracy elde ederken hiçbir pozitif pencereyi yakalayamaz.

Güneş patlaması uyarıları için evrensel kabul edilebilir bir precision eşiği
yoktur. Operasyonel değer, kaçırılan bir patlamanın ve yanlış alarm üzerine
hareket etmenin maliyetine bağlıdır. 0.079622 sonucu dondurulmuş karşılaştırmalı
geliştirme kriterlerini karşılar; fakat operasyonel hazırlık iddiası için hâlâ
çok düşüktür.

## Reddedilen precision deneyleri

Altı XGBoost yapılandırması kalibrasyon üzerinde karşılaştırıldı.
`positive_weight`, 0.067306 kalibrasyon precision değeriyle bu aramayı kazandı;
fakat doğrulamada 11.851 yanlış pozitif ve 0.171683 AP ile 0.058922 precision'a
düştü. Bu nedenle reddedildi. Bu olumsuz sonuç, sınıf ağırlığının ve ağaç
karmaşıklığının sonraki yıla güvenilir biçimde aktarılmadığını gösterir.

| Aday | Kalibrasyon precision | Kalibrasyon FP | Kalibrasyon AP |
| --- | ---: | ---: | ---: |
| control | 0.058746 | 6409 | 0.230126 |
| shallow | 0.062824 | 5967 | 0.225990 |
| depth4 | 0.066500 | 5615 | 0.161133 |
| regularized | 0.060809 | 6178 | 0.189601 |
| positive_weight | 0.067306 | 5543 | 0.179510 |
| region_weight | 0.065115 | 5743 | 0.164416 |

Olasılık stacking, logit stacking ve sıra ortalaması da denendi; doğrulama
precision'ında sabit 0.45/0.55 olasılık karışımını geçemedi. Bu yöntemler
dondurulmuş protokole alınmadı.

## Sınırlamalar ve belirsizlik

- Ensemble adayı eklenmeden önce bağımsız modellerin ilk sonuçları doğrulama
  üzerinde incelendi. Ağırlığı yalnızca kalibrasyonda seçilmiş olsa da bu durum
  daha geniş geliştirme sürecini uyarlamalı hâle getirir.
- Eşik bilinçli olarak doğrulama üzerinde seçildi. Bu sayılar seçilen geliştirme
  çalışma noktasını değerlendirir; dokunulmamış bir genelleme tahmini değildir.
- Bu revizyonda güven aralığı raporlanmaz. Örtüşen pencereler HARP bölgeleri
  içinde bağımlıdır; sıradan satır bootstrap yanıltıcı olur. Gelecekteki bir
  aralık bütün HARP'ları yeniden örneklemelidir.
- TP, FP ve FN bağımsız patlamaları veya operasyonel alarm olaylarını değil,
  örtüşen tahmin pencerelerini sayar. Pencere recall'u olay recall'una eşit değildir.
- V2 arşivini üreten kesin upstream Git revizyonu mevcut değildir. Ayrı denetlenen
  sözleşme veri seti yerel modellemeyi destekler; ham manyetogramdan tam yeniden
  üretilebilirlik sağlamaz.
- Sonuç Dünya etkisini, uydu hasarını veya patlamanın kesin saatini tahmin etmez.
  Canlı veri uyumluluğu henüz doğrulanmamıştır.

## Yeniden üretim ve dondurulmuş kanıt

```sh
.venv/bin/python scripts/run_v2_development.py \
  --materialized artifacts/v2_development_features_20261025_r2 \
  --protocol config/experiment5-v7.json \
  --output artifacts/experiment5_v2_development_20261026_r2
.venv/bin/python scripts/publish_reports.py \
  --output artifacts/bilingual_reports_v2_precision_20261026
```

Seçilen yapılandırma ve çalışma noktası `config/experiment5-v8.json` içinde
dondurulmuştur. Yerel geliştirme raporunun SHA-256 özeti
`b57ce8e12de3d18740872b1504f97ff6a9dee22b272143836bb1a739d155ef03`;
tahminlerin SHA-256 özeti
`44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff`
değeridir. Reddedilen ağaç deneyi raporunun SHA-256 özeti
`0540f797dd44795a14e19557346d2563b29bb76582b605163d1171d4db3efd01`
değeridir. Modeller, tahminler, veri setleri ve üretilen HTML dosyaları yerel,
yok sayılan artifact olarak kalır. Sürüm kontrolündeki protokoller, kod ve iki
dilli rapor gözden geçirilebilir kaydı oluşturur.
