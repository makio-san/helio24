"""Create a standalone Turkish report of all saved experiments; never refit."""
import base64
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.metric_summary import enrich
from helio24.sensitivity import verify_report


def run(root=ROOT):
    output = root / 'artifacts/metrics_summary'
    if output.exists():
        raise RuntimeError('Preserve the existing metrics summary before rerunning')
    names = ['artifacts/report.json', 'artifacts/experiment1/snapshot.json',
             'artifacts/experiment2/report.json', 'artifacts/experiment2/frozen_decisions.json',
             'artifacts/experiment2/calibration.csv', 'artifacts/experiment2/cluster_intervals.csv',
             'artifacts/experiment3/report.json', 'artifacts/event_audit/report.json',
             'artifacts/label_sensitivity/report.json', 'artifacts/label_sensitivity/metrics.csv',
             'artifacts/source_review/report.json']
    def read(name):
        return json.loads((root / name).read_text())
    first = read(names[0])
    snapshot = read(names[1])
    if sha256(root / names[0]) != snapshot['report.json']:
        raise ValueError('Dashboard report differs from frozen experiment 1')
    second, third = read(names[2]), read('artifacts/experiment3/report.json')
    if second['protocol'] != read(names[3]):
        raise ValueError('Experiment-2 decisions changed')
    for directory in ['event_audit', 'label_sensitivity', 'source_review']:
        verify_report(root, root / 'artifacts' / directory)
    rows = []
    for experiment, source, metrics in [
        ('experiment1', names[0], first['metrics']),
        ('experiment2', names[2], second['metrics']),
        ('experiment3', 'artifacts/experiment3/report.json',
         [dict(row, split='development') for row in third['development_metrics']] +
         [dict(row, split='retrospective') for row in third['retrospective_metrics']])]:
        rows.extend(dict(enrich(row), experiment=experiment, source=source) for row in metrics)
    all_metrics = pd.DataFrame(rows)
    main = all_metrics[
        ((all_metrics.experiment == 'experiment1') & (all_metrics.model == first['selection']['model']) &
         (all_metrics.split == 'test')) |
        ((all_metrics.experiment == 'experiment2') & (all_metrics.model == 'full_calibrated') &
         (all_metrics.recall_target == .9))].copy()
    if len(main) != 3:
        raise ValueError('Expected exactly three headline operating points')
    main['context'] = ['Dashboard · ilk test', 'Tam veri · doğrulama', 'Tam veri · sonraki dönem incelemesi']
    tradeoff = all_metrics[(all_metrics.experiment == 'experiment2') &
                          (all_metrics.model == 'full_calibrated')].copy()
    intervals = pd.read_csv(root / 'artifacts/experiment2/cluster_intervals.csv')
    reliability = pd.read_csv(root / 'artifacts/experiment2/calibration.csv')
    sensitivity = pd.read_csv(root / 'artifacts/label_sensitivity/metrics.csv')
    audit = read('artifacts/event_audit/report.json')
    event_keys = ['windows', 'regions', 'monitored_region_hours', 'alarm_region_hours',
                  'false_alarm_region_hours', 'false_alarm_hour_fraction', 'episodes',
                  'all_negative_episodes', 'boundary_or_gap_censored_episodes', 'longest_all_negative_hours',
                  'covered_mapped_events', 'detected_events', 'covered_event_recall', 'before_start_events',
                  'fully_covered_events', 'fully_covered_detected', 'fully_covered_recall',
                  'median_peak_lead_hours', 'median_start_lead_hours', 'covered_history_only_events',
                  'top10_region_false_hour_share', 'mapped_event_negative_label_conflicts']
    event_table = pd.DataFrame([dict(metric=key, value=audit[key]) for key in event_keys])
    output.mkdir(parents=True)
    for name, frame in [('all_metrics', all_metrics), ('headline_metrics', main), ('threshold_tradeoffs', tradeoff),
                         ('cluster_intervals', intervals), ('reliability_bins', reliability),
                         ('event_audit', event_table), ('association_sensitivity', sensitivity)]:
        frame.to_csv(output / (name+'.csv'), index=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for split, group in tradeoff.groupby('split'):
        group = group.sort_values('recall_target')
        axes[0].plot(group.fp, group.recall*100, 'o-', label=split)
        for row in group.itertuples():
            axes[0].annotate(f'{row.recall_target:.0%}', (row.fp, row.recall*100), xytext=(3, 5),
                             textcoords='offset points', fontsize=8)
    axes[0].set(xlabel='False-alarm windows', ylabel='Recall (%)', title='Frozen validation targets')
    for model in ['full_raw', 'full_calibrated']:
        group = reliability[(reliability.split == 'audit') & (reliability.model == model)]
        axes[1].plot(group.mean_probability, group.observed_rate, 'o-', label=model)
    axes[1].plot([0, 1], [0, 1], '--', color='gray')
    axes[1].set(xlabel='Mean predicted probability', ylabel='Observed positive-window rate',
                title='Retrospective reliability', xlim=(0, 1), ylim=(0, 1))
    for ax in axes:
        ax.legend(fontsize=8)
        ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(output / 'metrics.png', dpi=160)
    plt.close(fig)
    picture = base64.b64encode((output / 'metrics.png').read_bytes()).decode()

    percentages = ['accuracy', 'recall', 'precision', 'balanced_accuracy', 'false_positive_rate',
                   'false_alarm_ratio', 'threshold', 'always_quiet_accuracy']
    def table(frame):
        return '<div class="table">'+frame.to_html(index=False, escape=True, na_rep='—',
                                                    float_format=lambda x: f'{x:.6f}')+'</div>'
    display = main.copy()
    for key in percentages:
        display[key] = display[key].map(lambda x: f'{x:.2%}')
    headline_keys = ['accuracy', 'recall', 'precision', 'f1', 'balanced_accuracy', 'false_positive_rate',
                     'false_alarm_ratio', 'tss', 'average_precision', 'brier', 'log_loss', 'threshold',
                     'n', 'positives', 'tp', 'fp', 'fn', 'tn', 'alarms', 'always_quiet_accuracy']
    headline = display.set_index('context')[headline_keys].T.reset_index(names='Metrik')
    compact = ['experiment', 'model', 'split', 'fold', 'recall_target', 'n', 'positives', 'threshold',
               'accuracy', 'recall', 'precision', 'f1', 'balanced_accuracy', 'tp', 'fp', 'fn', 'tn',
               'alarms', 'false_positive_rate', 'false_alarm_ratio', 'tss', 'average_precision', 'brier',
               'log_loss', 'always_quiet_accuracy', 'precision_defined', 'recall_defined']
    created = datetime.now(timezone.utc).isoformat()
    paired = second['paired_brier_difference']
    html = f'''<!doctype html><html lang="tr"><meta charset="utf-8"><title>Helio24 — Metrik raporu</title>
<style>body{{font:16px/1.6 system-ui;color:#172b3a;max-width:1200px;margin:40px auto;padding:0 24px}}
table{{border-collapse:collapse;font-size:13px}}td,th{{padding:8px;border-bottom:1px solid #d5dfe5;text-align:left}}
.table{{overflow:auto;margin:20px 0}}img{{max-width:100%}}.note{{background:#fff3dd;padding:18px}}
@media print{{body{{margin:0;max-width:none}}.table{{overflow:visible}}details{{display:block}}}}</style>
<h1>Helio24 · Toplu performans raporu</h1><p>Oluşturulma zamanı (UTC): {escape(created)}</p>
<p class="note">Dashboard modelinin ilk test accuracy değeri %92,94; tam veri modelinin sonraki dönem
accuracy değeri %94,80. Veri kapsamları farklıdır. Beşinci bölüm daha önce incelendiği için sonraki
dönem sonuçları dokunulmamış final test olarak sunulamaz. Bu rapor yeni eğitim veya eşik seçimi yapmaz.</p>
<h2>1. Ana sonuçlar</h2>{table(headline)}
<p>Sayılar bağımsız patlamaları değil, örtüşebilen tahmin pencerelerini sayar. Tam veri modelinin
sonraki döneminde 897 doğru alarma karşı 3.824 yanlış alarm vardır. Alarmların yaklaşık %81'i yanlıştır.
Sürekli negatif tahminin accuracy değeri aynı dönemde %98,68 olur; recall ise sıfırdır.</p>
<h2>2. Metriklerin anlamı</h2><ul>
<li>Accuracy = (TP + TN) / N; F1 = 2TP / (2TP + FP + FN).</li>
<li>Recall = TP / (TP + FN); precision = TP / (TP + FP).</li>
<li>False positive rate = FP / (FP + TN); false alarm ratio = FP / (TP + FP).</li>
<li>Balanced accuracy = (recall + specificity) / 2; TSS = recall − false positive rate.</li>
<li>AP, precision–recall performansını özetleyen average precision'dır; trapez yöntemiyle PR-AUC değildir.</li>
<li>Brier ve log loss için düşük değer iyidir. Brier tek başına saf kalibrasyon ölçüsü değildir.</li></ul>
<p>Accuracy, F1 ve balanced accuracy kayıtlı sayılardan hesaplandı. Sıfır alarmda eski raporlar
precision ve false alarm ratio için 0 saklar; precision_defined=False bunların tanımsız olduğunu belirtir.
ROC-AUC, ECE veya canlı sistem başarısı ölçülmüş gibi eklenmedi.</p>
<h2>3. Eşik dengesi ve olasılık kalitesi</h2><img alt="Eşik dengesi ve güvenilirlik grafikleri" src="data:image/png;base64,{picture}">
<p>%80/%90/%95 hedefleri doğrulamada seçilmiştir; sonraki dönemde gerçekleşmeleri garanti değildir.
İki dönemin örnek sayıları farklı olduğundan ham yanlış alarm sayıları doğrudan gelişim ölçüsü değildir.
Güvenilirlik grafiğinde noktalar bağımsız olay değil pencere gruplarıdır.</p>
{table(tradeoff[compact])}
<p>Kalibre edilmiş eksi ham model Brier farkı: {paired['estimate']:.6f}; %95 aralık
[{paired['lower']:.6f}, {paired['upper']:.6f}]. Aralık sıfırı içerdiği için kesin iyileşme iddiası yoktur.</p>
<details><summary>Olasılık aralıklarındaki örnek sayıları ve gözlenen oranlar</summary>{table(reliability)}</details>
<h2>4. Belirsizlik aralıkları</h2><p>1.000 HARP bazlı bootstrap tekrarından %95 aralıklar.
Modelin yeniden eğitilmesinden doğan belirsizlik veya bütün güneş döngüsü değişimleri kapsanmaz.</p>{table(intervals)}
<h2>5. Olay ve alarm süresi incelemesi</h2><p>Bölüm 4 geliştirme verisidir. Bölge-saat, farklı bölgeler
üzerinden toplanır; duvar saati değildir. Olay recall'ı yalnızca eşleştirilen ve tahmin kapsamındaki
olaylar için geçerlidir. Ortak 85 olayda 84 yakalama (%98,82), genel final-test başarısı değildir.</p>
{table(event_table)}{table(sensitivity)}
<h2>6. Bütün model ve eşik sonuçları</h2><p>Deney 3'ün zamansal özellik adayı geliştirme kabul
koşullarını sağlayamadı; dashboard'a geçirilmedi. Aşağıdaki tablodaki oranlar 0–1 ölçeğindedir.</p>
{table(all_metrics[compact])}
<h2>7. Son durum ve sıradaki çalışma</h2><p>Üç olayın kaynak incelemesi tamamlandı. 9529 için HARP 4941
daha güçlü destek alıyor; 8765 ve 8864 çözümlenmedi. Etiketler değiştirilmedi. Sonraki çalışma, yeni
dönemin veri uyumluluğu ve model/eşik seçimine açılmayacak bir değerlendirme protokolüdür.</p>
<p>Bu rapordaki sayılar kaydedilmiş raporlardan okunmuştur. Kaynak ve çıktı SHA-256 özetleri
report.json içinde, bütün metrikler all_metrics.csv içinde bulunur.</p></html>'''
    (output / 'report.html').write_text(html)
    manifest = dict(created_utc=created, scope='Saved metrics consolidation; no refitting or new evaluation',
                    rows=len(all_metrics), source_hashes={name: sha256(root / name) for name in names},
                    code_hashes={name: sha256(root / name) for name in ['helio24/metric_summary.py', 'scripts/report_metrics.py']},
                    artifact_hashes={p.name: sha256(p) for p in output.iterdir()})
    (output / 'report.json').write_text(json.dumps(manifest, indent=2, allow_nan=False))
    print(f'{output / "report.html"}\n{len(all_metrics)} operating points consolidated')
    return manifest


if __name__ == '__main__':
    run()
