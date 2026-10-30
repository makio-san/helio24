"""Publish matching reports for the annual calibration-period experiment."""
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
    if any(p.exists() for p in paths):raise ValueError('Preserve reports')
    m=pd.DataFrame(r['metrics'])
    summary=table(m[['year','arm','n','positives','precision','recall','fp','fn','threshold']].fillna('undefined'))
    full=table(m.fillna('undefined'))
    folds=table(pd.DataFrame([{k:f.get(k) for k in ['year','status','reason','early_rows','early_positives',
        'late_rows','late_positives','boundary_removed','shared_harp_rows_removed','unavailable','passes_gate']} for f in r['folds']]).fillna('undefined'))
    ci=table(pd.DataFrame([{'year':x['year'],'control':x['control'],'metric':metric,**v} for x in r['paired_intervals']
                         for metric,v in x['differences'].items()]).fillna('undefined'))
    p=m[(m.arm=='separated_calibration') & m.positives.gt(0)];hits=int(p.recall.ge(.95).sum());total=len(p)
    passed=r['all_year_gate_passed']
    evidence=table(pd.DataFrame([{'source':str((source/n).relative_to(ROOT)),'SHA-256':sha256(source/n)} for n in ['report.json','metrics.csv']]))
    command=f'''```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_calibration_periods.py \\
  --protocol config/calibration-periods-v1.json --output {source.relative_to(ROOT)}
.venv/bin/python scripts/report_calibration_periods.py --source {source.relative_to(ROOT)} --report-name {name}
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en=f'''# Separate calibration and threshold periods across years

The separated policy reaches recall >=0.95 in {hits} of {total} positive evaluation
years. The all-year acceptance gate is `{passed}`. No dashboard model or alarm policy
was replaced, and the reserved 2024–2025 test remains closed. Improvements in one year
are not treated as general model improvement.

## Design and controls

The frozen protocol is `config/calibration-periods-v1.json`. The same yearly logistic
and XGBoost models, 96 features, 0.45/0.55 blend and evaluation populations from
`walk-forward-v1` are retained. This experiment fits new probability calibrators and
thresholds, not new underlying classifiers. Original source hashes, split audits and
evaluation metadata are verified before use.

Three arms are compared. `baseline_full_year` retains the frozen full-year sigmoid
calibrators and threshold. `late_threshold_control` retains those same calibrators and
probabilities but chooses its threshold only on the late half of the preceding year.
This deliberately retains calibration/threshold reuse to control for threshold recency.
`separated_calibration` fits sigmoid calibrators only on the early half and selects its
threshold only on the late half. Each threshold targets recall >=0.95 on its selection
period and is saved before evaluation predictions. Evaluation labels never retune it.

The boundary is July 1 of the year before evaluation. Early prediction windows must
end by the boundary; late observation windows must start on or after it. Late HARPs
also seen in the early half are excluded from both new arms' threshold-selection data.
Outer training and evaluation rows remain unchanged. Splitting changes both sample size
and timing, so this is not a causal isolation of data reuse alone. Source label/quality
exclusions are inherited.

## Fold availability and split audit

{folds}
Original 2019–2021 skips remain because their preceding calibration years lack positive
examples. If a late half lacked both classes, both new policies would be unavailable;
if only the early half lacked both classes, the separated policy would be unavailable.
No silent fallback to baseline is allowed. `undefined` is not a measured zero.

## Precision, recall and false-positive windows

{summary}
All scores are fractions on a 0–1 scale. Precision is the positive fraction among alarm
windows; recall is the caught fraction among positive windows. FP/FN are overlapping
forecast windows, not independent flares or notifications. Each arm uses its own frozen
threshold on the same annual evaluation rows. In 2018 there are no retained positive
windows. The separated policy also makes no alarms, so both precision and recall are
undefined; zero FP is not evidence that positive events would be caught.

## Complete metric comparison

