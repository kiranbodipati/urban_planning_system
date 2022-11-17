import streamlit as st
import pandas as pd
import numpy as np
import json
from math import floor, ceil
from statistics import median
import folium
from folium import Marker
from folium.plugins import MarkerCluster, HeatMap
from jinja2 import Template
from streamlit_folium import st_folium, folium_static
from neo4j import GraphDatabase
import branca.colormap
from collections import defaultdict

driver = GraphDatabase.driver("neo4j+s://7be14e4d.databases.neo4j.io", auth=("neo4j", "Wm9lnnu0db4fD_g9IOAf67zKNk8O6mCrpgk7lq2j3uI"))
st.set_page_config(layout='wide')

# Create nodes with props for marker cluster map
class MarkerWithProps(Marker):
    _template = Template(u"""
        {% macro script(this, kwargs) %}
        var {{this.get_name()}} = L.marker(
            [{{this.location[0]}}, {{this.location[1]}}],
            {
                icon: new L.Icon.Default(),
                {%- if this.draggable %}
                draggable: true,
                autoPan: true,
                {%- endif %}
                {%- if this.props %}
                props : {{ this.props }} 
                {%- endif %}
                }
            )
            .addTo({{this._parent.get_name()}});
        {% endmacro %}
        """)
    def __init__(self, location, popup=None, tooltip=None, icon=None,
                draggable=False, props = None ):
        super(MarkerWithProps, self).__init__(location=location,popup=popup,tooltip=tooltip,icon=icon,draggable=draggable)
        self.props = json.loads(json.dumps(props))    

def icon_create_function(feat):
    feature = """
        function(cluster) {
            var markers = cluster.getAllChildMarkers();
            var sum = 0;
            for (var i = 0; i < markers.length; i++) {
                sum += markers[i].options.props.
                """ + feat + """;
            }
            var avg = sum/cluster.getChildCount();
            avg = avg.toFixed(2);

            return L.divIcon({
                html: '<b>' + avg + '</b>',
                className: 'marker-cluster marker-cluster-small',
                iconSize: new L.Point(20, 20)
            });
        }
    """
    return feature

# Run cql and return neo4j result
def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return result.data()

# Query returns all unique planning area
@st.cache(allow_output_mutation=True) 
def get_planning_areas():
    query = """
    MATCH (n) 
    RETURN DISTINCT n.planningArea
    """
    result = run_query(query)
    res = [i['n.planningArea'] for i in result]
    return res

# Query get nodes in planning area
def query_planningArea(planningArea, period):
    ## period = ['AM_Offpeak_Freq', 'AM_Peak_Freq', 'PM_Offpeak_Freq', 'PM_Peak_Freq']
    if planningArea:
        query = ("""
        MATCH (n1),(n2) MATCH (n1)-[r]-(n2) 
        WHERE n1.planningArea = '"""+planningArea+"""' OR n2.planningArea = '"""+planningArea+"""'
        RETURN n1.latitude,n1.longitude, n2.latitude, n2.longitude, r."""+period)
    else:
        query = ("""
        MATCH (n1),(n2) MATCH (n1)-[r]-(n2) 
        RETURN n1.latitude,n1.longitude, n2.latitude, n2.longitude, r."""+period)
    result = run_query(query)
    res = [((i['n1.latitude'], i['n1.longitude']), (i['n2.latitude'], i['n2.longitude'])) for i in result]
    freq_in_period = [i['r.'+period] for i in result]
    return res, freq_in_period

# Query get deficit and population estimate
def query_deficit_pop():
    query = ("""
    MATCH (n) 
    RETURN n.latitude,n.longitude, n.deficit, n.pop_estimate""")
    result = run_query(query)

    return result
    
def get_zoom_loc(planningArea):
    query = ("""
        MATCH (n) 
        WHERE n.planningArea = '"""+planningArea+"""' 
        RETURN n.latitude, n.longitude""")
    result = run_query(query)
    lat = [i['n.latitude'] for i in result]
    lon = [i['n.longitude'] for i in result]

    return median(lat), median(lon)


st.title('Data Analysis')
st.markdown("""---""")

space1, map1, space2, map2, space3 = st.columns([0.5, 5, 0.5, 5, 0.5])
marker_data = query_deficit_pop()

