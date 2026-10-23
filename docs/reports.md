# Raporlar / Reports

Her raporun Türkçe ve İngilizce sürümü aşağıdadır. İki sürüm aynı bulguları,
tabloları, sınırlamaları ve yeniden üretim adımlarını içerir. Deney tarihleri
tarihsel bağlamı korur; çeviri yeni bir değerlendirme sonucu değildir.

Every report has Turkish and English editions below, covering the same
findings, tables, limitations and reproduction steps. Experiment dates retain
their historical context; translation does not constitute a new evaluation.

| Rapor / Report | Türkçe | English |
| --- | --- | --- |
| İlk deney / First experiment | [Türkçe](first-experiment.tr.md) | [English](first-experiment.md) |
| Tam veri kalibrasyonu / Full-data calibration | [Türkçe](second-experiment.tr.md) | [English](second-experiment.md) |
| Zamansal özellikler / Temporal features | [Türkçe](third-experiment.tr.md) | [English](third-experiment.md) |
| Alarm ve olay incelemesi / Alarm and event audit | [Türkçe](event-audit.tr.md) | [English](event-audit.md) |
| Etiket kaynağı / Label provenance | [Türkçe](event-provenance.tr.md) | [English](event-provenance.md) |
| Birincil kaynak incelemesi / Primary-source review | [Türkçe](event-source-review.tr.md) | [English](event-source-review.md) |
| İlişkilendirme duyarlılığı / Association sensitivity | [Türkçe](label-sensitivity.tr.md) | [English](label-sensitivity.md) |
| Toplu metrikler / Consolidated metrics | [Türkçe](metrics-status-report.md) | [English](metrics-status-report.en.md) |
| Yakalama öncelikli deney / Recall-first experiment | [Türkçe](recall-first-results.md) | [English](recall-first-results.en.md) |
| Ölçüm uyumluluğu / Measurement compatibility | [Türkçe](measurement-compatibility-report.md) | [English](measurement-compatibility-report.en.md) |
| EPS ve kalite incelemesi / EPS and quality audit | [Türkçe](eps-quality-audit.tr.md) | [English](eps-quality-audit.md) |

## HTML çıktıları / HTML editions

```sh
python scripts/publish_reports.py
# Yeni sürüm / New revision:
python scripts/publish_reports.py --output artifacts/bilingual_reports_v2
```

Komut, her rapor için dil bağlantıları içeren iki bağımsız HTML sayfası ve
ortak `index.html` üretir. Özgün deney dosyalarını değiştirmez; mevcut çıktı
dizinine yazmayı reddeder. Sayısal tablolar veya çevirinin dayandığı kaynak
değişirse yayın durur ve iki sürümün gözden geçirilmesi gerekir.
Kaynak ve çıktı SHA-256 özetleri `manifest.json` içinde tutulur.

The command generates two standalone HTML document editions per report,
language links and a shared `index.html`. Original experiment artifacts stay
unchanged; an existing output directory is rejected. Publication stops when
numeric tables disagree or the translation's source has changed, requiring
review of both editions. `manifest.json` records source and output SHA-256 hashes.

Bu sayfalar rapor belgelerinin iki dilli sürümleridir. Önceki deneylerin
grafikli tek dilli HTML çıktıları tarihsel kanıt olarak yerinde korunur.
JSON/CSV sütunları, model kimlikleri ve komutlar teknik adlarını korur.
Sayısal tablolar kaynak belgenin sayı yazımını korur.

These pages are bilingual editions of the report documents. Earlier
single-language experiment HTML files with figures remain preserved as
historical evidence. JSON/CSV fields, model identifiers and commands retain
their technical names. Numeric tables retain the source document's number notation.
