"""Render paired multi-period hard-negative experiment results."""
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
    result=json.loads((source/'report.json').read_text())
    for p,h in result['artifact_hashes'].items():
        if sha256(source/p)!=h:raise ValueError('Experiment artifact changed')
    paths=[ROOT/'docs'/f'{name}{s}.md' for s in ['', '.tr']]
    if any(p.exists() for p in paths):raise ValueError('Preserve reports')
    m=pd.DataFrame(result['metrics']);summary=table(m[['year','arm','n','positives','precision','recall','fp','fn','threshold']].fillna('undefined'))
    full=table(m.fillna('undefined'))
    fold=table(pd.DataFrame([{k:f.get(k) for k in ['year','status','reason','teacher_rows','eligible_negatives',
        'hard_negatives','targeted_weight_sum','uniform_weight_sum','passes_gate','beats_uniform_precision']} for f in result['folds']]).fillna('undefined'))
    ci=table(pd.DataFrame([{'year':r['year'],'control':r['control'],'metric':metric,**v}
        for r in result['paired_intervals'] for metric,v in r['differences'].items()]).fillna('undefined'))
    differences=[]
    for year,g in m.groupby('year'):
        a=g.set_index('arm');b=a.loc['baseline_unweighted'];h=a.loc['hard_negative_weighted'];u=a.loc['uniform_negative_matched_weight']
        differences.append({'year':year,'precision_delta':h.precision-b.precision,'recall_delta':h.recall-b.recall,
            'fp_delta':int(h.fp-b.fp),'precision_delta_vs_uniform':h.precision-u.precision})
    delta=table(pd.DataFrame(differences).fillna('undefined'))
    valid=m[(m.arm=='hard_negative_weighted') & m.positives.gt(0)]
    hits=int(valid.recall.ge(.95).sum());den=len(valid)
    better=sum(d['precision_delta']>0 for d in differences)
    passed=result['all_year_gate_passed']
    evidence=table(pd.DataFrame([{'source':str((source/p).relative_to(ROOT)),'SHA-256':sha256(source/p)} for p in ['report.json','metrics.csv']]))
    commands=f'''```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_hard_negative_years.py \\
  --protocol config/hard-negative-v2.json --output {source.relative_to(ROOT)}
.venv/bin/python scripts/report_hard_negative_years.py --source {source.relative_to(ROOT)} --report-name {name}
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en=f'''# Multi-period hard-negative training comparison

The hard-negative candidate reaches recall >=0.95 in {hits} of {den} comparable positive
evaluation years. Precision exceeds baseline in {better} evaluated years. The all-year
gate result is `{passed}`. No dashboard model was promoted; the reserved 2024–2025 test
remains closed. A gain in one year is not presented as general improvement.

## Frozen design and data separation

`config/hard-negative-v2.json` makes the previously selected design executable without
changing its candidate budget. The annual populations, 96 magnetic features and baseline
hyperparameters match `walk-forward-v1`. All prior model and prediction hashes are verified;
new annual split audits and evaluation metadata must exactly match the frozen baseline.
All original outer-training rows are retained. Historical label/quality exclusions remain.

For evaluation year Y, calibration is Y-1 and outer training precedes that year. A teacher
XGBoost fits before January 1 of Y-3; mining uses known negatives from the last two outer-
training years. Observation/prediction boundaries are purged; mining HARPs also seen by
the teacher are excluded from mining, not from final student training. The highest-scored
ceil(0.10 * eligible_count) negatives are selected, using forecast time and HARP to break
ties. The teacher never sees the mining windows during fitting. Evaluation-year errors
are not used as training examples, features or mining labels.

Three fixed arms are evaluated:

- `baseline_unweighted`: the frozen 0.45 logistic/0.55 XGBoost ensemble.
- `hard_negative_weighted`: selected negatives receive weight 3, every other training
  row weight 1. Only the XGBoost component is retrained; logistic stays unchanged.
- `uniform_negative_matched_weight`: all training negatives receive weight
  `1 + 2 * hard_negative_count / outer_training_negative_count`, positives weight 1.
  Its total training negative weight matches the targeted arm exactly up to rounding.

Each new XGBoost is sigmoid-calibrated on the same outer calibration year. Its 0.45/0.55
ensemble threshold is selected there at recall >=0.95 and written before evaluation
predictions. It is never retuned on evaluation labels. Neither the blend nor the weight
factor is selected from evaluation results. Separating probability calibration and
threshold selection into different periods was not part of this experiment.

## Coverage, mining counts and gates

{fold}
The existing 2019–2021 fold skips are preserved because their preceding calibration
years lack positive examples. In the retained 2018 evaluation data there are no positives;
recall is undefined, while false alarms remain measurable. Missing class diversity in
teacher fitting or no mining negatives would make new arms unavailable, not silently
replace them with baseline. `undefined` never means a measured zero.

## Precision, recall and false alarms by period

{summary}
Scores are fractions on a 0–1 scale. FP and FN count overlapping forecast windows, not
independent flares or alert episodes. Each annual comparison uses the same population
and transferred thresholds for all arms, but populations and event prevalence differ
between years. More precision at the cost of missing the recall objective is not accepted
as the requested improvement.

