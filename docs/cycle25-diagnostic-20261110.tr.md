# 25. döngü sıralama teşhisi: 2022–2023 neden daha zayıf (2026-11-10)

## Karar

[Dondurulmuş protokolün](../config/cycle25-diagnostic-v1.json) R1 okuması geçerli: 96 manyetik özetin sonraki 24
saat hakkında taşıdığı bilgi 25. güneş döngüsünde azaldı; eğitim dağılımının kayması ana neden değil. 2022–2023
dönemi içinde, o dönemin kendi geleceğini gören ve bu yüzden bir tavan olan HARP gruplu uydurma, ileri yürüyen
temel modelden daha iyi sıralamıyor (2022'de AP 0.1877'ye karşı 0.2800, 2023'te 0.2190'a karşı 0.2206). En iyi tek
ham özet 2022 ve 2023'ü AP 0.2089 ve 0.1823 ile sıralıyor; 2014 ve 2017'de 0.4900 ve 0.7216. R2 okuması (kayma)
yanlış, R3 okuması (zamanlama baskın) hiçbir yılda geçerli değil. 25. döngüye duyarlı bir eğitim protokolü bu
kanıtla gerekçelendirilemez. Hiçbir model, eşik veya uyarı değişmedi; ayrılmış 2024–2025 testine erişilmedi.
Protokol herhangi bir sonuçtan önce donduruldu ve commit edildi.

## Neden bu inceleme

İki kademeli inceleme, precision hedefli uyarı kademesinin bile 2022 ve 2023'te başarısız olduğunu gösterdi; temel
modelin AP'si bu yıllarda 0.2800 ve 0.2206, 2014, 2015 ve 2017'de 0.4924–0.8117. Soru, 25. döngüde modelin mi,
eğitim dağılımının mı, yoksa verinin kendisinin mi daha zayıf olduğuydu.

## Yöntem

