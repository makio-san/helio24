# Deney 5: sonraki dönem değerlendirme protokolü

Tasarım tarihi: 2026-10-23. Durum: **tasarım sabit; tamamlanmamış veri
sözleşmesi yürütmeyi engelliyor**. Yeni performans sonucu içermez.
Makinece okunabilir karşılığı `config/experiment5.json`. Değişiklikler eğitimden
önce yeni sürüm ve açıklama gerektirir; test sonrası sessiz değişiklik yapılamaz.

## Tahmin sorusu ve kapsam

Önceki 12 saatin ölçümlerini kullanarak bir HARP için
`[forecast_time, forecast_time + 24h)` içinde en az bir M/X patlama zirvesi
olasılığını tahmin et. Bu mevcut zirve tabanlı benchmark hedefidir;
başlangıç zamanı, Dünya etkisi veya uydu hasarı tahmini iddiası değildir.
Bir HARP birden çok NOAA bölgesi içerebilir. Güvenilir olay kimliği ve kapsam
izin veriyorsa patlama başlangıcından önceki alarm oranını ayrıca raporla.
Pencere recall değerini olay recall değeri diye adlandırma.

## Sabit zaman tasarımı

Aşağıdaki sınırlar UTC; başlangıç dahil, bitiş hariçtir.

| Rol | Başlangıç | Bitiş | Amaç |
| --- | --- | --- | --- |
| train | 2010-05-01 00:00 | 2022-01-01 00:00 | Ön işleme ve model eğitimi |
| calibration | 2022-01-01 00:00 | 2023-01-01 00:00 | Olasılık kalibrasyonu |
| validation | 2023-01-01 00:00 | 2024-01-01 00:00 | Model ve eşik seçimi |
| test | 2024-01-01 00:00 | 2026-01-01 00:00 | Sabitlemeden sonra tek final değerlendirme |

Tahmin zamanına göre ata, sonra bütün gözlem ve hedef aralığı rolün içinde
kalan pencereleri tut. Hedef bitişi hariç olduğundan tam rol sınırında bitiş
kabul edilir. Önceki rolde tutulan HARP'ın sonraki rol satırlarını çıkar.
Yinelenen HARP/tahmin anahtarlarını reddet. Çıkarmaları, kalan bölgeleri,
sınıf sayılarını ve tarih kapsamını kaydet. Performans düşük diye kuralları
gevşetme veya tarihleri taşıma. Boş rol, eksik sınıf veya yetersiz kapsam
yürütmeyi durdurur; model skorlarından önce belgeli tasarım değişikliği gerektirir.

`development_split` yalnızca HARP ve zaman dilimi açık aralık metadata'sını
kabul eder; etiket/özellikleri ve ayrılmış test döneminin tahmin zamanlarını
reddeder. Dosya yüklemez. Çağıran kod filtreyi depolama okuyucusunda uygulamalı;
önce testi okuyup sonra atmamalıdır. Ayrı final-test çalıştırıcısı henüz
uygulanıp incelenmelidir. Bu kontroller iş akışı kurallarıdır; doğrudan dosya
erişimine karşı güvenlik bariyeri değildir.

## Eğitimden önce yedi önkoşul

| Koşul | Güncel durum |
| --- | --- |
| measurement_semantics | pending |
| quality_policy | pending |
| utc_conversion | pending |
| label_inclusion_policy | pending |
| versioned_dataset_manifest | pending |
| development_coverage_audit | pending |
| training_runner_review | pending |

Ölçüm kanıtı EPS dahil üretim sürümünü ve birim/formülleri belirlemeli.
Kalite politikası özgün bayrakları yeniden üretmeli veya eski geliştirme
verisinde ayrı sürümlü alternatifi tanımlayıp denetlemeli. UTC dönüşümü ve
aralık kuralları açık olmalı. Çözülmemiş olay kimlikleri sessizce negatif
örnek olmamalı: hedef üretiminden önce güven, belirsizlik ve dışlama kuralları
sabitlenmeli. Kesin V2 etiket sözleşmesi hâlâ bekliyor.

Veri manifesti dosyaları, özetleri, şemayı, özellik/etiket/kalite sürümlerini,
çıkarma kodunu ve ortamı sabitlemeli; final dönemin seçimi etkilemediğini
belgelemeli. Eğitimden önce geliştirme kapsamı denetlenmeli. Durum dizgeleri
inceleme beyanıdır, bilimsel geçerliliğin otomatik kanıtı değildir.
Kanıt kaydedilip incelenene kadar pending tutulmalı; `require_training_ready`
başarılı olmadan yürütme sözleşmesi de sabitlenmeli. Bu hazırlık adımında
protokole ait eğitim çalıştırıcısı teslim edilmiyor.

## Sabit aday bütçesi ve ön işleme

Hiperparametre araması olmadan yalnızca üç yöntem eğit:

| ID | Sabit tasarım |
| --- | --- |
| baseline | Eğitimdeki pozitif pencere oranını sabit verme |
| logistic | C=1.0, lbfgs, max_iter=2000, sınıf ağırlığı yok, seed=24 |
| xgboost | 200 ağaç, depth=3, learning_rate=0.04, min_child_weight=5, L2=5, gamma=0, pozitif ağırlık=1, subsample=1, sütun örnekleme=1, hist, threads=2, seed=24 |

