import streamlit as st
import pandas as pd
import numpy as np
import json
from math import floor, ceil
import folium
from folium import Marker
from folium.plugins import MarkerCluster, HeatMap
from jinja2 import Template
from streamlit_folium import st_folium, folium_static
from neo4j import GraphDatabase

driver = GraphDatabase.driver("neo4j+s://7be14e4d.databases.neo4j.io", auth=("neo4j", "Wm9lnnu0db4fD_g9IOAf67zKNk8O6mCrpgk7lq2j3uI"))

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

# Filter nodes by planning area for node link visualization
@st.cache(allow_output_mutation=True) 
def filter_by_planning_area(transport_graph,planningAreaFilter,bus_info):
    nodes_data = transport_graph['nodes']
    filter_nodes = []
    filter_links = []

    for i in nodes_data:
        if(i['planningArea'] == planningAreaFilter):
            filter_nodes.append(i['id'])
    links_data = transport_graph['links']
    for link in links_data:
        try:
            if(link['source'] in filter_nodes or link['target'] in filter_nodes):
                filter_links.append(((bus_info[link['source']]['Latitude'],bus_info[link['source']]['Longitude']),(bus_info[link['target']]['Latitude'],bus_info[link['target']]['Longitude'])))
        except:
            pass
    
    return filter_links

# Query get nodes in planning area
def query_planningArea(planningArea):
    query = ("""
    MATCH (n1),(n2) MATCH (n1)-[r]-(n2) 
    WHERE n1.planningArea = '"""+planningArea+"""' OR n2.planningArea = '"""+planningArea+"""'
    RETURN n1.latitude,n1.longitude, n2.latitude,n2.longitude
    """)
    result = run_query(query)
    res = [((i['n1.latitude'], i['n1.longitude']), (i['n2.latitude'], i['n2.longitude'])) for i in result]
    return res

st.title('Data Analysis')

### Map 1: marker cluster of average deficit

map = folium.Map(location=[1.36, 103.83], zoom_start=11.5, tiles = 'cartodbpositron')

f = open('../data/new_bus_transport_graph_new_dist.json')
data = json.load(f)
marker_data = data['nodes']

feature = 'deficit'
st.write("feature = " + feature)
marker_cluster = MarkerCluster(icon_create_function=icon_create_function(feature))

for marker_item in marker_data:
    marker = MarkerWithProps(
        location=[marker_item['latitude'],marker_item['longitude']],
        props = {feature: marker_item[feature]}
    )
    marker.add_to(marker_cluster)

marker_cluster.add_to(map)    

st_folium(map, width=1200, height=600)


### Map 2: heatmap of population estimation

feature = 'pop_estimate'
st.write("feature = " + feature)

new_feat = []
for i in marker_data:
    new_feat.append([i['latitude'],i['longitude'],i[feature]])
new_feat = pd.DataFrame(new_feat)
heat_data = new_feat.values.tolist()

m=folium.Map([1.36, 103.83],zoom_start=11.5,tiles="cartodbpositron")
hm = HeatMap(heat_data,gradient={0.1: 'blue', 0.3: 'lime', 0.5: 'yellow', 0.7: 'orange', 1: 'red'}, 
                min_opacity=0.05, 
                max_opacity=0.9, 
                radius=25,
                use_local_extrema=False).add_to(m)

st_folium(m, width=1200, height=600)


### Map 3: node link graph with area filtering

planning_areas = get_planning_areas()

st.session_state.disabled = 0
options = st.multiselect(
        'Select Planning area',
        planning_areas,
        planning_areas[1],
        max_selections=1,
        disabled=st.session_state.disabled)

try:
    if(st.session_state.disabled == 0):
        st.write('You selected:', options[0])
    area_selected = options[0]
    # index = data[data['name']==name_selected].index[0]
    index = planning_areas.index(area_selected)
    planningAreaFilter = planning_areas[index]
except:
    st.write("You haven't chosen an option")
    name_selected = ''
    index = None


if(index is not None):
    filter_links = query_planningArea(planningAreaFilter)
    base=folium.Map([1.36, 103.83],zoom_start=11.5,tiles="cartodbpositron")
    for i in range(len(filter_links)):
        # for pos_lat_long in bus_stops:
        #     # print("printing:",pos_lat_long)
        folium.PolyLine(
                filter_links[i], # tuple of coordinates 
                # color = color_dict[inperiod[i]], # map each segment with the speed 
                # colormap = color_dict, # map each value with a color 
                ).add_to(base)
            # print(pos_lat_long)
    st_folium(base, width=1200, height=600)



driver.close()