{full}
Accuracy measures all correctly classified windows and can be misleading under class
imbalance. AP measures ranking; lower Brier/log loss is better probabilistic scoring.
The frozen acceptance gate requires coverage of all comparable positive years, strictly
higher precision at recall >=0.95 in each, no lower AP and no higher Brier/log loss than
baseline. The late-threshold control changes no probabilities, so its AP, Brier and log
loss match baseline exactly. A threshold adjustment is not itself a ranking improvement.

## Interpretation

In 2022 the separated policy raises precision from 0.039573 to 0.070566 and reduces FP
from 10072 to 5308 while retaining recall 0.957245. However, the late-threshold control
already produces precision 0.070197 and 5338 FP at the same recall. Most of the observed
gain that year is reproduced without separating probability fitting from threshold
selection. The separated probabilities have worse Brier/log loss and slightly lower AP
than baseline, so even that year does not pass the full gate.

In 2014 and 2015 precision rises but recall falls to 0.844156 and 0.946863, below the
required target. In 2023 recall rises from 0.884763 to 0.956466, while precision falls
from 0.103397 to 0.064247 and FP rises from 5992 to 10880. The late-threshold control
achieves the same recall with 10501 FP, fewer than the separated policy. The trade-off
therefore changes by year; separating periods is not a consistent precision solution.
No positive evaluation year passes all acceptance checks.

## Paired conditional uncertainty

{ci}
Intervals are separated policy minus the named control, using 1000 paired whole-HARP
bootstrap draws per year with seed 24. The same resampled regions contribute to both
arms. Fitted classifiers, calibrators and thresholds remain fixed; fitting and historical
selection uncertainty are excluded. Undefined precision/recall draws are counted through
`valid_draws`; a zero-positive year has no valid recall draws. An interval spanning zero
does not establish a directional change at that interval level. Years share historical
training and are not independent replications.

## Limitations and next decision

This is adaptive retrospective development informed by earlier errors, not a fresh
independent test. It does not establish a physical cause for temporal changes. Fewer
calibration positives can make the fitted mapping and selected threshold unstable.
The result rejects this fixed half-year recipe as a general replacement, not every
possible chronological calibration policy. Do not tune the split date repeatedly on
these outcomes or lower the recall requirement to declare success.

Before another policy search, inspect the calibration-period score distributions and
positive-region counts across years, then freeze any candidate using earlier inner
chronological folds. A practical policy must demonstrate both recall and false-alarm
burden across periods; calibration alone cannot guarantee better separation of positive
and negative cases. That follow-up analysis and any additional training are not claimed
to have been performed here. The reserved test remains outside development.

## Reproduction

{command}
Use fresh output directories and report names; never overwrite frozen evidence.
Review both full document editions, register their source hash and links in
`docs/reports.json` and `docs/reports.md`, then publish to a fresh HTML directory.
Calibrators, predictions, thresholds and HTML remain local ignored artifacts. Source,
code and output hashes are recorded in the experiment report.

{evidence}
'''
    tr=f'''# Yıllar boyunca kalibrasyon ve eşik dönemlerini ayırma

Ayrılmış yöntem, pozitif değerlendirme yıllarının {total} tanesinden {hits} tanesinde
recall >=0.95 sağladı. Tüm yıllar için kabul kontrolü `{passed}` oldu. Dashboard modeli
ve alarm kuralı değiştirilmedi; ayrılmış 2024–2025 testi kapalı kaldı. Tek yıldaki
iyileşme genel model iyileşmesi sayılmadı.

## Tasarım ve kontrol kolları

Sabit protokol `config/calibration-periods-v1.json` dosyasındadır. `walk-forward-v1`
deneyinin aynı yıllık lojistik ve XGBoost modelleri, 96 özelliği, 0.45/0.55 birleşimi ve
değerlendirme toplulukları korundu. Bu deney yeni temel sınıflandırıcılar değil, yeni
olasılık kalibratörleri ve eşikler öğrenir. Özgün kaynak özetleri, ayrım denetimleri ve
değerlendirme meta verileri kullanımdan önce doğrulanır.

