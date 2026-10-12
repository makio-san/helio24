"""Helio24 local historical replay dashboard. No live or synthetic predictions."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from helio24.data import ROOT, MAGNETIC_COLUMNS, read_observation
from helio24.modeling import metrics

st.set_page_config(page_title='Helio24 · Güneş patlaması tahmini', page_icon='☀️', layout='wide')
st.markdown('''<style>
.block-container {max-width:1280px;padding-top:2.4rem;}
h1,h2,h3 {letter-spacing:-.035em;}
[data-testid="stMetric"] {background:#141d27;border:1px solid #283442;border-radius:14px;padding:18px;}
.eyebrow {font-size:.76rem;letter-spacing:.22em;color:#ffad5c;font-weight:600;}
.intro {color:#9cabbc;max-width:760px;font-size:1.06rem;line-height:1.7;}
.orbit {width:58px;height:58px;border-radius:50%;background:radial-gradient(circle at 36% 32%,#ffe9a6,#ffad5c 40%,#d85128 73%,#332621);box-shadow:0 0 38px #f9913033;margin-bottom:20px;}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="orbit"></div><div class="eyebrow">HELIO24 / ARŞİV LABORATUVARI</div>', unsafe_allow_html=True)
st.title('Güneş’in sonraki 24 saati.')
st.markdown('<p class="intro">Geçmiş ölçümlerden bir tahmin oluştur. Sonraki 24 saatte ne olduğunu gör. Modelin güçlü olduğu yerleri ve kaçırdığı olayları incele.</p>', unsafe_allow_html=True)

output = ROOT / 'artifacts'
required = ['report.json', 'predictions.parquet', 'calibration.csv']
if not all((output / name).exists() for name in required):
    st.info('Henüz değerlendirilmiş bir model yok. Önce gerçek veri notebook’unu çalıştırın.')
    st.code('.venv/bin/python scripts/run_notebook.py', language='bash')
    st.caption('Veriler hazır değilse önce: python scripts/download.py')
    st.stop()


@st.cache_data
def load_results(version):
    report = json.loads((output / 'report.json').read_text())
    predictions = pd.read_parquet(output / 'predictions.parquet')
    calibration = pd.read_csv(output / 'calibration.csv')
    return report, predictions, calibration


report, predictions, calibration = load_results((output / 'report.json').stat().st_mtime_ns)
chosen = report['selection']['model']
threshold = report['selection']['threshold']
fractions = report.get('sample_fractions', {})
sample_description = ', '.join(f'Bölüm {part}: %{100*fraction:g}' for part, fraction in fractions.items()) or 'Örneklem oranı bu raporda belirtilmemiş'
names = {'baseline': 'Sabit referans', 'logistic': 'Lojistik regresyon', 'xgboost': 'XGBoost'}
test = predictions[(predictions.model == chosen) & (predictions.split == 'test')].copy()
with st.sidebar:
    st.header('☀ Helio24')
    st.caption('24 saatlik M / X tahmini')
    st.divider()
    st.write('**Çalışma modu**')
    st.write('Geçmiş gerçek veriler')
    st.write('**Seçilen model**')
    st.write(names[chosen])
    st.write('**Sabit alarm eşiği**')
    st.write(f'%{100*threshold:.2f}')
    st.caption('Model ve eşik doğrulama verisinde seçildi.')
    st.divider()
    st.caption(f'SWAN-SF · {sample_description}. Canlı veri bağlantısı yok.')
    st.caption('Patlama olasılığı, uydu hasarı veya Dünya’ya etki olasılığı değildir.')

replay_tab, performance_tab, data_tab = st.tabs(['Geçmişi oynat', 'Modelin karnesi', 'Veri ve yöntem'])

with replay_tab:
    st.subheader('O gün ne biliyorduk?')
    st.caption('Yalnızca son test bölümündeki HARP bölgeleri ve mevcut gözlem pencereleri gösterilir. Tüm saatler UTC.')
    left, right = st.columns([1, 2])
    with left:
        region = st.selectbox('Aktif bölge · HARP', sorted(test.harp.unique()), format_func=lambda value: f'HARP {value}')
    available = test[test.harp.eq(region)].sort_values('forecast_time')
    with right:
        day = st.selectbox('Geçmiş tarih · UTC', sorted(available.forecast_time.dt.date.unique()))
    windows = available[available.forecast_time.dt.date.eq(day)]
    stamp = st.select_slider('Tahmin anı · UTC', options=windows.forecast_time.tolist(), format_func=lambda value: value.strftime('%H:%M'))
    row = windows[windows.forecast_time.eq(stamp)].iloc[0]
    c1, c2, c3 = st.columns([1.4, 1, 1])
    probability_text = '< %0,1' if row.probability < 0.001 else f'%{100*row.probability:.1f}'
    c1.metric('Önümüzdeki 24 saatte M / X olasılığı', probability_text)
    c2.metric('Alarm eşiği', f'%{100*threshold:.2f}')
    c3.metric('Tahmin ufku', '24 saat')
    if row.probability >= threshold:
        st.warning('Alarm eşiği aşıldı. Model bu pencere için M / X patlama alarmı veriyor.')
    else:
        st.info('Alarm eşiği aşılmadı. Bu, patlama olmayacağının garantisi değildir.')
    st.caption('Bu bir arşiv modeli olasılık tahminidir. Kalibrasyon sonuçlarını “Modelin karnesi” bölümünde inceleyin.')
    st.markdown('#### Tahmin öncesindeki 12 saat')
    measurement = st.selectbox('Manyetik ölçüm', MAGNETIC_COLUMNS,
                               index=MAGNETIC_COLUMNS.index('USFLUX'))
    path = ROOT / row.file
    if path.exists():
        observation = read_observation(path)
        trusted = observation.IS_TMFI.astype(str).str.lower().isin(['true', '1', '1.0']) & observation.QUALITY.eq(0)
        series = pd.to_numeric(observation[measurement], errors='coerce').where(trusted)
        st.line_chart(pd.DataFrame({measurement: series.to_numpy()}, index=observation.Timestamp), height=260, color='#FFAD5C')
        st.caption(f'Gözlem: {row.observation_start:%d.%m.%Y %H:%M} – {row.forecast_time:%d.%m.%Y %H:%M} UTC (bitiş hariç). Son ölçüm: {row.observation_last:%H:%M}.')
    else:
        st.warning('Bu pencerenin ham ölçüm dosyası yerelde bulunamadı. Veri indirme adımını yeniden çalıştırın.')
    st.divider()
    st.markdown('#### Sonra gerçekte ne oldu?')
    st.caption(f'Sonuç aralığı: {row.forecast_time:%d.%m.%Y %H:%M} – {row.prediction_end:%d.%m.%Y %H:%M} UTC (bitiş hariç).')
    if st.toggle('Gerçek sonucu göster', value=False):
        if row.target:
            st.error(f'M / X patlaması kaydedildi · {row.label.split("@")[0]}')
        else:
            detail = 'FQ — veri setinde sakin pencere' if row.label == 'FQ' else f'En güçlü kayıt: {row.label.split("@")[0]}'
            st.success(f'M / X patlaması kaydedilmedi · {detail}')
        if pd.notna(row.peak_time):
            st.caption(f'Etiketteki patlamanın katalog tepe zamanı: {row.peak_time:%d.%m.%Y %H:%M} UTC')
        alarm = row.probability >= threshold
        outcome = ('Doğru alarm' if row.target else 'Yanlış alarm') if alarm else ('Kaçırılan olay' if row.target else 'Doğru sakin tahmin')
        st.write(f'**Bu pencerenin sonucu:** {outcome}')
        st.caption('Gerçek sonuç ayrı tutulur; model özelliklerine dahil değildir.')

with performance_tab:
    st.subheader('Tahminleri ölç, dengeyi gör.')
    results = pd.DataFrame(report['metrics'])
    selected = results[(results.model == chosen) & (results.split == 'test')].iloc[0]
    a, b, c, d = st.columns(4)
    a.metric('Yakalama oranı · recall', f'%{100*selected.recall:.1f}')
    b.metric('Alarm doğruluğu · precision', f'%{100*selected.precision:.1f}')
    c.metric('Yanlış alarm', str(int(selected.fp)))
    d.metric('Kaçırılan pozitif pencere', str(int(selected.fn)))
    st.caption(f'{int(selected.n):,} test penceresi · {int(selected.positives)} pozitif pencere. Sayılar tekil patlama sayısı değildir.')
    st.markdown('#### Üç modelin aynı test üzerindeki sonuçları')
    summary = results[results.split.eq('test')][['model', 'recall', 'precision', 'fp', 'fn', 'false_positive_rate', 'average_precision', 'brier', 'tss']].copy()
    summary['model'] = summary.model.map(names)
    st.dataframe(summary, hide_index=True, width='stretch')
    st.caption('Brier: düşük daha iyi. Average precision: nadir pozitifleri sıralama başarısı. Seçilen model doğrulamadaki average precision ile belirlenmiştir.')
    st.markdown('#### “%30” dediğinde yaklaşık %30 gerçekleşiyor mu?')
    selected_calibration = calibration[(calibration.model == chosen) & (calibration.split == 'test')]
    with plt.style.context('dark_background'):
        fig, ax = plt.subplots(figsize=(7, 3))
        fig.patch.set_facecolor('#0B1016'); ax.set_facecolor('#0B1016')
        ax.plot([0, 1], [0, 1], '--', color='#738194', label='İdeal kalibrasyon')
        ax.plot(selected_calibration.mean_probability, selected_calibration.observed_rate, 'o-', color='#FFAD5C', label=names[chosen])
        ax.set(xlabel='Ortalama tahmin', ylabel='Gerçek olay oranı', xlim=(0,1), ylim=(0,1))
        ax.legend()
        st.pyplot(fig); plt.close(fig)
    with st.expander('Kalibrasyon grupları ve örnek sayıları'):
        st.dataframe(selected_calibration[['bin', 'count', 'mean_probability', 'observed_rate']], hide_index=True)
    st.markdown('#### Alarm eşiğini keşfet · yalnızca doğrulama verisi')
    experimental = st.slider('Deneysel eşik (%)', 0.0, 100.0, float(round(threshold*100, 2)), step=0.01)
    validation = predictions[(predictions.model == chosen) & predictions.split.eq('validation')]
    tradeoff = metrics(validation.target, validation.probability, experimental/100)
    a, b, c = st.columns(3)
    a.metric('Doğrulama recall', f'%{100*tradeoff["recall"]:.1f}')
    b.metric('Doğrulama precision', f'%{100*tradeoff["precision"]:.1f}')
    c.metric('Doğrulama yanlış alarm', tradeoff['fp'])
    st.caption('Bu deneme, kaydedilmiş model eşiğini veya test sonuçlarını değiştirmez. Yanlış pozitif oranı FP/(FP+TN); yanlış alarm payı FP/(TP+FP).')

with data_tab:
    st.subheader('Gerçek veri. Açık sınırlar.')
    st.dataframe(pd.DataFrame(report['splits']).T, width='stretch')
    st.markdown('''
    - **Kaynak:** [SWAN-SF / Harvard Dataverse](https://doi.org/10.7910/DVN/EBCFKM).
    - **Girdi:** 12 saatlik 24 manyetik ölçümden 96 özet özellik.
    - **Hedef:** Sonraki 24 saatte M veya X; C, B ve FQ negatif sınıfta tutulur.
    - **Ayırma:** Eğitim 1, doğrulama 3, test 5. Bölümler arası zaman ve HARP denetimi uygulanır.
    - **Örneklem:** Her bölümden, etiketi kullanmadan yapılan seçim. Oranlar aşağıda gösterilir.
    - **Olasılıklar:** Ham model çıktılarıdır; ek bir kalibrasyon modeli uygulanmamıştır.
    - **Kısıt:** Arşivdeki kesinleştirilmiş SHARP verilerinin o tarihte canlı olarak hazır olduğu varsayılmaz.
    ''')
    st.caption(sample_description)
    st.info('Bir HARP birden fazla NOAA aktif bölgesini kapsayabilir. Aynı bölümdeki pencereler örtüşebilir; ölçülen recall tekil patlama yakalama oranı değildir.')
    st.caption(f'Çalıştırma veri özeti: {report["input_sha256"][:16]} · scikit-learn {report["versions"]["sklearn"]}')
