# Etiket kapsamı denetimi: hangi M/X patlamaları pozitif etikete ulaşıyor (2026-11-10)

## Karar

[Dondurulmuş protokolün](../config/label-coverage-v1.json) R1 okuması geçerli: etiket kapsamı 25. güneş döngüsünde
çöktü. Kesin JSOC `NOAA_ARS` ilişkilendirmesinin bir HARP'a eşlediği SGAS M/X patlamalarının %90,1'i (2014) ve
%87,4'ü (2015) pozitif bir geliştirme penceresine düşerken, 2022'de yalnızca %29,6'sı ve 2023'te %28,9'u düşüyor.
Eksik patlamalar, SWAN-SF V2'nin hiçbir HARP'a atamadığı HEK M/X olaylarıdır: 2022'de 174, 2023'te 293; bunların
132 ve 272'si `NOAA_ARS` üzerinden bir HARP'a eşleniyor. Kapalı-güvenli kural bunları içeren pencereleri dışladığı
için patlayan HARP yalnızca negatif pencerelerle kalıyor. 2022 ve 2023'te bu gizli HARP'lar (28 ve 52), izleme
eşiğindeki yanlış alarm pencerelerinin %38,6 ve %57,2'sini üretiyor; pencerelerinin çıkarılması precision'ı
0.0442'den 0.0701'e ve 0.1186'dan 0.2390'a, AP'yi 0.2800'den 0.3500'e ve 0.2206'dan 0.3445'e yükseltiyor. Eğitim
tablosu aynı boşluğu taşıyor; dolayısıyla temel model 25. döngü patlamalarının üçte birinden azıyla uyduruldu.
M/X olaylarının bağımsız HARP ilişkilendirmesi ve yeniden etiketlenmiş tabloda ileri yürüyen yeniden çalıştırma
için ayrı bir dondurulmuş protokol gerekçelidir. Burada hiçbir şey yeniden etiketlenmedi; hiçbir model, eşik veya
uyarı değişmedi; ayrılmış 2024–2025 testi okunmadı. Protokol herhangi bir sonuçtan önce donduruldu ve commit edildi.

## Neden bu denetim

25. döngü teşhisi, FP pencerelerinin %83'ünün (2022) ve %74'ünün (2023) yıl içinde hiç pozitif penceresi olmayan
HARP'lardan geldiğini ve 528 ile 703 HARP'tan yalnızca 12 ve 27'sinin patladığını buldu. Dondurulmuş V2 etiket
envanteri denetimi hiçbir HARP'a atanmamış 622 HEK M/X olayını zaten listelemişti; yıllara dağılımı incelenmemişti.

## Yöntem

