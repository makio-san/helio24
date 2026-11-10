# SHARP Br haritası CNN özellikleri: veri edinimi ve sonuçlar (2026-11-10)

## Karar

Olumsuz sonuç. Günlük SHARP CEA radyal alan (Br) haritalarından küçük bir CNN'in öğrendiği skoru 96 manyetik özete
eklemek, proje çalışma noktasında (önceki yıl eşiği, pencere recall 0,90) precision'ı yükseltmiyor. Birincil aday
`image_lag24` birincil kabulü 6 yılın 1 tanesinde, `flag_lag24` 0 tanesinde, duyarlılık adayları `image_same`
ve `flag_same` ise 0 ve 0 tanesinde karşılıyor. Accuracy her adayda ve her yılda hep-negatif accuracy
değerinin altında kalıyor. Hiçbir model terfi ettirilmedi, hiçbir uyarı veya eşik değişmedi. Ayrılmış 2024–2025
testine erişilmedi. Edinim protokolü [`config/sharp-maps-v1.json`](../config/sharp-maps-v1.json) herhangi bir
indirmeden önce, deney protokolü [`config/image-features-v1.json`](../config/image-features-v1.json) ise herhangi
bir aday sonucundan önce donduruldu ve commit edildi.

## Neden bu kaynak

Skaler özetlere, bağlama ve yayımlanmış patlama geçmişine dayanan önceki dokuz yol precision'ı yükseltmedi. 96
özet her manyetogramı skalerlere indirger; harita, aynı aletten geriye kalan bilgidir. İndirme, ölçülmüş 12,4 GB
boyut tahmininden sonra kullanıcı tarafından onaylandı.

| kalem | değer |
| --- | --- |
| seri / segment | `hmi.sharp_cea_720s` / `Br` |
| dizin | `http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info` (`op=rs_list`) |
| dosyalar | `https://jsoc1.stanford.edu` |
| sıklık | HARP başına günde bir kayıt, `T_REC` 00:00:00 TAI |
| dönem | 2010-05-01 – 2023-12-31 |
| geliştirme HARP-günü | 33249 |
| kaydı olan HARP-günü | 32717 |
| alınan harita | 32717 |
| erişilemeyen | 0 |
| aktarılan ham bayt | 12280512960 |
| geçerli pikseli olmayan harita | 20 |
| kullanılan harita | 32697 |
| NaN payı 0.5'in üstünde olan harita | 878 |
| `records.jsonl` sha256 | `4a631c976c3f840dfbcf457718f59c35b68aaf8aa35a4864d4c9c83a1dbfb416` |

Her harita, geçerli pikseller üzerinden alan ortalamasıyla 128 × 256 boyutuna indirilir ve gauss cinsinden float16
olarak saklanır; geçerli pikseli olmayan hücreler 0 olarak saklanır. Ham FITS dosyaları özetleri alındıktan sonra
silindi; harita başına ham sha256, ham bayt, özgün genişlik ve yükseklik ile NaN payı tutulur. `T_REC` değeri
2024-01-01 veya sonrası olan hiçbir kayıt dizine alınmadı veya istenmedi.

## Yöntem

Kullanılabilirlik kuralları. `lag24` (birincil): tahmin zamanı t olan bir pencere, aynı HARP'ın `T_REC` değeri t
eksi 24 saatte veya öncesinde olan ve t eksi 48 saatten eski olmayan en son haritasını kullanır. `same` (yalnızca
duyarlılık): `T_REC` değeri t'de veya öncesinde olan ve t eksi 24 saatten eski olmayan en son harita. Yayın
gecikmesi ölçülmedi; bu yüzden yalnızca `same` altında bir geçiş ancak bir gecikme ölçümünü gerekçelendirebilirdi.
Böyle bir haritası olmayan pencerede `map_available` = 0 olur, yaş ve skor eksik kalır; yokluk hiçbir zaman sakin
bölge olarak kodlanmaz.

