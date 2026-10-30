"""Write full bilingual results for the shared-training calibration-window experiment."""
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
    r=json.loads((source/'report.json').read_text())
    for p,h in r['artifact_hashes'].items():
        if sha256(source/p)!=h:raise ValueError('Artifact changed')
    paths=[ROOT/'docs'/f'{name}{s}.md' for s in ['', '.tr']]
    if any(p.exists() for p in paths):raise ValueError('Preserve report')
    m=pd.DataFrame(r['metrics'])
    short=table(m[['year','arm','n','positives','precision','recall','fp','fn','threshold']].fillna('undefined'))
    full=table(m.fillna('undefined'))
    coverage=table(pd.DataFrame([{'year':f['year'],'role':role,**a} for f in r['folds'] for role,a in f['audit']['roles'].items()]))
    availability=table(pd.DataFrame([{'year':f['year'],'status':f['status'],
        'additional_evaluation_rows_removed':f['audit']['additional_evaluation_rows_removed'],
        'unavailable':json.dumps(f.get('unavailable',{}),sort_keys=True),'passes_gate':f.get('passes_gate')} for f in r['folds']]).fillna('undefined'))
    ci=table(pd.DataFrame([{'year':x['year'],'control':x['control'],'metric':metric,**v} for x in r['paired_intervals'] for metric,v in x['differences'].items()]).fillna('undefined'))
    deltas=[]
    for year,g in m.groupby('year'):
        a=g.set_index('arm')
        if 'shared_train_two_year' not in a.index:continue
        for control in ['original_baseline','shared_train_one_year']:
            if control not in a.index:continue
            new,old=a.loc['shared_train_two_year'],a.loc[control]
            deltas.append({'year':year,'control':control,'precision_delta':new.precision-old.precision,
                'recall_delta':new.recall-old.recall,'fp_delta':int(new.fp-old.fp)})
    delta=table(pd.DataFrame(deltas).fillna('undefined'))
    positive=m[(m.arm=='shared_train_two_year') & m.positives.gt(0)]
    hits=int(positive.recall.ge(.95).sum());total=len(positive)
    gate=r['all_year_gate_passed']
    evidence=table(pd.DataFrame([{'source':str((source/p).relative_to(ROOT)),'SHA-256':sha256(source/p)} for p in ['report.json','metrics.csv']]))
    command=f'''```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_calibration_windows.py \\
  --protocol config/calibration-windows-v1.json --output {source.relative_to(ROOT)}
.venv/bin/python scripts/report_calibration_windows.py --source {source.relative_to(ROOT)} --report-name {name}
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en=f'''# One- and two-year calibration with shared classifier training

The two-year arm reaches recall >=0.95 in {hits} of {total} positive evaluation years.
The all-year acceptance gate is `{gate}`. No model or alarm policy was promoted to the
dashboard. The reserved 2024–2025 test stays closed. Year-specific gains must not be
presented as a consistent improvement without the control comparisons below.

## Frozen question and controls

The preceding audit found sparse positive-region support and threshold sensitivity.
This experiment asks whether a fixed two-year calibration window improves temporal
transfer compared with a fixed one-year window when underlying classifier training is
identical. `config/calibration-windows-v1.json` freezes the design; there is no duration
grid or retrospective split-date tuning.

For evaluation year Y, the two new arms share logistic and XGBoost classifiers trained
before January 1 of Y-2. Prediction windows must end by that date. Both retain the same
96 features, original hyperparameters and 0.45/0.55 blend. `shared_train_two_year` calibrates
on Y-2 and Y-1; `shared_train_one_year` uses only the Y-1 subset. Training HARPs are removed
from calibration, and observation/prediction intervals must lie within calendar boundaries.
Each arm fits sigmoid calibration and selects its recall >=0.95 threshold on its own
calibration window, freezes the threshold, then predicts the evaluation year. Probability
fitting and threshold selection still reuse the same calibration rows; this is explicit.

`original_baseline` uses the frozen original annual model with an extra year of classifier
training, where available. Comparing the two new arms isolates calibration duration
under shared training. Comparing either with the original baseline also changes the
classifier training history and is not solely a calibration-duration contrast.

Use the original annual evaluation population, excluding any additional HARP shared
with the new training or two-year pool, and apply the same resulting rows to all arms.
Report any removed rows. Original label/quality exclusions remain. All source models,
predictions and input manifests are hash-verified; baseline keys and labels must align.

## Counts, region diversity and availability

{coverage}
`positive_regions` counts HARPs with retained positive windows, not independent flares.
More windows do not automatically imply more positive-region diversity; inspect the
one-year and two-year counts together. Counts refer to purged populations.