Kaynaklar: yayımlanmış NOAA SGAS ürünleri (bölge numarası, tepe zamanı ve X-ışını sınıfıyla A bölümü enerjik
olaylar; D günü ürünü UT günü D−1'i listeler), HARP başına günlük JSOC `NOAA_ARS` anahtar sözcüğü, dondurulmuş
geliştirme tablosu, saklanan temel model olasılıkları ve recall 0,90 izleme eşikleri ile V2'nin atamadığı HEK M/X
olaylarının dondurulmuş listesi. Bir SGAS M/X olayı, tepe tarihinde `NOAA_ARS` değeri bölge numarasını içeren her
HARP'a eşlenir. O HARP'ın tepeyi içeren bir geliştirme penceresi varsa ve pozitifse `covered`; böyle pencereler
varsa ve hepsi negatifse `hidden`; hiçbiri tepeyi içermiyorsa (kapalı-güvenli kuralla dışlanmış, kat sınırında
çıkarılmış veya gözlenmemiş) `no_window`. HEK atanmamış olayları SGAS olaylarıyla sınıf ve en fazla 5 dakikalık
tepe zamanı farkıyla eşleştirilir. Bir değerlendirme yılının gizli HARP'ları, `hidden` veya `no_window` olayı olan
ve pozitif penceresi olmayan HARP'lardır; çıkarılmaları etiket etkisi için bir sınırdır, yeniden etiketleme değil.

## Yıla göre kapsam

| yıl | SGAS M/X olayı | bölgeli | HARP'a eşlenen | covered | hidden | no_window | covered payı | pozitif pencere |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 207 | 193 | 172 | 155 | 0 | 17 | 0.9012 | 2363 |
| 2015 | 130 | 124 | 119 | 104 | 2 | 13 | 0.8739 | 1403 |
| 2016 | 16 | 15 | 15 | 13 | 0 | 2 | 0.8667 | 205 |
| 2017 | 45 | 42 | 42 | 40 | 0 | 2 | 0.9524 | 253 |
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 |
| 2019 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 |
| 2020 | 2 | 0 | 0 | 0 | 0 | 0 |  | 0 |
| 2021 | 29 | 28 | 26 | 16 | 0 | 10 | 0.6154 | 204 |
| 2022 | 178 | 156 | 152 | 45 | 2 | 105 | 0.2961 | 421 |
| 2023 | 359 | 343 | 342 | 99 | 26 | 217 | 0.2895 | 781 |

2018–2020'de geliştirme tablosunda M/X patlaması yok; 2020'de bölge numarası olmayan iki SGAS olayı var.

## V2'nin atamadığı HEK olayları

| yıl | HEK atanmamış | SGAS olayıyla eşleşen | HARP'a eşlenen |
| --- | --- | --- | --- |
| 2014 | 45 | 40 | 25 |
| 2015 | 21 | 20 | 13 |
| 2016 | 6 | 6 | 5 |
| 2017 | 6 | 6 | 3 |
| 2020 | 2 | 2 | 0 |
| 2021 | 16 | 16 | 13 |
| 2022 | 174 | 157 | 132 |
| 2023 | 293 | 282 | 272 |

## Altı değerlendirme yılına etkisi

| yıl | gizli HARP | pencereleri | FP penceresi | gizli HARP FP penceresi | FP payı | precision | gizlisiz precision | AP | gizlisiz AP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | 2 | 304 | 7634 | 167 | 0.0219 | 0.2082 | 0.2118 | 0.5079 | 0.5105 |
| 2015 | 8 | 1791 | 6294 | 528 | 0.0839 | 0.1721 | 0.1849 | 0.4924 | 0.4985 |
| 2016 | 0 | 0 | 1303 | 0 | 0.0000 | 0.1106 | 0.1106 | 0.3664 | 0.3664 |
| 2017 | 1 | 203 | 1035 | 51 | 0.0493 | 0.1850 | 0.1928 | 0.8117 | 0.8125 |
| 2022 | 28 | 5127 | 8949 | 3456 | 0.3862 | 0.0442 | 0.0701 | 0.2800 | 0.3500 |
| 2023 | 52 | 7708 | 4852 | 2773 | 0.5715 | 0.1186 | 0.2390 | 0.2206 | 0.3445 |

- 2014 ve 2015'te az sayıdaki gizli HARP, FP pencerelerinin %2,2 ve %8,4'ünü tutuyor ve çıkarılmaları precision'ı
  0,013'ten az değiştiriyor. 2022 ve 2023'te %38,6 ve %57,2'sini tutuyorlar.
- Negatif bir pencerenin içinde kalan gizli patlamalar nadir (2022'de 2, 2023'te 26); baskın durum `no_window`:
  V2 patlamayı hiçbir bölgeye atamadığı için tepeyi içeren pencere dışlandı, HARP'ın diğer pencereleri negatif kaldı.
- 2023'te birden fazla HARP'a eşlenen 7 olay var; en iyi sonuçlarına göre sınıflandırıldılar.

## Sınırlar

SGAS bölge numaraları ve `NOAA_ARS` de V2'ninki gibi ilişkilendirmedir; bu denetim uyuşmalarını ölçer, gerçeği
değil ve `NOAA_ARS`'nin bir HARP'a eşlediği bir patlama yine de yanlış atfedilmiş olabilir. SGAS enerjik olayları
listeler ve bazı M sınıfı patlamaları atlayabilir. Yalnızca geliştirme yılları; ayrılmış test okunmadı. Gizli
HARP'ların çıkarılması, doğru bir ilişkilendirmenin izleme eşiğinde geri kazandıracağının üst sınırıdır; çünkü
yeniden etiketlenmiş bir tablo uydurulan modeli ve kalibrasyon yılı eşiğini de değiştirir.

## Yeniden üretim

```sh
python -m scripts.audit_label_coverage --output artifacts/label_coverage_20261110_r1
```

Config sha256 `6065e626e83ec2c241e5b695d372314569c154a6c040d43c2ae47594d5ea8927`. Yeni çıktı dizinleri kullanın; var olan çıktının üzerine yazılmaz.
