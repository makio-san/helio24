"""Document the frozen feature, weighting, pooling and spline experiments in both languages."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from scripts.report_precision_followup import table


def run(output):
    paths = {name: ROOT / f'artifacts/precision_{name}_20261027_r1'
             for name in ['features', 'weighted', 'pool', 'splines']}
    reports = {name: json.loads((path / 'report.json').read_text()) for name,path in paths.items()}
    output.mkdir(parents=True, exist_ok=False)
    current = reports['features']['metrics']['incumbent']
    promoted = [(name, r) for name,r in reports.items() if r['promote']]
    chosen = max(promoted,key=lambda item:item[1]['metrics']['selected']['precision']) if promoted else None
    selected = chosen[1]['metrics']['selected'] if chosen else current
    selection = {'experiment':chosen[0] if chosen else 'incumbent', 'metrics':selected,
                 'reserved_test_accessed':False}
    (output / 'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    rows, candidates, intervals, hashes = [], [], [], {}
    for name,r in reports.items():
        rows.append({'experiment':name,'selected_candidate':r['winner']['candidate'],
                     'promote':r['promote'],**{k:r['metrics']['selected'][k] for k in
                                              ['recall','precision','fp','average_precision','brier','log_loss']}})
        c=pd.read_csv(paths[name]/'calibration_candidates.csv')
        c.insert(0,'experiment',name)
        candidates.append(c[['experiment','candidate','recall','precision','fp','average_precision','brier','log_loss']])
        for metric, value in r['conditional_cluster_intervals']['selected'].items():
            intervals.append({'experiment':name,'metric':metric,**value})
        for filename in ['report.json','calibration_candidates.csv','validation_predictions.parquet']:
            hashes[str((paths[name]/filename).relative_to(ROOT))]=sha256(paths[name]/filename)
    (output/'source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    comparisons=table(pd.DataFrame(rows))
    search=table(pd.concat(candidates,ignore_index=True))
    uncertainty=table(pd.DataFrame(intervals))
    values=table(pd.DataFrame([{'metric':k,'incumbent':current[k],'selected':selected[k]}
                              for k in ['precision','recall','tp','fp','fn','tn','accuracy','balanced_accuracy',
                                        'f1','false_positive_rate','false_alarm_ratio','tss','average_precision',
                                        'brier','log_loss','threshold']]))
    evidence=table(pd.DataFrame(hashes.items(),columns=['source','SHA-256']))
    reproduction='''```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py --protocol config/precision-features-v1.json --output artifacts/precision_features_20261027_r1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py --protocol config/precision-weighted-v1.json --output artifacts/precision_weighted_20261027_r1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_pool.py --output artifacts/precision_pool_20261027_r1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py --protocol config/precision-splines-v1.json --output artifacts/precision_splines_20261027_r1
.venv/bin/python scripts/report_precision_features.py --output artifacts/precision_features_summary_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_precision_features_20261027
```
'''
    decision_en = (f"The selected experiment is `{chosen[0]}`. Validation precision changes from {current['precision']:.6f} to {selected['precision']:.6f}." if chosen else
                   'No candidate met the promotion rule. Validation precision remains 0.079622; recall remains 0.950064. The objective of increasing precision was not achieved in this round.')
    decision_tr = (f"Seçilen deney `{chosen[0]}`. Doğrulama precision değeri {current['precision']:.6f} düzeyinden {selected['precision']:.6f} düzeyine değişti." if chosen else
                   'Hiçbir aday model değiştirme kuralını karşılamadı. Doğrulama precision değeri 0.079622, recall değeri 0.950064 kaldı. Bu turda precision artırma hedefi gerçekleşmedi.')
    texts = {
    'en':f'''# Precision research: magnetic features and training objectives

Date: 2026-10-27. {decision_en}

## Scope and design

The same frozen V2 population was used: training has 484549 windows and 8698
positives; calibration has 50756 windows and 421 positives; validation has
60366 windows and 781 positives. Training ends before 2022; calibration is
2022; validation is 2023. The reserved 2024–2025 test remained unopened.
The threshold question remains M/X GOES peak in the next 24 hours from a
12-hour observation history. This is development evidence, not a final test.

Catalog event times do not establish when a flare report or retrospective HARP
association became available. That availability is unverified, so event-history
features were excluded. No target, label or future event is used as a feature.

Four sequential bounded searches were recorded before their respective runs:

- `features`: three logistic models append 78 products of 12 signed-log,
  train-standardized mean measurements, with C=0.01, 0.1, 1. One XGBoost
  model appends 72 relative-evolution features: std/(abs(mean)+std),
  delta/(abs(mean)+std), and (last-mean)/(abs(mean)+std) per measurement.
  Zero denominators become missing; ratios are clipped to [-100,100].
- `weighted`: four logistic models use either raw or signed-log features,
  with positive weight 10 or balanced training class weights, and C=1.
- `pool`: 57 probability pools use powers -1, 0, 2 (harmonic, geometric,
  quadratic mean), each with 19 logistic weights from 0.05 through 0.95.
  Each pool receives monotonic sigmoid calibration on calibration data.
- `splines`: three logistic models append training-quantile quadratic spline
  bases for all 24 mean measurements, with 4 knots, constant extrapolation,
  and C=0.01, 0.1, 1. Missing-value imputation, signed-log scales, spline knots
  and standardization fit on training data only.

The 11 newly trained models were each blended with the fixed incumbent using
new-model weights 0.25, 0.5, 0.75, 1.0: 44 candidates plus 57 pools, or 101
new probability combinations in total. All searches include the incumbent.
Candidate selection uses calibration precision at recall >=0.95, then AP,
then candidate ID. The selected candidate alone is compared on validation.
Validation promotion requires higher precision at recall >=0.95, AP no lower,
and Brier/log loss no higher than the incumbent. Thresholds are selected on
validation; the recall target is not relaxed to manufacture precision gains.

## Validation decisions

{comparisons}
The weighted candidate tied incumbent calibration precision and won the AP
tie-break, but validation precision fell to 0.074289 with 9246 false positives.
It was rejected despite slightly better AP and probability error. Improving
AP or calibration alone does not establish better precision at 95% recall.
The spline candidate improved calibration precision to 0.092764, but validation
precision was 0.076385 with 8972 false positives, so it was also rejected.

## Selected operating point

{values}
## Every calibration candidate

{search}
## Uncertainty and limits

{uncertainty}
These are conditional 95% HARP-cluster bootstrap intervals from 1000 draws,
seed 24. They hold model and threshold fixed, excluding training, calibration,
model-selection and threshold-selection uncertainty. FP/TP/FN count overlapping
windows rather than independent flares or operational alerts. Precision still
measures the fraction of alarm windows that are truly positive.

Calibration was reused for probability fitting and candidate selection, and
previous development results influenced these new designs. Thus the process
is adaptive; neither calibration nor validation results are independent final
tests. More searches can overfit development data. Lack of improvement does
not prove a theoretical ceiling, nor does the current point estimate guarantee
future recall. The historical V1 precision 0.164840 uses a different population
and cannot serve as a matched before/after comparison.

## Reproduction and provenance

{reproduction}
Existing outputs are protected. Repeat with fresh output paths and corresponding
report input paths; this reporting script uses the dated inputs shown above.
Review both Markdown editions and register their source hash before publishing
changed content. The frozen model selection remains development-only; dashboard
models are not automatically replaced. Dataset/model/generated artifacts remain
outside Git, and local Streamlit branding changes remain uncommitted.

{evidence}
''',
    'tr':f'''# Precision araştırması: manyetik özellikler ve eğitim hedefleri

Tarih: 2026-10-27. {decision_tr}

## Kapsam ve tasarım

Aynı dondurulmuş V2 popülasyonu kullanıldı: eğitimde 484549 pencere ve 8698
pozitif; kalibrasyonda 50756 pencere ve 421 pozitif; doğrulamada 60366 pencere
ve 781 pozitif var. Eğitim 2022'den önce biter; kalibrasyon 2022, doğrulama
2023 dönemidir. Ayrılmış 2024–2025 testi açılmadı. Tahmin sorusu, 12 saatlik
gözlem geçmişinden sonraki 24 saatte M/X GOES tepe noktası olup olmayacağıdır.
Bu geliştirme kanıtıdır, nihai test değildir.

Katalogdaki olay zamanları, bir patlama raporunun veya geçmişe dönük HARP
ilişkisinin ne zaman erişilebilir olduğunu göstermez. Bu erişilebilirlik
doğrulanmadığı için olay geçmişi özellikleri dışlandı. Hedef, etiket veya
gelecekteki olaylar özellik olarak kullanılmadı.

Dört ardışık, sınırlı arama kendi çalıştırmalarından önce kaydedildi:

- `features`: üç lojistik model, işaret koruyan logaritma ve eğitimde öğrenilen
  standartlaştırma sonrasında 12 ortalama ölçümün 78 çarpımını ekler;
  C=0.01, 0.1, 1 kullanılır. Bir XGBoost modeli 72 göreli değişim özelliği ekler:
  her ölçüm için std/(abs(mean)+std), delta/(abs(mean)+std) ve
  (last-mean)/(abs(mean)+std). Sıfır paydalar eksik değer olur;
  oranlar [-100,100] aralığında kırpılır.
- `weighted`: dört lojistik model, ham veya işaret koruyan logaritmik özellikleri,
  10 pozitif ağırlığı veya dengeli eğitim sınıf ağırlıklarıyla ve C=1 ile kullanır.
- `pool`: 57 olasılık birleşimi -1, 0, 2 kuvvetlerini (harmonik, geometrik,
  karesel ortalama) kullanır; her biri 0.05–0.95 arasındaki 19 lojistik ağırlıkla
  denenir. Her birleşime kalibrasyon verisinde monoton sigmoid kalibrasyonu uygulanır.
- `splines`: üç lojistik model, 24 ortalama ölçüme eğitim kuantillerine dayanan
  ikinci dereceden spline tabanları ekler; 4 düğüm, sabit dışdeğerleme ve
  C=0.01, 0.1, 1 kullanılır. Eksik değer doldurma, logaritmik ölçekler, spline
  düğümleri ve standartlaştırma yalnızca eğitim verisinde öğrenilir.

Yeni eğitilen 11 modelin her biri, 0.25, 0.5, 0.75, 1.0 yeni-model ağırlıklarıyla
sabit mevcut modelle birleştirildi: 44 aday ve 57 havuzlama, toplam 101 yeni
olasılık birleşimi. Tüm aramalara mevcut model dahildir. Aday seçimi recall
>=0.95 düzeyindeki kalibrasyon precision'ını, ardından AP'yi ve aday kimliğini
kullanır. Doğrulamada yalnızca seçilen aday karşılaştırılır. Model değiştirmek
recall >=0.95 düzeyinde daha yüksek precision, daha düşük olmayan AP ve daha
yüksek olmayan Brier/log loss gerektirir. Eşikler doğrulamada seçilir;
precision artışı üretmek için recall hedefi gevşetilmez.

## Doğrulama kararları

{comparisons}
Ağırlıklı aday, kalibrasyon precision'ında mevcut modelle eşitlendi ve AP eşitlik
bozma kuralıyla seçildi; fakat doğrulamada precision 9246 yanlış pozitifle
0.074289'a düştü. Biraz daha iyi AP ve olasılık hatasına rağmen reddedildi.
Yalnızca AP veya kalibrasyonun iyileşmesi, %95 recall düzeyinde precision'ın
iyileştiğini göstermez. Spline adayı kalibrasyon precision değerini 0.092764
düzeyine yükseltti; ancak doğrulamada 8972 yanlış pozitifle precision 0.076385
olduğu için o da reddedildi.

## Seçili çalışma noktası

{values}
## Tüm kalibrasyon adayları

{search}
## Belirsizlik ve sınırlar

{uncertainty}
Bunlar 24 tohumuyla 1000 tekrar yapılan HARP kümeli bootstrap'tan elde edilen
koşullu %95 aralıklardır. Model ve eşiği sabit tutar; eğitim, kalibrasyon, model
seçimi ve eşik seçimi belirsizliğini içermez. FP/TP/FN bağımsız patlamaları veya
operasyonel alarmları değil, örtüşen pencereleri sayar. Precision, alarm verilen
pencerelerin ne kadarının gerçekten pozitif olduğunu ölçmeye devam eder.

Kalibrasyon hem olasılık öğreniminde hem aday seçiminde tekrar kullanıldı;
önceki geliştirme sonuçları bu yeni tasarımları etkiledi. Dolayısıyla süreç
uyarlamalıdır; kalibrasyon ve doğrulama bağımsız nihai test değildir. Daha fazla
arama geliştirme verisine aşırı uyuma yol açabilir. İyileşme olmaması teorik
bir üst sınırı kanıtlamaz; mevcut nokta tahmini gelecekteki recall'u garanti
etmez. Tarihsel V1 precision değeri 0.164840 farklı bir popülasyondadır ve
eşlenmiş önce/sonra karşılaştırması olarak kullanılamaz.

## Yeniden üretim ve kaynak izi

{reproduction}
Mevcut çıktılar korunur. Tekrar için yeni çıktı yolları ve karşılık gelen rapor
girdi yolları kullanın; bu raporlama betiği yukarıdaki tarihli girdileri kullanır.
İçerik değişikliğini yayımlamadan önce iki Markdown sürümünü gözden geçirip
kaynak hash'ini kaydedin. Dondurulmuş model seçimi yalnızca geliştirme içindir;
dashboard modelleri otomatik değiştirilmez. Veri/model/üretilen dosyalar Git
dışında, yerel Streamlit marka değişiklikleri commit dışında kalır.

{evidence}
'''}
    for language, text in texts.items():
        suffix='' if language=='en' else '.tr'
        dest=ROOT / f'docs/precision-features-20261027{suffix}.md'
        if dest.exists():
            raise ValueError('Preserve existing report')
        dest.write_text(text)
    print(json.dumps(selection,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