CNN. Girdi, 500 G'ye bölünüp [-6, 6] aralığına kırpılmış haritadır. Dört blok 3×3 evrişim (16, 32, 64, 128 kanal),
batch normalisation, ReLU ve 2×2 max pooling; global ortalama ve max pooling üç skalerle birleştirilir
(log(genişlik/500), log(yükseklik/250), NaN payı); dropout 0.3; tek doğrusal çıktı. Bir haritanın etiketi, HARP'ın
tahmin zamanı [`T_REC`, `T_REC` + 48 sa) aralığında pozitif bir eğitim rolü penceresi varsa 1'dir. Adam, öğrenme
oranı 0.001, weight decay 0.0001, batch 64, 6 epoch, rastgele sol-sağ çevirme ve kutup işareti çevirme, tohum 24.
Yığınlama, eğitim rolü içinde HARP numarası mod 3 ile üç kat kullanır: eğitim rolündeki bir HARP, kendisini hiç
görmemiş kat modelinin skorunu alır; kalibrasyon ve değerlendirme HARP'ları üç kat modelinin ortalama logit'ini
alır. Hiçbir kalibrasyon veya değerlendirme etiketi CNN'e ulaşmaz.

Kural başına özellikler: `map_available_<rule>`, `map_age_hours_<rule>`, `cnn_logit_<rule>`. `flag_<rule>`,
değişmemiş `config/walk-forward-v1.json` tariflerini 96 özet ve ilk iki özellikle yeniden uydurur; `image_<rule>`
buna `cnn_logit_<rule>` ekler. `control`, yeniden uydurma yapılmamış dondurulmuş temel modeldir. Eşikler,
kalibrasyon yılı olasılıklarından pencere recall 0,90'da gelir ve herhangi bir değerlendirme etiketi okunmadan önce
özetlendi. Hiperparametre araması yok; 18 CNN uydurması ve 48 bileşen uydurması; aygıt `mps`.

Değerlendirme yılı harita kapsamı:

| yıl | değerlendirme penceresi | harita payı lag24 | harita payı same | haritası olan pozitif pencere payı lag24 | haritası olan pozitif pencere payı same |
| --- | --- | --- | --- | --- | --- |
| 2014 | 75228 | 0.8907 | 0.9848 | 0.9498 | 0.9879 |
| 2015 | 69138 | 0.8926 | 0.9919 | 0.9365 | 0.9801 |
| 2016 | 42987 | 0.8572 | 0.9820 | 0.8785 | 1.0000 |
| 2017 | 19529 | 0.8390 | 0.9709 | 1.0000 | 1.0000 |
| 2022 | 50756 | 0.8604 | 0.9945 | 0.9121 | 1.0000 |
| 2023 | 60366 | 0.8401 | 1.0000 | 0.7823 | 1.0000 |

CNN eğitim kümeleri (üç kat üzerindeki aralık):

| yıl | harita | pozitif harita | son kayıp |
| --- | --- | --- | --- |
| 2014 | 4884–5276 | 157–188 | 0.0938–0.0993 |
| 2015 | 7567–7843 | 228–266 | 0.0938–0.1006 |
| 2016 | 10279–10756 | 380–405 | 0.0968–0.1085 |
| 2017 | 12910–13143 | 455–502 | 0.0909–0.1053 |
| 2022 | 15769–16129 | 479–526 | 0.0825–0.0922 |
| 2023 | 16814–17077 | 494–544 | 0.0808–0.0917 |

## Sonuçlar

