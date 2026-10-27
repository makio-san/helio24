"""Publish bilingual precision follow-up evidence without changing frozen runs."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256


def table(frame):
    def fmt(value):
        return f'{value:.6f}' if isinstance(value, float) else str(value)
    return '\n'.join(['| '+' | '.join(frame.columns)+' |',
                      '| '+' | '.join(['---']*len(frame.columns))+' |']+
                     ['| '+' | '.join(map(fmt, row))+' |' for row in frame.itertuples(index=False, name=None)])+'\n'


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    dirs = [ROOT / 'artifacts' / f'precision_{kind}_20261027_r1' for kind in ['log', 'hist']]
    reports = [json.loads((d / 'report.json').read_text()) for d in dirs]
    origin = ROOT / 'artifacts/experiment5_v2_development_20261026_r2'
    origin_report = json.loads((origin / 'report.json').read_text())
    path = origin / 'validation_predictions.parquet'
    if sha256(path) != origin_report['artifact_hashes'][path.name]:
        raise ValueError('Frozen predictions changed')
    p = pd.read_parquet(path)
    p = p[p.model.eq('ensemble')].copy()
    p['fp'] = p.alarm & p.target.eq(0)
    p['tp'] = p.alarm & p.target.eq(1)
    regions = p.groupby('harp').agg(rows=('target', 'size'), positives=('target', 'sum'),
                                  fp=('fp', 'sum'), tp=('tp', 'sum')).sort_values('fp', ascending=False)
    diagnostics = {'top10_fp': int(regions.head(10).fp.sum()),
                   'zero_positive_region_fp': int(regions.loc[regions.positives.eq(0), 'fp'].sum()),
                   'total_fp': int(regions.fp.sum())}
    regions.to_csv(output / 'region_errors.csv')
    sources = {str(d.relative_to(ROOT) / 'report.json'): sha256(d / 'report.json') for d in dirs}
    for d in dirs:
        sources[str(d.relative_to(ROOT) / 'calibration_candidates.csv')] = sha256(d / 'calibration_candidates.csv')
    sources[str(path.relative_to(ROOT))] = sha256(path)
    (output / 'audit.json').write_text(json.dumps({'diagnostics': diagnostics, 'source_hashes': sources}, indent=2)+'\n')
    historical = table(pd.DataFrame([
        ['V1 historical', 50631, 1076, 1076/50631, .950743, .104591, .164840],
        ['V2 incumbent', 60366, 781, 781/60366, .950064, .143946, .079622]],
        columns=['population', 'windows', 'positives', 'prevalence', 'recall', 'FPR', 'precision']))
    candidates = []
    for kind, d in zip(['log', 'hist'], dirs):
        f = pd.read_csv(d / 'calibration_candidates.csv')
        f.insert(0, 'experiment', kind)
        candidates.append(f[['experiment', 'candidate', 'recall', 'precision', 'fp', 'average_precision', 'brier', 'log_loss']])
    search = table(pd.concat(candidates))
    metrics = reports[0]['metrics']['incumbent']
    values = table(pd.DataFrame([[key, metrics[key]] for key in
        ['precision','recall','fp','fn','tp','tn','accuracy','balanced_accuracy','f1',
         'false_positive_rate','false_alarm_ratio','tss','average_precision','brier','log_loss','threshold']],
        columns=['metric', 'value']))
    ci = table(pd.DataFrame([{'metric': key, **value} for key,value in
                            reports[0]['conditional_cluster_intervals']['incumbent'].items()]))
    evidence = table(pd.DataFrame(list(sources.items()), columns=['source', 'SHA-256']))
    reproduction = '''```sh
OMP_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \\
  --protocol config/precision-log-v1.json --output artifacts/precision_log_20261027_r1
OMP_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \\
  --protocol config/precision-hist-v1.json --output artifacts/precision_hist_20261027_r1
.venv/bin/python scripts/report_precision_followup.py --output artifacts/precision_followup_20261027_r1
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_precision_followup_20261027
```
'''
    texts = {
'en': f'''# Precision follow-up: comparison, experiments and uncertainty

Date: 2026-10-27. **Precision remains 0.079622 at recall 0.950064.** Six new
models and 24 probability mixtures did not beat the incumbent on calibration.
Neither experiment promoted a new model. The reserved 2024–2025 test stayed closed.

## Why the current number is below the historical number

{historical}
The previous 0.164840 came from V1 development; the current 0.079622 comes
from V2 validation in 2023. These are different populations, feature calculations,
label coverage and exclusion policies. The previously reported improvement
0.061597 to 0.079622 compared XGBoost with the ensemble on the same V2 rows.
It did not surpass the historical V1 number. Earlier updates did not make this
distinction sufficiently clear.

Precision obeys `recall * prevalence / (recall * prevalence + FPR * (1 - prevalence))`.
The V2 positive-window prevalence is lower, and its measured FPR is higher.
Both terms explain the numerical difference; these observations do not establish
which archive, label or modeling change caused it. As an algebraic illustration,
holding V2 recall and FPR fixed while substituting V1 prevalence gives precision
0.125347. This is a counterfactual calculation, not a measured model result.
Class imbalance alone is not an adequate explanation for the observed gap.

## Error concentration

Of 8577 false-positive windows, 2180 occur in the top 10 HARPs ranked by this
count. Another grouping finds 6815 in HARPs with no positive window in the
retained validation sample. This does not mean those regions never flared:
excluded windows and events outside the sample remain outside the statement.
These are retrospective diagnostics, never inference features or rules for
removing difficult negatives. Counts refer to overlapping forecast windows,
not independent flare events or alarm episodes.

## Bounded experiments

The signed-log experiment fitted median imputation, training-column median
absolute scales, sign-preserving `log1p`, standardization and logistic regression
on training data. The C values were 0.1, 1 and 10. The histogram experiment
fitted HistGradientBoostingClassifier with 15 or 31 leaves, 200 iterations,
learning rate 0.05, minimum leaf size 100 and L2 regularization 10. A third
histogram candidate used 15 leaves and training dates from 2018 onward.
Early stopping was disabled to avoid a random internal validation split.

For each of these six models, sigmoid calibration used 2022 data. The new
model's probability weight was 0.25, 0.5, 0.75 or 1.0; the remaining weight
went to the fixed incumbent. Each bounded search was recorded in its JSON
protocol before execution. Selection used calibration precision at recall
>= 0.95, then AP and candidate ID. Only the selected candidate proceeded to
validation; both searches selected the incumbent. No rejected candidate was
searched on validation. All calibration candidates are retained below.

{search}
## Current validation metrics

{values}
The development promotion rule required increased precision at recall >= 0.95,
nondecreasing AP and nonincreasing Brier and log loss. No candidate passed the
first selection step, so the frozen ensemble and threshold remain selected.
The models and prediction artifacts used for the existing dashboard were not
replaced. There was no improvement in this follow-up; failed searches are evidence.

## Conditional uncertainty

{ci}
Intervals are 95% percentile intervals from 1000 whole-HARP bootstrap draws,
seed 24, with the model and threshold held fixed. They exclude training,
calibration, model-selection and threshold-selection uncertainty and do not
validate future recall. In particular, the recall lower bound is below 0.95.
The same calibration data was used for probability calibration and candidate
selection, so calibration scores are optimistic development scores. Validation
had already informed previous model design; this remains adaptive development.
No independent test result or operational readiness is claimed.

## Next research direction

The bounded model-only searches did not improve precision. The next experiment
should add information known at forecast time, such as verified prior-flare
history and richer magnetic evolution, with availability times and region
associations audited before training. New features may help, but improvement is
not guaranteed. The existing recall constraint remains 0.95; raising the alarm
threshold and silently reducing recall would change the user's objective.

## Reproduction and evidence

{reproduction}
Commands refuse existing artifact directories; use fresh paths for a repeat,
and pass those paths to the reporting script after adapting its input paths.
The reporting script uses the dated input paths shown above. It creates a new
error audit and the paired Markdown documents. Review both editions and refresh
the catalog source hash before publishing if their content changes.

{evidence}
Source code and protocols are committed; data, models, predictions and generated
HTML remain ignored local artifacts. Previous reports and experiment outputs
are preserved. Historical comparison source: [recall-first results](recall-first-results.en.md).
''',
'tr': f'''# Precision takibi: karşılaştırma, deneyler ve belirsizlik

Tarih: 2026-10-27. **Precision, 0.950064 recall düzeyinde 0.079622 olarak kaldı.**
Altı yeni model ve 24 olasılık karışımı kalibrasyonda mevcut modeli geçemedi.
İki deneyde de yeni model seçilmedi. Ayrılmış 2024–2025 testi kapalı kaldı.

## Güncel sayı neden tarihsel sayıdan düşük?

{historical}
Önceki 0.164840, V1 geliştirme verisinden; güncel 0.079622, 2023 V2 doğrulama
verisinden geliyor. Bunların popülasyonları, özellik hesapları, etiket kapsamı
ve dışlama kuralları farklı. Daha önce bildirilen 0.061597 → 0.079622 artışı,
aynı V2 satırlarında XGBoost ile ensemble karşılaştırmasıydı. Tarihsel V1
sayısını aşmadı. Önceki açıklamalar bu ayrımı yeterince açık yapmadı.

Precision şu eşitliği sağlar:
`recall * prevalence / (recall * prevalence + FPR * (1 - prevalence))`.
V2 pozitif pencere sıklığı daha düşük ve ölçülen FPR daha yüksek. Bu iki terim
sayısal farkı açıklar; gözlemler hangi arşiv, etiket veya modelleme değişikliğinin
buna neden olduğunu kanıtlamaz. Cebirsel bir örnekte, V2 recall ve FPR sabit
tutulup V1 olay sıklığı yerleştirildiğinde precision 0.125347 olur. Bu varsayımsal
bir hesaplamadır, ölçülmüş model sonucu değildir. Gözlenen farkı yalnızca sınıf
dengesizliğiyle açıklamak yeterli değildir.

## Hataların yoğunlaştığı bölgeler

8577 yanlış pozitif pencerenin 2180 tanesi, bu sayıya göre ilk 10 HARP'tadır.
Başka bir gruplama, 6815 tanesinin tutulan doğrulama örnekleminde pozitif
penceresi olmayan HARP'larda bulunduğunu gösterir. Bu, o bölgelerin hiç
patlamadığı anlamına gelmez; dışlanan pencereler ve örneklem dışı olaylar bu
ifadenin kapsamı dışındadır. Bunlar geçmişe dönük hata incelemeleridir; tahmin
girdisi veya zor negatifleri eleme kuralı olarak kullanılamaz. Sayılar bağımsız
patlamaları veya alarm olaylarını değil, örtüşen tahmin pencerelerini sayar.

## Sınırlı deneyler

İşaret koruyan logaritma deneyi; medyanla eksik değer doldurma, eğitim
sütunlarının medyan mutlak büyüklük ölçekleri, işaret koruyan `log1p`,
standartlaştırma ve lojistik regresyonu eğitim verisinde öğrendi. C değerleri
0.1, 1 ve 10 idi. Histogram deneyi HistGradientBoostingClassifier ile 15 veya
31 yaprak, 200 iterasyon, 0.05 öğrenme oranı, 100 minimum yaprak örneği ve
10 L2 düzenlileştirmesi kullandı. Üçüncü histogram adayı 15 yaprakla yalnızca
2018 ve sonrasındaki eğitim tarihlerini kullandı. Rastgele iç doğrulama
bölünmesini önlemek için erken durdurma kapatıldı.

Bu altı modelin her birinde sigmoid kalibrasyonu 2022 verisini kullandı.
Yeni modelin olasılık ağırlığı 0.25, 0.5, 0.75 veya 1.0 idi; kalan ağırlık
sabit mevcut modele verildi. Her sınırlı arama, çalıştırılmadan önce JSON
protokolüne kaydedildi. Seçim recall >= 0.95 düzeyindeki kalibrasyon
precision'ı, ardından AP ve aday kimliğini kullandı. Yalnızca seçilen aday
doğrulamaya geçti; her iki arama da mevcut modeli seçti. Reddedilen adaylar
doğrulama üzerinde aranmadı. Tüm kalibrasyon adayları aşağıda korunuyor.

{search}
## Güncel doğrulama metrikleri

{values}
Geliştirmede model değiştirme kuralı; recall >= 0.95 düzeyinde precision artışı,
AP'nin azalmaması, Brier ve log loss'un artmamasıydı. Hiçbir aday ilk seçim
adımını geçmedi; dondurulmuş ensemble ve eşik seçili kaldı. Mevcut dashboard'ın
kullandığı model ve tahmin dosyaları değiştirilmedi. Bu takipte iyileşme olmadı;
başarısız aramalar da kanıttır.

## Koşullu belirsizlik

{ci}
Aralıklar, model ve eşik sabit tutularak 24 tohumuyla bütün HARP'ları örnekleyen
1000 bootstrap tekrarından elde edilen %95 yüzdelik aralıklardır. Eğitim,
kalibrasyon, model seçimi ve eşik seçimi belirsizliğini içermez; gelecekteki
recall'u doğrulamaz. Özellikle recall alt sınırı 0.95'in altındadır. Aynı
kalibrasyon verisi hem olasılık kalibrasyonunda hem aday seçiminde kullanıldığı
için kalibrasyon skorları iyimser geliştirme skorlarıdır. Doğrulama daha önce
model tasarımını etkilemişti; süreç hâlâ uyarlamalı geliştirmedir. Bağımsız test
sonucu veya operasyonel hazırlık iddiası yoktur.

## Sonraki araştırma yönü

Yalnızca modeli değiştiren sınırlı aramalar precision'ı artırmadı. Sonraki deney,
doğrulanmış geçmiş patlama bilgisi ve daha ayrıntılı manyetik değişim gibi tahmin
anında bilinen bilgileri eklemeli; eğitimden önce erişilebilirlik zamanları ve
bölge ilişkileri denetlenmelidir. Yeni özellikler yardımcı olabilir, ancak
iyileşme garantisi yoktur. Mevcut recall koşulu 0.95 olarak kalır; alarm eşiğini
yükseltip recall'u sessizce düşürmek kullanıcının hedefini değiştirir.

## Yeniden üretim ve kanıt

{reproduction}
Komutlar mevcut artifact dizinlerini reddeder; tekrar için yeni yollar kullanın
ve raporlama betiğinin girdi yollarını uyarlayarak bu yolları kullanın.
Raporlama betiği yukarıdaki tarihli girdi yollarını kullanır. Yeni bir hata
denetimi ve eşlenmiş Markdown belgeleri üretir. İçerikleri değişirse yayımdan
önce iki sürümü gözden geçirip katalog kaynak hash'ini yenileyin.

{evidence}
Kaynak kod ve protokoller commitlenir; veri, modeller, tahminler ve üretilen
HTML yerel, Git tarafından yok sayılan artifact olarak kalır. Önceki raporlar
ve deney çıktıları korunur. Tarihsel karşılaştırma kaynağı:
[yakalama öncelikli sonuçlar](recall-first-results.md).
'''}
    for lang, content in texts.items():
        suffix = '' if lang == 'en' else '.tr'
        path = ROOT / f'docs/precision-followup-20261027{suffix}.md'
        if path.exists():
            raise ValueError('Preserve existing report; use a new revision')
        path.write_text(content)
    print(json.dumps(diagnostics))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