Mevcut 24 ağırlıksız manyetik büyüklük için ortalama, standart sapma, son
değer ve değişim kullan: uyumluluk koşuluna bağlı 96 özellik. Tarihsel
çıkarma tanımını koru; ağırlıklı sütun koyma veya veriden EPS dönüşümü öğrenme.
Yalnızca tahmin öncesi ölçümler katkı yapmalı; sonraki gözlemlerden
interpolasyon yok. Önce sabit kalite politikasını uygula. Eksiklik göstergeli
medyan doldurma yalnız eğitimde öğrenilir. Lojistik regresyonun standart
ölçeklemesi de yalnız eğitimde öğrenilir; XGBoost ölçeklenmez.
Yakınsamama raporlanmış başarısızlıktır, uyarlamalı arama izni değildir.

Öğrenilen her model için kalibrasyon verisinde pozitif eğimli sigmoid eğit;
ham ve kalibre olasılıkları kaydet, seçimde kalibre skorları kullan.
Sabit referans kalibre edilmez. Doğrulama/test üzerinde erken durdurma yok.
Eşik seçiminden sonra kalibrasyon/doğrulamayı eğitime ekleyip yeniden eğitme.
V1 modelleri ancak köprü doğrulanırsa kullanılabilir; o zamana kadar tarihsel
referanstır. Farklı örneklemlerin sayılarını iyileşme kanıtı olarak karşılaştırma.

## Seçim, başarı koşulları ve final değerlendirme

Doğrulamada recall >=0.95 koşuluyla yanlış pozitifleri en aza indiren eşiği
seç; eşitlikte en yüksek eşiği kullan. 0.90 ve 0.99 noktalarını duyarlılık
olarak sakla; alternatif kazanan ölçütü yapma. Öğrenilen adayları FP artan,
AP azalan, Brier artan, ID sırasıyla sırala. Lojistik ancak FP daha az,
AP daha düşük değil, Brier/log loss daha yüksek değilse XGBoost kontrolünü
değiştirir. Aksi halde kontrol korunur. Kontrole göre %10 FP azaltma proje
iyileştirme hedefidir; evrensel bilimsel eşik değildir. İki öğrenilen modelden
hiçbiri doğrulamada eğitim-oranı referansını AP, Brier ve log loss açısından
geçemiyorsa başarısızlığı raporla ve final testi açma.

Final erişiminden önce seçilen model, kontrol, referans, ön işleme,
kalibratörler, eşikler, veri/protokol özetleri ve paket sürümlerini değişmez
karar manifestinde sabitle. Final çalıştırıcı sonuçları okumadan tek seferlik
değerlendirme kaydı ayırmalı; başarısız deneme daha iyi sonuç seçmek için
sessizce yinelenmek yerine kaydedilmeli. Teste göre özellik, etiket, model
veya eşik değiştirilemez. Test incelendikten sonraki yinelemeler yeni ayrılmış
dönem gerektirir veya geriye dönük olarak adlandırılmalıdır.

Aynı uygun test satırlarında seçilen model, kontrol ve referansı sabit
eşikleriyle raporla. Ana istek recall >=0.95; doğrulamada sağlanması bunu
garantilemez. FP sayısı, FPR, precision, FAR, accuracy, balanced accuracy,
F1, TSS, AP, Brier, log loss, karışıklık sayıları ve güvenilirlik gruplarını
raporla. Sağlanmayan hedefi açık göster. FP azalmasını gerçekleşen recall
ile birlikte karşılaştır; recall kaybı alarm kalitesi iyileşmesi değildir.
Aday iyileşmesi iddiası test recall en az %95, kontrole göre FP en az %10 az,
AP daha düşük değil ve Brier/log loss daha yüksek değil koşullarını gerektirir.
Kazanan olarak korunan kontrol kendisine karşı iyileşme iddia edemez.
Bunlar nokta tahminine dayalı proje koşullarıdır; anlamlılık testi değildir.

Sabit eşiklerde %95 aralık için 24 tohumu ile bütün HARP'ları 1,000 kez
bootstrap örnekle; eşleştirilmiş farklar aynı örneklenmiş bölgeleri kullanır.
Aralıklar eğitim/seçim belirsizliğini kapsamaz, güneş döngüsü dayanıklılığını
kanıtlamaz. Pencere ve uygun olay analizlerini ayrı raporla. Test otomatik
dashboard değişikliği veya canlı yayına geçiş başlatmaz.

## Hazırlık çıktıları ve yeniden üretim

```sh
python scripts/check_evaluation_protocol.py
python scripts/publish_reports.py --output artifacts/bilingual_reports_protocol5
```

Hazırlık kontrolü yalnız yapılandırmayı okur, kod/belge özetlerini
`artifacts/experiment5_preflight/` altında kaydeder; önkoşullar açıkken
çıkış kodu 2 verir. Mevcut dizin korunur; yeni sürüm için `--output` kullanılır.
Gözlem, etiket veya model tahmini okumaz. Yürütülebilir veri sözleşmesi
koşulları sağlanmadığından gerçek veri satır sayıları ve final test başarısı
bilinçli olarak raporlanmamıştır.
