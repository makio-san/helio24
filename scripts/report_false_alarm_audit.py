"""Render paired error-audit findings and the selected, unexecuted model design."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from scripts.report_precision_followup import table


def run(source, name):
    report=json.loads((source/'report.json').read_text())
    for relative,digest in report['artifact_hashes'].items():
        if sha256(source/relative)!=digest:raise ValueError('Audit changed')
    protocol_path=ROOT/'config/hard-negative-v1.json'
    protocol=json.loads(protocol_path.read_text())
    if protocol['evidence_sha256']!=sha256(source/'report.json'):raise ValueError('Design evidence changed')
    paths=[ROOT/'docs'/f'{name}{suffix}.md' for suffix in ['', '.tr']]
    if any(p.exists() for p in paths):raise ValueError('Preserve existing editions')
    s=pd.read_csv(source/'summary.csv');r=pd.read_csv(source/'regions.csv')
    concentration=table(s[['year','negatives','fp','fpr','top10_fp','top10_fp_share','top10_negative_share']])
    structure=table(s[['year','zero_positive_region_fp','complete_measurement_fp',
                       'both_models_alarm_fp','fp_windows_in_runs_ge6','max_fp_run_windows']])
    tops=table(r.groupby('year',sort=True).head(3)[['year','harp','rows','positives','negatives','fp','fpr','mean_missing']])
    missing=table(pd.read_csv(source/'missing_bins.csv'))
    files=[source/'report.json',protocol_path]
    evidence=table(pd.DataFrame([{'source':str(p.relative_to(ROOT)),'SHA-256':sha256(p)} for p in files]))
    command=f'''```sh
.venv/bin/python scripts/audit_false_alarms.py --output {source.relative_to(ROOT)}
.venv/bin/python scripts/report_false_alarm_audit.py --source {source.relative_to(ROOT)} --report-name {name}
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en=f'''# False-alarm localization and next model selection

This audit compares frozen annual development predictions and selects a controlled
hard-negative-weighted XGBoost experiment. **The new model has not been trained and no
precision improvement is claimed.** Labels, forecasts, dashboard model and the reserved
2024–2025 test remain unchanged. The design is `config/hard-negative-v1.json`, explicitly
marked `design_frozen_not_executed`.

## Evidence and scope

Inputs are the completed 2014–2018, 2022 and 2023 folds of
`artifacts/walk_forward_20261028_r1`. Every registered artifact hash is checked, alarms
are reconstructed from each frozen calibration threshold, and ensemble FP totals must
match the original metrics. Years 2019–2021 have no completed fold because their preceding
calibration populations lack positive examples. In the retained 2018 evaluation population
there are no positives; false alarms remain measurable, but recall is undefined.

These are adaptive, retrospective development diagnostics, not independent validation of
a new model. Counts describe overlapping forecast windows, not independent solar flares,
notifications or spacecraft impacts. All proportions below use a 0–1 scale.

## Regional concentration, adjusted for exposure

{concentration}
`fpr` is FP divided by negative windows. The top ten HARPs are selected post hoc by FP
count within each year. Their FP share must be compared with their negative-window share,
not with a uniform-region assumption. In 2023 these regions account for 0.306409 of FP
but only 0.039238 of negative windows. In 2017 the corresponding shares are 0.930847 and
0.123055. Concentration is therefore not explained solely by those regions having more
observed negative windows. This does not identify a physical cause.

The three largest contributors per year are:

{tops}
These are post-hoc diagnostic priorities, never a region exclusion list. Different HARP
identifiers across years are different catalogued regions; the recurring finding is
concentration, not proof that one physical region repeats across years.

## Missing measurements

{missing}
Missingness bins were fixed before this comparison: exactly zero, (0,0.01], (0.01,0.05]
and (0.05,1]. `missing_fraction` measures missing entries in the original observation
window; it is not a complete instrument-quality flag. Compare each bin's FP with its
negative denominator. In every completed year the (0,0.01] bin has the highest observed
FPR, but the pattern is not a monotonic increase with missingness. In 2023 it is 0.370599
versus 0.083642 for zero missingness. Region composition, measurement timing and label
selection may confound this association; this audit does not establish causation.

Moreover, most FP windows in every year have zero missingness. In 2023, 3708 of 5992 FP
windows have no missing entries. Improving imputation alone is therefore not established
as the main solution. Do not drop the small-missingness bin to manufacture better scores.

## Persistence and model agreement

{structure}
`zero_positive_region_fp` counts errors in regions with no retained positive evaluation
window; it does not prove those regions never flared. `both_models_alarm_fp` requires
both component models to alarm at their own frozen calibration thresholds, as well as
the ensemble being wrong. In 2023 this occurs in 5600 of 5992 FP windows: simply relying
on agreement between the two models would not remove most observed errors.

A run requires consecutive FP windows from the same HARP at exactly one-hour spacing.
A missing/excluded timestamp, non-FP window or region change breaks it. The at-least-six
criterion counts six forecast windows, not six independent events or a physical duration
of six hours. In 2023, 5474 of 5992 FP windows belong to such runs; the longest has 145
windows. In 2018 the longest has 129 windows. This is a descriptive persistence measure,
not a retrospectively applied alarm-suppression rule. Fewer repeated notifications would
be a separate operational metric and would not itself improve window-level precision.

## Selected model experiment and controls

The working hypothesis is that some persistently flare-like negative examples are not
adequately separated by the current decision boundary. This is an inference from the
error structure, not a proven cause. Choose **training-only out-of-time hard-negative
mining**, followed by a weighted XGBoost student, keeping the same 96 input features and
existing hyperparameters. This tests a different learning emphasis rather than another
large parameter search.

For each evaluation year Y, outer training still ends before Y-1. Fit a teacher XGBoost
before January 1 of Y-3; mine only the final two outer-training years. Purge overlapping
observation/prediction intervals and remove mining HARPs seen in teacher training.
Rank eligible known-negative training windows by teacher raw score and select exactly
ceil(0.10 * eligible_count), with forecast time and HARP as deterministic tie-breakers.
No evaluation-year scores, labels or error lists enter this selection. Those outer-training
labels are available when the final student is fitted; they are not forecast inputs.

Compare three fixed arms on the same annual splits:

1. Existing unweighted baseline ensemble.
2. Hard-negative student: selected negatives have training weight 3; every other training
   window has weight 1. All original outer-training rows remain.
3. Matched uniform-negative control: all outer-training negatives have weight
   `1 + 2 * hard_negative_count / outer_training_negative_count`, positives have weight 1.
   Its total negative weight equals arm 2, separating targeted mining from simply putting
   more weight on the negative class.

Keep the logistic component unchanged and replace only XGBoost in the fixed 0.45/0.55
blend. Refit each student's sigmoid calibration on the unchanged outer calibration year;
choose its ensemble threshold there at recall >=0.95 and transfer it unchanged. Keeping
the calibration scheme fixed isolates weighting; separating probability fitting and
threshold fitting remains a different, unexecuted experiment. If a teacher lacks both
classes or eligible negatives are absent, mark the candidate arms unavailable rather
than silently substituting baseline. Preserve the original outer-fold skip rules.

There is no automatic promotion. The frozen design requires higher precision and
recall >=0.95 in every comparable positive evaluation year, no lower AP and no higher
Brier/log loss per year versus baseline. Report all arms and failed years, including
FP/FPR in zero-positive years. Use 1000 paired whole-HARP bootstrap draws with seed 24;
intervals are conditional on trained models and frozen thresholds. Improvement over the
matched uniform control is needed to attribute benefit to targeted mining. This demanding
gate may reject the candidate. Weighting can worsen recall or calibration; success is
not guaranteed. All evaluation remains adaptive development, and the reserved test stays
closed until the complete policy is frozen.

## Reproduction and limitations

{command}
Use fresh output directories and report names for reruns, preserving frozen evidence.
If the audit report hash changes, create a new design revision and update the reporting
script's design path; never overwrite the frozen protocol. Review both editions, register
the source hash and links in `docs/reports.json` and `docs/reports.md`, then publish to a
new HTML directory. Data and generated artifacts remain outside Git. There is no training
command for the selected design yet: implementation and execution are the next task.

The audit is descriptive, with correlated windows, changing yearly prevalence and
pre-existing label/quality exclusions. It reports observed counts and rates, not confidence
intervals or causal effects for the missingness association. It does not verify physical
region identities across rotations, resolve event associations or prove any label is wrong.

{evidence}
'''
    tr=f'''# Yanlış alarmların yoğunlaşması ve sonraki model seçimi

Bu denetim, dondurulmuş yıllık geliştirme tahminlerini karşılaştırır ve kontrollü bir
zor negatif ağırlıklı XGBoost deneyi seçer. **Yeni model henüz eğitilmedi; precision
iyileşmesi iddia edilmez.** Etiketler, tahminler, dashboard modeli ve ayrılmış 2024–2025
testi değişmedi. Tasarım `config/hard-negative-v1.json` dosyasındadır; açıkça
`design_frozen_not_executed` olarak işaretlenmiştir.

## Kanıt ve kapsam

Girdiler, `artifacts/walk_forward_20261028_r1` dizininin tamamlanmış 2014–2018, 2022 ve
2023 turlarıdır. Kaydedilmiş her artifact özeti kontrol edilir; alarmlar her dondurulmuş
kalibrasyon eşiğinden yeniden hesaplanır ve birleşik modelin FP toplamları özgün metriklerle
eşleşmek zorundadır. 2019–2021 yıllarında, önceki kalibrasyon topluluklarında pozitif örnek
olmadığından tamamlanmış tur yoktur. Korunan 2018 değerlendirme verisinde pozitif yoktur;
yanlış alarmlar ölçülebilir, recall tanımsızdır.

Bunlar uyarlamalı, geçmişe dönük geliştirme incelemeleridir; yeni modelin bağımsız
doğrulaması değildir. Sayılar bağımsız Güneş patlamalarını, bildirimleri veya uydu
etkilerini değil, örtüşen tahmin pencerelerini anlatır. Tüm oranlar 0–1 ölçeğindedir.

## Gözlem sayısıyla karşılaştırılan bölgesel yoğunlaşma

{concentration}
`fpr`, FP sayısının negatif pencere sayısına bölümüdür. En yüksek katkılı on HARP, her
yılda FP sayısıyla sonradan seçilir. FP payları, bölgelerin eşit büyüklükte olduğu
varsayımıyla değil, negatif pencere paylarıyla karşılaştırılmalıdır. 2023'te bu bölgeler
FP'nin 0.306409'unu, negatif pencerelerin yalnızca 0.039238'ini oluşturur. 2017'de karşılıkları
0.930847 ve 0.123055'tir. Dolayısıyla yoğunlaşma yalnızca bu bölgelerde daha fazla negatif
pencere gözlenmesiyle açıklanmaz. Bu, fiziksel nedeni belirlemez.

Yıl başına en fazla katkı yapan üç bölge:

{tops}
Bunlar sonradan belirlenen inceleme öncelikleridir; bölge dışlama listesi değildir.
Yıllar arasındaki farklı HARP kimlikleri farklı katalog bölgeleridir; tekrarlanan bulgu
yoğunlaşmadır, aynı fiziksel bölgenin yıllar boyunca tekrarlandığının kanıtı değildir.

## Eksik ölçümler

{missing}
Eksiklik aralıkları karşılaştırmadan önce sabitlendi: tam sıfır, (0,0.01], (0.01,0.05]
ve (0.05,1]. `missing_fraction`, özgün gözlem penceresindeki eksik girdileri ölçer; tam
bir cihaz kalitesi bayrağı değildir. Her aralığın FP sayısı negatif paydasıyla karşılaştırılmalıdır.
Tamamlanan her yılda en yüksek gözlenen FPR, (0,0.01] aralığındadır; fakat örüntü eksiklik
arttıkça düzenli bir yükseliş değildir. 2023'te bu oran 0.370599, sıfır eksiklikte 0.083642'dir.
Bölge bileşimi, ölçüm zamanlaması ve etiket seçimi ilişkiyi etkileyebilir; denetim nedensellik
kurmaz.

Ayrıca her yılda FP pencerelerinin çoğunda eksiklik sıfırdır. 2023'te 5992 FP penceresinin
3708'inde eksik girdi yoktur. Bu nedenle yalnızca eksik değer doldurmayı iyileştirmenin
temel çözüm olduğu gösterilmemiştir. Daha iyi skor üretmek için az eksiklikli aralık çıkarılmamalıdır.

## Süreklilik ve modellerin ortak hataları

{structure}
`zero_positive_region_fp`, korunan değerlendirme pencerelerinde pozitif olmayan bölgelerdeki
hataları sayar; o bölgelerin hiç patlamadığını kanıtlamaz. `both_models_alarm_fp`, birleşik
modelin yanlış olduğu pencerede iki bileşenin de kendi sabit kalibrasyon eşiğinde alarm
vermesini gerektirir. 2023'te bu, 5992 FP penceresinin 5600'ünde gerçekleşir: yalnızca iki
modelin anlaşmasına güvenmek gözlenen hataların çoğunu ortadan kaldırmaz.

Bir dizi, aynı HARP'ın tam bir saat aralıklı ardışık FP pencerelerini gerektirir. Eksik
veya dışlanmış zaman damgası, FP olmayan pencere veya bölge değişimi diziyi keser. En az
altı koşulu, altı tahmin penceresini sayar; altı bağımsız olay veya altı saatlik fiziksel
süre değildir. 2023'te 5992 FP penceresinin 5474'ü böyle dizilerdedir; en uzunu 145 pencere
içerir. 2018'de en uzun dizi 129 penceredir. Bu, betimsel süreklilik ölçüsüdür; sonradan
uygulanan alarm bastırma kuralı değildir. Tekrarlı bildirimleri azaltmak ayrı bir uygulama
metriğidir ve tek başına pencere düzeyindeki precision'ı iyileştirmez.

## Seçilen model deneyi ve kontroller

Çalışma hipotezi, sürekli patlama benzeri görünen bazı negatif örneklerin mevcut karar
sınırıyla yeterince ayrılamadığıdır. Bu, hata yapısından çıkarımdır; kanıtlanmış neden
değildir. Aynı 96 girdi özelliği ve mevcut hiperparametreler korunarak **yalnızca eğitim
içinde, zaman sıralı zor negatif seçimi**, ardından ağırlıklı XGBoost öğrenci modeli
seçilmiştir. Böylece geniş bir parametre araması yerine farklı öğrenme ağırlığı sınanır.

Her Y değerlendirme yılında dış eğitim yine Y-1 öncesinde biter. Öğretmen XGBoost, Y-3
yılının 1 Ocak tarihinden önce eğitilir; seçim yalnızca dış eğitimin son iki yılında yapılır.
Örtüşen gözlem/tahmin aralıkları temizlenir; öğretmen eğitiminde görülen HARP'lar seçim
bölümünden çıkarılır. Uygun, negatif olduğu bilinen eğitim pencereleri öğretmenin ham
skoruyla sıralanır; tam olarak ceil(0.10 * eligible_count) örnek seçilir. Eşitlikler tahmin
zamanı ve HARP ile belirlenimci çözülür. Değerlendirme yılı skorları, etiketleri veya hata
listeleri seçime girmez. Bu dış eğitim etiketleri son öğrenci eğitilirken erişilebilirdir;
tahmin girdisi değildir.

Aynı yıllık ayrımlarda üç sabit deney kolu karşılaştırılacaktır:

1. Mevcut, ağırlıksız referans model birleşimi.
2. Zor negatif öğrenci: seçilen negatiflerin eğitim ağırlığı 3, diğer tüm eğitim
   pencerelerinin ağırlığı 1 olur. Özgün dış eğitim satırlarının tamamı korunur.
3. Eşleştirilmiş tekdüze negatif kontrol: dış eğitimdeki tüm negatiflerin ağırlığı
   `1 + 2 * hard_negative_count / outer_training_negative_count`, pozitiflerin ağırlığı 1 olur.
   Toplam negatif ağırlığı ikinci kolla aynıdır; hedefli seçimin etkisini yalnızca negatif
   sınıfa daha fazla ağırlık vermekten ayırır.

Lojistik bileşen korunur; sabit 0.45/0.55 birleşiminde yalnızca XGBoost değiştirilir.
Her öğrencinin sigmoid kalibrasyonu aynı dış kalibrasyon yılında yeniden öğrenilir;
birleşim eşiği orada recall >=0.95 koşuluyla seçilip değiştirilmeden aktarılır. Kalibrasyon
düzenini sabit tutmak ağırlıklandırmayı ayrı sınar; olasılık öğrenimiyle eşik öğrenimini
ayırmak farklı ve henüz çalıştırılmamış deney olarak kalır. Öğretmende iki sınıf yoksa
veya uygun negatif yoksa sessizce referansa dönülmez; aday kollar kullanılamıyor olarak
işaretlenir. Özgün dış tur atlama kuralları korunur.

Otomatik model değiştirme yoktur. Sabit tasarım, karşılaştırılabilir her pozitif değerlendirme
yılında daha yüksek precision ve recall >=0.95; referansa göre yıl başına düşmeyen AP ve
artmayan Brier/log loss gerektirir. Pozitif olmayan yılların FP/FPR değerleri dahil tüm
kollar ve başarısız yıllar raporlanır. 24 tohumla eşleştirilmiş bütün HARP'ları örnekleyen
1000 bootstrap tekrarı kullanılır; aralıklar eğitilmiş model ve sabit eşik koşulludur.
Kazancı hedefli seçime bağlamak için eşleştirilmiş tekdüze kontrolden de iyi sonuç gerekir.
Bu sıkı ölçüt adayı reddedebilir. Ağırlıklandırma recall veya kalibrasyonu bozabilir;
başarı garanti değildir. Değerlendirme uyarlamalı geliştirme olarak kalır; tüm kural
dondurulana kadar ayrılmış test kapalı tutulur.

## Yeniden üretim ve sınırlamalar

{command}
Tekrarda dondurulmuş kanıtı koruyarak yeni çıktı dizinleri ve rapor adları kullanın.
Denetim raporu özeti değişirse yeni tasarım sürümü oluşturup rapor betiğindeki tasarım
yolunu güncelleyin; sabit protokolün üzerine yazmayın. İki sürümü gözden geçirip kaynak
özetini ve bağlantıları `docs/reports.json` ile `docs/reports.md` dosyalarına kaydedin,
ardından yeni HTML dizinine yayımlayın. Veri ve üretilen çıktılar Git dışında kalır.
Seçilen tasarım için henüz eğitim komutu yoktur: uygulama ve çalıştırma sonraki görevdir.

Denetim betimseldir; pencereler bağımlıdır, yıllık olay sıklığı değişir ve önceki etiket/kalite
dışlamaları geçerlidir. Eksiklik ilişkisi için güven aralığı veya nedensel etki değil,
gözlenen sayı ve oranları raporlar. Güneş dönüşleri arasında fiziksel bölge kimliğini
doğrulamaz, olay ilişkilerini çözmez ve herhangi bir etiketin yanlış olduğunu kanıtlamaz.

{evidence}
'''
    for p,content in zip(paths,[en,tr]):p.write_text(content)
    print('\n'.join(map(str,paths)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--report-name',required=True);a=p.parse_args();run(a.source.resolve(),a.report_name)
