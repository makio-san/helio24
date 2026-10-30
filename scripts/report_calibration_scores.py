"""Publish paired score-distribution and regional threshold-sensitivity reports."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from scripts.report_precision_followup import table


def run(source,name):
    report=json.loads((source/'report.json').read_text())
    for p,digest in report['artifact_hashes'].items():
        if sha256(source/p)!=digest:raise ValueError('Audit changed')
    paths=[ROOT/'docs'/f'{name}{s}.md' for s in ['', '.tr']]
    if any(p.exists() for p in paths):raise ValueError('Preserve report')
    s=pd.read_csv(source/'summary.csv');d=pd.read_csv(source/'region_influence.csv')
    coverage=table(s[['evaluation_year','calibration_year','period','rows','positives','positive_regions',
        'top1_positive_share','top3_positive_share','concentration_equivalent_regions']].fillna('undefined'))
    scores=table(s[['evaluation_year','period','positive_q05','positive_q50','positive_q95',
        'negative_q05','negative_q50','negative_q95','threshold','negative_alarm_rate']].fillna('undefined'))
    influence=table(s[['evaluation_year','period','threshold','loro_min','loro_max','loro_valid','loro_undefined']].fillna('undefined'))
    top=d.assign(abs_delta=d.threshold_delta.abs()).sort_values('abs_delta',ascending=False).groupby(['evaluation_year','period'],sort=False).head(1)
    examples=table(top.drop(columns='abs_delta').sort_values(['evaluation_year','period']).fillna('undefined'))
    evidence=table(pd.DataFrame([{'source':str((source/p).relative_to(ROOT)),'SHA-256':sha256(source/p)} for p in ['report.json','summary.csv','region_influence.csv']]))
    command=f'''```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/audit_calibration_scores.py \\
  --output {source.relative_to(ROOT)}
.venv/bin/python scripts/report_calibration_scores.py --source {source.relative_to(ROOT)} --report-name {name}
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en=f'''# Calibration score distributions and regional threshold sensitivity

The audit identifies two concrete sources of threshold sensitivity: positive windows
can be concentrated in very few HARPs, and the lower tail of positive scores can change
substantially between halves of a year. This is descriptive evidence, not proof of a
physical cause or a newly improved model. No model, label, deployed threshold or evaluation
population was changed; the reserved 2024–2025 test remains closed.

## Scope and method

The frozen annual models from `artifacts/walk_forward_20261028_r1` are verified by hashes.
For each completed evaluation year, inspect its preceding calibration year: full year,
early half and late half. The July boundary purges crossing observation/prediction windows
and excludes late HARPs shared with the early half, exactly as in the previous experiment.
This changes half-year composition; the full-year population need not equal the sum of
the purged halves. The 2019–2021 outer skips remain as previously documented.

All three periods are scored with the same frozen full-year sigmoid calibrators and
0.45 logistic/0.55 XGBoost blend for that year. This avoids changing the score mapping
while comparing halves; it does not provide prospective early-half estimates, because
the full-year calibrators have seen that year's labels. Scores are in-sample with respect
to calibration, while the underlying classifiers were trained earlier. No new classifiers
or calibrators are fitted and no evaluation-year prediction results are used in this audit.

## How many positive regions support each period?

{coverage}
`positives` counts overlapping windows, not independent flares. `positive_regions` counts
HARPs with at least one retained positive window. The top shares show concentration of
positive windows. `concentration_equivalent_regions` is 1/sum(p_h**2), where p_h is each
region's share of positives. It is a concentration index expressed as equally sized
regions, not an estimated independent sample size or a count of physical flares.

For evaluation 2017, the late half of calibration 2016 has 70 positive windows from only
2 HARPs; the largest contributes 0.685714. For evaluation 2018, the early half of calibration
2017 has 65 positive windows from a single HARP. For evaluation 2023, the late half of
calibration 2022 has 229 positive windows from 7 HARPs; the top three contribute 0.580786.
Hundreds of windows therefore need not provide broad region diversity.

## Score distributions on the common mapping

{scores}
Quantiles are the 5th, 50th and 95th percentiles computed separately for positive and
negative windows. The threshold is the existing exact threshold-selection routine at
recall >=0.95 within that period; it need not equal an interpolated 5th percentile.
`negative_alarm_rate` is the negative-window fraction at or above that period's threshold.
These are calibration diagnostics, not fresh evaluation metrics. All scores and shares
use a 0–1 scale.

For evaluation 2023, early/late thresholds are 0.030397 and 0.006393. Positive 5th percentiles
fall from 0.030897 to 0.006854, while negative 95th percentiles are 0.030738 and 0.033747.
The lower positive tail shifts much more than this negative-tail summary. A lower threshold
is consequently needed to retain 95% of the late-half positives. In evaluation 2022 the
direction reverses: early/late thresholds are 0.008212 and 0.023981. The direction of
within-year change is not stable across these years. Differences in region composition,
activity and retained labels may contribute; this audit does not distinguish their causes.

## Leave-one-positive-region-out sensitivity

{influence}
For each positive HARP, temporarily exclude all its windows, including its negative
windows, from the period. Recompute only the recall threshold on the remaining rows,
keeping model scores and calibrators fixed. Restore the region for the next calculation.
No permanent exclusion, policy update or evaluation-year optimization occurs. `loro_min`
and `loro_max` are observed perturbation extrema, not confidence intervals. `loro_undefined`
counts cases where both target classes no longer remain.

In evaluation 2017's late calibration half, removing one positive HARP changes the threshold
from 0.006265 to values ranging from 0.003033 to 0.077669. In evaluation 2023's late half,
the corresponding range is 0.005466–0.020886 around 0.006393. In evaluation 2018's early
half, removing the only positive HARP makes recall-threshold selection undefined. These
examples establish sensitivity to region composition conditional on the fitted scores;
they do not estimate future recall or prove that any region is mislabeled.

Largest absolute threshold change per period:

{examples}
The full list is preserved in `region_influence.csv`. For a period with no defined
perturbation, the table shows an undefined row rather than inventing an influence value.

## Decision and next experiment boundary

Do not repeatedly move the half-year boundary until past precision looks better. This
audit motivates evaluating calibration support by region diversity, as well as window
count. It does not establish a universal minimum region count or an optimal calibration
duration. A future candidate should compare fixed multi-year calibration windows and
their region diversity using earlier inner chronological folds; any longer calibration
window must remain entirely after classifier training, with temporal and HARP separation.
Comparisons must control for altered training history and evaluate the final fixed policy
on the same outer periods. No such new training or duration search has been run here.

Lack of calibration support should be reported explicitly rather than promising 95%
future recall. Calibration adjusts probability interpretation and operating points; it
does not guarantee better separation of hard positive and negative examples. The current
dashboard model remains unchanged. This is adaptive retrospective development, not an
independent test; associated windows and prior label/quality exclusions limit inference.

## Reproduction and evidence

{command}
Use fresh artifact directories and report names; preserve all frozen outputs. Review
both full editions and register their source hash and links in `docs/reports.json` and
`docs/reports.md` before publishing to a new HTML directory. Score tables and generated
HTML remain local ignored artifacts. Original model/threshold hashes, audit code hashes
and result hashes support reproducibility. No causal significance test is claimed.

{evidence}
'''
    tr=f'''# Kalibrasyon skor dağılımları ve bölgesel eşik duyarlılığı

Denetim, eşik duyarlılığı için iki somut bulgu ortaya koyuyor: pozitif pencereler çok az
HARP'ta yoğunlaşabiliyor ve pozitif skorların alt kuyruğu yılın yarıları arasında belirgin
değişebiliyor. Bu betimsel kanıttır; fiziksel nedenin veya yeni model iyileşmesinin kanıtı
değildir. Model, etiket, uygulama eşiği ve değerlendirme topluluğu değiştirilmedi;
ayrılmış 2024–2025 testi kapalı kaldı.

## Kapsam ve yöntem

`artifacts/walk_forward_20261028_r1` içindeki sabit yıllık modeller özetleriyle doğrulanır.
Tamamlanan her değerlendirme yılı için önceki kalibrasyon yılının tamamı, erken yarısı
ve geç yarısı incelenir. Temmuz sınırı, önceki deneyde olduğu gibi sınırı aşan gözlem/tahmin
pencerelerini temizler; erken yarıyla ortak HARP'ları geç yarıdan çıkarır. Bu işlem yarım
yıllık bileşimi değiştirir; tam yıllık topluluk, temizlenmiş yarıların toplamına eşit
olmak zorunda değildir. Önceki 2019–2021 dış tur atlamaları korunur.

Üç dönem de o yılın aynı sabit tam yıllık sigmoid kalibratörleri ve 0.45 lojistik/0.55
XGBoost birleşimiyle puanlanır. Böylece yarıları karşılaştırırken skor dönüşümü değişmez;
ancak tam yıllık kalibratörler o yılın etiketlerini gördüğünden erken yarı için ileriye
dönük tahmin üretilmiş olmaz. Temel sınıflandırıcılar daha önce eğitilse de skorlar
kalibrasyon açısından örneklem içidir. Yeni sınıflandırıcı veya kalibratör öğrenilmez;
bu denetimde değerlendirme yılı tahmin sonuçları kullanılmaz.

## Her dönemi kaç pozitif bölge destekliyor?

{coverage}
`positives`, bağımsız patlamaları değil, örtüşen pencereleri sayar. `positive_regions`,
en az bir korunan pozitif penceresi olan HARP sayısıdır. En yüksek paylar pozitif
pencerelerin yoğunlaşmasını gösterir. `concentration_equivalent_regions`, p_h her
bölgenin pozitif payı olmak üzere 1/sum(p_h**2) değeridir. Eşit büyüklükte bölgeler
cinsinden ifade edilen yoğunlaşma endeksidir; bağımsız örnek sayısı tahmini veya fiziksel
patlama sayısı değildir.

2017 değerlendirmesi için 2016 kalibrasyonunun geç yarısında 70 pozitif pencere yalnızca
2 HARP'tan gelir; en büyük pay 0.685714'tür. 2018 değerlendirmesi için 2017 kalibrasyonunun
erken yarısındaki 65 pozitif pencere tek HARP'tandır. 2023 değerlendirmesi için 2022
kalibrasyonunun geç yarısında 7 HARP'tan 229 pozitif pencere vardır; ilk üç bölgenin payı
0.580786'dır. Dolayısıyla yüzlerce pencere geniş bölge çeşitliliği sağlamayabilir.

## Ortak dönüşüm üzerindeki skor dağılımları

{scores}
Yüzdelikler, pozitif ve negatif pencereler için ayrı hesaplanan 5., 50. ve 95. yüzdeliklerdir.
Eşik, mevcut kesin eşik seçimi yordamının o dönemde recall >=0.95 için seçtiği değerdir;
ara değerlemeli 5. yüzdeliğe eşit olmak zorunda değildir. `negative_alarm_rate`, o dönemin
eşiğinde veya üzerindeki negatif pencere oranıdır. Bunlar yeni değerlendirme metrikleri
değil, kalibrasyon incelemeleridir. Tüm skorlar ve paylar 0–1 ölçeğindedir.

2023 değerlendirmesinde erken/geç eşikler 0.030397 ve 0.006393'tür. Pozitif 5. yüzdelikler
0.030897'den 0.006854'e düşerken negatif 95. yüzdelikler 0.030738 ve 0.033747'dir.
Pozitif alt kuyruk, bu negatif kuyruk özetinden çok daha fazla değişir. Bu nedenle geç
yarı pozitiflerinin %95'ini yakalamak için daha düşük eşik gerekir. 2022 değerlendirmesinde
yön tersinedir: erken/geç eşikler 0.008212 ve 0.023981'dir. Bu yıllar arasında yıl içi
değişimin yönü sabit değildir. Bölge bileşimi, etkinlik ve korunan etiket farkları katkı
yapabilir; denetim nedenleri birbirinden ayırmaz.

## Her pozitif bölgeyi sırayla dışarıda bırakma duyarlılığı

{influence}
Her pozitif HARP için negatif pencereleri dahil tüm pencereleri geçici olarak dönemden
çıkarılır. Model skorları ve kalibratörler sabitken kalan satırlarda yalnızca recall eşiği
yeniden hesaplanır. Bir sonraki hesapta bölge geri konur. Kalıcı dışlama, kural güncellemesi
veya değerlendirme yılı optimizasyonu yapılmaz. `loro_min` ve `loro_max`, gözlenen değişim
uçlarıdır; güven aralığı değildir. `loro_undefined`, iki hedef sınıfının artık bulunmadığı
durumları sayar.

2017 değerlendirmesinin geç kalibrasyon yarısında tek pozitif HARP'ı çıkarmak, eşiği
0.006265'ten 0.003033–0.077669 aralığındaki değerlere değiştirir. 2023 değerlendirmesinin
geç yarısında karşılık gelen aralık, 0.006393 çevresinde 0.005466–0.020886'dır. 2018
değerlendirmesinin erken yarısında tek pozitif HARP'ı çıkarmak recall eşiği seçimini tanımsız
yapar. Bu örnekler öğrenilmiş skorlar sabitken bölge bileşimine duyarlılığı gösterir;
gelecekteki recall'ı tahmin etmez veya herhangi bir bölgenin yanlış etiketlendiğini kanıtlamaz.

Dönem başına mutlak değerce en büyük eşik değişimi:

{examples}
Tam liste `region_influence.csv` içinde korunur. Tanımlı değişimi olmayan dönemde tablo,
etki değeri uydurmak yerine tanımsız satır gösterir.

## Karar ve sonraki deneyin sınırı

Geçmiş precision daha iyi görünene kadar yarım yıl sınırı tekrar tekrar kaydırılmamalıdır.
Bu denetim, kalibrasyon desteğini pencere sayısının yanında bölge çeşitliliğiyle değerlendirmeyi
gerekçelendirir. Evrensel minimum bölge sayısı veya en uygun kalibrasyon süresini belirlemez.
Sonraki aday, daha erken iç kronolojik bölümlerde sabit çok yıllık kalibrasyon pencerelerini
ve bölge çeşitliliğini karşılaştırmalıdır. Uzatılan her kalibrasyon penceresi, zaman ve
HARP ayrımıyla bütünüyle sınıflandırıcı eğitiminden sonra kalmalıdır. Karşılaştırmalar
değişen eğitim geçmişini kontrol etmeli ve son sabit kuralı aynı dış dönemlerde ölçmelidir.
Burada böyle yeni bir eğitim veya süre araması yapılmadı.

Kalibrasyon desteği yetersizse gelecekte %95 recall sözü vermek yerine açıkça raporlanmalıdır.
Kalibrasyon olasılık yorumunu ve çalışma noktasını ayarlar; zor pozitif ve negatif
örneklerin daha iyi ayrılmasını garanti etmez. Mevcut dashboard modeli korunur. Bu,
bağımsız test değil, uyarlamalı geçmişe dönük geliştirmedir; bağımlı pencereler ve önceki
etiket/kalite dışlamaları çıkarımları sınırlar.

## Yeniden üretim ve kanıt

{command}
Yeni artifact dizinleri ve rapor adları kullanın; tüm sabit çıktıları koruyun. İki tam
sürümü gözden geçirip kaynak özetini ve bağlantıları `docs/reports.json` ve `docs/reports.md`
dosyalarına kaydedin; ardından yeni HTML dizinine yayımlayın. Skor tabloları ve üretilen
HTML yerel, Git dışında çıktılar olarak kalır. Özgün model/eşik özetleri, denetim kodu
özetleri ve sonuç özetleri yeniden üretimi destekler. Nedensel anlamlılık testi iddia edilmez.

{evidence}
'''
    for p,text in zip(paths,[en,tr]):p.write_text(text)
    print('\n'.join(map(str,paths)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--report-name',required=True);a=p.parse_args();run(a.source.resolve(),a.report_name)
