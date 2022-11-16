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

# @st.cache(allow_output_mutation=True)
# def main():
st.title('Data Analysis')

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

map = folium.Map(location=[1.36, 103.83], zoom_start=11.5, tiles = 'cartodbpositron')
marker_data =(
    {
        'lat':40.67,
        'lon':-73.94,
        'population': 200     
    },
    {
        'lat':44.67,
        'lon':-73.94,
        'population': 300     
    }
)

# def read_json(file_path):
# f = open('../data/new_bus_transport_graph_new_dist.json')
# data = json.load(f)
@st.cache(allow_output_mutation=True) 
def read_json(file_path):
    f = open(file_path)
    data = json.load(f)
    f.close()
    return data

@st.cache(allow_output_mutation=True) 
def load_all_data():
    transport_graph = read_json("../data/new_bus_transport_graph_new_dist.json")
    bus_stop = read_json('../data/bus_stop_full_info.json')

    return transport_graph,bus_stop

data,bus_stops = load_all_data()


# data = read_json("../data/new_bus_transport_graph_new_dist.json")

# f = open('../data/bus_stop_full_info.json')
# bus_stops = json.load(f)
marker_data = data['nodes']

# def icon_create_function(feat):
#     feature = """
#         function(cluster) {
#             var markers = cluster.getAllChildMarkers();
#             var sum = 0;
#             for (var i = 0; i < markers.length; i++) {
#                 sum += markers[i].options.props.
#                 """ + feat + """;
#             }
#             var avg = sum/cluster.getChildCount();
#             avg = avg.toFixed(2);

#             return L.divIcon({
#                 html: '<b>' + avg + '</b>',
#                 className: 'marker-cluster marker-cluster-small',
#                 iconSize: new L.Point(20, 20)
#             });
#         }
#     """
#     return feature

# feature = 'deficit'
# st.write("feature = " + feature)
# marker_cluster = MarkerCluster(icon_create_function=icon_create_function(feature))

# for marker_item in marker_data:
#     marker = MarkerWithProps(
#         location=[marker_item['latitude'],marker_item['longitude']],
#         props = {feature: marker_item[feature]}
#     )
#     marker.add_to(marker_cluster)

# marker_cluster.add_to(map)    

# st_folium(map, width=1200, height=600)


# feature = 'pop_estimate'
# st.write("feature = " + feature)

# new_feat = []
# for i in marker_data:
#     new_feat.append([i['latitude'],i['longitude'],i[feature]])
# new_feat = pd.DataFrame(new_feat)
# heat_data = new_feat.values.tolist()

# m=folium.Map([1.36, 103.83],zoom_start=11.5,tiles="cartodbpositron")
# hm = HeatMap(heat_data,gradient={0.1: 'blue', 0.3: 'lime', 0.5: 'yellow', 0.7: 'orange', 1: 'red'}, 
#                 min_opacity=0.05, 
#                 max_opacity=0.9, 
#                 radius=25,
#                 use_local_extrema=False).add_to(m)

# st_folium(m, width=1200, height=600)

# period_selection = st.sidebar.radio('Period:', ['AM_Offpeak_Freq', 'AM_Peak_Freq', 'PM_Offpeak_Freq', 'PM_Peak_Freq'])

# line_data = data['links']

# def process_lat_longs(line_data,bus_stops):
#     pos = []
#     period = []
#     for i in line_data:
#         try:
#             source = bus_stops[i['source']]
#             target = bus_stops[i['target']]
#             pos.append(((source['Latitude'], source['Longitude']),(target['Latitude'], target['Longitude'])))
#             # print(pos[-1])
#             period.append(i[period_selection])
#         except:
#             pass

#     return pos,period

# pos,period=process_lat_longs(line_data,bus_stops)


# values = st.sidebar.slider(
#      'Select frequency range:',
#      floor(min(period)), ceil(np.percentile(period, 95)), (floor(min(period)), ceil(np.percentile(period, 95))))


# inperiod = [True if (i >= values[0] and i <= values[1]) else False for i in period]
# color_dict = {True:'#17becf', False:'#D3D3D3'}

# base=folium.Map([1.36, 103.83],zoom_start=11.5,tiles="cartodbpositron")
# for i in range(len(pos)):
#     # for pos_lat_long in bus_stops:
#     #     # print("printing:",pos_lat_long)
#     folium.PolyLine(
#             pos[i], # tuple of coordinates 
#             color = color_dict[inperiod[i]], # map each segment with the speed 
#             # colormap = color_dict, # map each value with a color 
#             ).add_to(base)
#         # print(pos_lat_long)
# st_folium(base, width=1200, height=600)

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

@st.cache(allow_output_mutation=True) 
def get_planning_areas(transport_graph):
    planning_areas = []
    for i in transport_graph['nodes']:
        planning_areas.append(i['planningArea'])
    return list(set(planning_areas))

planning_areas = get_planning_areas(data)

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
    filter_links = filter_by_planning_area(data,planningAreaFilter,bus_stops)
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