Üç kol karşılaştırılır. `baseline_full_year`, sabit tam yıllık sigmoid kalibratörleri
ve eşiği korur. `late_threshold_control`, aynı kalibratörleri ve olasılıkları korur,
ancak eşiği yalnızca önceki yılın ikinci yarısında seçer. Eşik verisinin yakın tarihli
olmasını kontrol etmek için kalibrasyon/eşik verisinin tekrar kullanımı bilinçli korunur.
`separated_calibration`, sigmoid kalibratörlerini yalnızca ilk yarıda öğrenir ve eşiği
yalnızca ikinci yarıda seçer. Her eşik kendi seçim döneminde recall >=0.95 hedefler ve
değerlendirme tahminlerinden önce kaydedilir. Değerlendirme etiketleriyle yeniden ayarlanmaz.

Sınır, değerlendirmeden önceki yılın 1 Temmuz tarihidir. Erken tahmin pencereleri bu
sınıra kadar bitmeli, geç gözlem pencereleri sınırda veya sonrasında başlamalıdır.
İlk yarıda görülen HARP'lar iki yeni kolun da geç dönem eşik seçimi verisinden çıkarılır.
Dış eğitim ve değerlendirme satırları değişmez. Bölme hem örnek sayısını hem zamanlamayı
değiştirir; yalnızca veri tekrar kullanımının nedensel etkisini ayırmaz. Kaynak etiket/kalite
dışlamaları geçerlidir.

## Tur kullanılabilirliği ve ayrım denetimi

{folds}
Önceki kalibrasyon yıllarında pozitif örnek olmadığı için özgün 2019–2021 atlamaları
korunur. Geç yarıda iki sınıf olmasaydı iki yeni yöntem de kullanılamazdı; yalnızca erken
yarıda iki sınıf olmasaydı ayrılmış yöntem kullanılamazdı. Sessizce referansa dönülmez.
`undefined`, ölçülmüş sıfır değildir.

## Precision, recall ve yanlış pozitif pencereler

{summary}
Tüm skorlar 0–1 ölçeğinde oranlardır. Precision alarm pencerelerindeki pozitiflerin,
recall pozitif pencerelerdeki yakalananların oranıdır. FP/FN bağımsız patlamalar veya
bildirimler değil, örtüşen tahmin pencereleridir. Her kol aynı yıllık değerlendirme
satırlarında kendi sabit eşiğini kullanır. 2018'de korunan pozitif pencere yoktur.
Ayrılmış yöntem ayrıca hiç alarm vermediğinden hem precision hem recall tanımsızdır;
sıfır FP, pozitif olayların yakalanacağını göstermez.

## Tüm metriklerin karşılaştırması

{full}
Accuracy tüm doğru sınıflandırılan pencereleri ölçer; sınıf dengesizliğinde yanıltıcı
olabilir. AP sıralamayı ölçer; düşük Brier/log loss daha iyi olasılıksal puanlamadır.
Sabit kabul kontrolü, tüm karşılaştırılabilir pozitif yılların kapsanmasını, her yılda
recall >=0.95 koşulunda kesinlikle daha yüksek precision, referansa göre düşmeyen AP ve
artmayan Brier/log loss gerektirir. Geç eşik kontrolü olasılıkları değiştirmez; dolayısıyla
AP, Brier ve log loss referansla aynıdır. Eşik ayarı tek başına sıralama iyileşmesi değildir.

## Yorum

2022'de ayrılmış yöntem precision'ı 0.039573'ten 0.070566'ya yükseltip FP'yi 10072'den
5308'e indirirken recall 0.957245 kalır. Ancak geç eşik kontrolü aynı recall ile zaten
0.070197 precision ve 5338 FP üretir. O yıl gözlenen kazancın çoğu, olasılık öğrenimiyle
eşik seçimini ayırmadan yeniden elde edilir. Ayrılmış olasılıkların Brier/log loss
değerleri daha kötü, AP biraz daha düşüktür; dolayısıyla o yıl da tüm kabul kontrolünü geçmez.

