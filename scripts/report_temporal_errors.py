"""Render complete bilingual editions of the fixed partial temporal error audit."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sequence_training import verify_files


def table(frame):
    def cell(v):
        if pd.isna(v):return 'undefined'
        if isinstance(v,(np.integer,int)):return str(int(v))
        if isinstance(v,(np.floating,float)):return f'{v:.6f}'
        return str(v)
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+''.join('| '+' | '.join(cell(v) for v in row)+' |\n' for row in frame.itertuples(index=False,name=None))+'\n'


def run(source,name):
    r=json.loads((source/'report.json').read_text());verify_files(source,r['artifact_hashes']);verify_files(ROOT,r['code_hashes'])
    plan=ROOT/'config/temporal-error-audit-v1.json'
    if sha256(plan)!=r['plan_sha256']:raise ValueError('Plan changed')
    paths=[ROOT/'docs'/f'{name}{suffix}.md' for suffix in ['', '.tr']]
    if any(p.exists() for p in paths):raise ValueError('Preserve reports')
    s=pd.read_csv(source/'summary.csv');main=s[(s.candidate=='chronological')&(s.control=='baseline')]
    performance=table(s[s.control.eq('baseline')][['year','candidate','candidate_precision','control_precision','candidate_recall','control_recall','candidate_fp','control_fp']])
    decomposition=table(s[['year','candidate','control','extra_fp','removed_fp','shared_fp','net_fp','extra_tp','removed_tp']])
    concentration=table(main[['year','top10_extra_fp','top10_extra_fp_share','top10_negative_share','complete_measurement_extra_fp','zero_positive_region_extra_fp','extra_fp_in_runs_ge6','max_extra_run']])
    regions=pd.read_csv(source/'regions.csv');regions=regions[(regions.candidate=='chronological')&(regions.control=='baseline')].sort_values(['year','extra_fp','harp'],ascending=[True,False,True])
    tops=table(regions.groupby('year',sort=True).head(3)[['year','harp','positives','negatives','extra_fp','removed_fp','net_fp']])
    b=pd.read_csv(source/'missing_bins.csv');b=b[(b.candidate=='chronological')&(b.control=='baseline')&b.rows.gt(0)]
    missing=table(b[['year','missing_bin','negatives','extra_fp','removed_fp','net_fp','candidate_fpr','control_fpr']])
    f=pd.read_csv(source/'measurement_bins.csv');f=f[(f.candidate=='chronological')&(f.control=='baseline')]
    high=table(f[f.field.str.endswith('__last')&f.measurement_bin.eq('bin4')][['year','field','negatives','extra_fp','removed_fp','net_fp','candidate_fpr','control_fpr']])
    worst=f[f.year.eq(2016)&f.measurement_bin.ne('unavailable')].sort_values(['field','net_fp','measurement_bin'],ascending=[True,False,True]).groupby('field',sort=True).head(1)
    worst=table(worst[['field','measurement_bin','negatives','extra_fp','removed_fp','net_fp','candidate_fpr','control_fpr']])
    scoring=table(main[['year','candidate_average_precision','control_average_precision','candidate_brier','control_brier','candidate_log_loss','control_log_loss']])
    intervals=[]
    for record in r['source_folds']:
        path=ROOT/r['source']/str(record['year'])/'finished.json'
        if sha256(path)!=record['finished_sha256']:raise ValueError('Fold changed')
        result=json.loads(path.read_text())
        item=next(i for i in result['paired_intervals'] if i['arm']=='chronological' and i['control']=='baseline')
        for metric,values in item['differences'].items():intervals.append({'year':record['year'],'metric':metric,**values})
    uncertainty=table(pd.DataFrame(intervals))
    evidence=table(pd.DataFrame([{'source':str(p.relative_to(ROOT)),'sha256':sha256(p)} for p in [source/'report.json',plan]]))
    commands=f'''```sh
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/audit_temporal_errors.py --plan config/temporal-error-audit-v1.json --output {source.relative_to(ROOT)}
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/report_temporal_errors.py --source {source.relative_to(ROOT)} --name {name}
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" -m pytest tests/test_temporal_errors.py tests/test_false_alarm_audit.py tests/test_bilingual_reports.py -q
"/Users/esma/Library/Application Support/Helio24/runtime-py314-20261101/bin/python" scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en=f'''# Temporal-model false alarms: completed-year localization

**Finding:** the 2016 TCN deterioration is concentrated in persistent regional alarm
sequences and high measurement-level cohorts. Missing values alone do not explain the
extra alarms. The pattern varies by year, and chronological order has not shown a
consistent advantage over its shuffled control. Continue the frozen experiment; this
audit does not justify promotion, threshold tuning or changing the ongoing recipe.

## Scope and operating points

This is a fixed snapshot of completed 2014–2016 development folds. Later folds are still
being trained and are excluded even if they finish during reporting. Frozen fold/output
hashes, original feature-shard hashes, forecast keys, labels and annual split audits are
verified. Alarm counts and precision/recall must reproduce the frozen metrics. Neither
the 2024–2025 test nor raw outcome metadata is accessed. No new training is performed.

The plan was written after inspecting global results but before the granular audit.
This is adaptive descriptive analysis, not an independent prospective evaluation.
Candidate and control keep their own prior-year calibration thresholds: recall differs,
so these comparisons are not at matched recall. Fractional scores use a 0–1 scale.
Counts refer to overlapping forecast windows, not independent flares or notifications.

{performance}
2015's small precision increase accompanies lower recall. In 2016 the chronological TCN
has recall 0.955801, versus 0.972376 for the baseline, yet produces 4096 more FP windows.
2014 has identical aggregate recall but more FP. Net FP alone is not a complete success
criterion; identify gained and lost positive windows as well.

## Paired additions and removals

{decomposition}
`extra_fp` means the candidate alarms on a negative window where the named control does
not; `removed_fp` is the reverse. `shared_fp` is alarmed by both. Net change equals
extra minus removed, with the equality checked for every group. `extra_tp` and
`removed_tp` describe the same switches on positive windows. These are window counts,
not counts of distinct flare events. In 2016, 4446 extra minus 350 removed FP gives
4096 net additional FP. One new TP is offset by four removed TP. In 2015, 2541 extra
minus 2857 removed FP gives a net reduction of 316, with one gained and 31 lost TP.

## Regional concentration and persistence

{concentration}
The ten HARPs with most extra FP are selected post hoc separately in each comparison.
Their extra-FP share must be assessed against their share of negative-window exposure.
For 2016 those shares are 0.350202 and 0.064080. They identify diagnostic priorities,
not an exclusion list. Region ranks and zero-positive status use future evaluation
outcomes and cannot be treated as predictors available at forecast time.

The three largest extra-FP contributors per year are:

{tops}
In 2016 HARP 6789 has 229 extra FP and no removed FP among 272 negative windows.
Of all 4446 extra FP that year, 3946 belong to runs of at least six hourly windows;
the longest run has 107 windows. Runs require exactly one-hour adjacency within a HARP;
any missing/excluded timestamp or nonmatching window breaks a run. Hourly forecasts
have overlapping 12-hour observations and 24-hour targets; these are not independent
repeated failures. Notification deduplication addresses presentation, not window precision.

## Missing measurements

{missing}
The five fixed missingness categories include an unavailable category, retained in CSV
but omitted above when empty. FPR is FP divided by negative windows in the same bin.
In 2016 the small-missingness bin (0,0.01] has FPR 0.388385 versus baseline 0.154870.
Its relative risk is high, but zero-missingness windows contribute 3072 of 4446 extra FP
and 2801 of 4096 net extra FP. Fully measured windows also supply most extra FP in 2014
and 2015. Improving imputation alone is therefore not established as the main remedy.
Missingness associations can be confounded by region composition and measurement level;
no missingness bin or region is removed or relabeled.

## Measurement conditions using training-only cutpoints

Eight fields were fixed: last and delta of USFLUX, TOTUSJH, R_VALUE and MEANSHR.
Each year's original training data supplies finite-value 25/50/75 percentile cuts,
with duplicate cuts removed. Evaluation labels and scores do not choose cuts. Bins use
right-closed intervals; unavailable values are preserved. Evaluation exposure need not
be balanced between bins. Exact cutpoints are in measurement_cutpoints.csv. The highest
last-value bin in these data is bin4:

{high}
In 2016 the upper USFLUX__last bin adds 2235 net FP among 6397 negative windows;
FPR is 0.645928 versus 0.296545. The upper TOTUSJH__last and R_VALUE__last bins add
2150 and 2177 net FP. Upper last-value bins also deteriorate in 2014; in 2015 the
USFLUX/TOTUSJH/R_VALUE upper bins improve, while upper MEANSHR still worsens.
This is not a stable universal high-value rejection rule.

For compact inspection, the following table selects the finite bin with largest net FP
for each field in 2016. This selection is post hoc; all bins remain in measurement_bins.csv:

{worst}
The field views overlap: the same window can appear in several fields. Never sum their
counts as independent contributions. Delta is last minus first, not a slope or a complete
sequence pattern. High-value and changing-field associations do not establish a physical
cause, a label error or one unique model mechanism. A possible coarse activity shortcut
is a hypothesis for later ablation, not a demonstrated causal explanation.

## Ranking, probability scores and uncertainty

{scoring}
Chronological TCN AP is lower and Brier/log loss higher than the baseline in all three
years. AP does not depend on the alarm threshold; this makes a purely threshold-only
explanation insufficient for the observed ranking deficit. It does not isolate the
cause between representation, optimization, class weighting and distribution shift.
Chronological ordering outperforms shuffled AP in 2014 and 2015 but underperforms it in
2016 (0.146877 versus 0.187088). The ordering hypothesis is not consistently supported.

Existing paired HARP-bootstrap intervals for chronological minus baseline are reproduced
below. These use fixed models/thresholds, 1000 draws and seed 24; they exclude retraining
uncertainty and do not adjust for this audit's multiple views:

{uncertainty}
The 2015 precision interval crosses zero; its small point gain is not established as a
reliable improvement. In 2016 some resamples have no positives, leaving 973 valid recall
draws, and the precision interval reaches zero. Do not infer a universal causal effect
or independent statistical confirmation from region ranks or selected measurement bins.

## Research consequence and reproduction

Keep the incumbent and the ongoing sequence recipe fixed. Complete the annual experiment
before changing direction. If the pattern persists, prioritize an ablation of discrimination
within high-measurement, mostly negative cohorts while preserving the strong summary-feature
reference; a hybrid/static-summary control is a candidate for a future frozen protocol.
This audit does not select or start that experiment. Further missing-value tweaks alone
and evaluation-based threshold retuning are not supported as sufficient remedies.

{commands}
Use new output/report names for reruns; retain frozen outputs. The first audit revision
was preserved; r2 adds frozen ranking/probability context and explicit bin coverage checks.
Review both full editions, register the source hash and language links in docs/reports.json
and docs/reports.md, then publish paired HTML to a fresh directory. Full regional,
missingness, run and measurement tables remain in local ignored CSV artifacts. Only
analysis code, plan and documents enter Git; local app.py branding edits remain uncommitted.

{evidence}
'''
    tr=f'''# Zamansal modelin yanlış alarmları: tamamlanan yılların incelenmesi

**Bulgu:** 2016 TCN gerilemesi, kalıcı bölgesel alarm dizilerinde ve yüksek ölçüm düzeyi
gruplarında yoğunlaşıyor. Ek alarmları yalnızca eksik değerler açıklamıyor. Örüntü yıla
göre değişiyor; kronolojik sıra, karıştırılmış kontrolüne karşı tutarlı üstünlük göstermedi.
Sabit deney sürdürülmeli; bu denetim modeli değiştirmeyi, eşiği ayarlamayı veya devam eden
eğitim düzenini değiştirmeyi gerekçelendirmiyor.

## Kapsam ve çalışma noktaları

Bu, tamamlanmış 2014–2016 geliştirme bölümlerinin sabit kaydıdır. Sonraki bölümler hâlâ
eğitiliyor; raporlama sırasında bitseler bile dışarıda kalır. Sabit bölüm/çıktı hash
ve özgün özellik parçası hash değerleri, tahmin anahtarları, etiketler ve yıllık bölüm
denetimleri doğrulanır. Alarm sayıları ve precision/recall sabit metrikleri yeniden
üretmelidir. 2024–2025 testine ve ham sonuç meta verisine erişilmez. Yeni eğitim yapılmaz.

Plan, genel sonuçlar görüldükten sonra ama ayrıntılı denetimden önce yazıldı. Bu uyarlamalı,
betimsel incelemedir; bağımsız ileriye dönük değerlendirme değildir. Aday ve kontrol kendi
önceki yıl kalibrasyon eşiklerini korur; recall farklı olduğu için karşılaştırma eşit
recall'da yapılmaz. Oransal skorlar 0–1 ölçeğindedir. Sayılar bağımsız patlamaları veya
bildirimleri değil, örtüşen tahmin pencerelerini ifade eder.

{performance}
2015'in küçük precision artışına daha düşük recall eşlik eder. 2016'da kronolojik TCN
recall 0.955801, referans 0.972376 iken TCN 4096 daha fazla yanlış pozitif (FP) pencere
üretir. 2014'te toplam recall aynıdır, FP daha fazladır. Net FP tek başına tam başarı
koşulu değildir; kazanılan ve kaybedilen pozitif pencereler de belirlenmelidir.

## Eşleştirilmiş eklemeler ve önlenen hatalar

{decomposition}
`extra_fp`, adayın alarm verdiği ama belirtilen kontrolün vermediği negatif pencere;
`removed_fp`, bunun tersidir. `shared_fp`, ikisinin de alarm verdiği penceredir. Net
fark, eklenen eksi önlenendir ve eşitlik her grupta kontrol edilir. `extra_tp` ve
`removed_tp` aynı geçişleri pozitif pencerelerde gösterir. Bunlar pencere sayılarıdır,
benzersiz patlama sayısı değildir. 2016'da 4446 eklenen eksi 350 önlenen FP, net 4096
ek FP verir. Bir yeni TP'ye karşı dört TP kaybedilir. 2015'te 2541 eklenen eksi 2857
önlenen FP, net 316 azalma verir; bir TP kazanılırken 31 TP kaybedilir.

## Bölgesel yoğunlaşma ve kalıcılık

{concentration}
En fazla ek FP üreten on HARP her karşılaştırmada sonradan ayrı seçilir. Ek FP payları,
negatif pencere gözlem paylarıyla birlikte değerlendirilmelidir. 2016'da bu paylar
0.350202 ve 0.064080'dir. Bunlar dışlama listesi değil, inceleme önceliğidir. Bölge
sıralaması ve sıfır-pozitif durumu gelecekteki değerlendirme sonuçlarını kullanır;
tahmin anında erişilebilir girdi gibi ele alınamaz.

Her yılın en fazla ek FP üreten üç bölgesi:

{tops}
2016'da HARP 6789, 272 negatif pencerede 229 ek FP ve sıfır önlenen FP içerir. O yılki
4446 ek FP'nin 3946'sı en az altı saatlik pencere dizilerine aittir; en uzun dizi 107
penceredir. Diziler aynı HARP'ta tam bir saatlik komşuluk gerektirir; eksik/dışlanmış
zaman veya eşleşmeyen pencere diziyi keser. Saatlik tahminler 12 saatlik gözlemi ve
24 saatlik hedefi örtüştürür; bunlar bağımsız tekrarlı hatalar değildir. Bildirimleri
tekilleştirmek sunumu iyileştirir, pencere precision'ını değil.

## Eksik ölçümler

{missing}
Beş sabit eksiklik kategorisi erişilemeyen grubunu da içerir; bu grup CSV'de korunur,
boş olduğunda yukarıda gösterilmez. FPR aynı gruptaki FP'nin negatif pencere sayısına
oranıdır. 2016'da küçük eksiklik grubu (0,0.01] için FPR 0.388385, referansta 0.154870'dir.
Göreli risk yüksektir; ancak eksiksiz pencereler 4446 ek FP'nin 3072'sini ve 4096 net ek
FP'nin 2801'ini üretir. 2014 ve 2015'te de ek FP'nin çoğu eksiksiz pencerelerdedir.
Dolayısıyla yalnızca eksik değer doldurmayı iyileştirmek ana çözüm olarak gösterilemez.
Eksiklik ilişkisi bölge bileşimi ve ölçüm düzeyiyle karışabilir; hiçbir eksiklik grubu
veya bölge dışlanmaz, yeniden etiketlenmez.

## Yalnızca eğitimden seçilen sınırlarla ölçüm koşulları

Sekiz alan sabitlendi: USFLUX, TOTUSJH, R_VALUE ve MEANSHR için last ve delta. Her yılın
özgün eğitim verisinin sonlu değerlerinden yüzde 25/50/75 kesimleri çıkarılır; tekrar eden
kesimler kaldırılır. Değerlendirme etiketi ve skoru kesim seçmez. Gruplar sağdan kapalı
aralık kullanır; erişilemeyen değerler korunur. Değerlendirme gözlem sayısı gruplarda eşit
olmak zorunda değildir. Tam sınırlar measurement_cutpoints.csv içindedir. Bu verilerde
son değer için en yüksek grup bin4'tür:

{high}
2016'da üst USFLUX__last grubu 6397 negatif pencerede 2235 net ek FP üretir;
FPR 0.645928, referansta 0.296545'tir. Üst TOTUSJH__last ve R_VALUE__last grupları
2150 ve 2177 net ek FP üretir. Üst son-değer grupları 2014'te de geriler; 2015'te üst
USFLUX/TOTUSJH/R_VALUE grupları iyileşirken üst MEANSHR yine kötüleşir. Bu, yüksek
değerleri reddeden evrensel ve kararlı bir kural değildir.

Kısa inceleme için aşağıdaki tablo 2016'da her alanın en fazla net FP üreten sonlu
grubunu seçer. Bu seçim sonradandır; tüm gruplar measurement_bins.csv içinde kalır:

{worst}
Alan görünümleri örtüşür: aynı pencere birden fazla alanda yer alabilir. Sayılar bağımsız
katkılar gibi toplanmamalıdır. Delta son eksi ilk değerdir; eğim veya tam zaman serisi
örüntüsü değildir. Yüksek değer ve değişim ilişkileri fiziksel neden, etiket hatası veya
tek bir model mekanizması kanıtlamaz. Kaba etkinlik düzeyine dayalı olası kestirme,
sonraki bileşen deneyleri için hipotezdir; gösterilmiş nedensel açıklama değildir.

## Sıralama, olasılık skorları ve belirsizlik

{scoring}
Üç yılda da kronolojik TCN'nin AP'si daha düşük, Brier/log loss'u referanstan daha yüksektir.
AP alarm eşiğine bağlı değildir; bu nedenle görülen sıralama açığını yalnızca eşik sorunu
ile açıklamak yeterli değildir. Temsil, optimizasyon, sınıf ağırlığı ve dağılım değişimi
arasından nedeni ayırmaz. Kronolojik sıra, 2014 ve 2015'te karıştırılmış AP'den daha iyi;
2016'da daha kötüdür (0.146877 ve 0.187088). Sıra hipotezi tutarlı desteklenmiyor.

Kronolojik eksi referans için mevcut eşleştirilmiş HARP-bootstrap aralıkları aşağıda
yeniden verilir. Sabit model/eşiklerle 1000 çekiliş ve 24 tohumu kullanılır; yeniden
eğitim belirsizliğini içermez, bu denetimin çoklu görünümleri için düzeltme yapılmaz:

{uncertainty}
2015 precision aralığı sıfırı kapsar; küçük nokta kazancı güvenilir iyileşme olarak
kurulmuş değildir. 2016'da bazı yeniden örneklemelerde pozitif bulunmaz, 973 geçerli
recall çekilişi kalır; precision aralığı sıfıra ulaşır. Bölge sırası veya seçilmiş ölçüm
gruplarından evrensel nedensel etki ya da bağımsız istatistiksel doğrulama çıkarılmamalıdır.

## Araştırma sonucu ve yeniden üretim

Mevcut model ve devam eden zaman serisi düzeni sabit tutulmalıdır. Yön değiştirmeden önce
yıllık deney tamamlanmalıdır. Örüntü sürerse güçlü özet-özellik referansını koruyarak yüksek
ölçümlü, çoğunlukla negatif gruplar içindeki ayrımı inceleyen bileşen deneyine öncelik
verilebilir; hibrit/statik-özet kontrolü gelecekte sabitlenecek protokol için adaydır.
Bu denetim o deneyi seçmez veya başlatmaz. Yeni eksik değer ayarları ve değerlendirmeye
göre eşik seçimi tek başına yeterli çözüm olarak desteklenmiyor.

{commands}
Tekrarlarda yeni çıktı/rapor adı kullanın; sabit çıktıları koruyun. İlk denetim sürümü
korundu; r2 sabit sıralama/olasılık bağlamını ve açık grup kapsamı kontrollerini ekler.
İki tam sürümü inceleyip kaynak hash ve dil bağlantılarını docs/reports.json ile
docs/reports.md içine kaydedin; yeni dizine çift dilli HTML yayımlayın. Tam bölge,
eksiklik, dizi ve ölçüm tabloları yerel ve Git dışında CSV çıktılarında kalır. Yalnızca
analiz kodu, plan ve belgeler Git'e girer; yerel app.py marka düzenlemeleri commit edilmez.

{evidence}
'''
    paths[0].write_text(en);paths[1].write_text(tr)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--name',required=True)
    a=p.parse_args();run(a.source.resolve(),a.name)