Yıllık katların dondurulmuş temel model olasılıkları; değerlendirme yılı pencereleri dondurulmuş parçaların 96
özetiyle birleştirildi. D1: yıl başına bileşim. D2: temel model sıralamasının bölge problemine (HARP başına en
yüksek olasılık, HARP'ın herhangi bir pozitif penceresi olup olmamasına karşı) ve zamanlama problemine (yalnızca
patlayan HARP'lar içinde pencere sıralaması) ayrıştırılması; ayrıca recall 0,90 izleme eşiğinde, yıl içinde hiç
pozitif penceresi olmayan HARP'lardan gelen FP pencerelerinin payı. D3: her özetin ve olumsuzunun ham sıralama
olarak AP'si; en iyisi ve kapasite vekili olarak `USFLUX__last`. D4: değişmemiş walk-forward-v1 lojistik ve
xgboost tariflerinin her dönem (2014–2017 ve 2022–2023) içinde HARP gruplu 5 katlı çapraz doğrulaması, ham
olasılıklar 0,45/0,55 ile birleştirilmiş, 20 uydurma; dönem için bir tavan, hiçbir zaman uygulanabilir değil.
Referans kapasite medyanı, 24. döngü pozitif pencerelerinin `USFLUX__last` medyanıdır: 3.63e+22.

## D1 Bileşim

| yıl | pencere | HARP | patlayan HARP | pozitif pencere | pozitif seri | pozitif pay | patlayan HARP başına medyan pencere | pozitif medyan USFLUX__last | tüm medyan USFLUX__last | 24. döngü medyanı altındaki pozitif pay | ortalama missing_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 75228 | 629 | 44 | 2310 | 83 | 0.0307 | 260 | 4.34e+22 | 2.80e+21 | 0.4281 | 0.0139 |
| 2015 | 69138 | 599 | 24 | 1355 | 51 | 0.0196 | 274 | 3.18e+22 | 1.84e+21 | 0.5934 | 0.0138 |
| 2016 | 42987 | 357 | 4 | 181 | 7 | 0.0042 | 285 | 3.77e+22 | 1.63e+21 | 0.4641 | 0.0155 |
| 2017 | 19529 | 163 | 3 | 253 | 6 | 0.0130 | 253 | 3.79e+22 | 2.24e+21 | 0.4466 | 0.0156 |
| 2022 | 50756 | 528 | 12 | 421 | 16 | 0.0083 | 193 | 3.86e+22 | 3.02e+21 | 0.4466 | 0.0167 |
| 2023 | 60366 | 703 | 27 | 781 | 38 | 0.0129 | 134 | 3.38e+22 | 2.53e+21 | 0.5493 | 0.0148 |

## D2 Temel model sıralamasının ayrıştırılması

| yıl | genel AP | bölge AP | patlayan HARP içi AP | izleme eşiğinde FP penceresi | hiç patlamayan HARP FP payı |
| --- | --- | --- | --- | --- | --- |
| 2014 | 0.5079 | 0.7618 | 0.5609 | 7634 | 0.4353 |
| 2015 | 0.4924 | 0.8266 | 0.5469 | 6294 | 0.5261 |
| 2016 | 0.3664 | 0.4958 | 0.4371 | 1303 | 0.6078 |
| 2017 | 0.8117 | 1.0000 | 0.8821 | 1035 | 0.7459 |
| 2022 | 0.2800 | 0.7187 | 0.3860 | 8949 | 0.8301 |
| 2023 | 0.2206 | 0.5951 | 0.4024 | 4852 | 0.7422 |

## D3 ve D4 Tavanlar

| yıl | ileri yürüyen AP | en iyi ham özet | en iyi ham özet AP | USFLUX__last AP | dönem içi uydurma AP | dönem içi eksi ileri yürüyen |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 0.5079 | `TOTUSJH__mean` | 0.4900 | 0.4362 | 0.4270 | -0.0810 |
| 2015 | 0.4924 | `R_VALUE__mean` | 0.3960 | 0.2181 | 0.4569 | -0.0355 |
| 2016 | 0.3664 | `TOTFX__mean` | 0.4637 | 0.1407 | 0.2376 | -0.1289 |
| 2017 | 0.8117 | `TOTUSJH__mean` | 0.7216 | 0.5602 | 0.8011 | -0.0106 |
| 2022 | 0.2800 | `ABSNJZH__last` | 0.2089 | 0.1390 | 0.1877 | -0.0924 |
| 2023 | 0.2206 | `ABSNJZH__std` | 0.1823 | 0.0825 | 0.2190 | -0.0016 |

- D4: dönem içi uydurma hiçbir yılda ileri yürüyen temel modeli geçmiyor; 2022'de 0.0924, 2023'te 0.0016 altında.
  2022–2023 dönemi 39 patlayan HARP'ta 1202 pozitif pencere içeriyor; dolayısıyla içindeki uydurma da küçük.
  R1'in "dışlandı" değil "bu kanıtla gerekçelendirilemez" diye okunmasının nedeni budur.
- D3: en iyi ham özet AP 0.49–0.72'den (2014, 2017) 0.21 ve 0.18'e (2022, 2023) düşüyor; kapasite vekili
  `USFLUX__last` 0.44 ve 0.56'dan 0.14 ve 0.08'e. 25. döngüde en iyi özellikler akım helisitesi özetleri
  (`ABSNJZH`), akı veya akım toplamları değil.
- D2: bölge problemi 25. döngüde hâlâ kısmen çözülebilir (bölge AP 0.72 ve 0.60), ancak FP pencerelerinin %83 ve
  %74'ü yıl içinde hiç patlamayan HARP'lardan geliyor; 2014 ve 2015'te %44 ve %53. 25. döngüde özetlere göre
  patlamaya elverişli görünen ama yıl içinde patlamayan çok sayıda bölge var: 528 ve 703 HARP'tan 12 ve 27'si
  patlıyor; 2014'te 629'dan 44'ü.
- 25. döngüdeki pozitif pencereler daha küçük bölgelerden gelmiyor: pozitif pencerelerin kapasite medyanı 3.86e+22
  ve 3.38e+22, 24. döngüde 3.18e+22–4.34e+22; her yıl %45–55'i 24. döngü medyanının altında. Patlayan HARP'lar
  daha az pencerede gözleniyor (medyan 193 ve 134, 253–285'e karşı).

## Sınırlar

Zaten incelenmiş yıllar: uyarlanabilir geliştirme betimlemesi, bağımsız test değil. Sayılar örtüşen tahmin
pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir. Dönem içi tavan 25. döngünün yalnızca iki
yılını kullanır ve kendisi küçük örneklemli bir kestirimdir. Tek özellik AP'si uydurmasız ham sıralamadır. Teşhis
96 özeti sınırlar, 25. döngüye ilişkin başka verileri değil.

## Yeniden üretim

```sh
python -m scripts.audit_cycle25 --output artifacts/cycle25_diagnostic_20261110_r1
```

Config sha256 `e9466137c619a72ae420e017e59b1f38ce2e42f583f364b7d36225677e92543a`. Yeni çıktı dizinleri kullanın; var olan çıktının üzerine yazılmaz.
