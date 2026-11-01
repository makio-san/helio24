"""Freeze a bilingual launch-status report without claiming model performance."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from scripts.report_precision_followup import table


def run(source,output,name):
    if output.exists():raise ValueError('Preserve snapshot')
    paths=[ROOT/'docs'/f'{name}{suffix}.md' for suffix in ['', '.tr']]
    if any(p.exists() for p in paths):raise ValueError('Preserve documents')
    prepared=json.loads((source/'prepared.json').read_text());progress=json.loads((source/'progress.json').read_text())
    protocol=ROOT/'config/temporal-sequence-v2.json'
    if sha256(protocol)!=prepared['protocol_sha256']:raise ValueError('Protocol changed')
    rows=[]
    for f in prepared['folds']:
        row={'year':f['year'],'preparation':'ready' if f['status']=='complete' else 'skipped'}
        for a in f['audit']:
            row[f"{a['role']}_rows"]=a['rows'];row[f"{a['role']}_positives"]=a['positives']
        rows.append(row)
    current=source/str(progress['year'])/f"{progress['arm']}_seed{progress['seed']}"/'progress.json'
    epoch=json.loads(current.read_text()) if current.exists() else None
    if (source/'failure.json').exists():raise ValueError('Runner recorded a failure; investigate before reporting launch')
    snapshot={'scope':'Execution status snapshot, not a model-performance report','progress':progress,'epoch':epoch,
        'prepared_sha256':sha256(source/'prepared.json'),'protocol_sha256':sha256(protocol),'rows':rows,
        'tests_passed':140,'reserved_test_accessed':False,'performance_results_available':False,
        'limitations':['Process status is a snapshot, not evidence of eventual completion.','Training loss is an optimizer diagnostic, not precision, recall or calibration.','No annual comparison is complete at this snapshot.','CPU estimate excludes IO and evaluation.']}
    if progress['completed_years']:raise ValueError('Use an evaluation report once annual results are complete')
    output.mkdir(parents=True);(output/'report.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    coverage=table(pd.DataFrame(rows));state=table(pd.DataFrame([{'field':k,'value':str(v)} for k,v in {'year':progress['year'],'arm':progress['arm'],'seed':progress['seed'],'completed_epochs_current_fit':epoch['epoch'] if epoch else 0,'completed_annual_evaluations':len(progress['completed_years'])}.items()]))
    evidence=table(pd.DataFrame([{'source':str(p.relative_to(ROOT)),'sha256':sha256(p)} for p in [protocol,source/'prepared.json',output/'report.json']]))
    commands=f'''```sh
.venv/bin/python -m pip install -r requirements-sequence.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output {source.relative_to(ROOT)} --cache artifacts/sequence_cache_20261101_r1 --prepare-only
.venv/bin/python scripts/run_temporal_years.py --protocol config/temporal-sequence-v2.json --output {source.relative_to(ROOT)} --cache artifacts/sequence_cache_20261101_r1
.venv/bin/python scripts/report_temporal_execution.py --source {source.relative_to(ROOT)} --output {output.relative_to(ROOT)} --name {name}
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_{name}
```
'''
    en=f'''# Annual temporal experiment: integration and launch

The sequence reader, training-only preprocessing, isolated neural worker and annual
evaluation orchestrator are implemented. All seven eligible annual folds passed exact
population checks against both the original ensemble and the shorter-training control.
The actual experiment has started. This document freezes a launch-status snapshot;
it does not report improved precision or finished annual results.

## Prepared populations

{coverage}
`ready` means input preparation passed, not that training or evaluation finished.
The ten calendar years yield seven eligible folds. Preserve the zero-positive 2018
evaluation with undefined recall; skip 2019–2021 under the original baseline rules.
Every fold uses the original boundary purging and HARP separation. The complete cache
retains 595671 forecast keys, 60 steps and 24 magnetic values per key. Disk-backed arrays
allow indexed access without constructing every fold as a full in-memory tensor.

Scaling uses signed log1p and float64 channel statistics from training windows only.
Repeated observations count as they occur in those windows. Missing values are filled
by zero after scaling, with separate masks; finite scaled values are clipped to [-8,8].
Each fold has one shared scaler for both input arms and all three seeds. Input shuffles
are deterministic from seed/HARP/UTC forecast key, preserve first/last steps, and move
measurement/mask channels together. Batch order cannot change a window's permutation.

## Fixed experiment and current state

{state}
The v2 execution protocol retains v1's model, optimizer, 10 epochs, batch size 128,
seeds 24/42/97, chronological/shuffled arms and annual folds: 42 neural fits in total.
CPU training uses four threads in a fresh Python exec process for each fit. No sklearn
or XGBoost is imported in neural workers. The previously observed native-runtime crash
is addressed by isolation; its exact underlying cause remains unresolved.

Evaluation targets are read during preparation only for frozen population audits;
they are never passed to neural workers. Workers receive training targets and unlabeled
calibration/evaluation indices. The parent calibrates the equal mean of three raw sigmoid
probabilities and persists the recall >=0.95 threshold using the prior calibration year
before computing evaluation metrics. Individual seeds are separately reported, never
selected. The original and shorter-training references must have identical evaluation
keys; their different training histories remain explicit. Paired HARP bootstrap and
chronological-versus-shuffled comparisons run after all six fits of a year finish.

No annual metric comparison is complete at this snapshot. Training loss, when available
in progress files, is an optimization diagnostic and is not precision, recall or evidence
of better probabilities. The earlier synthetic CPU estimate was approximately 18.31
compute hours, excluding loading, preprocessing, inference and evaluation. This is not
a promised completion time. The reserved 2024–2025 test remains closed.

## Recovery and validation

Each completed epoch atomically saves model parameters, AdamW state, torch RNG state,
NumPy batch RNG state and epoch history. Intermediate checkpoints are solely recovery
state; only the final epoch is evaluated. Synthetic testing forcibly interrupts a fit,
resumes it and checks exact prediction equality with an uninterrupted fit. Final-checkpoint
reuse also reproduces predictions, and changed input hashes fail closed. Additional tests
verify training-only scaling, missingness, stable keyed permutations, key alignment and
cache corruption detection. The suite passed 140 tests; the strengthened interruption
test passed separately after that suite run.

Resume verifies the protocol, runner code, prepared inputs, cache and completed jobs.
A runner lock prevents duplicate execution. A failed worker aborts the parent and records
failure.json; completed annual outputs are verified before reuse. No completed experiment
is overwritten. Process survival and eventual completion still require monitoring.

## Reproduction and monitoring

{commands}
The foreground execution command also resumes an interrupted run from its last completed
epoch. Do not start another runner while the existing one holds the lock. Inspect
`{source.relative_to(ROOT)}/progress.json`, `run.log` and each
`year/arm_seed/worker.log` and `progress.json`; inspect `failure.json` if a process exits.
Completed annual results appear in `year/finished.json`; the final report.json and
metrics.csv are produced only after all eligible years finish. The active launch uses
a detached local process recorded in launcher.json. This snapshot is not a live monitor.

For independent reruns use new output/cache directories. Freeze a new protocol revision
for changes to design or hashed runner code. Use new snapshot directories/document names;
register both reviewed editions in docs/reports.json and docs/reports.md, then publish
paired HTML. Datasets, caches, checkpoints, predictions and generated HTML remain outside
Git. Local app.py branding changes remain uncommitted.

{evidence}
'''
    tr=f'''# Yıllık zamansal deney: bütünleştirme ve başlatma

Zaman serisi okuyucusu, yalnızca eğitimden öğrenilen ön işleme, ayrı süreçte sinir ağı
işçisi ve yıllık değerlendirme yürütücüsü uygulandı. Uygun yedi yıllık bölümün tamamı,
özgün birleşim ve kısa eğitim kontrolüyle tam örnek eşleşmesi kontrollerini geçti.
Gerçek deney başlatıldı. Bu belge başlangıç durumunun sabit bir kaydıdır;
precision artışı veya tamamlanmış yıllık sonuç bildirmez.

## Hazırlanmış örneklemler

{coverage}
`ready`, girdi hazırlığının geçtiğini belirtir; eğitim veya değerlendirmenin bittiğini
belirtmez. On takvim yılından yedisi uygundur. Pozitif örneği olmayan 2018 değerlendirmesi
tanımsız recall ile korunur; 2019–2021 özgün referans kurallarıyla atlanır. Her bölüm özgün
sınır temizliğini ve HARP ayrımını kullanır. Tam önbellek 595671 tahmin anahtarını, anahtar
başına 60 adımı ve 24 manyetik değeri korur. Disk tabanlı diziler, her bölümü tamamen
bellekte bir tensöre dönüştürmeden indeksli erişim sağlar.

Ölçekleme, yalnızca eğitim pencerelerinden işaretli log1p ve float64 kanal istatistikleri
kullanır. Tekrarlanan gözlemler bu pencerelerde göründükleri kadar sayılır. Eksik değerler
ölçekleme sonrasında sıfırla doldurulur ve ayrı maskeler taşır; sonlu ölçeklenmiş değerler
[-8,8] aralığına kırpılır. Her bölümde iki girdi kolu ve üç tohum ortak ölçekleyici kullanır.
Girdi karıştırması tohum/HARP/UTC tahmin anahtarından deterministik üretilir, ilk/son adımı
korur ve ölçüm/maske kanallarını birlikte taşır. Batch sırası pencerenin karıştırmasını
değiştiremez.

## Sabit deney ve mevcut durum

{state}
v2 çalıştırma protokolü v1'in modelini, optimizasyon yöntemini, 10 epoch'u, 128 örneklik
batch boyutunu, 24/42/97 tohumlarını, kronolojik/karıştırılmış kolları ve yıllık bölümleri
korur: toplam 42 sinir ağı eğitimi. CPU eğitimi her eğitim için yeni Python exec sürecinde
dört iş parçacığı kullanır. Sinir ağı işçileri sklearn veya XGBoost içe aktarmaz. Önceden
görülen yerel çalışma zamanı çökmesi süreç ayrımıyla ele alınır; alttaki kesin neden
henüz çözülmemiştir.

Değerlendirme etiketleri hazırlıkta yalnızca sabit örneklem denetimleri için okunur;
sinir ağı işçilerine hiç verilmez. İşçiler eğitim etiketlerini ve etiketsiz kalibrasyon/
değerlendirme indekslerini alır. Ana süreç üç ham sigmoid olasılığının eşit ortalamasını
kalibre eder; değerlendirme metriklerinden önce recall >=0.95 eşiğini önceki kalibrasyon
yılında seçip kaydeder. Tohumlar ayrı raporlanır, aralarından seçim yapılmaz. Özgün ve kısa
eğitim referanslarının değerlendirme anahtarları aynı olmalıdır; farklı eğitim geçmişleri
açıkça belirtilir. Eşleştirilmiş HARP bootstrap ve kronolojik/karıştırılmış karşılaştırması,
bir yılın altı eğitimi bittikten sonra yapılır.

Bu kayıtta yıllık metrik karşılaştırması henüz tamamlanmamıştır. İlerleme dosyalarında
bulunan eğitim kaybı optimizasyon tanısıdır; precision, recall veya daha iyi olasılık
kanıtı değildir. Önceki sentetik CPU tahmini yaklaşık 18.31 hesaplama saatiydi; yükleme,
ön işleme, çıkarım ve değerlendirmeyi içermez. Bu bir bitiş zamanı sözü değildir.
Ayrılmış 2024–2025 testi kapalıdır.

## Kesintiden devam ve doğrulama

Tamamlanan her epoch; model parametrelerini, AdamW durumunu, torch rastgele üreteç durumunu,
NumPy batch rastgele üreteç durumunu ve epoch geçmişini atomik kaydeder. Ara checkpoint'ler
yalnızca kesintiden devam içindir; sadece son epoch değerlendirilir. Sentetik test eğitimi
zorla keser, devam ettirir ve kesintisiz eğitimle tahminlerin tam eşitliğini kontrol eder.
Son checkpoint'in yeniden kullanımı da tahminleri üretir; değişen girdi hash değerleri
çalışmayı durdurur. Ek testler yalnızca eğitimden ölçeklemeyi, eksiklikleri, anahtara bağlı
sabit karıştırmayı, anahtar eşleşmesini ve önbellek bozulmasının saptanmasını doğrular.
Toplu kontrolde 140 test geçti; güçlendirilmiş kesinti testi bu çalıştırmadan sonra ayrıca
geçti.

Devam işlemi protokolü, yürütücü kodunu, hazırlanmış girdileri, önbelleği ve tamamlanmış
işleri doğrular. Yürütücü kilidi çift çalıştırmayı engeller. İşçi hatası ana süreci
durdurur ve failure.json'a kaydedilir; tamamlanmış yıllık çıktılar yeniden kullanılmadan
önce doğrulanır. Tamamlanmış deneyin üzerine yazılmaz. Sürecin çalışması ve sonunda
bitmesi yine takip gerektirir.

## Yeniden üretim ve takip

{commands}
Ön planda çalıştırma komutu, kesilmiş deneye tamamlanan son epoch'tan devam etmek için de
kullanılır. Mevcut yürütücü kilidi tutarken ikinci yürütücüyü başlatmayın.
`{source.relative_to(ROOT)}/progress.json`, `run.log` ve her
`year/arm_seed/worker.log` ile `progress.json` dosyasını inceleyin; süreç çıkarsa
`failure.json` dosyasına bakın. Tamamlanan yıllık sonuçlar `year/finished.json` içinde;
son report.json ve metrics.csv ise uygun tüm yıllar bittikten sonra üretilir. Etkin
başlatma, launcher.json'da kayıtlı ayrılmış yerel süreçtir. Bu kayıt canlı izleyici değildir.

Bağımsız tekrarlarda yeni çıktı/önbellek dizinleri kullanın. Tasarım veya hash ile bağlı
yürütücü kodu değişirse yeni protokol sürümü sabitleyin. Yeni durum kaydı dizinleri/belge
adları kullanın; iki incelenmiş sürümü docs/reports.json ve docs/reports.md içine kaydedip
çift dilli HTML yayımlayın. Veri, önbellek, checkpoint, tahmin ve üretilmiş HTML Git dışında
kalır. Yerel app.py marka değişiklikleri commit edilmez.

{evidence}
'''
    paths[0].write_text(en);paths[1].write_text(tr)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--name',required=True)
    a=p.parse_args();run(a.source.resolve(),a.output.resolve(),a.name)
