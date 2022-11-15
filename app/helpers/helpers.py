import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import folium

def get_sorted_table(metric_dict, metric, topk=10):
    records = [{'Service No.':k, metric:v[metric]} for k, v in metric_dict.items()]
    temp_df = pd.DataFrame.from_records(records)
    temp_df.sort_values(metric, ascending=False, ignore_index=True, inplace=True)
    return temp_df.iloc[:topk, :]

def get_route_coords(stops, stop_details):
    coords = []
    names = []
    for stop in stops:
        coords.append([stop_details[stop]['Latitude'], stop_details[stop]['Longitude']])
        names.append(stop_details[stop]['Description'])
    return coords, names

def get_suggested_reinforcements_map(busnos, full_bus_info):
    fig = folium.Figure(height=600,width=1200)
    map = folium.Map(location=[1.36, 103.83], zoom_start=11.5, tiles='cartodbpositron', zoomSnap=0.5)
    fig.add_child(map)

    color_options = px.colors.sample_colorscale('Reds', np.linspace(0.4, 0.8, len(busnos)))
    for i, busno in enumerate(busnos[::-1]):
        temp_coords, temp_names = get_route_coords(full_bus_info[busno]['busstop'], full_bus_info[busno]['busstop_info'])
        temp_f = folium.FeatureGroup(f"Service No. {busno}")
        folium.vector_layers.PolyLine(temp_coords, tooltip=f"Service No. {busno}", color=color_options[i], weight=3).add_to(temp_f)
        temp_f.add_to(map)
        for j in range(len(temp_coords)):
            folium.Circle(location=temp_coords[j], color='black', radius=20, weight=0.7, 
                        fillcolor='black', fill=True, fill_opacity=0.7, tooltip=temp_names[j]).add_to(map)
    return fig