{availability}
Arms independently require both training and calibration classes and nonempty evaluation.
Unavailable arms are never replaced by baseline. The original baseline exists only in
its previously completed folds. A two-year arm may be available in a year without an
original baseline; such results are unpaired evidence, not a measured improvement.
Zero-positive evaluation years retain FP/FPR but have undefined recall/AP. If no alarms
are emitted, precision is undefined too. `undefined` does not mean zero.

## Annual precision, recall and false-positive windows

{short}
Scores are fractions on a 0–1 scale; counts are overlapping forecast windows, not
independent flares or notifications. Each arm uses its own transferred calibration
threshold. Do not count a higher precision at recall below 0.95 as the requested success.

Two-year arm minus each available control:

{delta}
Positive precision/recall differences favor the two-year arm; negative FP differences
mean fewer false-positive windows. No pooled multi-year average replaces these contrasts.

## Complete metrics and acceptance

{full}
Precision measures positives among alarms, recall caught positive windows, and accuracy
all correct classifications. AP measures ranking; lower Brier/log loss is better
probabilistic scoring. The frozen gate requires complete candidate coverage of all
originally baseline-comparable positive years, higher precision with recall >=0.95,
AP no lower and Brier/log loss no higher than both controls in every such year. No
automatic deployment follows even a passed gate. Sparse or missing periods stay visible.

## Findings from this run

Only 2022 passes the full per-year gate against both controls. Even there, versus the
shared-training one-year control, precision changes from 0.041375 to 0.041491 and false
positives from 9592 to 9564, with recall unchanged at 0.983373. Both windows contain 9
positive HARPs; extending the window does not add positive-region diversity in that year.

In 2016, positive HARPs increase from 25 to 69, yet false positives rise from 2137 to
3812 and precision falls from 0.076092 to 0.044612 versus the shared-training control.
In 2023, positive HARPs increase from 12 to 21; recall rises from 0.889885 to 0.959027,
but false positives rise from 5840 to 11694 and precision falls from 0.106350 to 0.060194.
More positive-region coverage therefore does not itself establish a better operating
point. No additional evaluation rows were removed in any year.

The 2019 two-year arm has 312 false-positive windows and no positive evaluation windows;
there is no original or one-year control available for that year. In 2020 and 2021 no
arm is available. These periods are not omitted or counted as improvements. The tested
two-year policy is not adopted; another duration search is not justified by this run alone.

## Paired conditional uncertainty

{ci}
Intervals are two-year arm minus the named control, from 1000 paired whole-HARP bootstrap
draws per year, seed 24. Both arms use the same sampled regions with classifiers,
calibrators and thresholds fixed. Fitting and historical model-selection uncertainty
are excluded. `valid_draws` identifies undefined precision/recall draws. Adjacent annual
folds share historical training and are not independent replications. Intervals spanning
zero do not establish a directional change at that interval level.

## Interpretation limits

This is adaptive retrospective development motivated by prior diagnostics, not an
untouched test. A longer window trades recency for more data and potentially more positive
regions; neither calibration stability nor precision improvement follows automatically.
The shared-training control is necessary because making room for a longer calibration
period shortens classifier training. Stronger or weaker scores against the original
baseline cannot be attributed solely to duration.

Retain the current model unless the multi-period evidence supports replacing it. Any
next policy must be fixed using earlier inner chronological folds; do not pick a different
duration for each evaluated year using its outcomes. No live forecast, label correction,
additional duration search or release decision is claimed in this report.

## Reproduction

{command}
Choose fresh output directories and report names. Preserve frozen source artifacts
and protocols. Review both full editions, register their source hash and links in
`docs/reports.json` and `docs/reports.md`, and publish into a fresh HTML directory.
Models, calibrators, predictions and generated HTML remain local ignored artifacts.
The experiment records source, protocol, code and output hashes.

{evidence}
'''
    tr=f'''# Ortak sınıflandırıcı eğitimiyle bir ve iki yıllık kalibrasyon

İki yıllık kol, pozitif değerlendirme yıllarının {total} tanesinden {hits} tanesinde
recall >=0.95 sağladı. Tüm yıllar için kabul kontrolü `{gate}` oldu. Dashboard modeli
ve alarm kuralı değiştirilmedi. Ayrılmış 2024–2025 testi kapalı kaldı. Aşağıdaki kontrol
karşılaştırmaları olmadan tek yıllık kazanımlar tutarlı iyileşme olarak sunulmamalıdır.

## Sabit soru ve kontrol kolları

