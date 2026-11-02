"""Publish paired annual-comparison documents from a frozen evaluation snapshot."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sequence_training import verify_files
from scripts.report_temporal_errors import table


def run(source,name):
    r=json.loads((source/'report.json').read_text());verify_files(source,r['artifact_hashes']);verify_files(ROOT,r['code_hashes'])
    paths=[ROOT/'docs'/f'{name}{suffix}.md' for suffix in ['', '.tr']]
    if any(p.exists() for p in paths):raise ValueError('Preserve documents')
    main_arms=['baseline','short_training','chronological','shuffled_interior']
    metrics=pd.read_csv(source/'metrics.csv');m=metrics[metrics.arm.isin(main_arms)]
    performance=table(m[['year','arm','n','positives','threshold','tp','fp','fn','tn','precision','recall']])
    scoring=table(m[['year','arm','accuracy','always_quiet_accuracy','balanced_accuracy','f1','tss','false_positive_rate','average_precision','brier','log_loss']])
    folds=table(pd.read_csv(source/'folds.csv'))
    comparison=pd.read_csv(source/'comparisons.csv');gates=table(comparison[['candidate','control','required_positive_years','comparable_years','missing_eligible_years','precision_win_count','recall_met_count','fp_reduced_count','primary_met_count','full_met_count','all_year_full']])
    intervals=pd.read_csv(source/'intervals.csv');primary=intervals[(intervals.candidate=='chronological')&(intervals.control=='baseline')]
    uncertainty=table(primary[['year','metric','estimate','lower','upper','valid_draws','undefined_draws']])
    ordering=table(intervals[(intervals.candidate=='chronological')&(intervals.control=='shuffled_interior')][['year','metric','estimate','lower','upper','valid_draws','undefined_draws']])
    curve=pd.read_csv(source/'reliability.csv')
    supported=curve[curve.arm.isin(['baseline','chronological'])].sort_values(['year','arm','n','bin'],ascending=[True,True,False,True]).groupby(['year','arm'],sort=True).head(1)
    calibration=table(supported[['year','arm','left','right','n','regions','positive_regions','mean_probability','observed_rate','lower','upper','valid_draws']])
    spread=table(pd.read_csv(source/'seed_spread.csv')[['year','arm','seeds','precision_min','precision_max','recall_min','recall_max','fp_min','fp_max','average_precision_min','average_precision_max']])
    baseline=m[m.arm.eq('baseline')].set_index('year');tcn=m[m.arm.eq('chronological')].set_index('year');shuffled=m[m.arm.eq('shuffled_interior')].set_index('year')
    ap_n=int((tcn.average_precision.notna()&baseline.average_precision.notna()).sum());order_ap_n=int((tcn.average_precision.notna()&shuffled.average_precision.notna()).sum())
    n=len(tcn);ap_worse=int((tcn.average_precision<baseline.average_precision).sum());brier_worse=int((tcn.brier>baseline.brier).sum());log_worse=int((tcn.log_loss>baseline.log_loss).sum());order_ap_wins=int((tcn.average_precision>shuffled.average_precision).sum())
    selected=', '.join(map(str,r['selected_years']));missing=', '.join(map(str,r['missing_eligible_years'])) or 'none'
    interim=r['status']!='final_complete'
    en_status='INTERIM SNAPSHOT — experiment incomplete' if interim else 'FINAL COMPLETED EXPERIMENT'
    tr_status='ARA DEĞERLENDİRME — deney tamamlanmadı' if interim else 'TAMAMLANMIŞ DENEYİN SON DEĞERLENDİRMESİ'
    evidence=table(pd.DataFrame([{'source':str(p.relative_to(ROOT)),'sha256':sha256(p)} for p in [source/'report.json',ROOT/'config/temporal-evaluation-report-v1.json',ROOT/'config/temporal-sequence-v2.json']]))
    years_arg='--years '+' '.join(map(str,r['selected_years'])) if interim else '--require-complete'
    commands=f'''```sh
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/evaluate_temporal_snapshot.py {years_arg} --output {source.relative_to(ROOT)}
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/report_temporal_evaluation.py --source {source.relative_to(ROOT)} --name {name}
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pytest -q
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    gain_en=('The small 2015 precision gain over baseline has an interval crossing zero; it is not established as a reliable improvement.' if 2015 in r['selected_years'] else 'Interpret point gains with their paired intervals; they do not alone establish reliable improvement.')
    gain_tr=('2015’in referansa göre küçük precision kazancının aralığı sıfırı kapsar; güvenilir iyileşme olarak kurulmuş değildir.' if 2015 in r['selected_years'] else 'Nokta kazançları eşleştirilmiş aralıklarla yorumlanmalıdır; tek başlarına güvenilir iyileşme kurmazlar.')
    en=f'''# Annual TCN comparison: performance, calibration and uncertainty

**{en_status}.** Included years: {selected}. Eligible periods absent from this snapshot:
{missing}. This is a frozen comparison of completed outputs, not a live dashboard.
The incumbent remains in use; no model was promoted and the 2024–2025 test stays closed.

## Coverage and controls

{folds}
Seven annual periods are eligible under the original frozen split. The original
2019–2021 folds are skipped because their preceding calibration populations lack positive
examples. Retain the zero-positive 2018 evaluation: recall and AP are undefined, while
false alarms and probability losses remain measurable. Missing eligible years, including
zero-positive ones, prevent a completed all-year gate. Final mode refuses to run until
all eligible annual outputs and the final experiment manifest exist.

The four reported arms are the original 96-summary-feature ensemble (`baseline`), its
shorter-training reference (`short_training`), raw-order TCN (`chronological`) and the
same architecture with shuffled interior steps (`shuffled_interior`). The shorter-training
reference uses different classifier history and is a separate benchmark. Both neural
arms use identical training/calibration/evaluation rows and three seeds 24/42/97.
They average raw sigmoid probabilities equally before sigmoid calibration. Individual
seed results are also retained, without choosing a winning seed. The dashboard's Historical
replay area displays Experiment 1; Experiment progress monitors these V2 training records.

Frozen artifact hashes are checked and every saved metric, including seed metrics, is
recomputed from stored predictions and thresholds. Thresholds are transferred from the
prior calibration year unchanged. This report performs no fitting, calibration refit,
threshold tuning or exclusions. The outer years have been repeatedly inspected during
development, so these are adaptive retrospective results, not an independent final test.

## Operating-point performance

{performance}
Fractions use a 0–1 scale. Precision is TP/(TP+FP), recall TP/(TP+FN), and FPR FP/(FP+TN).
TP, FP, FN and TN count overlapping hourly forecast windows, not independent flares or
notifications. Candidates keep their own calibration thresholds; comparisons are not
at matched recall. A precision increase with recall below 0.95 does not meet the objective.

## Ranking, probability scores and accuracy

{scoring}
Accuracy is (TP+TN)/n; balanced accuracy averages recall and specificity; F1 is the
harmonic mean of precision and recall; TSS is recall minus FPR. The always-quiet accuracy
shows why high accuracy alone is not a rare-event success criterion. AP measures ranking
across operating points and is not threshold-specific. Brier is mean squared probability
error; log loss penalizes confident wrong predictions. Both probability losses are proper
scores, but combine calibration and discrimination rather than isolating calibration.

Across the {n} included years, chronological AP is below baseline in {ap_worse} of {ap_n}
years with defined AP, Brier is higher in {brier_worse}, and log loss higher in {log_worse}.
Chronological AP exceeds shuffled AP in {order_ap_wins} of {order_ap_n} comparable AP years. This does not establish a stable benefit of temporal
ordering; the control also changes the ordering of missingness masks, so it does not isolate
physical magnetic evolution from availability patterns. No pooled average hides weak years.
All measured fields and individual seed rows remain in metrics.csv.

## Explicit acceptance and incomplete coverage

{gates}
The common primary check requires higher precision, recall >=0.95 and fewer FP together.
The full check additionally requires AP no lower and Brier/log loss no higher than the
named control. Point wins and simultaneous passes are separate counts. All-year success
also requires every required positive year and every original eligible period, with no
missing candidates. These are the frozen design's operational comparison rules, not
universal acceptable metric ranges or proof of statistical significance. No automatic
promotion follows even if a complete future comparison passes.

## Conditional paired uncertainty

Chronological minus baseline intervals:

{uncertainty}
Chronological minus shuffled-order intervals:

{ordering}
Intervals are percentile 95% intervals from 1000 paired whole-HARP bootstrap draws with
seed 24. The same sampled regions and their full windows contribute to both arms.
Existing precision/recall/FP intervals are reused; paired Brier/log-loss difference
intervals are newly calculated from the frozen probabilities. Positive precision/recall
differences favor the candidate; negative FP/Brier/log-loss differences favor it.
An interval crossing or touching zero does not establish a directional difference at
that interval level. `valid_draws` and `undefined_draws` expose resamples without defined
precision/recall. AP is reported as a point estimate, with no bootstrap AP interval here.

Models, calibrators, thresholds and original HARP identities remain fixed. These intervals
exclude retraining, calibration-fit and historical-selection uncertainty. Adjacent years
share training history, and multiple comparisons are not multiplicity-adjusted. HARP
resampling handles within-region window dependence but does not establish independence
between catalogued regions. {gain_en} Whole-year and subgroup
results must not be read as universal causal claims.

## Probability reliability

The highest-count bin for each baseline/chronological pair is displayed below to show
sample and region support; selecting it is only a display choice, not a modeling rule.
All bins and all four arms remain in reliability.csv.

{calibration}
Bin edges are fixed in config/temporal-evaluation-report-v1.json, from 0 to 1 with finer
resolution at low probabilities. Intervals are right-closed, with zero in the first bin.
For each populated bin, mean_probability is compared with observed_rate. The difference
observed minus predicted is saved in CSV. Observed-rate bounds resample complete HARPs,
keeping probabilities and membership fixed. Empty bins remain undefined, and sparse bins
may have few valid draws or few positive regions. A 0–0 observed-rate interval after no
observed events is not a guarantee of zero future flare probability.

The local standalone figure `reliability.png` shows every populated bin on a full 0–1
range for baseline and chronological arms. It does not suppress low-support bins or
show uncertainty whiskers; numerical support and conditional bounds are in CSV and the
table. Reliability plots diagnose probability agreement; they do not change predictions.

## Seed variability

{spread}
Each seed has its own calibration-only threshold for its diagnostic result. Min/max
ranges are descriptive variability across three fits, not confidence intervals or ranges
for the seed-averaged model. No best seed or favorable year is selected. Full Brier/log-loss
seed ranges are in seed_spread.csv.

## Decision and completion path

The current snapshot provides no basis to replace the incumbent. Complete the fixed annual
experiment, retaining weak years and absent periods explicitly. The prior error audit
localizes failures but does not justify changing the ongoing training recipe. A future
hybrid/static-summary control remains a hypothesis requiring a new frozen protocol after
this comparison. The report generator supports final mode without overwriting this snapshot.

{commands}
Use fresh output/report names on reruns. To create the final comparison, replace the
explicit --years list with --require-complete and choose a new output directory; the
command fails while the experiment is incomplete. Publish a new paired document revision
and register both reviewed editions/source hash in docs/reports.json and docs/reports.md.
Earlier snapshot revisions remain preserved. Local CSV, PNG, predictions and model files
stay outside Git. The current snapshot report records every source-fold hash and code hash;
no reserved test is opened and local app.py branding edits remain uncommitted.

{evidence}
'''
    tr=f'''# Yıllık TCN karşılaştırması: performans, kalibrasyon ve belirsizlik

**{tr_status}.** Dahil edilen yıllar: {selected}. Bu kayıtta bulunmayan uygun dönemler:
{missing}. Bu, tamamlanmış çıktıların sabit karşılaştırmasıdır; canlı dashboard değildir.
Mevcut model kullanılmaya devam eder; yeni model alınmadı ve 2024–2025 testi kapalı kaldı.

## Kapsam ve kontroller

{folds}
Özgün sabit ayrıma göre yedi yıllık dönem uygundur. Önceki kalibrasyon örneklemlerinde
pozitif bulunmadığından özgün 2019–2021 bölümleri atlanır. Pozitif olmayan 2018 değerlendirmesi
korunur: recall ve AP tanımsızdır; yanlış alarm ve olasılık kayıpları ölçülebilir.
Sıfır-pozitif yıllar dahil eksik uygun dönemler, tamamlanmış tüm-yıllar koşulunu engeller.
Son değerlendirme modu, tüm uygun yıllık çıktılar ve son deney kaydı oluşmadan çalışmaz.

Dört kol raporlanır: özgün 96 özet özellikli birleşim (`baseline`), daha kısa eğitimli
referansı (`short_training`), ham sıralı TCN (`chronological`) ve iç adımları karıştırılmış
aynı mimari (`shuffled_interior`). Kısa eğitim referansı farklı sınıflandırıcı geçmişi
kullanır; ayrı bir karşılaştırmadır. İki sinir ağı kolu aynı eğitim/kalibrasyon/değerlendirme
satırlarını ve 24/42/97 tohumlarını kullanır. Ham sigmoid olasılıkları eşit ortalandıktan
sonra sigmoid kalibrasyonu yapılır. Tekil tohum sonuçları da korunur; kazanan tohum seçilmez.
Dashboard'ın Historical replay alanı Deney 1'i, Experiment progress sekmesi bu V2 eğitim
kayıtlarını gösterir.

Sabit çıktı hash değerleri doğrulanır; tohumlar dahil her kayıtlı metrik, saklanan tahmin
ve eşiklerden yeniden hesaplanır. Eşikler önceki kalibrasyon yılından değiştirilmeden
aktarılır. Bu rapor eğitim, yeniden kalibrasyon, eşik ayarı veya dışlama yapmaz. Dış yıllar
geliştirmede tekrar tekrar incelendiğinden sonuçlar uyarlamalı geçmiş değerlendirmesidir;
bağımsız son test değildir.

## Çalışma noktasındaki performans

{performance}
Oranlar 0–1 ölçeğindedir. Precision TP/(TP+FP), recall TP/(TP+FN), FPR FP/(FP+TN)'dir.
TP, FP, FN ve TN bağımsız patlama veya bildirimleri değil, örtüşen saatlik tahmin
pencerelerini sayar. Adaylar kendi kalibrasyon eşiklerini korur; karşılaştırmalar eşit
recall'da değildir. Recall 0.95 altındayken precision artışı hedefi karşılamaz.

## Sıralama, olasılık skorları ve accuracy

{scoring}
Accuracy (TP+TN)/n'dir; balanced accuracy, recall ile özgüllüğün ortalamasıdır; F1,
precision ve recall'un harmonik ortalamasıdır; TSS recall eksi FPR'dir. Sürekli olay yok
diyen modelin accuracy değeri, yüksek accuracy'nin tek başına nadir olay başarısı olmadığını
gösterir. AP farklı çalışma noktaları boyunca sıralamayı ölçer; belirli alarm eşiğine
bağlı değildir. Brier ortalama karesel olasılık hatasıdır; log loss emin yanlış tahminleri
cezalandırır. İkisi de doğru olasılıklara yönelten skorlardır; kalibrasyonu tek başına
ayırmak yerine kalibrasyon ve ayırt etmeyi birlikte içerir.

Dahil edilen {n} yılda kronolojik AP, AP tanımlı {ap_n} yılın {ap_worse} tanesinde referanstan
düşüktür; Brier {brier_worse} yılda, log loss {log_worse} yılda daha yüksektir. Kronolojik AP,
karıştırılmış AP'den karşılaştırılabilir {order_ap_n} AP yılının {order_ap_wins} tanesinde yüksektir. Bu, zaman sırasının kararlı faydasını göstermez;
kontrol eksiklik maskelerinin sırasını da değiştirdiği için fiziksel manyetik gelişimi
erişilebilirlik örüntülerinden ayırmaz. Ortak ortalamayla zayıf yıllar gizlenmez.
Tüm ölçülen alanlar ve tekil tohum satırları metrics.csv içinde korunur.

## Açık kabul koşulları ve eksik kapsam

{gates}
Ortak birincil kontrol, daha yüksek precision, recall >=0.95 ve daha az FP'yi birlikte
ister. Tam kontrol ayrıca belirtilen kontrole göre düşmeyen AP ve artmayan Brier/log loss
ister. Nokta kazançları ve aynı anda geçilen koşullar ayrı sayılır. Tüm-yıllar başarısı,
eksik aday olmadan tüm gerekli pozitif yılları ve özgün uygun dönemleri de gerektirir.
Bunlar sabit tasarımın uygulama karşılaştırma kurallarıdır; evrensel kabul edilebilir metrik
aralıkları veya istatistiksel anlamlılık kanıtı değildir. Gelecekte eksiksiz karşılaştırma
geçse bile otomatik model değişikliği yapılmaz.

## Koşullu eşleştirilmiş belirsizlik

Kronolojik eksi referans aralıkları:

{uncertainty}
Kronolojik eksi karıştırılmış sıra aralıkları:

{ordering}
Aralıklar 24 tohumuyla 1000 eşleştirilmiş tam-HARP bootstrap çekilişinin yüzde 95 yüzdelik
aralıklarıdır. Aynı örneklenen bölgeler ve tüm pencereleri iki kola da katkı verir.
Mevcut precision/recall/FP aralıkları korunur; eşleştirilmiş Brier/log-loss fark aralıkları
sabit olasılıklardan yeni hesaplanır. Pozitif precision/recall farkı aday lehinedir;
negatif FP/Brier/log-loss farkı aday lehinedir. Sıfırı kesen veya sıfıra değen aralık,
o aralık düzeyinde yönlü fark göstermez. `valid_draws` ve `undefined_draws`, precision/recall
hesaplanamayan örneklemeleri görünür tutar. AP nokta tahmini olarak verilir; burada
bootstrap AP aralığı yoktur.

Modeller, kalibratörler, eşikler ve özgün HARP kimlikleri sabittir. Aralıklar yeniden
eğitim, kalibrasyon öğrenimi ve tarihsel seçim belirsizliğini içermez. Komşu yıllar eğitim
geçmişini paylaşır; çoklu karşılaştırma düzeltmesi yapılmaz. HARP örneklemesi bölge içi
pencere bağımlılığını ele alır; katalog bölgelerinin birbirinden bağımsızlığını kanıtlamaz.
{gain_tr} Yıl ve alt grup sonuçları evrensel nedensel iddia gibi okunmamalıdır.

## Olasılık güvenilirliği

Aşağıda her referans/kronolojik çifti için örnek ve bölge desteğini göstermek üzere en
çok pencere içeren grup verilir. Bu seçim yalnızca gösterim içindir, model kuralı değildir.
Tüm gruplar ve dört kol reliability.csv içinde korunur.

{calibration}
Grup sınırları config/temporal-evaluation-report-v1.json içinde 0–1 arasında sabittir;
düşük olasılıklarda daha ince ayrım vardır. Aralıklar sağdan kapalıdır, sıfır ilk gruptadır.
Dolu gruplarda mean_probability ile observed_rate karşılaştırılır. Gözlenen eksi tahmin
farkı CSV'ye kaydedilir. Gözlenen oran sınırları, olasılık ve üyeliği sabit tutarak tam
HARP'ları yeniden örnekler. Boş gruplar tanımsız kalır; seyrek gruplarda az geçerli çekiliş
veya az pozitif bölge olabilir. Hiç olay gözlenmeyen gruptaki 0–0 oran aralığı, gelecekteki
patlama olasılığının sıfır olacağını garanti etmez.

Yerel bağımsız `reliability.png` görseli referans ve kronolojik kolların tüm dolu gruplarını
tam 0–1 aralığında gösterir. Desteği düşük grupları gizlemez ve belirsizlik çubuklarını
çizmez; sayısal destek ve koşullu sınırlar CSV ve tablodadır. Güvenilirlik grafikleri
olasılık uyumunu inceler, tahminleri değiştirmez.

## Tohum değişkenliği

{spread}
Tanısal sonuç için her tohumun yalnızca kalibrasyonda seçilmiş kendi eşiği vardır. Min/max
aralıkları üç eğitim arasındaki betimsel değişkenliktir; güven aralığı veya tohum ortalaması
modelinin aralığı değildir. En iyi tohum veya avantajlı yıl seçilmez. Tam Brier/log-loss
tohum aralıkları seed_spread.csv içindedir.

## Karar ve tamamlanma yolu

Mevcut kayıt, kullanılan modeli değiştirmeyi desteklemiyor. Sabit yıllık deney, zayıf yıllar
ve eksik dönemler açıkça korunarak tamamlanmalıdır. Önceki hata analizi sorunları yerelleştirir;
devam eden eğitim düzenini değiştirmeyi gerekçelendirmez. Gelecekteki hibrit/statik-özet
kontrolü, bu karşılaştırmadan sonra yeni sabit protokol gerektiren hipotez olarak kalır.
Raporlama aracı bu kaydın üzerine yazmadan son değerlendirme modunu destekler.

{commands}
Tekrarlarda yeni çıktı/rapor adı kullanın. Son karşılaştırma için açık --years listesini
--require-complete ile değiştirip yeni çıktı dizini seçin; deney eksikken komut çalışmayı
reddeder. Yeni çift dilli belge sürümü yayımlayın; iki incelenmiş sürümü/kaynak hash değerini
docs/reports.json ile docs/reports.md içine kaydedin. Önceki kayıt sürümleri korunur. Yerel
CSV, PNG, tahmin ve model dosyaları Git dışında kalır. Mevcut kayıt raporunda her kaynak
bölümün ve kodun hash değerleri bulunur; ayrılmış test açılmaz ve yerel app.py marka
düzenlemeleri commit edilmez.

{evidence}
'''
    paths[0].write_text(en);paths[1].write_text(tr)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--name',required=True)
    a=p.parse_args();run(a.source.resolve(),a.name)
