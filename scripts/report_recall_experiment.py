"""Create Turkish target comparisons from the frozen experiment-4 outputs."""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.metric_summary import enrich


def table(frame):
    headers = list(frame.columns)
    def cell(value):
        return f'{value:.6f}' if isinstance(value, float) else str(value)
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |'] +
                     ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None)])


def run():
    output = ROOT / 'artifacts/experiment4'
    report = json.loads((output / 'report.json').read_text())
    for path, digest in report['source_code'].items():
        if sha256(ROOT / path) != digest:
            raise ValueError(f'Experiment source changed: {path}')
    if sha256(ROOT / 'docs/fourth-experiment-protocol.md') != report['protocol_sha256']:
        raise ValueError('Protocol changed after training')
    frame = pd.DataFrame([enrich(row) for row in report['metrics']])
    primary = frame[(frame.probability_kind == 'calibrated') & (frame.threshold_role == 'development') & (frame.recall_target == .95)]
    primary = primary.sort_values(['fp', 'average_precision', 'brier', 'model'], ascending=[True, False, True, True])
    transfer = frame[(frame.probability_kind == 'calibrated') & (frame.threshold_role == 'calibration_transfer')]
    control = primary[primary.model == 'control'].iloc[0]
    selected = primary[primary.model == report['selected_for_analysis']].iloc[0]
    transferred = transfer[transfer.model == selected.model].iloc[0]
    decision = next(d for d in report['decisions'] if d['model'] == selected.model)
    target_rows = []
    for key, label, target in [('recall', 'Yakalama oranı', '>= 0.95'), ('fp', 'Yanlış pozitif pencere', f'< {int(control.fp)}; ek hedef <= {int(.9*control.fp)}'),
                                ('average_precision', 'Average precision (AP)', f'>= {control.average_precision:.6f}'),
                                ('brier', 'Brier skoru', f'<= {control.brier:.6f}'), ('log_loss', 'Log loss', f'<= {control.log_loss:.6f}')]:
        target_rows.append(dict(Metrik=label, Hedef=target, Kontrol=control[key], Aday=selected[key]))
    comparison = pd.DataFrame(target_rows)
    columns = ['model', 'recall', 'precision', 'fp', 'fn', 'accuracy', 'balanced_accuracy', 'f1', 'false_positive_rate',
               'false_alarm_ratio', 'tss', 'average_precision', 'brier', 'log_loss', 'threshold', 'tp', 'tn']
    decisions = pd.DataFrame([dict(model=d['model'], promising=d['promising'], stretch_target=d['stretch_target'],
                                   false_alarm_reduction=d['false_alarm_reduction'],
                                   failed_checks=', '.join(k for k, v in d['checks'].items() if not v)) for d in report['decisions']])
    outcome = 'Geliştirme hedefi karşılandı.' if decision['stretch_target'] else 'Tüm geliştirme hedefleri birlikte karşılanmadı.'
    intro = f'''# Helio24: yakalama öncelikli dördüncü deney

Kullanıcı hedefi: recall ≥ %95; bu seviyede yanlış alarmları azaltmak.
{outcome} İnceleme adayı: **{selected.model}**.
Geliştirme verisinde recall %{100*selected.recall:.2f}, yanlış pozitif pencere {int(selected.fp):,};
kontrole göre azalma %{100*decision['false_alarm_reduction']:.2f}.
Önceki dönemde seçilen eşik değiştirilmeden uygulandığında recall %{100*transferred.recall:.2f},
yanlış pozitif pencere {int(transferred.fp):,}. Bu iki eşik farklı soruları yanıtlar.

## Deney kapsamı ve sınırlar

Sekiz önceden belirlenmiş XGBoost adayı gerçekten yeniden eğitildi. Eğitim: partition 1–2
({report['roles']['train']['n']:,} pencere); sigmoid kalibrasyonu ve aktarım eşiği: partition 3
({report['roles']['calibration']['n']:,} pencere); karşılaştırma: partition 4
({report['roles']['validation']['n']:,} pencere, {report['roles']['validation']['positives']:,} pozitif,
{report['roles']['validation']['harps']} HARP).
Zaman sınırında tahmin ufku taşan pencereler ve bölümler arası ortak bölgeler ayrıldı.
Kontrolün TP=1023, FP=5183, FN=53, TN=44372 sonucu önceki deneyle aynen yeniden üretildi.

Partition 4 daha önce incelenmiştir ve eşik/model seçimi için kullanılmıştır.
Burada %95 recall elde etmek bağımsız test başarısı değildir. Partition 5'in özellik veya
tahmin verileri ve ayrılan 2024–2025 verileri bu deneyde açılmadı. Aktarım eşiği partition 3'te
kalibrasyonla aynı örneklerde seçildi; partition 4 üzerinde değiştirilmedi, ancak adaylar
partition 4 ile karşılaştırıldığı için aktarım sonucu da nihai bağımsız test değildir.
Dashboard modeli otomatik değiştirilmedi. Yeni veri sürümünün uyumluluk sorunu devam ediyor.

FP ve FN sayıları **örtüşen tahmin pencereleridir**; bağımsız patlama/uyarı sayısı değildir.
%95 pencere recall'u, patlamaların %95'ini yakalama garantisi vermez.

## Hedefler ve sonuçlar

Evrensel bir “doğru metrik aralığı” yoktur. %95 recall kullanıcı hedefidir; %10 daha az FP
proje iyileştirme hedefidir. AP yüksek, Brier ve log loss düşük olmalıdır; burada kontrolle
karşılaştırılır. Accuracy için eşik koyulmadı: hep “patlama yok” tahmini bu bölümde
%{100*control.always_quiet_accuracy:.2f} accuracy verir. Bu yöntem pozitiflerin hiçbirini yakalamaz.
Oranlar tablolarda 0–1 ölçeğindedir. Precision doğru alarmların tüm alarmlara oranıdır;
FPR=FP/(FP+TN), yanlış alarm oranı (FAR)=FP/(TP+FP). AP eşikten bağımsız sıralamayı,
Brier ve log loss olasılık hatasını ölçer; kalibrasyon çizelgeleri ayrıca kaydedilmiştir.
'''
    sections = [('Hedef karşılaştırması', comparison), ('Tüm adaylar: doğrulamada seçilen %95 recall eşiği', primary[columns]),
                ('Önceki dönemin %95 eşiğinin sonraki döneme aktarımı', transfer[columns]),
                ('Önceden belirlenen kabul kontrolleri', decisions),
                ('HARP kümeli bootstrap: koşullu %95 aralıklar', pd.DataFrame(report['intervals']))]
    ending = '''
## Belirsizlik ve sonraki adım

Bootstrap 1.000 kez bütün HARP bölgelerini yeniden örnekler. Eşikler sabittir; aralıklar
eğitim, model seçimi ve eşik seçimi belirsizliğini içermez. İki adayın aralıkları arasındaki
fark istatistiksel anlamlılık testi olarak okunmamalıdır.
Sekiz adaylık önceden tanımlanmış eğitim bütçesi tamamlandı. Başarısız adaylar saklandı;
hedef tutana kadar aynı doğrulama bölümünde sınırsız arama yapılmadı.
Bir sonraki değerlendirme, veri uyumluluğu doğrulandıktan ve tüm seçimler dondurulduktan
sonra ayrılmış gelecek dönemde yapılmalıdır. Geliştirme sonucu tek başına canlı kullanım
veya %95 gelecekte yakalama iddiasını desteklemez.

## Yeniden üretim ve çıktılar

Protokol: `docs/fourth-experiment-protocol.md`.
Eğitim: `.venv/bin/python scripts/run_recall_experiment.py` (mevcut deneyin üzerine yazmaz).
Rapor: `.venv/bin/python scripts/report_recall_experiment.py`.
Yerel `artifacts/experiment4/` içinde sekiz model, ham/kalibre olasılıklar, tüm %90/%95/%99
eşik metrikleri, kalibrasyon kutuları, bölme denetimi, bootstrap ve kaynak SHA-256 bilgileri vardır.
Veriler, modeller ve büyük çıktılar Git'e eklenmez. İzlenebilir rapor ve kod Git'tedir.
'''
    markdown = intro + '\n'.join('\n## ' + title + '\n\n' + table(data) + '\n' for title, data in sections) + ending
    (ROOT / 'docs/recall-first-results.md').write_text(markdown)
    (output / 'report.html').write_text('<!doctype html><html lang="tr"><meta charset="utf-8"><title>Helio24 — Deney 4</title>'
                                      '<style>body{font:16px system-ui;margin:32px;line-height:1.5}table{border-collapse:collapse;font-size:13px}td,th{padding:8px;border:1px solid #bbb}pre{white-space:pre-wrap}.scroll{overflow:auto}</style>'
                                      '<body><pre>' + html.escape(intro) + '</pre>' + ''.join('<h2>'+html.escape(title)+'</h2><div class="scroll">'+data.to_html(index=False, float_format=lambda x: f'{x:.6f}')+'</div>' for title, data in sections)
                                      + '<pre>'+html.escape(ending)+'</pre></body></html>')
    (output / 'report_manifest.json').write_text(json.dumps(dict(training_report_sha256=sha256(output / 'report.json'),
        renderer_sha256=sha256(Path(__file__)), markdown_sha256=sha256(ROOT / 'docs/recall-first-results.md'),
        html_sha256=sha256(output / 'report.html')), indent=2))
    print(primary[columns].to_string(index=False))
    print('Report:', output / 'report.html')


if __name__ == '__main__':
    run()
