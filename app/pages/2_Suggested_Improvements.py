from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))  # adds the app folder to path, all relative imports made w/ that

import streamlit as st
import json
import folium
from streamlit_folium import st_folium, folium_static
import pickle
import networkx as nx

from app.helpers.helpers import *

st.set_page_config(layout="wide")

tab1, tab2, tab3, tab4 = st.tabs(['Bus Load Analysis', 'Reinforce Existing Routes', 'Build New Links', 'TEMP: MRT/LRT Analysis'])

@st.cache(allow_output_mutation=True)  # required to allow caching for large objects, need to be careful about mutations now
def load_data():
    with open('../results/bus_ttt_contributions.json', 'r') as fileobj:
        bus_metrics = json.load(fileobj)
    
    with open('../data/service_no_dict.json', 'r') as fileobj:
        full_bus_info = json.load(fileobj)
    
    with open('../data/bus_stop_full_info.json', 'r') as fileobj:
        full_stop_info = json.load(fileobj)
        
    with open('../results/model1.pkl', 'rb') as fileobj:
        model1 = pickle.load(fileobj)
    
    with open('../results/model2.pkl', 'rb') as fileobj:
        model2 = pickle.load(fileobj)
    
    with open('../results/model3.pkl', 'rb') as fileobj:
        model3 = pickle.load(fileobj)
    
    with open('../results/model4.pkl', 'rb') as fileobj:
        model4 = pickle.load(fileobj)
    
    with open('../results/train_daily_traveler_stops.json', 'r') as fileobj:
        daily_train_traveler_stops = json.load(fileobj)
    
    with open('../results/train_daily_travelers.json', 'r') as fileobj:
        daily_train_travelers = json.load(fileobj)
    
    with open('../results/trains_graph_num_travelers.json', 'r') as fileobj:
        json_graph = json.load(fileobj)
        G_train = nx.readwrite.node_link_graph(json_graph)
    
    new_link_features =pd.read_csv('../data/new_link_features.csv')
    
    return bus_metrics, full_bus_info, full_stop_info, new_link_features, model1, model2, model3, model4, daily_train_traveler_stops, daily_train_travelers, G_train

bus_metrics, full_bus_info, full_stop_info,new_link_features, model1, model2, model3, model4, daily_train_traveler_stops, daily_train_travelers, G_train = load_data()

#---------------------------------------------------------------------------------------------------------------------------------------------------------------

def load_analysis_page():
    st.title('Bus-wise Load Analysis')
    st.markdown('Select a service no. to view its position in across various metrics')
    busno = st.selectbox("Service No.:", bus_metrics.keys())
    temp_fig = plot_hist_percentiles_bus(busno, bus_metrics)
    st.pyplot(temp_fig)
    # st.plotly_chart(temp_fig)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

def reinforce_page():
    st.title('Reinforcing Existing Architecture')
    st.subheader('Top 10 Overloaded Buses')
    st.markdown('The following tables show top 10 most overloaded bus services by our metrics.')
    st.markdown('Note that TTT stands for **Total Travel Time**, i.e. the sum total time spent traveling by all travellers daily (on average).')

    col1, col2 = st.columns(2)
    loaded_buses = [[], [], []]
    with col1:
        temp_df = get_sorted_table(bus_metrics, 'ttt_contribution').rename(columns={'ttt_contribution':'TTT (s)'})
        loaded_buses[1] = list(temp_df['Service No.'])
        st.dataframe(temp_df, use_container_width=True)
    with col2:
        temp_df = get_sorted_table(bus_metrics, 'ttt_pm').rename(columns={'ttt_pm':'TTT per meter (s/m)'})
        loaded_buses[0] = list(temp_df['Service No.'])
        st.dataframe(temp_df, use_container_width=True)
    
    loaded_buses[2] = list(get_sorted_table(bus_metrics, 'trips_influenced')['Service No.'])
    st.subheader('Top 10 Overloaded Bus Routes')
    display_options = ['Distance-Normalized Total Travel Time (TTT/m)', 'Total Travel Time (TTT)', 'No. of Daily Trips']
    map_metric = st.selectbox('Display by metric:', np.arange(len(display_options)), format_func=lambda x: display_options[x])
    temp_fig = get_suggested_reinforcements_map(loaded_buses[map_metric], full_bus_info)
    st_folium(temp_fig, width=1200, height=600)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

def recommend_links(key1=1, key2=2):
    model_keys=['Distance, Location and Population Estimate', 'Distance, Location and Average Flow', 'Distance and Population Estimate','Distance and Average Flow']
    models=[model1, model2, model3, model4]
    model_metric= st.selectbox("Select how to optimise predictions", range(len(model_keys)), format_func=lambda x: model_keys[x], key=key1)
    
    new_links_df=get_link_predictions(models[model_metric], model_metric+1, new_link_features)
    topk = st.slider('Number of top links:', 0, 1000, 100, key=key2)
    temp_fig = get_top_links_map(new_links_df, full_stop_info, topk)
    st_folium(temp_fig, width=1200, height=600)

def new_infra_page():
    st.title('Recommended New Links')
    st.markdown('The following map shows the recommended new links to be built based on our algorithm:')
    compare=st.checkbox('Compare Models')
    col1, col2 = st.columns(2)
    if compare:
        with col1:
            recommend_links(1,2)
        with col2:
            recommend_links(3,4)
    else:
        recommend_links()
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

def train_analysis_page():
    st.title('Analysis of MRT/LRT Routes')
    st.markdown('The following bar plots show the number of travelers and traveler-stops per day on average.')
    st.markdown('Traveler-Stops is the sum of total stops traveled by in each unique trip in a day. It is proportional to man-days spent traveling on MRTs everyday.')

    col1, col2 = st.columns(2)
    with col1:
        temp_fig = get_sorted_bar_plot(daily_train_travelers, 'Daily No. of Travelers')
        st.plotly_chart(temp_fig, use_container_width=True)
    with col2:
        temp_fig = get_sorted_bar_plot(daily_train_traveler_stops, 'Daily Avg. Traveler-Stops')
        st.plotly_chart(temp_fig, use_container_width=True)
    
    st.subheader('MRT/LRT Flow Graph')
    temp_fig = get_train_routes_map(G_train)
    st_folium(temp_fig, width=1200, height=600)


with tab1:
    load_analysis_page()
with tab2:
    reinforce_page()
with tab3:
    new_infra_page()
with tab4:
    train_analysis_page()