| yıl | aday | TP | FP | FN | recall | precision | accuracy | hep-negatif accuracy | epizot precision | alarm verilen pozitif seri | AP | Brier | log loss | birincil kabul |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | control | 2007 | 7634 | 303 | 0.8688 | 0.2082 | 0.8945 | 0.9693 | 0.1636 | 77/83 | 0.5079 | 0.0207 | 0.0765 |  |
| 2014 | flag_lag24 | 1996 | 7381 | 314 | 0.8641 | 0.2129 | 0.8977 | 0.9693 | 0.1685 | 76/83 | 0.5086 | 0.0206 | 0.0765 | hayır |
| 2014 | image_lag24 | 1992 | 7585 | 318 | 0.8623 | 0.2080 | 0.8949 | 0.9693 | 0.1549 | 76/83 | 0.5092 | 0.0206 | 0.0765 | hayır |
| 2014 | flag_same | 2002 | 7600 | 308 | 0.8667 | 0.2085 | 0.8949 | 0.9693 | 0.1601 | 76/83 | 0.5074 | 0.0207 | 0.0766 | hayır |
| 2014 | image_same | 2002 | 7584 | 308 | 0.8667 | 0.2088 | 0.8951 | 0.9693 | 0.1584 | 76/83 | 0.5077 | 0.0207 | 0.0765 | hayır |
| 2015 | control | 1308 | 6294 | 47 | 0.9653 | 0.1721 | 0.9083 | 0.9804 | 0.1138 | 51/51 | 0.4924 | 0.0136 | 0.0478 |  |
| 2015 | flag_lag24 | 1309 | 6311 | 46 | 0.9661 | 0.1718 | 0.9081 | 0.9804 | 0.1128 | 51/51 | 0.4934 | 0.0136 | 0.0479 | hayır |
| 2015 | image_lag24 | 1321 | 6444 | 34 | 0.9749 | 0.1701 | 0.9063 | 0.9804 | 0.1065 | 51/51 | 0.4953 | 0.0135 | 0.0477 | hayır |
| 2015 | flag_same | 1308 | 6272 | 47 | 0.9653 | 0.1726 | 0.9086 | 0.9804 | 0.1125 | 51/51 | 0.4951 | 0.0136 | 0.0478 | hayır |
| 2015 | image_same | 1318 | 6526 | 37 | 0.9727 | 0.1680 | 0.9051 | 0.9804 | 0.1093 | 51/51 | 0.4840 | 0.0137 | 0.0482 | hayır |
| 2016 | control | 162 | 1303 | 19 | 0.8950 | 0.1106 | 0.9692 | 0.9958 | 0.0347 | 7/7 | 0.3664 | 0.0033 | 0.0145 |  |
| 2016 | flag_lag24 | 161 | 1300 | 20 | 0.8895 | 0.1102 | 0.9693 | 0.9958 | 0.0342 | 7/7 | 0.3648 | 0.0033 | 0.0146 | hayır |
| 2016 | image_lag24 | 161 | 1293 | 20 | 0.8895 | 0.1107 | 0.9695 | 0.9958 | 0.0350 | 7/7 | 0.3317 | 0.0033 | 0.0144 | evet |
| 2016 | flag_same | 162 | 1314 | 19 | 0.8950 | 0.1098 | 0.9690 | 0.9958 | 0.0338 | 7/7 | 0.3648 | 0.0033 | 0.0146 | hayır |
| 2016 | image_same | 161 | 1341 | 20 | 0.8895 | 0.1072 | 0.9683 | 0.9958 | 0.0352 | 7/7 | 0.3549 | 0.0033 | 0.0143 | hayır |
| 2017 | control | 235 | 1035 | 18 | 0.9289 | 0.1850 | 0.9461 | 0.9870 | 0.0781 | 5/6 | 0.8117 | 0.0049 | 0.0205 |  |
| 2017 | flag_lag24 | 236 | 1093 | 17 | 0.9328 | 0.1776 | 0.9432 | 0.9870 | 0.0649 | 5/6 | 0.8117 | 0.0049 | 0.0205 | hayır |
| 2017 | image_lag24 | 235 | 1051 | 18 | 0.9289 | 0.1827 | 0.9453 | 0.9870 | 0.0735 | 5/6 | 0.8156 | 0.0049 | 0.0210 | hayır |
| 2017 | flag_same | 235 | 1024 | 18 | 0.9289 | 0.1867 | 0.9466 | 0.9870 | 0.0725 | 5/6 | 0.8129 | 0.0049 | 0.0204 | hayır |
| 2017 | image_same | 234 | 1035 | 19 | 0.9249 | 0.1844 | 0.9460 | 0.9870 | 0.0685 | 5/6 | 0.8014 | 0.0051 | 0.0212 | hayır |
| 2022 | control | 414 | 8949 | 7 | 0.9834 | 0.0442 | 0.8235 | 0.9917 | 0.0316 | 16/16 | 0.2800 | 0.0071 | 0.0292 |  |
| 2022 | flag_lag24 | 414 | 9024 | 7 | 0.9834 | 0.0439 | 0.8221 | 0.9917 | 0.0311 | 16/16 | 0.2794 | 0.0071 | 0.0292 | hayır |
| 2022 | image_lag24 | 414 | 9042 | 7 | 0.9834 | 0.0438 | 0.8217 | 0.9917 | 0.0312 | 16/16 | 0.2740 | 0.0071 | 0.0293 | hayır |
| 2022 | flag_same | 414 | 8956 | 7 | 0.9834 | 0.0442 | 0.8234 | 0.9917 | 0.0314 | 16/16 | 0.2811 | 0.0071 | 0.0292 | hayır |
| 2022 | image_same | 414 | 8843 | 7 | 0.9834 | 0.0447 | 0.8256 | 0.9917 | 0.0314 | 16/16 | 0.2818 | 0.0070 | 0.0290 | hayır |
| 2023 | control | 653 | 4852 | 128 | 0.8361 | 0.1186 | 0.9175 | 0.9871 | 0.0905 | 35/38 | 0.2206 | 0.0112 | 0.0440 |  |
| 2023 | flag_lag24 | 655 | 4944 | 126 | 0.8387 | 0.1170 | 0.9160 | 0.9871 | 0.0875 | 35/38 | 0.2210 | 0.0112 | 0.0441 | hayır |
| 2023 | image_lag24 | 648 | 4671 | 133 | 0.8297 | 0.1218 | 0.9204 | 0.9871 | 0.0938 | 33/38 | 0.2246 | 0.0112 | 0.0438 | hayır |
| 2023 | flag_same | 652 | 4860 | 129 | 0.8348 | 0.1183 | 0.9174 | 0.9871 | 0.0894 | 34/38 | 0.2205 | 0.0112 | 0.0440 | hayır |
| 2023 | image_same | 653 | 4764 | 128 | 0.8361 | 0.1205 | 0.9190 | 0.9871 | 0.0870 | 34/38 | 0.2374 | 0.0111 | 0.0435 | hayır |