Candidate minus baseline differences, and precision difference versus the uniform control:

{delta}
Positive precision/recall differences favor the candidate; negative FP differences mean
fewer false-positive windows. No pooled multi-year score substitutes for this table.

## Complete metric results

{full}
Precision measures true positive windows among alarms, recall the positive windows caught,
and accuracy all correct classifications. AP measures ranking; lower Brier/log loss is
better probabilistic scoring. The frozen gate requires higher precision and recall >=0.95
in every comparable positive evaluation year, AP no lower and Brier/log loss no higher
than baseline in each year. To attribute benefit to targeted mining, precision must also
beat the matched uniform control in those years. Gate success alone would not trigger
automatic deployment; failure retains the existing model.

## Paired conditional uncertainty

{ci}
Each interval is candidate minus the named control, using 1000 paired whole-HARP bootstrap
draws with seed 24 within a year. Both arms use the same sampled regions and fixed models
and thresholds. Training, calibration and model-selection uncertainty are omitted. FP
intervals concern resampled window counts; recall draws are undefined in a zero-positive
year. Intervals spanning zero do not establish a directional difference at that interval
level. Adjacent years share historical training data and are not independent replications.

## Interpretation limits and next decision

This is an adaptive development experiment: prior annual errors motivated the design.
The test years were not fresh, even though no evaluation rows were used for fitting.
Hard-negative weighting can suppress true positives or distort calibration as well as
reduce false alarms. A negative result rejects this particular weighting recipe, not
every possible method of learning from difficult negatives. Inspect the year-by-year
and uniform-control comparisons before choosing another hypothesis. Any next experiment
needs a new frozen protocol; do not change thresholds on these years to manufacture a
95% recall claim. No further candidate search or live deployment is claimed here.

## Reproduction and evidence

{commands}
Choose fresh output directories and report names for reruns. Preserve frozen models,
protocols and predictions. Review both editions and register their source hash and links
in `docs/reports.json` and `docs/reports.md` before publishing. Generated models, mined
training windows, predictions and HTML remain local ignored artifacts. Model, threshold,
prediction and code hashes are recorded in the experiment report.

{evidence}
'''
    tr=f'''# Birden fazla dönemde zor negatif ağırlıklı eğitim karşılaştırması

Zor negatif adayı, karşılaştırılabilir {den} pozitif değerlendirme yılının {hits} tanesinde
recall >=0.95 sağladı. Precision, {better} değerlendirme yılında referansı geçti. Tüm yıllar
için kabul kontrolü sonucu `{passed}` oldu. Dashboard modeli değiştirilmedi; ayrılmış
2024–2025 testi kapalı kaldı. Tek yıldaki kazanç genel iyileşme olarak sunulmaz.

## Sabit tasarım ve veri ayrımı

`config/hard-negative-v2.json`, önceki seçilmiş tasarımı aday bütçesini değiştirmeden
çalıştırılabilir hale getirir. Yıllık örnek toplulukları, 96 manyetik özellik ve referans
hiperparametreler `walk-forward-v1` ile aynıdır. Önceki model ve tahmin özetleri doğrulanır;
yeni yıllık ayrım denetimleri ve değerlendirme meta verileri sabit referansla birebir
eşleşmelidir. Özgün dış eğitim satırlarının tamamı korunur. Önceki etiket/kalite dışlamaları geçerlidir.

Y değerlendirme yılında kalibrasyon Y-1'dir, dış eğitim bu yıldan öncedir. Öğretmen XGBoost,
Y-3 yılının 1 Ocak tarihinden önce eğitilir; seçim dış eğitimin son iki yılındaki negatif
olduğu bilinen örneklerden yapılır. Gözlem/tahmin sınırları temizlenir; öğretmenin gördüğü
HARP'lar seçimden çıkarılır, son öğrenci eğitiminden çıkarılmaz. En yüksek skorlu
ceil(0.10 * eligible_count) negatif seçilir; eşitlikler tahmin zamanı ve HARP ile çözülür.
Öğretmen eğitim sırasında seçim pencerelerini görmez. Değerlendirme yılı hataları eğitim
örneği, özellik veya seçim etiketi olarak kullanılmaz.

Üç sabit deney kolu değerlendirilir:

- `baseline_unweighted`: sabit 0.45 lojistik/0.55 XGBoost birleşimi.
- `hard_negative_weighted`: seçilen negatiflerin ağırlığı 3, diğer tüm eğitim satırlarının
  ağırlığı 1 olur. Yalnızca XGBoost yeniden eğitilir; lojistik bileşen korunur.
- `uniform_negative_matched_weight`: tüm eğitim negatiflerinin ağırlığı
  `1 + 2 * hard_negative_count / outer_training_negative_count`, pozitiflerin ağırlığı 1 olur.
  Toplam eğitim negatif ağırlığı, yuvarlama farkları dışında hedefli kolla aynıdır.

