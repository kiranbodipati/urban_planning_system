from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))  # adds the app folder to path, all relative imports made w/ that

import streamlit as st
import json
import folium
from streamlit_folium import st_folium, folium_static
from neo4j import GraphDatabase
import pickle
import networkx as nx

from app.helpers.helpers import *

def load_data():
    with open('../results/train_daily_traveler_stops.json', 'r') as fileobj:
        daily_train_traveler_stops = json.load(fileobj)
    
    with open('../results/train_daily_travelers.json', 'r') as fileobj:
        daily_train_travelers = json.load(fileobj)
    
    with open('../results/trains_graph_num_travelers.json', 'r') as fileobj:
        json_graph = json.load(fileobj)
        G_train = nx.readwrite.node_link_graph(json_graph)
    
    return daily_train_traveler_stops, daily_train_travelers, G_train

daily_train_traveler_stops, daily_train_travelers, G_train = load_data()

def train_analysis_page():
    st.title('Analysis of MRT/LRT Routes')
    st.markdown('The following bar plots show the average number of travelers per day and number of stops traveled.')
    # st.markdown('Traveler-Stops is the sum of total stops traveled by in each unique trip in a day. It is proportional to man-days spent traveling on MRTs everyday.')

    col1, col2 = st.columns(2)
    with col1:
        temp_fig = get_sorted_bar_plot(daily_train_travelers, 'Daily No. of Travelers')
        st.plotly_chart(temp_fig, use_container_width=True)
    with col2:
        temp_dict = {}
        for i in daily_train_traveler_stops.keys():
            temp_dict[i] = daily_train_traveler_stops[i]/daily_train_travelers[i]
        temp_fig = get_sorted_bar_plot(temp_dict, 'Avg. Stops Traveled')
        st.plotly_chart(temp_fig, use_container_width=True)
    
    st.subheader('MRT/LRT Flow Graph')
    temp_fig = get_train_routes_map(G_train)
    st_folium(temp_fig, width=1200, height=600)

train_analysis_page()