Önceki denetim, az sayıda pozitif bölge desteği ve eşik duyarlılığı buldu. Bu deney,
temel sınıflandırıcı eğitimi aynıyken sabit iki yıllık kalibrasyon penceresinin sabit
bir yıllık pencereye göre dönemler arası aktarımı iyileştirip iyileştirmediğini sorar.
Tasarım `config/calibration-windows-v1.json` ile sabittir; süre ızgarası veya sonradan
bölme tarihi ayarlaması yoktur.

Y değerlendirme yılında iki yeni kol, Y-2 yılının 1 Ocak tarihinden önce eğitilmiş aynı
lojistik ve XGBoost sınıflandırıcılarını paylaşır. Tahmin pencereleri o tarihe kadar
bitmelidir. İki kolda aynı 96 özellik, özgün hiperparametreler ve 0.45/0.55 birleşimi
korunur. `shared_train_two_year`, Y-2 ve Y-1'de; `shared_train_one_year`, yalnızca Y-1
alt kümesinde kalibre edilir. Eğitim HARP'ları kalibrasyondan çıkarılır, gözlem/tahmin
aralıkları takvim sınırları içinde kalmalıdır. Her kol kendi kalibrasyon penceresinde
sigmoid kalibrasyonunu öğrenir, recall >=0.95 eşiğini seçip sabitler, ardından değerlendirme
yılını tahmin eder. Olasılık öğrenimi ve eşik seçimi aynı kalibrasyon satırlarını tekrar
kullanır; bu açıkça belirtilmiştir.

`original_baseline`, mevcutsa sınıflandırıcı eğitiminde bir yıl daha kullanan sabit
özgün yıllık modeldir. İki yeni kolun karşılaştırılması, ortak eğitim altında kalibrasyon
süresini ayırır. Bunlardan herhangi birini özgün referansla karşılaştırmak sınıflandırıcı
eğitim geçmişini de değiştirir; yalnızca kalibrasyon süresi karşılaştırması değildir.

Özgün yıllık değerlendirme topluluğu kullanılır; yeni eğitim veya iki yıllık havuzla
ortak ek HARP varsa çıkarılır, aynı kalan satırlar tüm kollara uygulanır. Çıkarılan
satırlar raporlanır. Özgün etiket/kalite dışlamaları korunur. Kaynak modeller, tahminler
ve girdi kayıtları özetleriyle doğrulanır; referans anahtarları ve etiketleri eşleşmelidir.

## Sayılar, bölge çeşitliliği ve kullanılabilirlik

{coverage}
`positive_regions`, bağımsız patlamaları değil, korunan pozitif penceresi olan HARP'ları
sayar. Daha fazla pencere otomatik olarak daha fazla pozitif bölge çeşitliliği demek
değildir; bir ve iki yıllık sayılar birlikte incelenmelidir. Sayılar temizlenmiş topluluklara aittir.

{availability}
Her kol bağımsız olarak eğitim ve kalibrasyonda iki sınıfı ve boş olmayan değerlendirmeyi
gerektirir. Kullanılamayan kollar referansla doldurulmaz. Özgün referans yalnızca önceki
tamamlanmış turlarında vardır. İki yıllık kol, özgün referansı olmayan bir yılda kullanılabilir
olabilir; böyle sonuçlar ölçülmüş iyileşme değil, eşleşmemiş kanıttır. Pozitif olmayan
değerlendirme yıllarında FP/FPR korunur, recall/AP tanımsızdır. Hiç alarm yoksa precision
da tanımsızdır. `undefined` sıfır değildir.

## Yıllık precision, recall ve yanlış pozitif pencereler

{short}
Skorlar 0–1 ölçeğindedir; sayılar bağımsız patlama veya bildirimleri değil, örtüşen
tahmin pencerelerini anlatır. Her kol kendi aktarılmış kalibrasyon eşiğini kullanır.
Recall 0.95 altındayken daha yüksek precision, istenen başarı olarak sayılmamalıdır.

İki yıllık kol eksi kullanılabilir her kontrol:

{delta}
Pozitif precision/recall farkları iki yıllık kolu destekler; negatif FP farkları daha
az yanlış pozitif pencere demektir. Çok yıllık tek ortalama bu karşılaştırmaların yerine geçmez.

## Tüm metrikler ve kabul

{full}
Precision alarmlar içindeki pozitifleri, recall yakalanan pozitif pencereleri, accuracy
tüm doğru sınıflandırmaları ölçer. AP sıralamayı ölçer; düşük Brier/log loss daha iyi
olasılıksal puanlamadır. Sabit kontrol, özgün referansla karşılaştırılabilir tüm pozitif
yılların kapsanmasını; her birinde iki kontrole göre recall >=0.95 koşulunda daha yüksek
precision, düşmeyen AP ve artmayan Brier/log loss gerektirir. Kontrol geçilse bile otomatik
dağıtım yoktur. Seyrek veya eksik dönemler görünür tutulur.

