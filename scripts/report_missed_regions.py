"""Render the verified two-region audit as paired English/Turkish documents."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from scripts.report_precision_followup import table


def run():
    source=ROOT/'artifacts/missed_regions_20261027_r2'
    report=json.loads((source/'report.json').read_text())
    for name,digest in report['artifact_hashes'].items():
        if sha256(source/name)!=digest:raise ValueError('Audit artifact changed')
    regions=table(pd.DataFrame(report['regions'])[['harp','raw_rows','retained_windows','positive_windows','tp','fn','fp',
        'cadence_gaps','raw_rows_nonfinite','zero_flux_rows','missed_windows_without_missing_values','reproduced_feature_values']])
    events=pd.DataFrame(report['events'])
    association=table(events[['harp','peak_utc','goes_class','confidence','harp_vote','max_pair_distance_deg','hek_noaa','jsoc_noaa','noaa_matches','header_offset_seconds']])
    lead=table(events[['harp','peak_utc','eligible_windows','alarm_windows','first_alarm_utc','lead_to_peak_hours','lead_to_start_hours']])
    headers=table(pd.DataFrame(report['headers']))
    flux=[]
    for h in [9152,9584]:
        o=pd.read_csv(source/f'harp_{h}_observations.csv');o['utc']=pd.to_datetime(o.utc,utc=True)
        w=pd.read_csv(source/f'harp_{h}_windows.csv');w['forecast_time']=pd.to_datetime(w.forecast_time,utc=True)
        positives=w[w.target.eq(1)]
        for stage,t in [('first_positive_forecast',positives.forecast_time.min()),('first_alarm',positives[positives.alarm].forecast_time.min())]:
            row=o[o.utc<t].iloc[-1]
            flux.append({'harp':h,'stage':stage,'forecast_utc':t.isoformat(),'last_observation_utc':row.utc.isoformat(),
                         'USFLUX':f'{float(row.usflux):.8e}','TOTUSJH':float(row.totusjh)})
    growth=table(pd.DataFrame(flux))
    evidence=table(pd.DataFrame([{'source':'artifacts/missed_regions_20261027_r2/report.json','SHA-256':sha256(source/'report.json')},
                                 *[{'source':k,'SHA-256':v} for k,v in report['source_hashes'].items()]]))
    commands='''```sh
.venv/bin/python scripts/extract_region_audit.py --output data/region_audit_20261027_r2
.venv/bin/python scripts/fetch_region_headers.py
.venv/bin/python scripts/audit_missed_regions.py --raw data/region_audit_20261027_r2 --output artifacts/missed_regions_20261027_r2
.venv/bin/python scripts/report_missed_regions.py
.venv/bin/python scripts/publish_reports.py --output artifacts/bilingual_reports_missed_regions_20261027
```
'''
    texts={
'en':f'''# HARP 9152 and 9584: label, measurement and warning-time audit

Audit date: 2026-10-27. **No label or feature correction is justified by the
current evidence.** All 257 retained windows, their labels and 24672 feature
values reproduce from verified raw V2 observations. All 768 finite USFLUX pairs
match JSOC headers at relative tolerance 1e-5. The 34 missed positive windows
all have zero missing fraction. They are not 34 independent missed flares:
there are three attached M-class events, each with at least one earlier alarm.
This retrospective subset result does not establish overall event recall.

## Sources and scope

Two full compressed archives were verified against frozen SHA-256, ETag and
byte length; logical Parquet reads selected only HARP 9152/9584 and observation
times before 2024. The downloaded archives contain other periods, but reserved
test records were not logically read or scored. Predictions remain the frozen
2023 ensemble at threshold 0.00931081050648097. No retraining or relabeling occurred.

HEK/SWPC monthly responses were checked against their recorded hashes. Three
bounded definitive SHARP header queries supplied NOAA associations, timestamps,
QUALITY flags and USFLUX. JSOC HTTPS certificate verification failed; the
existing read-only HTTP fallback supplied the headers. Transport was therefore
unauthenticated, with response hashes and attempts preserved. TLS checks were
not disabled. This comparison checks separately retrieved metadata; JSOC and
V2 share underlying observations and are not independent instruments.

## Window reconstruction and missingness

{regions}
There are 1363 and 1365 raw observation rows, with no non-12-minute cadence
steps. Nonfinite rows and zero flux values exist elsewhere in these region
lifetimes. All 34 missed positive windows nevertheless contain finite inputs;
missing-value imputation does not directly explain those misses. Finite values
do not guarantee a clean QUALITY flag or physically reliable measurements.

The raw quality policy retains 261 and 262 candidate windows before label
exclusions; only 106 and 151 remain in the frozen evaluation population.
Therefore gaps in the prediction scatter plots are not evidence of missing
raw observations. The audit does not reintroduce excluded evaluation windows.
The two regions contribute 102 of the incumbent's 8577 false-positive windows;
this audit alone does not explain the full precision problem.

## Event association and time checks

{association}
The SWPC GOES classes and UTC peak times exactly match all three attached V2
events. JSOC NOAA_ARS maps HARP 9152 to NOAA 13243 and HARP 9584 to NOAA 13315,
matching SWPC. Archive observation times were converted from TAI to UTC using
the 37-second offset applicable here; all frozen labels reproduce with the
half-open target interval [forecast_time, forecast_time + 24h).

The 24 May association remains a limitation: V2 confidence is `low`, vote is
`2-1`, and maximum pairwise source separation is 54.203321 degrees. The matching
SWPC/JSOC NOAA number supports the assignment but does not resolve source-position
disagreement or prove exact spatial origin. No label is changed. The other
associations are `very_high` and `high`; these are source metadata, not new
independent confidence estimates. Nearest header offsets are reported explicitly.

## Window recall versus event warning

{lead}
For these three selected events, the first eligible retained alarm preceded
the reported event start by 1.510278, 11.093611 and 23.810278 hours. HARP 9152
has only 2 alarmed windows out of 24 positive windows, despite warning before
the flare. HARP 9584 has 12/24 and 24/24. Thus demanding 95% positive-window
recall is different from requiring at least one warning per flare.

This is a post-hoc audit of regions selected for errors, not an independent
3/3 event-detection benchmark. Excluded windows limit lead-time estimates.
The user objective and official metrics are unchanged: precision 0.079622 and
recall 0.950064 across the original validation population.

## Magnetic evolution and quality evidence

{growth}
Both first events show increasing unsigned flux and total unsigned current
helicity between the first retained positive forecast and the first alarm.
The model's probability also rises. This supports testing evolution-sensitive
features; it does not establish why the model missed earlier windows or prove
that emergence caused the flare. Values are reported in dataset-native units.

{headers}
There are 9 nonzero QUALITY headers for HARP 9152 and 20 for HARP 9584 within
the queried intervals. The audit records the bits without interpreting them
as a blanket invalidity rule. All 300 and 468 finite time-matched USFLUX pairs
agree with JSOC; the remaining headers have no selected raw timestamp counterpart.
Agreement on USFLUX does not validate all 24 parameters or their physical units.

## Figures

[HARP 9152 — English figure](../artifacts/missed_regions_20261027_r2/harp_9152.en.png)

[HARP 9584 — English figure](../artifacts/missed_regions_20261027_r2/harp_9584.en.png)

Each figure contains frozen probabilities, raw USFLUX, raw TOTUSJH, window
missingness and nonzero QUALITY markers. Red points are positive windows;
red vertical lines are flare peaks; the dashed line is the frozen threshold.
Measurement axes use symmetric log scaling. Markers at -2 in the last panel
indicate QUALITY flags, not negative missingness. Future event markers are
retrospective annotations and are not model inputs.

## Decision and next experiment

Keep the labels, population, model and threshold unchanged. The most useful
next experiment is 24/48-hour evolution features from raw observations, with
training-only preprocessing and chronological comparison. Histories must not
be constructed solely from label-filtered windows. Independently investigate
the low-confidence 24 May spatial association before any proposed correction.
Also inspect the regions contributing most false positives; reducing late
misses in two regions is not itself proof of improved precision.

A separate event-level assessment should report warning lead time and alert
episodes alongside existing window metrics, with event matching and alert
merging rules fixed before evaluation. It must not replace the original recall
objective or rebrand this selected subset as a new success metric.

## Reproduction and evidence

{commands}
Existing outputs are protected. Repeats require new paths and corresponding
updates to dated report/header input paths. The accepted raw extraction is r2;
the first extraction attempt failed on network resolution. Audit r1 stopped
on a relative-path error before producing a report; r2 is the accepted audit.
Data, raw headers and PNG/CSV/JSON/HTML artifacts stay outside Git. Source code,
paired Markdown reports and the bilingual catalog are version controlled.

{evidence}
''',
'tr':f'''# HARP 9152 ve 9584: etiket, ölçüm ve uyarı zamanı denetimi

Denetim tarihi: 2026-10-27. **Mevcut kanıtlar etiket veya özellik düzeltmesini
gerektirmiyor.** Tutulan 257 pencerenin tamamı, etiketleri ve 24672 özellik
değeri doğrulanmış ham V2 gözlemlerinden yeniden üretildi. 768 sonlu USFLUX
çiftinin tamamı 1e-5 göreli toleransla JSOC başlıklarına uydu. Kaçırılan 34
pozitif pencerenin tamamında eksik oranı sıfır. Bunlar 34 bağımsız kaçırılan
patlama değil: ilişkilendirilmiş üç M sınıfı olay var ve her biri öncesinde en
az bir alarm bulunuyor. Bu geçmişe dönük alt küme sonucu genel olay recall'unu kanıtlamaz.

## Kaynaklar ve kapsam

İki tam sıkıştırılmış arşivin SHA-256, ETag ve bayt uzunluğu dondurulmuş kayıtla
doğrulandı; mantıksal Parquet okumaları yalnızca HARP 9152/9584 ve 2024 öncesi
gözlem zamanlarını seçti. İndirilen arşivlerde başka dönemler de bulunur, ancak
ayrılmış test kayıtları mantıksal olarak okunmadı veya skorlanmadı. Tahminler,
0.00931081050648097 eşikli dondurulmuş 2023 ensemble modeline aittir. Yeniden
eğitim veya yeniden etiketleme yapılmadı.

HEK/SWPC aylık yanıtları kayıtlı hash'leriyle doğrulandı. Üç sınırlı definitive
SHARP başlık sorgusu NOAA ilişkilerini, zamanları, QUALITY bayraklarını ve
USFLUX değerlerini sağladı. JSOC HTTPS sertifika doğrulaması başarısız oldu;
mevcut salt okunur HTTP alternatifi başlıkları sağladı. Bu nedenle aktarım
kimliği doğrulanmamıştır; yanıt hash'leri ve denemeler saklandı. TLS kontrolleri
kapatılmadı. Bu karşılaştırma ayrı alınmış metaveriyi denetler; JSOC ve V2 aynı
temel gözlemleri paylaşır, bağımsız cihazlar değildir.

## Pencere yeniden üretimi ve eksiklik

{regions}
1363 ve 1365 ham gözlem satırı var; 12 dakikalık aralıktan farklı adım yok.
Bu bölge yaşamlarının başka kısımlarında sonlu olmayan satırlar ve sıfır akı
değerleri bulunuyor. Buna karşın kaçırılan 34 pozitif pencerenin tamamındaki
girdiler sonlu; eksik değer doldurma bu kaçırmaları doğrudan açıklamıyor.
Sonlu değerler temiz QUALITY bayrağını veya fiziksel ölçüm güvenilirliğini garanti etmez.

Ham kalite politikası etiket dışlamalarından önce 261 ve 262 aday pencereyi
tutuyor; dondurulmuş değerlendirme popülasyonunda yalnızca 106 ve 151 kalıyor.
Dolayısıyla tahmin saçılım grafiklerindeki boşluklar ham gözlem eksikliğinin
kanıtı değil. Denetim dışlanan değerlendirme pencerelerini geri eklemiyor.
Bu iki bölge mevcut modelin 8577 yanlış pozitif penceresinin 102'sini oluşturuyor;
bu denetim tek başına tüm precision sorununu açıklamıyor.

## Olay ilişkisi ve zaman kontrolleri

{association}
SWPC GOES sınıfları ve UTC tepe zamanları üç V2 olayıyla tam eşleşiyor.
JSOC NOAA_ARS, HARP 9152'yi NOAA 13243'e, HARP 9584'ü NOAA 13315'e bağlıyor;
bunlar SWPC ile eşleşiyor. Arşiv gözlem zamanları, bu tarihlerde geçerli
37 saniyelik farkla TAI'den UTC'ye çevrildi; bütün dondurulmuş etiketler
[forecast_time, forecast_time + 24h) yarı açık hedef aralığıyla yeniden üretildi.

24 Mayıs ilişkisi hâlâ sınırlama: V2 güveni `low`, oyu `2-1`, kaynaklar arası
maksimum ikili ayrım 54.203321 derece. SWPC/JSOC NOAA numarasının eşleşmesi
atamayı destekliyor; ancak kaynak konum uyuşmazlığını çözmüyor veya kesin
uzamsal kökeni kanıtlamıyor. Etiket değiştirilmiyor. Diğer ilişkiler `very_high`
ve `high`; bunlar kaynak metaverisi, yeni bağımsız güven tahminleri değil.
En yakın başlığın zaman farkı tabloda açıkça veriliyor.

## Pencere recall'u ve olay öncesi uyarı

{lead}
Seçilen bu üç olayda ilk uygun tutulan alarm, bildirilen olay başlangıcından
1.510278, 11.093611 ve 23.810278 saat önceydi. HARP 9152, patlamadan önce
uyarmasına rağmen 24 pozitif pencerenin yalnızca 2'sinde alarm veriyor.
HARP 9584 için oranlar 12/24 ve 24/24. Bu nedenle pozitif pencerelerde %95
recall istemek, her patlamadan önce en az bir uyarı istemekten farklıdır.

Bu, hataları nedeniyle seçilen bölgelerin sonradan yapılan denetimidir;
bağımsız bir 3/3 olay yakalama ölçütü değildir. Dışlanan pencereler ön uyarı
süresi tahminlerini sınırlar. Kullanıcı hedefi ve resmî metrikler değişmedi:
özgün doğrulama popülasyonunda precision 0.079622, recall 0.950064.

## Manyetik değişim ve kalite kanıtı

{growth}
İki bölgenin ilk olaylarında, ilk tutulan pozitif tahmin ile ilk alarm arasında
işaretsiz akı ve toplam işaretsiz akım helisitesi artıyor. Model olasılığı da
yükseliyor. Bu, değişime duyarlı özellikleri sınamayı destekler; modelin erken
pencereleri neden kaçırdığını veya manyetik ortaya çıkışın patlamaya neden
olduğunu kanıtlamaz. Değerler veri setinin yerel birimleriyle raporlanır.

{headers}
Sorgulanan aralıklarda HARP 9152 için 9, HARP 9584 için 20 sıfır olmayan QUALITY
başlığı bulunuyor. Denetim bitleri kaydeder; bunları genel bir geçersizlik kuralı
olarak yorumlamaz. Zamanları eşleşen 300 ve 468 sonlu USFLUX çiftinin tamamı
JSOC ile uyumlu; kalan başlıkların seçilen ham zamanlarda karşılığı yok.
USFLUX uyumu 24 parametrenin tümünü veya fiziksel birimlerini doğrulamaz.

## Grafikler

[HARP 9152 — Türkçe grafik](../artifacts/missed_regions_20261027_r2/harp_9152.tr.png)

[HARP 9584 — Türkçe grafik](../artifacts/missed_regions_20261027_r2/harp_9584.tr.png)

Her grafik dondurulmuş olasılıkları, ham USFLUX, ham TOTUSJH, pencere eksikliğini
ve sıfır olmayan QUALITY işaretlerini içerir. Kırmızı noktalar pozitif pencereler,
kırmızı dik çizgiler patlama tepeleri, kesikli çizgi dondurulmuş eşiktir.
Ölçüm eksenleri simetrik logaritmik ölçek kullanır. Son paneldeki -2 işaretleri
negatif eksikliği değil, QUALITY bayraklarını gösterir. Gelecekteki olay
işaretleri geçmişe dönük açıklamadır; model girdisi değildir.

## Karar ve sonraki deney

Etiketler, popülasyon, model ve eşik korunsun. Sonraki en yararlı deney, ham
gözlemlerden 24/48 saatlik değişim özellikleri; yalnızca eğitimde öğrenilen
ön işleme ve kronolojik karşılaştırmadır. Geçmiş yalnızca etiketle filtrelenmiş
pencerelerden oluşturulmamalı. Herhangi bir düzeltme önermeden önce düşük güvenli
24 Mayıs uzamsal ilişkisi bağımsız incelenmeli. En fazla yanlış pozitif üreten
bölgeler de incelenmeli; iki bölgede geç uyarıları azaltmak tek başına precision
artışının kanıtı değildir.

Ayrı bir olay düzeyi değerlendirmesi, olay eşleştirme ve alarm birleştirme
kuralları değerlendirmeden önce sabitlenerek, mevcut pencere metriklerinin
yanında ön uyarı süresini ve alarm olaylarını raporlamalı. Özgün recall hedefini
değiştirmemeli veya bu seçilmiş alt kümeyi yeni bir başarı metriği olarak sunmamalı.

## Yeniden üretim ve kanıt

{commands}
Mevcut çıktılar korunur. Tekrar için yeni yollar ve tarihli rapor/başlık girdi
yollarının güncellenmesi gerekir. Kabul edilen ham çıkarım r2'dir; ilk çıkarım
ağ adresi çözümleme hatasıyla başarısız oldu. Denetim r1, rapor üretmeden göreli
yol hatasıyla durdu; kabul edilen denetim r2'dir. Veri, ham başlıklar ve
PNG/CSV/JSON/HTML çıktıları Git dışında kalır. Kaynak kod, eşlenmiş Markdown
raporları ve iki dilli katalog sürüm kontrolündedir.

{evidence}
'''}
    for lang,text in texts.items():
        suffix='' if lang=='en' else '.tr'
        path=ROOT/f'docs/missed-regions-audit-20261027{suffix}.md'
        if path.exists():raise ValueError('Preserve existing report')
        path.write_text(text)


if __name__=='__main__':run()
