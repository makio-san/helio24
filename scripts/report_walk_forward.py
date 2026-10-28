"""Publish matching Turkish and English annual evaluation evidence."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from scripts.report_precision_followup import table


def run(source, name):
    result = json.loads((source/'report.json').read_text())
    for relative, digest in result['artifact_hashes'].items():
        if sha256(source/relative) != digest:
            raise ValueError(f'Artifact changed: {relative}')
    paths = [ROOT/'docs'/f'{name}{suffix}.md' for suffix in ['', '.tr']]
    if any(path.exists() for path in paths):
        raise ValueError('Preserve existing documents')
    metrics = pd.DataFrame(result['metrics'])
    selected = metrics[metrics.model.eq('ensemble')].copy()
    summary = table(selected[['year','n','positives','threshold','precision','recall','fp','fn',
                              'accuracy','average_precision','brier']].fillna('undefined'))
    counts = table(pd.DataFrame([{'year': f['year'], 'status': f['status'], **{k:v for k,v in a.items() if k!='shared_harps'}}
                                for f in result['folds'] for a in f['audit']]))
    skipped = table(pd.DataFrame([{'year': f['year'], 'reason': f.get('reason','completed')}
                                  for f in result['folds']]))
    full = table(metrics.fillna('undefined'))
    intervals = table(pd.DataFrame([{'year': r['year'], 'model': r['model'], 'metric': metric,
                                     **value} for r in result['conditional_cluster_intervals']
                                    for metric,value in r['intervals'].items()]).fillna('undefined'))
    errors = table(pd.DataFrame([{'year': f['year'], **f['error_summary']}
                                 for f in result['folds'] if 'error_summary' in f]))
    hits = int(selected.recall.ge(.95).sum())
    eligible = int(selected.recall.notna().sum())
    complete = len(selected)
    evidence = table(pd.DataFrame([{'source':str((source/n).relative_to(ROOT)), 'SHA-256':sha256(source/n)}
                                    for n in ['report.json','metrics.csv']]))
    commands = f'''```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_walk_forward.py \\
  --protocol config/walk-forward-v1.json --output {source.relative_to(ROOT)}
.venv/bin/python scripts/report_walk_forward.py \\
  --source {source.relative_to(ROOT)} --report-name {name}
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en = f'''# Annual forecast stability and machine learning methods

The frozen ensemble reached recall >=0.95 in **{hits} of {eligible} evaluated years with
positive windows**. There were {complete} completed annual folds. This is a retrospective
development audit, not a new independent test or a model improvement claim. No dashboard
model was replaced. The reserved 2024–2025 test remains closed.

## What was evaluated

The protocol plans evaluation years 2014–2023. Each fold trains on all available years
before the preceding calendar year, calibrates on that preceding year, and evaluates
on the next year. Example: a 2023 evaluation trains before 2022 and calibrates in 2022.
Observation and 24-hour prediction intervals must remain inside their role boundaries.
HARPs seen in earlier roles are removed from later roles. The underlying development
population already contains earlier label, quality and region exclusions; these are
retained. Annual populations therefore differ from earlier single-period experiments.

This first annual audit retrains the existing **96-feature** logistic and XGBoost recipes,
their fixed 0.45/0.55 probability blend, and a constant training-prevalence baseline.
It does not rerun the 292-feature long-history candidates. Model settings and ensemble
weights were fixed before this run, but informed by previous development on these years;
the results must not be presented as untouched prospective estimates. There is no
evaluation-based candidate selection. Calibration probabilities and alarm thresholds
are fitted before each year's evaluation, and thresholds are saved before its predictions.

## Fold population and exclusions

{counts}
{skipped}
The retained source population has no positive windows in 2018, 2019 or 2020. This is
a statement about retained labels, not proof that no solar flare occurred in those years.
A calibration year missing either class cannot fit sigmoid calibration or a 95% recall
threshold; its fold is explicitly skipped. A zero-positive evaluation year remains in
the report: false positives and accuracy are measurable, recall/AP/TSS are undefined.
`undefined` is not zero. No years are removed for disappointing performance.

## Ensemble results at transferred calibration thresholds

{summary}
Precision is the fraction of alarm windows that are positive; recall is the fraction
of positive windows caught. FP counts negative windows producing alarms, FN counts
missed positive windows. Accuracy measures all correct windows and can be high under
class imbalance. AP summarizes ranking across thresholds; Brier and log loss score
probabilities, with smaller values better. All fractional scores are reported on a
0–1 scale, not as percentages. Counts are overlapping windows, not independent events.

## All model results

{full}
The constant baseline illustrates event prevalence and the high-recall cost of alarming
everywhere. A larger precision accompanied by lower recall is not automatically an
improvement against the user's recall >=0.95 objective. Do not pool these years into a
single success claim: event prevalence and available populations differ across years.

## False-alarm localization

{errors}
`top10_region_fp` counts false-positive windows in the ten HARPs with the most such
windows within that year. `zero_positive_region_fp` counts false positives in HARPs
with no retained positive evaluation window. This does not prove those regions never
flared. Per-region rows, positive counts, false positives, false negatives and mean
missing fraction are in each year's `region_errors.csv`. This localization is descriptive;
it does not establish a causal relationship with quality or permit removing hard regions.

## Conditional uncertainty

{intervals}
Intervals use 1000 whole-HARP bootstrap draws with seed 24. Models and thresholds remain
fixed; fitting, calibration and historical model-selection uncertainty are excluded.
For a zero-positive year, recall draws are undefined. Adjacent folds share historical
training data, so their results are not independent replications. Calibration is reused
for probability fitting and threshold selection, which may overfit that period.

## Techniques used and why

- Feature engineering: means, variation, latest values and changes from 24 magnetic
  measurements over 12 hours produce 96 baseline features using past observations only.
- Median imputation with missing indicators and standard scaling: transformations learn
  from training only; logistic regression uses scaling, XGBoost does not need it.
- Logistic regression: a regularized probabilistic linear reference model. XGBoost:
  gradient-boosted trees capturing nonlinear feature interactions. This audit uses the
  already frozen parameters, with no new hyperparameter search.
- Ensembling: a fixed weighted average of separately calibrated model probabilities.
- Sigmoid calibration: fits probability adjustment on the later calibration period.
  Threshold selection then targets recall >=0.95 in that period, without promising the
  same recall in a following year.
- Expanding-window evaluation, boundary purging and HARP separation: enforce temporal
  order and reduce similarity leakage between roles. Group bootstrap measures conditional
  uncertainty while retaining within-region dependence.

Earlier separate experiments also tried signed-log transforms, class weighting,
histogram boosting, Extra Trees, interactions, splines and 24/48-hour history summaries.
They are not all rerun here. Deep learning and live-data prediction have not been added
by this audit. Longer training by itself does not guarantee better precision.

## When can the best result be reached, and what follows?

There is no evidence-based date for a perfect model, nor a guarantee that the available
measurements and labels permit perfect separation. Training completion is not proof of
forecasting quality. Progress means reproducible gains at the required recall across
chronological evaluations, with uncertainty and false-alarm burden reported. A practical
precision requirement depends on how many false alerts an application can tolerate;
there is no universal satisfactory precision value.

Next, inspect temporal failures and regional error distributions, then freeze one
targeted candidate comparison using these same annual splits. Consider separating
probability fitting from threshold selection in time and assessing how much calibration
history is needed; do not retune on evaluation-year labels to force the 95% result.
Any revised policy must be measured as a new development experiment. Historical flare
features require verified availability timestamps and region associations. The reserved
test should be used only after the complete selection policy is frozen. These follow-up
experiments are not claimed to have been executed here.

## Reproduction

{commands}
Use fresh output directories, report names and protocol revisions for reruns; frozen
outputs cannot be overwritten. Review both full editions and register them in
`docs/reports.json` and `docs/reports.md` before publishing. Local model files, predictions,
raw data and generated HTML remain outside Git. Per-fold artifact hashes and code hashes
are recorded in `report.json`.

{evidence}
'''
    tr = f'''# Yıllık tahmin kararlılığı ve makine öğrenimi teknikleri

Sabit model birleşimi, **pozitif pencere içeren {eligible} değerlendirme yılının {hits}
tanesinde recall >=0.95** sağladı. Toplam {complete} yıllık tur tamamlandı. Bu, geçmişe
dönük geliştirme denetimidir; yeni bağımsız test veya model iyileşmesi iddiası değildir.
Dashboard modeli değiştirilmedi. Ayrılmış 2024–2025 testi kapalı kaldı.

## Ne değerlendirildi?

Protokol 2014–2023 değerlendirme yıllarını planlar. Her tur, bir önceki takvim yılından
önceki tüm kullanılabilir yıllarda eğitilir, önceki yılda kalibre edilir ve sonraki yılda
değerlendirilir. Örneğin 2023 değerlendirmesi, 2022 öncesinde eğitilir ve 2022'de kalibre
edilir. Gözlem ve 24 saatlik tahmin aralıkları kendi veri bölümlerinin sınırları içinde
kalmalıdır. Önceki bölümlerde görülen HARP'lar sonraki bölümlerden çıkarılır. Temel
geliştirme verisinde daha önce uygulanmış etiket, kalite ve bölge dışlamaları korunur.
Bu nedenle yıllık örnek toplulukları önceki tek dönemli deneylerden farklıdır.

Bu ilk yıllık denetim, mevcut **96 özellikli** lojistik regresyon ve XGBoost düzenlerini,
sabit 0.45/0.55 olasılık birleşimini ve eğitimdeki pozitif oranını sabit tahmin eden
referansı yeniden eğitir. 292 özellikli uzun geçmiş adaylarını yeniden çalıştırmaz.
Model ayarları ve birleşim ağırlıkları bu çalıştırmadan önce sabitlendi; ancak bu yıllar
üzerindeki önceki geliştirmeden etkilendi. Sonuçlar hiç görülmemiş geleceğin tahminleri
gibi sunulmamalıdır. Değerlendirmeye göre aday seçimi yapılmaz. Her yıl değerlendirilmeden
önce kalibrasyon olasılıkları ve alarm eşikleri öğrenilir; eşikler o yılın tahminlerinden
önce kaydedilir.

## Tur örnekleri ve dışlamalar

{counts}
{skipped}
Korunan kaynak veride 2018, 2019 ve 2020 yıllarında pozitif pencere yoktur. Bu, korunan
etiketlerle ilgili bir bulgudur; o yıllarda hiç Güneş patlaması olmadığına kanıt değildir.
İki sınıftan biri eksik olan kalibrasyon yılında sigmoid kalibrasyonu veya %95 recall
eşiği öğrenilemez; ilgili tur açık gerekçeyle atlanır. Pozitif içermeyen değerlendirme
yılı raporda kalır: yanlış pozitif ve accuracy ölçülebilir; recall/AP/TSS tanımsızdır.
`undefined` sıfır değildir. Hiçbir yıl kötü performans nedeniyle çıkarılmaz.

## Kalibrasyondan aktarılan eşiklerde birleşik model sonuçları

{summary}
Precision, alarm verilen pencereler içindeki pozitiflerin; recall, pozitif pencereler
içindeki yakalananların oranıdır. FP alarm üreten negatif pencereleri, FN kaçırılan
pozitif pencereleri sayar. Accuracy tüm doğru pencereleri ölçer ve sınıf dengesizliğinde
yüksek olabilir. AP eşikler boyunca sıralamayı özetler; Brier ve log loss olasılıkları
puanlar ve düşük olmaları daha iyidir. Tüm oransal skorlar yüzde olarak değil, 0–1
ölçeğinde verilir. Sayılar bağımsız olayları değil, örtüşen pencereleri anlatır.

## Tüm model sonuçları

{full}
Sabit referans, olay sıklığını ve her yerde alarm vermenin yüksek recall maliyetini
gösterir. Daha düşük recall ile gelen daha yüksek precision, kullanıcının recall >=0.95
hedefine göre otomatik olarak iyileşme değildir. Yılları tek bir başarı iddiasında
birleştirmeyin: olay sıklığı ve kullanılabilir örnek toplulukları yıllar arasında değişir.

## Yanlış alarmların bölgesel dağılımı

{errors}
`top10_region_fp`, o yılda en fazla yanlış pozitif pencere üreten on HARP'ın toplamını
verir. `zero_positive_region_fp`, korunan değerlendirme pencereleri arasında pozitif
olmayan HARP'lardaki yanlış pozitifleri sayar. Bu, o bölgelerin hiç patlamadığı anlamına
gelmez. Bölge başına satır, pozitif, yanlış pozitif, yanlış negatif sayıları ve ortalama
eksik ölçüm oranı her yılın `region_errors.csv` dosyasındadır. Bu dağılım betimseldir;
kaliteyle nedensel ilişki kurmaz ve zor bölgeleri çıkarmayı haklı göstermez.

## Koşullu belirsizlik

{intervals}
Aralıklar, 24 tohumla bütün HARP'ları örnekleyen 1000 bootstrap tekrarı kullanır. Model
ve eşikler sabittir; eğitim, kalibrasyon ve geçmiş model seçimi belirsizliği dahil
değildir. Pozitif olmayan yılda recall tekrarları tanımsızdır. Komşu turlar geçmiş eğitim
verisini paylaşır; sonuçları bağımsız tekrarlar değildir. Kalibrasyon hem olasılık
öğreniminde hem eşik seçiminde kullanılır ve o döneme aşırı uyum oluşabilir.

## Kullanılan teknikler ve amaçları

- Özellik mühendisliği: 24 manyetik ölçümün 12 saatlik ortalamaları, değişkenliği,
  son değerleri ve değişimleri, yalnızca geçmişten 96 temel özellik üretir.
- Medyanla eksik değer doldurma, eksiklik göstergeleri ve standart ölçekleme: dönüşümler
  yalnızca eğitimden öğrenilir; lojistik regresyon ölçekleme kullanır, XGBoost gerektirmez.
- Lojistik regresyon: düzenlileştirilmiş olasılıksal doğrusal referans modeldir. XGBoost:
  doğrusal olmayan özellik ilişkilerini yakalayan gradient boosting ağaçlarıdır. Bu
  denetim, yeni hiperparametre araması yapmadan önceden sabitlenen ayarları kullanır.
- Model birleştirme: ayrı kalibre edilmiş model olasılıklarının sabit ağırlıklı ortalaması.
- Sigmoid kalibrasyonu: daha sonraki kalibrasyon döneminde olasılık düzeltmesini öğrenir.
  Ardından eşik seçimi, o dönemde recall >=0.95 hedefler; sonraki yılda aynı recall'ı
  sağlayacağını garanti etmez.
- Genişleyen eğitim pencereli değerlendirme, sınır temizliği ve HARP ayrımı: zaman
  sırasını korur, bölümler arasındaki benzerlik sızıntısını azaltır. Grup bootstrap,
  bölge içi bağımlılığı koruyarak koşullu belirsizliği ölçer.

Önceki ayrı deneylerde işaret koruyan logaritmik dönüşümler, sınıf ağırlıkları, histogram
boosting, Extra Trees, etkileşimler, spline'lar ve 24/48 saatlik geçmiş özetleri de denendi.
Bunların tamamı burada yeniden çalıştırılmadı. Bu denetimle derin öğrenme veya canlı veri
tahmini eklenmedi. Daha uzun eğitim tek başına daha iyi precision garantisi değildir.

## En iyi sonuca ne zaman ulaşılır ve sırada ne var?

Mükemmel model için kanıta dayalı bir tarih yoktur; mevcut ölçümler ve etiketlerle
kusursuz ayrım yapılabileceği de garanti değildir. Eğitimin tamamlanması tahmin kalitesini
kanıtlamaz. İlerleme; belirsizlik ve yanlış alarm yükü raporlanırken, gereken recall
koşulunda kronolojik değerlendirmeler boyunca yeniden üretilebilir kazanımlar demektir.
Pratik precision gereksinimi, uygulamanın kaç yanlış alarma katlanabileceğine bağlıdır;
evrensel bir yeterli precision değeri yoktur.

Sonraki adım, zamansal başarısızlıkları ve bölgesel hata dağılımlarını inceleyip aynı yıllık
ayrımlar üzerinde hedefli tek bir aday karşılaştırmasını sabitlemektir. Olasılık öğrenimiyle
eşik seçimini zaman içinde ayırmak ve gereken kalibrasyon geçmişini değerlendirmek
düşünülebilir; %95 sonucunu zorlamak için değerlendirme yılı etiketleriyle eşik yeniden
ayarlanmamalıdır. Yeni kural, yeni bir geliştirme deneyi olarak ölçülmelidir. Geçmiş patlama
özellikleri, doğrulanmış erişilebilirlik zamanları ve bölge ilişkileri gerektirir. Ayrılmış
test ancak tüm seçim kuralı dondurulduktan sonra kullanılmalıdır. Bu takip deneylerinin
burada yürütüldüğü iddia edilmez.

## Yeniden üretim

{commands}
Tekrar için yeni çıktı dizinleri, rapor adları ve protokol sürümleri kullanın; dondurulmuş
çıktıların üzerine yazılmaz. Yayımdan önce iki tam sürümü gözden geçirip `docs/reports.json`
ve `docs/reports.md` dosyalarına kaydedin. Yerel model dosyaları, tahminler, ham veri ve
üretilen HTML Git dışında kalır. Tur başına artifact özetleri ve kod özetleri
`report.json` içinde kayıtlıdır.

{evidence}
'''
    for path, content in zip(paths,[en,tr]):
        path.write_text(content)
    print('\n'.join(map(str, paths)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--report-name',required=True)
    args = parser.parse_args()
    run(args.source.resolve(),args.report_name)
