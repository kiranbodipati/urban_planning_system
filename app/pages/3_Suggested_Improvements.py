from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))  # adds the app folder to path, all relative imports made w/ that

import streamlit as st
import json
import folium
from streamlit_folium import st_folium, folium_static

import pickle

from app.helpers.helpers import *

st.set_page_config(layout='wide')


tab1, tab2, tab3 = st.tabs(['Bus Load Analysis', 'Reinforce Existing Routes', 'Build New Links'])

@st.cache(allow_output_mutation=True)  # required to allow caching for large objects, need to be careful about mutations now
def load_data():
    with st.spinner(text="Fetching the data for you..."):
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
    
    new_link_features =pd.read_csv('../data/new_link_features.csv')
    
    return bus_metrics, full_bus_info, full_stop_info, new_link_features,model1, model2, model3,model4

bus_metrics, full_bus_info, full_stop_info,new_link_features, model1, model2, model3, model4 = load_data()

#---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Run cql and return neo4j result
def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return result.data()

# Query get deficit and population estimate
def query_service_no(busno):
    query = ("""
    MATCH (n1),(n2) MATCH (n1)-[r]-(n2) 
    WHERE '"""+busno+"""' IN r.service_list
    RETURN n1.latitude,n1.longitude, n2.latitude,n2.longitude""")
    # print(query)
    result = run_query(query)
    res = [((i['n1.latitude'], i['n1.longitude']), (i['n2.latitude'], i['n2.longitude'])) for i in result]
    return res

def load_analysis_page():
    st.title('Bus-wise Load Analysis')
    st.markdown('Select a service no. to view its position in across various metrics')
    busno = st.selectbox("Service No.:", bus_metrics.keys())

    map1, hist1 = st.columns([0.8, 2.2])
    with hist1:
        temp_fig = plot_hist_percentiles_bus(busno, bus_metrics)
        st.pyplot(temp_fig)

    with map1:
        st.write('')
        filter_links = query_service_no(str(busno))
        base=folium.Map([1.36, 103.90],zoom_start=9.5,tiles="cartodbpositron")
        for i in range(len(filter_links)):
            folium.PolyLine(
                    filter_links[i], # tuple of coordinates 
                    # color = color_dict[inperiod[i]], # map each segment with the speed 
                    # colormap = color_dict, # map each value with a color 
                    ).add_to(base)
        st_folium(base, width=400, height=250)
        with st.expander("Service Metrics"):
            service_metrics = bus_metrics[str(busno)]
            st.metric('TTT contribution (man-days)',("{:.2f}".format(round(service_metrics['ttt_contribution']/86400,2))))
            st.metric('TTT per metre (man-days per meter)',("{:.2f}".format(round(service_metrics['ttt_pm']/86400,2))))
            st.metric('Unique routes',("{:.0f}".format(round(service_metrics['num_routes'],0))))
            st.metric('Daily trips',("{:.0f}".format(round(service_metrics['trips_influenced'],0))))

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

def recommend_links(key=1, w=1200, h=600):
    model_keys=['Distance, Location and Popularity Estimate', 'Distance, Location and Average Flow', 'Distance and Popularity Estimate','Distance and Average Flow']
    models=[model1, model2, model3, model4]
    model_metric= st.selectbox("Select how to optimise predictions", range(len(model_keys)), format_func=lambda x: model_keys[x], key=key)
    
    # planning_areas = get_planning_areas()
    # planning_area_list = st.multiselect(
    #     'Select List of Areas to ',
    #     planning_areas, key=key+1)
    # if planning_area_list!=[]:
    multiplier = st.slider('Select Popularity/Flow Multiplier', min_value=0.5, max_value=2.0, value=1.0, step=0.05, key=key+2)
    # nodes_planning_area = query_planningArea(planning_area_list)
    # new_link_features_processed = process_new_links_features(nodes_planning_area,new_link_features,multiplier)
    with st.spinner(text="Generating the predictions based on your settings..."):
        new_links_df=get_link_predictions(models[model_metric], model_metric+1, new_link_features.copy(), multiplier)
    
    topk = st.slider('Number of top links:', 0, 1000, 100, key=key+3)
    temp_fig = get_top_links_map(new_links_df, full_stop_info, topk)
    st_folium(temp_fig, width=w, height=h, key=key+4)

def new_infra_page():
    st.title('Recommended New Links')
    st.markdown('The following map shows some of the recommended new links to be built based on our algorithm:', expanded=True)
    with st.expander("What does this mean?"):
        st.caption("""
            The maps below give the predicted links that can be built betweem existing bus stops based on the settings provided by the user. The user can compare different link prediction models to analyse and build optimum links.
        """)
    compare=st.checkbox('Compare Models')
    col1, col2 = st.columns(2)
    if compare:
        with col1:
            recommend_links(1, 600, 400)
        with col2:
            recommend_links(10, 600, 400)
    else:
        recommend_links(20)


with tab1:
    load_analysis_page()
with tab2:
    reinforce_page()
with tab3:
    new_infra_page()
    