## Bu çalıştırmanın bulguları

Yalnızca 2022, iki kontrole göre tüm yıllık kabul koşullarını geçer. O yılda bile ortak
eğitimli bir yıllık kontrole göre precision 0.041375'ten 0.041491'e, yanlış pozitifler
9592'den 9564'e değişir; recall 0.983373 olarak kalır. İki pencerede de 9 pozitif HARP
vardır; süreyi uzatmak o yılda pozitif bölge çeşitliliği eklemez.

2016'da pozitif HARP sayısı 25'ten 69'a çıkarken, ortak eğitimli kontrole göre yanlış
pozitifler 2137'den 3812'ye yükselir ve precision 0.076092'den 0.044612'ye düşer.
2023'te pozitif HARP sayısı 12'den 21'e çıkar; recall 0.889885'ten 0.959027'ye yükselir,
fakat yanlış pozitifler 5840'tan 11694'e çıkar ve precision 0.106350'den 0.060194'e düşer.
Dolayısıyla daha fazla pozitif bölge kapsamı tek başına daha iyi çalışma noktasını
kanıtlamaz. Hiçbir yılda ek değerlendirme satırı çıkarılmadı.

2019 iki yıllık kolunda 312 yanlış pozitif pencere vardır; pozitif değerlendirme penceresi
yoktur ve o yıl özgün veya bir yıllık kontrol bulunmaz. 2020 ve 2021'de hiçbir kol
kullanılamaz. Bu dönemler gizlenmez veya iyileşme sayılmaz. Denenen iki yıllık kural
benimsenmez; bu çalışma tek başına başka bir süre aramasını gerekçelendirmez.

## Eşleştirilmiş koşullu belirsizlik

{ci}
Aralıklar iki yıllık kol eksi belirtilen kontroldür; yıl başına 24 tohumla eşleştirilmiş
bütün HARP'ları örnekleyen 1000 bootstrap tekrarı kullanır. Sınıflandırıcılar, kalibratörler
ve eşikler sabitken iki kolda aynı örneklenmiş bölgeler kullanılır. Öğrenim ve geçmiş
model seçimi belirsizliği dahil değildir. `valid_draws`, tanımsız precision/recall
tekrarlarını izler. Komşu yıllık turlar geçmiş eğitimi paylaşır; bağımsız tekrarlar değildir.
Sıfırı içeren aralık o aralık düzeyinde yönlü değişimi göstermez.

## Yorum sınırları

Bu, önceki incelemelerin yönlendirdiği uyarlamalı geçmişe dönük geliştirmedir; el değmemiş
test değildir. Uzun pencere, yakın tarihli olma özelliğinden ödün verip daha fazla veri
ve olası pozitif bölge çeşitliliği sağlar; bundan otomatik olarak kalibrasyon kararlılığı
veya precision iyileşmesi çıkmaz. Uzun kalibrasyona yer açmak sınıflandırıcı eğitimini
kısalttığından ortak eğitim kontrolü gereklidir. Özgün referansa göre daha güçlü veya
zayıf skorlar yalnızca süreye bağlanamaz.

Çok dönemli kanıt model değiştirmeyi desteklemedikçe mevcut model korunmalıdır. Sonraki
kural daha erken iç kronolojik bölümlerde sabitlenmeli; değerlendirme sonuçlarına bakarak
her yıl için farklı süre seçilmemelidir. Bu raporda canlı tahmin, etiket düzeltmesi,
ek süre araması veya dağıtım kararı yapıldığı iddia edilmez.

## Yeniden üretim

{command}
Yeni çıktı dizinleri ve rapor adları seçin. Sabit kaynak çıktıları ve protokolleri
koruyun. İki tam sürümü gözden geçirip kaynak özetini ve bağlantıları `docs/reports.json`
ve `docs/reports.md` dosyalarına kaydedin; yeni HTML dizinine yayımlayın. Modeller,
kalibratörler, tahminler ve üretilen HTML yerel, Git dışında çıktılar olarak kalır.
Deney kaynak, protokol, kod ve çıktı özetlerini kaydeder.

{evidence}
'''
    for p,text in zip(paths,[en,tr]):p.write_text(text)
    print('\n'.join(map(str,paths)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--report-name',required=True);a=p.parse_args();run(a.source.resolve(),a.report_name)