Her yeni XGBoost aynı dış kalibrasyon yılında sigmoid ile kalibre edilir. 0.45/0.55
birleşiminin eşiği orada recall >=0.95 koşuluyla seçilir ve değerlendirme tahminlerinden
önce kaydedilir. Değerlendirme etiketleriyle yeniden ayarlanmaz. Birleşim ve ağırlık katsayısı
değerlendirme sonuçlarından seçilmez. Olasılık kalibrasyonu ile eşik seçimini farklı
dönemlere ayırmak bu deneyin parçası değildir.

## Kapsam, seçim sayıları ve kabul kontrolleri

{fold}
Önceki kalibrasyon yıllarında pozitif örnek olmadığı için mevcut 2019–2021 tur atlamaları
korunur. Korunan 2018 değerlendirmesinde pozitif yoktur; recall tanımsızdır, yanlış alarmlar
ölçülebilir. Öğretmen eğitiminde sınıf çeşitliliği veya seçilebilir negatif olmaması yeni
kolları kullanılamaz yapar; sessizce referansla değiştirilmezler. `undefined`, ölçülmüş sıfır değildir.

## Dönemlere göre precision, recall ve yanlış alarmlar

{summary}
Skorlar 0–1 ölçeğinde oranlardır. FP ve FN bağımsız patlamaları veya alarm dönemlerini
değil, örtüşen tahmin pencerelerini sayar. Her yıllık karşılaştırmada tüm kollar aynı
örnek topluluğunu ve aktarılmış eşikleri kullanır; yıllar arasında topluluklar ve olay
sıklığı değişir. Recall hedefini kaçırma pahasına daha yüksek precision, istenen iyileşme
olarak kabul edilmez.

Aday eksi referans farkları ve tekdüze kontrole göre precision farkı:

{delta}
Pozitif precision/recall farkları adayı destekler; negatif FP farkı daha az yanlış pozitif
pencere demektir. Yılların birleştirilmiş tek skoru bu tablonun yerine geçmez.

## Tüm metrik sonuçları

{full}
Precision alarmlar içindeki doğru pozitif pencereleri, recall yakalanan pozitif pencereleri,
accuracy tüm doğru sınıflandırmaları ölçer. AP sıralamayı ölçer; düşük Brier/log loss daha
iyi olasılıksal puanlamadır. Sabit kabul kontrolü, karşılaştırılabilir her pozitif yılda daha
yüksek precision ve recall >=0.95; her yılda referansa göre düşmeyen AP ve artmayan
Brier/log loss gerektirir. Kazancı hedefli seçime bağlamak için o yıllarda precision'ın
eşleştirilmiş tekdüze kontrolü de geçmesi gerekir. Kontrolün geçilmesi otomatik dağıtım
başlatmaz; başarısızlıkta mevcut model korunur.

## Eşleştirilmiş koşullu belirsizlik

{ci}
Her aralık aday eksi belirtilen kontroldür; yıl içinde 24 tohumla eşleştirilmiş bütün
HARP'ları örnekleyen 1000 bootstrap tekrarı kullanır. İki kolda aynı örneklenmiş bölgeler,
sabit model ve eşikler kullanılır. Eğitim, kalibrasyon ve model seçimi belirsizliği dahil
değildir. FP aralıkları yeniden örneklenmiş pencere sayılarını anlatır; pozitif olmayan
yılda recall tekrarları tanımsızdır. Sıfırı içeren aralık, o aralık düzeyinde yönlü farkı
göstermez. Komşu yıllar geçmiş eğitim verisini paylaşır ve bağımsız tekrarlar değildir.

## Yorum sınırları ve sonraki karar

Bu uyarlamalı geliştirme deneyidir: önceki yıllık hatalar tasarımı yönlendirdi. Değerlendirme
satırları eğitimde kullanılmasa da yıllar yeni, görülmemiş test değildir. Zor negatif
ağırlıklandırması yanlış alarmları azaltabileceği gibi doğru pozitifleri bastırabilir veya
kalibrasyonu bozabilir. Olumsuz sonuç, zor negatiflerden öğrenmenin her yöntemini değil,
bu belirli ağırlıklandırma düzenini eler. Yeni hipotez seçmeden önce yıllık sonuçlar ve
tekdüze kontrol karşılaştırmaları incelenmelidir. Sonraki deney yeni sabit protokol
gerektirir; %95 recall iddiası üretmek için bu yıllarda eşikler değiştirilmemelidir.
Burada başka aday araması veya canlı dağıtım yapıldığı iddia edilmez.

## Yeniden üretim ve kanıt

{commands}
Tekrarda yeni çıktı dizinleri ve rapor adları seçin. Sabit modelleri, protokolleri ve
tahminleri koruyun. İki sürümü gözden geçirip yayımdan önce kaynak özetini ve bağlantıları
`docs/reports.json` ile `docs/reports.md` dosyalarına kaydedin. Üretilen modeller, seçilmiş
eğitim pencereleri, tahminler ve HTML yerel, Git dışında çıktılar olarak kalır. Model,
eşik, tahmin ve kod özetleri deney raporunda kayıtlıdır.

{evidence}
'''
    for p,text in zip(paths,[en,tr]):p.write_text(text)
    print('\n'.join(map(str,paths)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--report-name',required=True);a=p.parse_args();run(a.source.resolve(),a.report_name)
