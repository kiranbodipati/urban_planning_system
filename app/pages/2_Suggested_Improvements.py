from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))  # adds the app folder to path, all relative imports made w/ that

import streamlit as st
import json
import folium
from streamlit_folium import st_folium, folium_static

from app.helpers.helpers import *

page_selection = st.sidebar.radio('Type:', ['Reinforce Existing', 'Build New'])

@st.cache(allow_output_mutation=True)  # required to allow caching for large objects, need to be careful about mutations now
def load_data():
    with open('../results/bus_ttt_contributions.json', 'r') as fileobj:
        bus_metrics = json.load(fileobj)
    
    with open('../data/service_no_dict.json', 'r') as fileobj:
        full_bus_info = json.load(fileobj)
    
    return bus_metrics, full_bus_info

bus_metrics, full_bus_info = load_data()

def reinforce_page():
    st.title('Reinforcing Existing Architecture')
    st.subheader('Overloaded Buses:')
    st.markdown('The following tables show top 10 most overloaded bus services by our metrics.')
    st.markdown('Note that TTT stands for **Total Travel Time**, i.e. the sum total time spent traveling by all travellers daily (on average).')

    col1, col2 = st.columns(2)
    loaded_buses = []
    with col1:
        temp_df = get_sorted_table(bus_metrics, 'ttt_contribution').rename(columns={'ttt_contribution':'TTT (s)'})
        st.dataframe(temp_df, use_container_width=True)
    with col2:
        temp_df = get_sorted_table(bus_metrics, 'ttt_pm').rename(columns={'ttt_pm':'TTT per meter (s/m)'})
        loaded_buses = list(temp_df['Service No.'])
        st.dataframe(temp_df, use_container_width=True)
    
    st.subheader('Overloaded Routes:')
    temp_fig = get_suggested_reinforcements_map(loaded_buses, full_bus_info)
    st_folium(temp_fig, width=1200, height=600)

def new_infra_page():
    st.title('Recommended New Links')
    st.markdown('The following map shows the recommended new links to be built based on our algorithm:')

if page_selection == 'Reinforce Existing':
    reinforce_page()
else:
    new_infra_page()