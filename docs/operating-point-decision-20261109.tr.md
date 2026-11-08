# Çalışma noktası kararı: pencere recall hedefi 0,90

## Karar

2026-11-09'dan itibaren yıllık V2 baseline için proje çalışma noktası, önceki kalibrasyon yılında pencere recall
0,90'da seçilip sonraki yıla değiştirilmeden uygulanan eşiktir. Bu, "pencere recall en az 0,95'te kesinlik 0,30"
geliştirme hedefinin yerini alır. Donmuş tanım
[`config/operating-point-v2.json`](../config/operating-point-v2.json) dosyasındadır.

Bu bir performans iyileşmesi değildir. Model, özellikleri ve olasılıkları değişmedi. Hedef, verinin
desteklediğiyle hizalandı ve bu çalışma noktasını belirten her rapor bunu söylemelidir.

## Neden

[Çalışma noktası incelemesi](operating-point-review-20261109.tr.md), yüksek recall'da 0,30 kesinliğin bu
modelin ve verinin sunabileceği bir özellik olmadığını gösterdi. Uygulanabilir olmayan değerlendirme yılı
oracle'ı bile 2014'te 0,67, 2015'te 0,79, 2016'da 0,58, 2022'de 0,23 ve 2023'te 0,25 veya altında recall
gerektirir; yalnızca 2017, 0,30'a 0,90'da ulaşır. 2026-11-07'den bu yana denenen sekiz bağımsız yol (önceki yıl
eşik kuralları, alarm kalıcılığı, yeniden kalibrasyon, olasılık gidişatı, yayımlanmış SRS bağlamı,
ağırlıklandırma, model grid'leri ve zamansal evrişim modeli) 0,95 hedefinde kesinliği 0,04–0,16 bandında
bıraktı. Hedefi 0,90'a gevşetmek yılda 1123 ile 6253 yanlış-alarm penceresi kaldırır; bedeli yılda 0 ile 3 ek
kaçan patlama dönemidir.

## Yeni çalışma noktasında beklenen geliştirme performansı

Zaten incelenmiş geliştirme yıllarında önceki yıl eşikleriyle gözlendi. Bunlar raporlama için beklentilerdir,
garanti değildir.

| yıl | kesinlik | sunulan recall | YA pencereleri | kaçan pozitif seri | 0,95'te kaçan pozitif seri |
| --- | --- | --- | --- | --- | --- |
| 2014 | 0.2082 | 0.8688 | 7634 | 6 | 3 |
| 2015 | 0.1721 | 0.9653 | 6294 | 0 | 0 |
| 2016 | 0.1106 | 0.8950 | 1303 | 0 | 0 |
| 2017 | 0.1850 | 0.9289 | 1035 | 1 | 1 |
| 2022 | 0.0442 | 0.9834 | 8949 | 0 | 0 |
| 2023 | 0.1186 | 0.8361 | 4852 | 3 | 2 |

Sunulan recall 0,836 ile 0,983 arasında değişir, çünkü kalibrasyon yılı ile değerlendirme yılı farklıdır. 2022
her hedefte en zayıf yıl olarak kalır.

## Kapsam ve raporlama kuralları

- Geliştirme raporlamasına ve gelecekteki geliştirme protokollerine uygulanır.
- Gösterge paneli uyarı eşiği ve dağıtılmış herhangi bir uyarı bu kararla değişmez. Bunları değiştirmek ayrı bir
  karar ve kapalı kalan ayrılmış 2024–2025 testini gerektirir.
- Raporlar her yıl için kesinliği, sunulan recall ve kaçan pozitif serilerle birlikte belirtir; hedefin
  2026-11-09'da neden yeniden tanımlandığını söyler ve önceki çalışmayla karşılaştırılan her yerde 0,95
  sonuçlarını görünür tutar.

## Sınırlar

Yukarıdaki beklentiler zaten incelenmiş yıllardan gelir ve uyarlanabilir geliştirme kanıtıdır, bağımsız bir test
değildir. Sayılar örtüşen tahmin pencereleri ve bunların gruplamalarıdır, fiziksel patlamalar değildir. Donmuş
dosya şununla incelenebilir:

```sh
cat config/operating-point-v2.json
```