Yıl başına birincil kabul: epizot precision'ı daha yüksek, FP pencereleri daha az, alarm verilen pozitif seriler
daha az değil, pencere recall düşüşü en fazla 0,02; hepsi kontrole göre.

- Precision: `image_lag24` yalnızca 2016'da (0.1107'ye karşı 0.1106) ve 2023'te (0.1218'e karşı 0.1186) kontrolün
  üstünde, diğer dört yılda altında. Tüm adaylar ve yıllarda precision 0.0438 ile 0.2129 arasındadır.
- Accuracy her adayda ve her yılda hep-negatif accuracy değerinin altında kalıyor. Bunu aşmak TP'nin FP'den büyük
  olmasını, yani precision'ın 0,50'nin üstünde olmasını gerektirir.
- `image_lag24` adayının tek geçişi 2016'dır: 1303 FP penceresinden 10 eksik ve epizot precision'ı 0.0347'ye karşı
  0.0350; bu sırada AP 0.3664'ten 0.3317'ye düşüyor. O yılın iki bootstrap aralığı da sıfırı içeriyor.
- 2023'te `image_lag24` 181 FP penceresini kaldırıyor ve FP aralığı sıfırı dışlıyor, ancak 38 pozitif serinin
  33'üne alarm veriyor (kontrol 35) ve bu yüzden kabulü karşılamıyor.
- `flag_lag24` ve `flag_same` kontrolden yalnızca yeniden uydurma gürültüsü kadar ayrılır ve hiçbir yılda geçmez.
- CNN'e daha taze harita veren `same` kuralı yardımcı olmuyor: `image_same` hiçbir yılda geçmiyor.

