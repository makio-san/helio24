"""Write paired reports from a completed, hash-verified long-history experiment."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from scripts.report_precision_followup import table


def run(source, report_name):
    result = json.loads((source / 'report.json').read_text())
    history_path = ROOT / result['protocol']['history']['artifact'] / 'report.json'
    if sha256(history_path) != result['protocol']['history']['report_sha256']:
        raise ValueError('History evidence changed')
    history = json.loads(history_path.read_text())
    paths = [ROOT / 'docs' / f'{report_name}{suffix}.md' for suffix in ['', '.tr']]
    if any(path.exists() for path in paths):
        raise ValueError('Preserve existing document editions')
    keys = ['precision', 'recall', 'tp', 'fp', 'fn', 'tn', 'accuracy', 'balanced_accuracy',
            'f1', 'false_positive_rate', 'false_alarm_ratio', 'tss', 'average_precision',
            'brier', 'log_loss', 'threshold']

    def comparison(field):
        values = result[field]
        return table(pd.DataFrame([{'metric': k, 'incumbent': values['incumbent'][k],
                                   'selected': values['selected'][k]} for k in keys]))

    diagnostic = comparison('metrics')
    operating = comparison('calibration_threshold_validation_metrics')
    candidates = table(pd.read_csv(source / 'calibration_candidates.csv')[[
        'candidate', 'precision', 'recall', 'fp', 'average_precision', 'brier', 'log_loss']])
    availability = {role: {'role': role, 'available_24h': 0, 'available_48h': 0}
                    for role in ['train', 'calibration', 'validation']}
    for shard in history['shards']:
        for role, values in shard['availability'].items():
            for hours in [24, 48]:
                availability[role][f'available_{hours}h'] += values[f'{hours}h']
    coverage = table(pd.DataFrame(availability.values()))
    intervals = table(pd.DataFrame([
        {'evaluation': scope, 'model': model, 'metric': metric, **interval}
        for scope, field in [('validation_reselected', 'conditional_cluster_intervals'),
                             ('calibration_transferred', 'calibration_threshold_cluster_intervals')]
        for model, values in result[field].items() for metric, interval in values.items()]))
    evidence_paths = [source / n for n in ['report.json', 'calibration_candidates.csv',
                                          'operating_thresholds.json', 'validation_predictions.parquet']]
    evidence_paths.append(history_path)
    evidence = table(pd.DataFrame([{'source': str(p.relative_to(ROOT)), 'SHA-256': sha256(p)}
                                   for p in evidence_paths]))
    winner = result['winner']['candidate']
    old, new = result['metrics']['incumbent'], result['metrics']['selected']
    difference = (new['precision'] - old['precision'])*100
    candidate_rows = pd.read_csv(source / 'calibration_candidates.csv')
    best_new = candidate_rows[candidate_rows.candidate.ne('incumbent')].sort_values(
        ['precision', 'average_precision', 'candidate'], ascending=[False, False, True]).iloc[0]
    baseline_cal = candidate_rows[candidate_rows.candidate.eq('incumbent')].iloc[0]
    protocol_id = result['protocol']['id']
    history_dir = history_path.parent.relative_to(ROOT)
    source_dir = source.relative_to(ROOT)
    command = f'''```sh
.venv/bin/python scripts/materialize_long_history.py --output {history_dir} --workers 1
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_precision_log.py \\
  --protocol config/{protocol_id}.json --output {source_dir}
.venv/bin/python scripts/report_long_history_precision.py \\
  --source {source_dir} --report-name {report_name}
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{report_name}
```
'''
    outcome_en = ('The selected candidate passed the development diagnostic promotion checks.'
                  if result['promote'] else 'The selected candidate did not pass all development diagnostic promotion checks.')
    outcome_tr = ('Seçilen aday, geliştirme amaçlı tanısal model değiştirme kontrollerini geçti.'
                  if result['promote'] else 'Seçilen aday, geliştirme amaçlı tanısal model değiştirme kontrollerinin tamamını geçmedi.')
    en = f'''# Long-history precision experiment

Calibration selected `{winner}`. {outcome_en} Precision changed by {difference:.6f}
percentage points in the matched-recall validation diagnostic. The dashboard model
has not been replaced. See the separate transferred-threshold results before
interpreting these values as operational performance.

## Data and features

The completed materialization verified exactly {history['rows']} original forecast keys.
Training contains 484549 windows/8698 positives; calibration contains 50756/421;
validation contains 60366/781. Training precedes 2022 calibration and 2023 validation.
Reserved 2024–2025 observations and labels were excluded at the logical reader boundary;
archive bytes containing those years were downloaded only for integrity verification.
No labels or retained forecasts were changed. Features use raw observations, independently
of outcome-based row exclusions. The previous disk-space blocker was cleared.

Each 24/48-hour history adds mean, population standard deviation, endpoint change and
normalized change for 24 magnetic measurements, plus coverage/missing indicators:
196 new features, 292 total. Complete cadence requires 120/240 observations strictly
before the forecast. Histories crossing a role boundary, cadence gap or leap-second
transition are unavailable; rows are retained. A measurement needs 80% finite values.
Normalized change divides endpoint change by absolute mean plus standard deviation,
clipped to [-100, 100]; a zero denominator produces a missing value. Availability is
temporal coverage, not an instrument-quality guarantee.

{coverage}
## Frozen search

Three candidates use signed-log logistic regression (C=1), XGBoost (200 trees, depth 3)
and histogram gradient boosting (200 iterations, 15 leaves). Full parameters and source
hashes are frozen in `config/{protocol_id}.json`. Preprocessing fits on training only;
sigmoid calibration fits on calibration. New-model mixture weights 0.25, 0.5, 0.75 and
1.0 produce 12 candidates plus the incumbent. Selection maximizes calibration precision
at recall >=0.95, then AP, then candidate ID. Only the selected candidate is evaluated
on validation. The incumbent remains the 0.45 logistic/0.55 XGBoost ensemble.

{candidates}
## Matched-recall development diagnostic

{diagnostic}
These thresholds are reselected using validation labels to compare precision at
recall >=0.95. They are not thresholds transferred from calibration. Diagnostic promotion
requires higher precision, AP no lower, and Brier/log loss no higher, with recall >=0.95.
Passing this comparison alone does not establish a deployable 95% recall operating point.

## Interpretation and next development step

The strongest new calibration candidate was `{best_new['candidate']}`: precision
{best_new['precision']:.6f} versus {baseline_cal['precision']:.6f} for the incumbent,
with {int(best_new['fp'])} versus {int(baseline_cal['fp'])} false-positive windows.
Its AP was {best_new['average_precision']:.6f} versus {baseline_cal['average_precision']:.6f}.
Improved overall ranking therefore did not translate into better precision at the
required high-recall operating point in calibration. This does not prove that longer
history is intrinsically unhelpful; it rejects these specific candidates and summaries.

The next research step is additional chronological development folds, with alarm
thresholds fitted on each earlier calibration period and transferred unchanged to the
following period. This should measure the stability of both precision and recall before
another broad parameter search. Any new search needs a frozen budget and must retain
the reserved test. This step has not been executed in this experiment.

## Frozen calibration thresholds on validation

{operating}
These thresholds were recorded before validation evaluation and were not adjusted to
validation labels. This table measures temporal transfer of the selected alarm policy;
recall can fall below 0.95. It is distinct from the matched-recall diagnostic above.

## Uncertainty and limitations

{intervals}
Intervals use 1000 whole-HARP bootstrap draws, seed 24, conditional on fitted models
and thresholds. They omit training, calibration and model-selection uncertainty.
Calibration is reused for probability fitting and candidate selection; earlier validation
findings guided this experiment. This is adaptive development, not an independent test.
Counts refer to overlapping forecast windows, not independent flares or alert episodes.
Longer histories do not resolve uncertain event-region associations. No future precision
or recall level is guaranteed. Accuracy is the fraction of all correct predictions;
precision is the positive fraction among alarms; recall is the caught fraction among
positive windows. AP measures ranking across thresholds; lower Brier/log loss indicates
better probabilistic scoring. There is no universal acceptable precision independent
of event prevalence and the cost of false alarms.

## Reproduction and evidence

{command}
Existing outputs must remain frozen. For another run, choose fresh artifact directories
and document names; freeze the new materialization hash in a new protocol revision before
training. Review both document editions, then register their source hash and links in
`docs/reports.json` and `docs/reports.md` before publishing to a new HTML directory.
Raw data, models, predictions and generated HTML remain outside Git.

{evidence}
'''
    tr = f'''# Uzun geçmişli precision deneyi

Kalibrasyonda `{winner}` seçildi. {outcome_tr} Aynı recall düzeyindeki doğrulama
incelemesinde precision değişimi {difference:.6f} yüzde puan oldu. Dashboard modeli
değiştirilmedi. Bu değerleri uygulama performansı olarak yorumlamadan önce ayrı
sunulan aktarılmış eşik sonuçlarına bakılmalıdır.

## Veri ve özellikler

Tamamlanan özellik hazırlığı, özgün {history['rows']} tahmin anahtarının birebir eşleştiğini doğruladı.
Eğitimde 484549 pencere/8698 pozitif, kalibrasyonda 50756/421, doğrulamada 60366/781 vardır.
Eğitim, 2022 kalibrasyonundan ve 2023 doğrulamasından öncedir. Ayrılmış 2024–2025
gözlemleri ve etiketleri mantıksal okuyucu sınırında dışlandı; bu yılları içeren arşiv
baytları yalnızca bütünlük doğrulaması için indirildi. Etiketler ve korunan tahminler
değiştirilmedi. Özellikler, sonuçlara bağlı satır dışlamalarından bağımsız olarak ham
gözlemleri kullanır. Önceki disk alanı engeli giderildi.

Her 24/48 saatlik geçmiş, 24 manyetik ölçümün ortalamasını, popülasyon standart sapmasını,
uç noktalar arasındaki değişimini ve normalize edilmiş değişimini; ayrıca kapsam/eksiklik
göstergelerini ekler: 196 yeni özellik, toplam 292 özellik. Tam gözlem sıklığı, tahminden
kesinlikle önceki 120/240 gözlemi gerektirir. Veri bölümü sınırını, gözlem boşluğunu veya
artık saniye geçişini aşan geçmişler kullanılamaz; satırlar korunur. Her ölçüm için %80
sonlu değer gerekir. Normalize edilmiş değişim, uç noktalar arasındaki farkı mutlak
ortalama ile standart sapmanın toplamına böler ve [-100, 100] aralığına kırpar; sıfır
payda eksik değer üretir. Kullanılabilirlik zamansal kapsamdır, cihaz kalitesi garantisi değildir.

{coverage}
## Dondurulmuş arama

Üç aday, işaret koruyan logaritmik lojistik regresyon (C=1), XGBoost (200 ağaç, derinlik 3)
ve histogram tabanlı gradient boosting (200 iterasyon, 15 yaprak) kullanır. Tüm parametreler
ve kaynak özetleri `config/{protocol_id}.json` içinde sabitlenmiştir. Ön işleme yalnızca
eğitimde, sigmoid kalibrasyonu kalibrasyon verisinde öğrenilir. 0.25, 0.5, 0.75 ve 1.0
yeni model karışım ağırlıkları, mevcut modele ek 12 aday üretir. Seçim, recall >=0.95
koşulunda kalibrasyon precision değerini, ardından AP değerini ve aday kimliğini kullanır.
Doğrulamada yalnızca seçilen aday değerlendirilir. Mevcut model, 0.45 lojistik/0.55 XGBoost
birleşimi olarak kalır.

{candidates}
## Aynı recall düzeyinde geliştirme incelemesi

{diagnostic}
Bu eşikler, recall >=0.95 düzeyinde precision karşılaştırmak için doğrulama etiketleriyle
yeniden seçilir. Kalibrasyondan aktarılmış eşikler değildir. Tanısal model değiştirme
kontrolü, recall >=0.95 koşulunda daha yüksek precision, daha düşük olmayan AP ve daha
yüksek olmayan Brier/log loss gerektirir. Yalnızca bu karşılaştırmayı geçmek, uygulamada
%95 recall sağlayan bir alarm eşiğini kanıtlamaz.

## Yorum ve sonraki geliştirme adımı

Kalibrasyondaki en güçlü yeni aday `{best_new['candidate']}` oldu: precision değeri
{best_new['precision']:.6f}, mevcut modelinki {baseline_cal['precision']:.6f}; yanlış
pozitif pencere sayıları sırasıyla {int(best_new['fp'])} ve {int(baseline_cal['fp'])}.
AP değerleri {best_new['average_precision']:.6f} ve {baseline_cal['average_precision']:.6f} oldu.
Dolayısıyla genel sıralamadaki iyileşme, kalibrasyonda hedeflenen yüksek recall çalışma
noktasında daha iyi precision sağlamadı. Bu, uzun geçmişin özünde yararsız olduğunu
kanıtlamaz; denenen belirli adayları ve özetleri eler.

Sonraki araştırma adımı, ek kronolojik geliştirme bölümleridir: alarm eşikleri her erken
kalibrasyon döneminde belirlenip sonraki döneme değiştirilmeden aktarılmalıdır. Yeni ve
geniş bir parametre aramasından önce hem precision hem recall kararlılığı ölçülmelidir.
Her yeni aramanın bütçesi önceden sabitlenmeli ve ayrılmış test korunmalıdır. Bu adım,
bu deney kapsamında yürütülmedi.

## Sabit kalibrasyon eşiklerinin doğrulama sonuçları

{operating}
Bu eşikler doğrulama değerlendirmesinden önce kaydedildi ve doğrulama etiketlerine göre
ayarlanmadı. Tablo, seçilen alarm kuralının daha sonraki döneme aktarımını ölçer; recall
0.95 altına düşebilir. Yukarıdaki aynı recall düzeyinde karşılaştırmadan ayrıdır.

## Belirsizlik ve sınırlamalar

{intervals}
Aralıklar, eğitilmiş modeller ve eşikler sabitken 24 tohumla bütün HARP'ları örnekleyen
1000 bootstrap tekrarı kullanır. Eğitim, kalibrasyon ve model seçimi belirsizliğini içermez.
Kalibrasyon hem olasılık öğrenimi hem aday seçimi için tekrar kullanılır; önceki doğrulama
bulguları bu deneyi yönlendirdi. Bu uyarlamalı geliştirmedir, bağımsız test değildir.
Sayılar bağımsız patlamaları veya alarm dönemlerini değil, örtüşen tahmin pencerelerini
anlatır. Daha uzun geçmişler belirsiz olay-bölge ilişkilerini çözmez. Gelecekte herhangi
bir precision veya recall düzeyi garanti edilmez. Accuracy tüm tahminler içindeki doğru
tahmin oranıdır; precision alarmlar içindeki pozitiflerin, recall pozitif pencereler
içindeki yakalananların oranıdır. AP eşikler boyunca sıralama başarısını ölçer; daha düşük
Brier/log loss daha iyi olasılıksal puanlama gösterir. Olay sıklığından ve yanlış alarm
maliyetinden bağımsız, evrensel bir kabul edilebilir precision değeri yoktur.

## Yeniden üretim ve kanıt

{command}
Mevcut çıktılar dondurulmuş olarak korunmalıdır. Yeni çalıştırmada yeni artifact dizinleri
ve belge adları seçilmeli; eğitimden önce yeni hazırlık özeti yeni protokol sürümünde
sabitlenmelidir. İki belge sürümü gözden geçirilmeli, ardından kaynak özeti ve bağlantılar
`docs/reports.json` ve `docs/reports.md` dosyalarına kaydedilmeli, yeni HTML dizinine
yayımlanmalıdır. Ham veri, modeller, tahminler ve üretilen HTML Git dışında kalır.

{evidence}
'''
    for path, content in zip(paths, [en, tr]):
        path.write_text(content)
    print('\n'.join(map(str, paths)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--report-name', required=True)
    args = parser.parse_args()
    run(args.source.resolve(), args.report_name)
