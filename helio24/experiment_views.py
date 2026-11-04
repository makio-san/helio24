"""Streamlit training status, refreshed independently of historical replay."""
from pathlib import Path
import pandas as pd
import streamlit as st
from helio24.experiment_monitor import snapshot

LABELS={'running':'Running','running_stale':'Running · no recent checkpoint','worker_only':'Worker active · coordinator unavailable',
        'completed':'Completed','stopped':'Stopped','failed':'Failed','unknown':'Process status unavailable','not_started':'Not started',
        'storage_unavailable':'Local experiment records unavailable',
        'queue_running':'Training queue active','queue_running_stale':'Training queue active · no recent checkpoint'}


@st.fragment(run_every='15s')
def render_training_tab(root, directory=None):
    st.subheader('Experiment progress')
    st.caption('Annual TCN experiment · development periods 2014–2023 · refreshes every 15 seconds.')
    st.button('Refresh status',key='refresh_training_status')
    state=snapshot(Path(root),directory)
    label=LABELS[state['state']]
    if state['state'] in ['running','queue_running','completed']:st.success(label)
    elif state['state'] in ['failed','stopped','worker_only','running_stale','queue_running_stale']:st.warning(label)
    else:st.info(label)
    if state['state']=='storage_unavailable':
        st.warning('Required records are cloud placeholders or inaccessible. Download them locally before checking progress. Counts and process status have not been verified.')
        return
    if state['state']=='unknown':st.caption('Process access could not be verified. The last saved record is shown below.')
    if state['state'] in ['running_stale','queue_running_stale']:st.caption('The process is active, but no new checkpoint has been recorded for at least 15 minutes.')
    if state['state'] in ['queue_running','queue_running_stale']:st.caption('Remaining model fits run in sequence. Annual evaluation follows when all reference inputs are available.')
    if state['state']=='worker_only':st.caption('A training worker is active. The coordinator could not be found; later fits may not start automatically.')
    if state['state']=='not_started':st.info('No prepared experiment records are available yet.');return
    current=state['current'];cols=st.columns(4)
    cols[0].metric('Completed fits',f"{state['completed']} / {state['total']}")
    cols[1].metric('Current year',str(current['year']) if current else '—')
    cols[2].metric('Current epoch',f"{current['epoch']} / {state['epochs']}" if current else '—')
    cols[3].metric('Evaluated periods',str(len(state['finished_years'])))
    if state['total']:
        st.progress(min(1.,state['completed']/state['total']),text=f"{state['completed']/state['total']:.0%} of planned model fits complete")
    if current:
        arm='Chronological measurements' if current['arm']=='chronological' else 'Shuffled interior steps'
        st.write(f"{arm} · seed {current['seed']}")
    if state['last_record']:
        st.caption(f"Last saved record (UTC): {state['last_record']} · {int(state['record_age_seconds']//60)} min ago")
    else:st.caption('No epoch record has been saved yet.')
    if state['completed']==state['total'] and state['state']!='completed':st.info('All model fits are saved. Final evaluation has not been marked complete.')
    if state['failure']:
        with st.expander('Latest failure'):st.code(state['failure'].get('error','The worker exited unsuccessfully.'))
    if state['warnings']:st.caption('Some records could not be read completely. They may be updating; refresh again.')
    if state['history']:
        st.markdown('**Current fit · training loss**')
        st.line_chart(pd.DataFrame(state['history']).set_index('epoch'),y='training_loss')
        st.caption('Training loss tracks optimization. Precision and recall are measured after each annual comparison is complete.')
    with st.expander('All scheduled fits'):
        rows=pd.DataFrame(state['jobs'])[['year','arm','seed','epoch','state']].rename(columns={'year':'Year','arm':'Input order','seed':'Seed','epoch':'Epoch','state':'Status'})
        rows['Status']=rows['Status'].map({'complete':'Saved','in_progress':'In progress','pending':'Pending'})
        rows['Input order']=rows['Input order'].map({'chronological':'Chronological','shuffled_interior':'Shuffled interior'})
        st.dataframe(rows,hide_index=True,width='stretch')
    st.caption('This tab reads local progress records. It does not start, stop or change training.')