`image_lag24` eksi kontrol için eşleştirilmiş tüm-HARP bootstrap %95 aralıkları (1000 çekiliş, tohum 24):

| yıl | epizot precision farkı | FP pencere farkı |
| --- | --- | --- |
| 2014 | [-0.0179, +0.0013] | [-114.0, +17.0] |
| 2015 | [-0.0185, +0.0016] | [+70.0, +244.0] |
| 2016 | [-0.0041, +0.0044] | [-73.0, +53.0] |
| 2017 | [-0.0216, +0.0077] | [-11.0, +54.0] |
| 2022 | [-0.0022, +0.0011] | [+31.0, +168.0] |
| 2023 | [-0.0051, +0.0122] | [-265.1, -109.0] |

Tüm adayların aralıkları `intervals.csv` içindedir.

Haritası olan değerlendirme pencerelerinde tek başına CNN skorunun average precision değeri ve aynı pencerelerde
kontrol:

| yıl | kural | kapsanan pay | yalnız CNN AP | aynı pencerelerde kontrol AP |
| --- | --- | --- | --- | --- |
| 2014 | lag24 | 0.8907 | 0.4156 | 0.5119 |
| 2014 | same | 0.9848 | 0.4762 | 0.5065 |
| 2015 | lag24 | 0.8926 | 0.3562 | 0.5018 |
| 2015 | same | 0.9919 | 0.4118 | 0.4962 |
| 2016 | lag24 | 0.8572 | 0.1649 | 0.4153 |
| 2016 | same | 0.9820 | 0.2170 | 0.3702 |
| 2017 | lag24 | 0.8390 | 0.5271 | 0.8170 |
| 2017 | same | 0.9709 | 0.6598 | 0.8126 |
| 2022 | lag24 | 0.8604 | 0.0931 | 0.2966 |
| 2022 | same | 0.9945 | 0.1792 | 0.2800 |
| 2023 | lag24 | 0.8401 | 0.1196 | 0.2282 |
| 2023 | same | 1.0000 | 0.1699 | 0.2206 |

Tek başına CNN skoru, her iki kural altında her yıl 96 özetli kontrolden daha kötü sıralıyor.

## Sınırlar

Zaten incelenmiş yıllar: uyarlanabilir geliştirme kanıtı, bağımsız test değil. Sayılar örtüşen tahmin pencereleri
ve bunların gruplamalarıdır, fiziksel patlamalar değildir. Günde bir harita, sabit 128 × 256 biçiminde; yeniden
boyutlandırma piksel ölçeğini her HARP için farklı değiştirir. Tek dondurulmuş tarifli, aramasız tek küçük CNN;
olumsuz sonuç bu tarifi ve sıklığı sınırlar, her görüntü modelini değil. Haritalar kesin seriden gelir, gerçek
zamana yakın seriden değil ve yayın gecikmesi ölçülmedi. `lag24` altında değerlendirme pencerelerinin yaklaşık
%84–89'unun haritası vardır. Tohumlar sabittir, ancak Apple MPS arka ucu bit düzeyinde deterministik değildir;
gerçekten kullanılan skorlar çıktıda saklanır ve özetlenir.

## Yeniden üretim

```sh
pip install -r requirements-maps.txt
python -m scripts.fetch_sharp_maps --output data/sharp_br_maps_20261109_r1 --index-cache data/sharp_dims_probe_20261109_r1
python -m scripts.audit_image_features --output artifacts/image_features_20261110_r1
```

Edinim config sha256 `37a182bf146dc4b76e6bad6d8181fb0379db2434dbe8a6b0339d2e803d7098d8`; config sha256 `56f1baa57522793d000bc4bedf8ab6e766af3d236e3a2e03c473b3bf70d986c5`; eşik sha256 `bf3fcbfe54c35c9790a2ede0d2c7e56662ef18d3c3f6e7c6b4f2ace97badf37c`. Yeni çıktı dizinleri kullanın; var olan
çıktının üzerine yazılmaz.