2014 ve 2015'te precision artar fakat recall sırasıyla 0.844156 ve 0.946863'e, gereken
hedefin altına düşer. 2023'te recall 0.884763'ten 0.956466'ya çıkarken precision
0.103397'den 0.064247'ye düşer ve FP 5992'den 10880'e çıkar. Geç eşik kontrolü aynı
recall'a 10501 FP ile ulaşır; bu, ayrılmış yöntemden daha azdır. Dolayısıyla denge yıla
göre değişir; dönemleri ayırmak tutarlı bir precision çözümü değildir. Hiçbir pozitif
değerlendirme yılı tüm kabul kontrollerini geçmez.

## Eşleştirilmiş koşullu belirsizlik

{ci}
Aralıklar ayrılmış yöntem eksi belirtilen kontroldür; yıl başına 24 tohumla eşleştirilmiş
bütün HARP'ları örnekleyen 1000 bootstrap tekrarı kullanır. İki kola aynı örneklenmiş
bölgeler katkı yapar. Öğrenilmiş sınıflandırıcılar, kalibratörler ve eşikler sabittir;
öğrenim ve geçmiş seçim belirsizliği dahil değildir. Tanımsız precision/recall tekrarları
`valid_draws` ile izlenir; pozitif olmayan yılda geçerli recall tekrarı yoktur. Sıfırı
içeren aralık, o aralık düzeyinde yönlü değişimi göstermez. Yıllar geçmiş eğitimi paylaşır
ve bağımsız tekrarlar değildir.

## Sınırlamalar ve sonraki karar

Bu, önceki hataların yönlendirdiği uyarlamalı, geçmişe dönük geliştirmedir; yeni bağımsız
test değildir. Zamansal değişimlerin fiziksel nedenini belirlemez. Kalibrasyonda daha
az pozitif örnek, öğrenilmiş olasılık dönüşümünü ve seçilen eşiği kararsızlaştırabilir.
Sonuç, tüm kronolojik kalibrasyon kurallarını değil, bu sabit yarım yıllık düzeni genel
model değişikliği olarak eler. Bu sonuçlar üzerinde bölme tarihini tekrar tekrar
ayarlayarak veya recall hedefini düşürerek başarı ilan edilmemelidir.

Yeni kural aramasından önce, kalibrasyon dönemi skor dağılımları ve pozitif bölge sayıları
yıllar arasında incelenmeli; ardından aday, daha erken iç kronolojik bölümlerde
sabitlenmelidir. Pratik kural hem recall'ı hem yanlış alarm yükünü farklı dönemlerde
göstermelidir; kalibrasyon tek başına pozitif ve negatiflerin daha iyi ayrılmasını
garanti etmez. Bu takip incelemesinin veya ek eğitimin burada yapıldığı iddia edilmez.
Ayrılmış test geliştirme dışında kalır.

## Yeniden üretim

{command}
Yeni çıktı dizinleri ve rapor adları kullanın; sabit kanıtın üzerine yazmayın.
İki tam belge sürümünü gözden geçirip kaynak özetini ve bağlantıları `docs/reports.json`
ve `docs/reports.md` dosyalarına kaydedin; ardından yeni HTML dizinine yayımlayın.
Kalibratörler, tahminler, eşikler ve HTML yerel, Git dışında çıktılar olarak kalır.
Kaynak, kod ve çıktı özetleri deney raporunda kayıtlıdır.

{evidence}
'''
    for p,text in zip(paths,[en,tr]):p.write_text(text)
    print('\n'.join(map(str,paths)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--report-name',required=True);a=p.parse_args();run(a.source.resolve(),a.report_name)
