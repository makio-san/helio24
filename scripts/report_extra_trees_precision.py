"""Produce paired Extra Trees results and an unchanged-model threshold diagnostic."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.calibration import recall_threshold
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.modeling import metrics
from scripts.report_precision_followup import table


def run(output):
    source = ROOT / 'artifacts/precision_extra_trees_20261027_r1'
    result = json.loads((source / 'report.json').read_text())
    incumbent_path = ROOT / 'artifacts/experiment5_v2_development_20261026_r2/validation_predictions.parquet'
    if sha256(incumbent_path) != '44a2852948b61cd8b42c77497588f16d76e601221ef1b2f8a923ede56b6d8bff':
        raise ValueError('Incumbent predictions changed')
    p = pd.read_parquet(incumbent_path)
    p = p[p.model.eq('ensemble')].copy()
    frontier = []
    for target_recall in [.95, .9, .8, .5]:
        m = metrics(p.target, p.probability, recall_threshold(p.target, p.probability, target_recall))
        frontier.append({key: m[key] for key in ['recall','precision','fp','fn','threshold']})
    positives=p[p.target.eq(1)].copy()
    positives['missed']=~positives.alarm
    regions=positives.groupby('harp').agg(positive_windows=('target','size'),missed_windows=('missed','sum'))
    regions=regions[regions.missed_windows.gt(0)].sort_values('missed_windows',ascending=False).reset_index()
    output.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(frontier).to_csv(output/'threshold_diagnostic.csv',index=False)
    regions.to_csv(output/'missed_regions.csv',index=False)
    keys=['precision','recall','fp','fn','tp','tn','accuracy','balanced_accuracy','f1','false_positive_rate',
          'false_alarm_ratio','tss','average_precision','brier','log_loss','threshold']
    m=result['metrics']
    comparison=table(pd.DataFrame([{'metric':key,'incumbent':m['incumbent'][key],
                                    'candidate':m['selected'][key]} for key in keys]))
    c=pd.read_csv(source/'calibration_candidates.csv')
    candidates=table(c[['candidate','recall','precision','fp','average_precision','brier','log_loss']])
    uncertainty=table(pd.DataFrame([{'model':model,'metric':metric,**value}
                                    for model,fields in result['conditional_cluster_intervals'].items()
                                    for metric,value in fields.items()]))
    hashes={str((source/name).relative_to(ROOT)):sha256(source/name)
            for name in ['report.json','calibration_candidates.csv','validation_predictions.parquet']}
    hashes[str(incumbent_path.relative_to(ROOT))]=sha256(incumbent_path)
    (output/'source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    evidence=table(pd.DataFrame(hashes.items(),columns=['source','SHA-256']))
    operating=table(pd.DataFrame(frontier)); errors=table(regions)
    outcome_en = ('The candidate passed all development promotion checks.' if result['promote'] else
                  'The candidate did not pass all development promotion checks; the incumbent remains selected.')
    outcome_tr = ('Aday geliştirmedeki tüm model değiştirme kontrollerini geçti.' if result['promote'] else
                  'Aday geliştirmedeki tüm model değiştirme kontrollerini geçmedi; mevcut model seçili kaldı.')
    winner=result['winner']['candidate']
    command='''```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \\
  --protocol config/precision-extra-trees-v1.json --output artifacts/precision_extra_trees_20261027_r1
.venv/bin/python scripts/report_extra_trees_precision.py --output artifacts/precision_extra_trees_audit_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_extra_trees_20261027
```
'''
    en=f'''# Extra Trees precision experiment

Date: 2026-10-27. Calibration selected `{winner}`. {outcome_en}

## Scope and frozen search

Three ExtraTreesClassifier models were fitted: raw features without class
weighting, raw features with balanced training class weights, and signed-log
features with balanced weights. Each has 256 trees, maximum depth 20, minimum
leaf size 20, sqrt feature sampling, seed 24 and 2 workers. Median imputation
and any signed-log scales fit on training only. No new external data or
future-derived features were added.

Each model's sigmoid calibration used 2022 data. Four new-model mixture weights
0.25, 0.5, 0.75 and 1.0 yielded 12 candidates plus the incumbent. Candidate
selection maximized calibration precision at recall >=0.95, then AP, then
candidate ID. Only the winner proceeded to 2023 validation. Promotion requires
higher validation precision at recall >=0.95, AP no lower, and Brier/log loss
no higher. The search was fixed in `config/precision-extra-trees-v1.json`
before execution. Training has 484549 windows/8698 positives; calibration has
50756/421; validation has 60366/781. Reserved 2024–2025 data remained unopened.

## All calibration candidates

{candidates}
## Validation comparison

{comparison}
## Conditional uncertainty

{uncertainty}
These 95% intervals use 1000 whole-HARP bootstrap draws with seed 24 and fixed
model/threshold. They exclude training, calibration and selection uncertainty.
Calibration is reused for probability fitting and candidate selection; prior
validation results informed development. The result is adaptive development,
not an independent test or a guarantee of future recall. Counts describe
overlapping forecast windows, not independent flares or alerts. The threshold
is selected on validation, not transferred unchanged from calibration.

## What else could improve precision?

The incumbent's missed positive windows are concentrated in these regions:

{errors}
HARP 9152 and 9584 account for 34 of the 39 missed windows. Independently audit
their flare associations, original timestamps and measurement quality. This
is a diagnostic priority, not evidence that their labels are wrong. Do not
remove difficult regions or change labels merely to improve metrics.

Next, materialize longer histories from raw, unfiltered observations and test
24/48-hour changes, persistence and flux evolution against the same population.
Earlier retained labeled windows alone are unsuitable history inputs: their
inclusion can depend on future label exclusions. Historical flare features
also require verified report availability and region-association provenance.
Finally, compare candidate families with additional chronological development
folds to reduce dependence on one calibration year. These are hypotheses for
future experiments, not improvements demonstrated by this run.

The following is an unchanged-incumbent threshold diagnostic:

{operating}
Higher thresholds can raise precision by sacrificing recall. These rows are
not model improvements; the user objective remains recall >=0.95. They are
shown to distinguish operating-point changes from better ranking. A probability
calibration improvement alone does not guarantee precision at that operating point.

## Reproduction and evidence

{command}
Existing artifact directories are protected. Repeat using fresh paths and
update the reporting script's dated input paths accordingly. Both document
editions must be reviewed and registered before publication. The existing
dashboard model is not automatically replaced. Models, data, predictions and
HTML are local ignored artifacts; source code and these reports are committed.

{evidence}
'''
    tr=f'''# Extra Trees precision deneyi

Tarih: 2026-10-27. Kalibrasyonda `{winner}` seçildi. {outcome_tr}

## Kapsam ve sabitlenmiş arama

Üç ExtraTreesClassifier modeli eğitildi: sınıf ağırlıksız ham özellikler,
dengeli eğitim sınıf ağırlıklarıyla ham özellikler ve dengeli ağırlıklarla
işaret koruyan logaritmik özellikler. Her birinde 256 ağaç, 20 maksimum derinlik,
20 minimum yaprak örneği, sqrt özellik örneklemesi, 24 tohum ve 2 işçi bulunur.
Medyanla eksik değer doldurma ve varsa logaritmik ölçekler yalnızca eğitimde
öğrenilir. Yeni dış veri veya gelecekten türetilen özellik eklenmedi.

Her modelin sigmoid kalibrasyonu 2022 verisini kullandı. 0.25, 0.5, 0.75 ve 1.0
yeni-model karışım ağırlıkları, mevcut modele ek 12 aday üretti. Aday seçimi,
recall >=0.95 düzeyindeki kalibrasyon precision'ını, ardından AP'yi ve aday
kimliğini kullandı. Yalnızca kazanan 2023 doğrulamasına geçti. Model değiştirmek,
recall >=0.95 düzeyinde daha yüksek doğrulama precision'ı, daha düşük olmayan AP,
daha yüksek olmayan Brier/log loss gerektirir. Arama çalıştırılmadan önce
`config/precision-extra-trees-v1.json` içinde sabitlendi. Eğitimde 484549
pencere/8698 pozitif, kalibrasyonda 50756/421, doğrulamada 60366/781 vardır.
Ayrılmış 2024–2025 verisi açılmadı.

## Tüm kalibrasyon adayları

{candidates}
## Doğrulama karşılaştırması

{comparison}
## Koşullu belirsizlik

{uncertainty}
Bu %95 aralıklar, sabit model/eşik ve 24 tohumla bütün HARP'ları örnekleyen
1000 bootstrap tekrarı kullanır. Eğitim, kalibrasyon ve seçim belirsizliğini
içermez. Kalibrasyon hem olasılık öğreniminde hem aday seçiminde kullanılır;
önceki doğrulama sonuçları geliştirmeyi etkiledi. Sonuç uyarlamalı geliştirmedir;
bağımsız test veya gelecekteki recall garantisi değildir. Sayılar bağımsız
patlama veya alarmları değil, örtüşen tahmin pencerelerini anlatır. Eşik,
kalibrasyondan değiştirilmeden aktarılmaz; doğrulamada seçilir.

## Precision artırmak için başka ne yapılabilir?

Mevcut modelin kaçırdığı pozitif pencereler şu bölgelerde yoğunlaşıyor:

{errors}
HARP 9152 ve 9584, kaçırılan 39 pencerenin 34'ünü oluşturuyor. Bu bölgelerin
patlama ilişkileri, özgün zaman damgaları ve ölçüm kalitesi bağımsız denetlenmeli.
Bu bir inceleme önceliğidir; etiketlerin yanlış olduğuna kanıt değildir.
Metrikleri artırmak amacıyla zor bölgeler çıkarılmamalı veya etiketleri değiştirilmemeli.

Ardından ham, filtrelenmemiş gözlemlerden daha uzun geçmiş üretilmeli; 24/48
saatlik değişim, süreklilik ve akı gelişimi aynı popülasyonda sınanmalı. Daha
önce tutulmuş etiketli pencereler tek başına geçmiş girdisi olmaya uygun değildir:
bu pencerelerin tutulması gelecekteki etiket dışlamalarına bağlı olabilir.
Geçmiş patlama özellikleri de doğrulanmış rapor erişilebilirliği ve bölge
ilişkisi kaynağı gerektirir. Son olarak tek kalibrasyon yılına bağımlılığı
azaltmak için aday aileleri ek kronolojik geliştirme bölümlerinde karşılaştırılmalı.
Bunlar sonraki deneylere yönelik hipotezlerdir; bu turda gösterilmiş iyileşmeler değildir.

Aşağıdaki tablo, değişmeyen mevcut modelin eşik incelemesidir:

{operating}
Daha yüksek eşikler recall'dan vazgeçerek precision'ı artırabilir. Bu satırlar
model iyileşmesi değildir; kullanıcı hedefi recall >=0.95 olarak kalır. Çalışma
noktası değişimini daha iyi sıralamadan ayırmak için gösterilmiştir. Tek başına
olasılık kalibrasyonunun iyileşmesi o çalışma noktasındaki precision'ı garanti etmez.

## Yeniden üretim ve kanıt

{command}
Mevcut artifact dizinleri korunur. Tekrar için yeni yollar kullanın ve raporlama
betiğindeki tarihli girdi yollarını buna göre güncelleyin. Yayımdan önce iki
belge sürümü gözden geçirilmeli ve kaydedilmelidir. Mevcut dashboard modeli
otomatik değiştirilmez. Modeller, veri, tahminler ve HTML yerel, yok sayılan
artifact olarak kalır; kaynak kod ve bu raporlar commitlenir.

{evidence}
'''
    for language, content in [('en', en), ('tr', tr)]:
        suffix='' if language=='en' else '.tr'
        path=ROOT/f'docs/precision-extra-trees-20261027{suffix}.md'
        if path.exists():
            raise ValueError('Preserve existing report')
        path.write_text(content)
    print(outcome_en)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
