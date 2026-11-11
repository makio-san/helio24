# Yeniden etiketlenmiş tabloda iki kademeli çalışma noktası (2026-11-11)

## Karar

[Dondurulmuş protokol](../config/two-tier-v2.json), `config/two-tier-v1.json` iki kademeli kuralını her hedef, taban
ve eşitlik kuralı değişmeden yeniden etiketlenmiş tabloya ve yeniden etiketlenmiş ileri yürüyen modellere uyguluyor.
Birincil precision hedefi 0,50'deki alarm katmanı hedefi öncekiyle aynı üç yılda tutuyor (2014, 2015, 2017);
`cycle25_now_met` yanlış ve `redefinition_supported` yanlış. Değişen şey, 25. döngüdeki kaçırma payının büyüklüğü.
2022'de alarm katmanı hâlâ bir geri dönüş yılı; çünkü yeniden etiketlenmiş 2021 kalibrasyon yılı (377 pozitif
pencere) en iyi ihtimalle 0.1996 precision'a ulaşıyor; yine de değerlendirme precision'ı recall 0.4822'de 0.4727
[0.3482, 0.6021] (dondurulmuş etiketlerde recall 0.5249'da 0.1659) ve accuracy 0.9648, hep-negatifin 0.0018
altında. 2023'te kural artık bir sayım rastlantısı değil: 79 yerine 1587 gerçek pencerede alarm veriyor, recall
0.1012 yerine 0.3879, precision 0.4263 [0.3483, 0.5053] (önce 0.4270 [0.0968, 0.7441]); nokta 0,50'yi kaçırıyor ve
accuracy 0.9522, hep-negatifin 0.0056 altında. Yeniden etiketlenmiş değerlendirme yılı kâhini 2022'de recall
0.4662'de precision 0,50'ye ulaşıyor (dondurulmuş: 0.1496), 2023'te ise yalnızca 0.0176'da (dondurulmuş: 0.0717).
Sıfır uydurma; model, olasılık, uyarı ya da panel değişikliği yok; ayrılmış 2024–2025 testi okunmadı. Protokol
herhangi bir sonuçtan önce donduruldu ve commit edildi.

## Neden bu protokol

Dondurulmuş etiketlerde alarm katmanı precision 0,50'yi yalnızca 24. döngü yıllarında tutuyordu ve 2022 ile 2023
kâhinleri 0,50'ye recall 0,15 ve 0,07'de ulaşıyordu. [Yeniden etiketleme](relabel-20261111.tr.md) 2022 ve 2023
ortalama precision'ını 0.4622 ve 0.3626'ya, 24. döngü aralığına yükselttiği için miras alınan önceki yıl precision
kuralı yeniden sınandı.

## Yöntem

Kol: `config/relabel-v1.json`'daki `relabelled_models`, saklanan yıllık modellerle birinci aşama çıkarımı. İzleme
katmanı: önceki yeniden etiketlenmiş kalibrasyon yılında pencere recall 0,90; yeniden etiketlenmiş ileri yürüyen
eşiklerden bit bit yeniden üretildi. Alarm katmanı: önceki yeniden etiketlenmiş kalibrasyon yılında
`helio24.two_tier.precision_threshold`, hedefler 0,30 ve 0,50, recall tabanı 0,10; hiçbir eşik hedefe ulaşmazsa en
iyi precision eşiği kullanılır ve yıl geri dönüş olarak işaretlenir. Her katman ve yılın eşikleri, herhangi bir
değerlendirme etiketi okunmadan önce yazıldı ve hash'lendi. Aralıklar %95 HARP kümesi bootstrap'ıdır (1000 çekiliş,
tohum 24). Dondurulmuş iki kademeli sonuç her satırın yanına eski etiket referansı olarak kopyalandı; iki çalıştırma
farklı pencere kümeleri kullanıyor (yeniden etiketlenmiş 2022 ve 2023 rolleri 50756 ve 60366'ya karşı 65593 ve
96991 pencere tutuyor).

## Precision hedefi 0,50'de alarm katmanı

| yıl | etiketler | geri dönüş | kalibrasyon precision | kalibrasyon recall | TP | FP | recall | precision | %95 aralık | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | hayır | 0.5000 | 0.1326 | 688 | 320 | 0.2824 | 0.6825 | [0.4308, 0.8477] | 0.9736 | 0.9689 | 66 / 88 |
| 2014 | dondurulmuş | hayır | 0.5000 | 0.1290 | 644 | 248 | 0.2788 | 0.7220 | [0.4414, 0.8625] | 0.9746 | 0.9693 | 63 / 83 |
| 2015 | yeniden etiketlenmiş | hayır | 0.5000 | 0.4906 | 545 | 457 | 0.3730 | 0.5439 | [0.3286, 0.7166] | 0.9805 | 0.9793 | 27 / 57 |
| 2015 | dondurulmuş | hayır | 0.5000 | 0.5074 | 551 | 476 | 0.4066 | 0.5365 | [0.3109, 0.7080] | 0.9815 | 0.9804 | 24 / 51 |
| 2016 | yeniden etiketlenmiş | hayır | 0.5000 | 0.4969 | 94 | 109 | 0.4393 | 0.4631 | [0.0000, 0.6230] | 0.9947 | 0.9950 | 3 / 8 |
| 2016 | dondurulmuş | hayır | 0.5000 | 0.5269 | 76 | 112 | 0.4199 | 0.4043 | [0.0000, 0.5249] | 0.9950 | 0.9958 | 2 / 7 |
| 2017 | yeniden etiketlenmiş | hayır | 0.5000 | 0.2196 | 177 | 27 | 0.6679 | 0.8676 | [0.0000, 1.0000] | 0.9942 | 0.9866 | 3 / 6 |
| 2017 | dondurulmuş | hayır | 0.5000 | 0.2983 | 182 | 43 | 0.7194 | 0.8089 | [0.0000, 0.9691] | 0.9942 | 0.9870 | 2 / 6 |
| 2022 | yeniden etiketlenmiş | evet | 0.1996 | 0.2361 | 1056 | 1178 | 0.4822 | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | dondurulmuş | evet | 0.1447 | 0.3382 | 221 | 1111 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | yeniden etiketlenmiş | hayır | 0.5000 | 0.4461 | 1587 | 2136 | 0.3879 | 0.4263 | [0.3483, 0.5053] | 0.9522 | 0.9578 | 68 / 159 |
| 2023 | dondurulmuş | hayır | 0.5000 | 0.1710 | 79 | 106 | 0.1012 | 0.4270 | [0.0968, 0.7441] | 0.9866 | 0.9871 | 30 / 38 |

## Precision hedefi 0,30'da alarm katmanı

| yıl | etiketler | geri dönüş | kalibrasyon precision | kalibrasyon recall | TP | FP | recall | precision | %95 aralık | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | hayır | 0.3000 | 0.5533 | 1401 | 2480 | 0.5751 | 0.3610 | [0.2396, 0.4873] | 0.9551 | 0.9689 | 32 / 88 |
| 2014 | dondurulmuş | hayır | 0.3000 | 0.6014 | 1371 | 2436 | 0.5935 | 0.3601 | [0.2211, 0.4974] | 0.9551 | 0.9693 | 29 / 83 |
| 2015 | yeniden etiketlenmiş | hayır | 0.3000 | 0.6560 | 1065 | 2140 | 0.7290 | 0.3323 | [0.2160, 0.4524] | 0.9641 | 0.9793 | 9 / 57 |
| 2015 | dondurulmuş | hayır | 0.3000 | 0.6571 | 986 | 1953 | 0.7277 | 0.3355 | [0.2038, 0.4564] | 0.9664 | 0.9804 | 8 / 51 |
| 2016 | yeniden etiketlenmiş | hayır | 0.3000 | 0.7707 | 178 | 740 | 0.8318 | 0.1939 | [0.0000, 0.3532] | 0.9820 | 0.9950 | 1 / 8 |
| 2016 | dondurulmuş | hayır | 0.3000 | 0.7911 | 152 | 684 | 0.8398 | 0.1818 | [0.0000, 0.3302] | 0.9834 | 0.9958 | 1 / 7 |
| 2017 | yeniden etiketlenmiş | hayır | 0.3002 | 0.5935 | 233 | 466 | 0.8792 | 0.3333 | [0.0000, 0.7200] | 0.9749 | 0.9866 | 1 / 6 |
| 2017 | dondurulmuş | hayır | 0.3000 | 0.5967 | 215 | 401 | 0.8498 | 0.3490 | [0.0000, 0.7524] | 0.9775 | 0.9870 | 1 / 6 |
| 2022 | yeniden etiketlenmiş | evet | 0.1996 | 0.2361 | 1056 | 1178 | 0.4822 | 0.4727 | [0.3482, 0.6021] | 0.9648 | 0.9666 | 32 / 72 |
| 2022 | dondurulmuş | evet | 0.1447 | 0.3382 | 221 | 1111 | 0.5249 | 0.1659 | [0.0725, 0.2543] | 0.9742 | 0.9917 | 2 / 16 |
| 2023 | yeniden etiketlenmiş | hayır | 0.3000 | 0.7539 | 3049 | 7653 | 0.7453 | 0.2849 | [0.2373, 0.3350] | 0.9104 | 0.9578 | 31 / 159 |
| 2023 | dondurulmuş | hayır | 0.3003 | 0.2162 | 123 | 225 | 0.1575 | 0.3534 | [0.0842, 0.6050] | 0.9854 | 0.9871 | 28 / 38 |

## İzleme katmanı (recall 0,90)

| yıl | etiketler | geri dönüş | kalibrasyon precision | kalibrasyon recall | TP | FP | recall | precision | %95 aralık | accuracy | hep-negatif accuracy | kaçırılan / pozitif koşu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | yeniden etiketlenmiş | hayır |  |  | 2146 | 9020 | 0.8810 | 0.1922 | [0.1318, 0.2594] | 0.8812 | 0.9689 | 6 / 88 |
| 2014 | dondurulmuş | hayır |  |  | 2007 | 7634 | 0.8688 | 0.2082 | [0.1327, 0.2868] | 0.8945 | 0.9693 | 6 / 83 |
| 2015 | yeniden etiketlenmiş | hayır |  |  | 1396 | 8079 | 0.9555 | 0.1473 | [0.0905, 0.2045] | 0.8846 | 0.9793 | 1 / 57 |
| 2015 | dondurulmuş | hayır |  |  | 1308 | 6294 | 0.9653 | 0.1721 | [0.1069, 0.2401] | 0.9083 | 0.9804 | 0 / 51 |
| 2016 | yeniden etiketlenmiş | hayır |  |  | 201 | 1722 | 0.9393 | 0.1045 | [0.0000, 0.1920] | 0.9598 | 0.9950 | 0 / 8 |
| 2016 | dondurulmuş | hayır |  |  | 162 | 1303 | 0.8950 | 0.1106 | [0.0000, 0.2039] | 0.9692 | 0.9958 | 0 / 7 |
| 2017 | yeniden etiketlenmiş | hayır |  |  | 243 | 1058 | 0.9170 | 0.1868 | [0.0000, 0.4619] | 0.9456 | 0.9866 | 1 / 6 |
| 2017 | dondurulmuş | hayır |  |  | 235 | 1035 | 0.9289 | 0.1850 | [0.0000, 0.4581] | 0.9461 | 0.9870 | 1 / 6 |
| 2022 | yeniden etiketlenmiş | hayır |  |  | 2024 | 11917 | 0.9242 | 0.1452 | [0.1002, 0.1969] | 0.8158 | 0.9666 | 5 / 72 |
| 2022 | dondurulmuş | hayır |  |  | 414 | 8949 | 0.9834 | 0.0442 | [0.0222, 0.0724] | 0.8235 | 0.9917 | 0 / 16 |
| 2023 | yeniden etiketlenmiş | hayır |  |  | 3695 | 16022 | 0.9032 | 0.1874 | [0.1518, 0.2232] | 0.8307 | 0.9578 | 10 / 159 |
| 2023 | dondurulmuş | hayır |  |  | 653 | 4852 | 0.8361 | 0.1186 | [0.0765, 0.1630] | 0.9175 | 0.9871 | 3 / 38 |

## Değerlendirme yılı kâhini (konuşlandırılamaz)

| yıl | precision hedefi | dondurulmuş en yüksek recall | yeniden etiketlenmiş en yüksek recall |
| --- | --- | --- | --- |
| 2014 | 0.3 | 0.6693 | 0.6736 |
| 2014 | 0.5 | 0.4818 | 0.4598 |
| 2015 | 0.3 | 0.7889 | 0.7844 |
| 2015 | 0.5 | 0.4841 | 0.4661 |
| 2016 | 0.3 | 0.5801 | 0.6916 |
| 2016 | 0.5 | 0.3260 | 0.3224 |
| 2017 | 0.3 | 0.8972 | 0.8943 |
| 2017 | 0.5 | 0.8024 | 0.7887 |
| 2022 | 0.3 | 0.2280 | 0.7466 |
| 2022 | 0.5 | 0.1496 | 0.4662 |
| 2023 | 0.3 | 0.2458 | 0.7169 |
| 2023 | 0.5 | 0.0717 | 0.0176 |

## Okuma

- `year_meets_primary`: her iki etiket kümesinde 2014, 2015, 2017. 2016 ikisinde de kaçırıyor (0.4043 ve 0.4631,
  aralıklar 0.0000'dan başlıyor); 2023, 0.0730 yerine 0.0737 ile kaçırıyor ama artık 185 yerine 3723 alarm
  penceresinde; 2022 ikisinde de geri dönüş yılı, precision 0.1659 yerine 0.4727.
- 2022 geri dönüşünün yeni bir nedeni var: yeniden etiketlenmiş 2021 kalibrasyon yılı temizlemeden sonra yalnızca
  377 pozitif pencere tutuyor (dondurulmuşta 182) ve recall tabanındaki en iyi precision'ı 0.1996. Kuralı sınırlayan
  sakin bir kalibrasyon yılı, 2022 sıralaması değil; 2022 kâhini artık recall 0.4662'de 0,50'ye ulaşıyor.
- 2023 tersi durum: kural, yeniden etiketlenmiş 2022 kalibrasyon yılında kesin olan bir eşik seçiyor (recall
  0.4461'de 0.50) ve 2023'te hedefin 0.0737 altında, 0.4263'e düşüyor; 2023 kâhini ise 0,50'ye yalnızca recall
  0.0176'da ulaşıyor. 2023 sıralaması hâlâ kalibrasyon yılından daha az ayrılabilir pozitif barındırıyor.
- İzleme katmanı: yeniden etiketlenmiş izleme katmanı, yeniden etiketleme raporundaki `relabelled_models` recall
  0,90 sonucunu her yılda yeniden üretiyor (2022 precision 0.1452, 2023 0.1874); 24. döngü yılları aralıkları içinde
  hareket ediyor.
- Hep-negatifin üstünde accuracy: izleme katmanında iki etiket kümesinin hiçbir yılında yok; alarm katmanında
  öncekiyle aynı üç yıl; 2022 ve 2023 artık 0.0175 ve 0.0005 yerine 0.0018 ve 0.0056 geride (2023 önceden 185
  alarmla gerideydi).

## Sınırlar

İncelenmiş yıllarda uyarlanabilir betimleme; yeniden etiketlenmiş etiketler bir ilişkilendirmedir, gerçeğin kendisi
değil; sayımlar örtüşen pencerelerdir, patlama değil. Eski ve yeni satırlar farklı pencere kümelerinde ölçülüyor ve
dondurulmuş satırlar yeniden hesaplanmadan kopyalandı. 2016 ve 2017'de alarm katmanı precision'ı 8 ve 6 pozitif
koşuya dayanıyor ve aralıkları 0.0000'a uzanıyor. Ayrılmış test okunmadı; burada hiçbir şey uyarıları ya da
modelleri değiştirmiyor.

## Yeniden üretim

```sh
python -m scripts.audit_two_tier_relabelled --output artifacts/two_tier_relabelled_20261111_r1
```

Config sha256 `c769693a5cd0c531ff6c705fd613138392148313deef78fbf789d814f6ade10c`. Yeni çıktı dizinleri kullanın; var olan çıktının üzerine yazılmaz.