planning_areas = get_planning_areas()

st.session_state.disabled = 0
options = st.sidebar.selectbox('Select Planning area',planning_areas)

zoom_lat, zoom_lon = get_zoom_loc(options)
period_selection = st.sidebar.radio('Period:', ['AM_Offpeak_Freq', 'AM_Peak_Freq', 'PM_Offpeak_Freq', 'PM_Peak_Freq'])

try:
    area_selected = options
    index = planning_areas.index(area_selected)
    planningAreaFilter = planning_areas[index]
except:
    st.write("You haven't chosen an option")
    name_selected = ''
    index = None

with map1:
    st.markdown('Deficit heatmap')
    new_feat = []
    for i in marker_data:
        new_feat.append([i['n.latitude'],i['n.longitude'],i['n.deficit']])
    new_feat = pd.DataFrame(new_feat)
    new_feat.columns = ['lat', 'lon', 'def']
    # new_feat['def'] = [(float(i)-min(new_feat['def']))/(max(new_feat['def'])-min(new_feat['def'])) for i in new_feat['def']]
    heat_data = new_feat.values.tolist()

    m=folium.Map([zoom_lat, zoom_lon],zoom_start=12,tiles="cartodbpositron")

    steps=20
    colormap = branca.colormap.linear.YlOrRd_09.scale(0, 1).to_step(steps)
    gradient_map=defaultdict(dict)
    for i in range(steps):
        gradient_map[1/steps*i] = colormap.rgb_hex_str(1/steps*i)
    colormap.add_to(m) #add color bar at the top of the map

    hm = HeatMap(heat_data,gradient={0.1: 'blue', 0.3: 'lime', 0.5: 'yellow', 0.7: 'orange', 1: 'red'}, 
                    min_opacity=0.05, 
                    max_opacity=0.9, 
                    radius=25,
                    use_local_extrema=False).add_to(m)
    st_folium(m, width=500, height=400)

### Map 2: heatmap of population estimation
with map2:
    st.markdown('Population estimation heatmap')
    new_feat = []
    for i in marker_data:
        new_feat.append([i['n.latitude'],i['n.longitude'],i['n.pop_estimate']])
    new_feat = pd.DataFrame(new_feat)
    heat_data = new_feat.values.tolist()

    m=folium.Map([zoom_lat, zoom_lon],zoom_start=12,tiles="cartodbpositron")
    steps=20
    colormap = branca.colormap.linear.YlOrRd_09.scale(0, 1).to_step(steps)
    gradient_map=defaultdict(dict)
    for i in range(steps):
        gradient_map[1/steps*i] = colormap.rgb_hex_str(1/steps*i)
    colormap.add_to(m) #add color bar at the top of the map

    hm = HeatMap(heat_data,gradient={0.1: 'blue', 0.3: 'lime', 0.5: 'yellow', 0.7: 'orange', 1: 'red'}, 
                    min_opacity=0.05, 
                    max_opacity=0.9, 
                    radius=25,
                    use_local_extrema=False).add_to(m)

    st_folium(m, width=500, height=400)

### Map 3: node link graph with area filtering

if(index is not None):
    filter_links, period = query_planningArea(planningAreaFilter, period_selection)
    values = st.sidebar.slider(
     'Select frequency range:',
     floor(min(period)), ceil(np.percentile(period, 95)), (floor(min(period)), ceil(np.percentile(period, 95))))
    inperiod = [True if (i >= values[0] and i <= values[1]) else False for i in period]
    color_dict = {True:'rgba(236, 90, 83, 1.0)', False:'rgba(128, 128, 128, 0.2)'}

    base=folium.Map([zoom_lat, zoom_lon],zoom_start=12.5,tiles="cartodbpositron")
    for i in range(len(filter_links)):
        # for pos_lat_long in bus_stops:
        #     # print("printing:",pos_lat_long)
        folium.PolyLine(
                filter_links[i], # tuple of coordinates 
                color = color_dict[inperiod[i]], # map each segment with the speed 
                colormap = color_dict, # map each value with a color 
                ).add_to(base)
            # print(pos_lat_long)
    st_folium(base, width=1200, height=600)

driver.close()