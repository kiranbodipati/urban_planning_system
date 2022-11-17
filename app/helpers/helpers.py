import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import plotly.express as px
# from plotly.subplots import make_subplots
import folium
import re
from neo4j import GraphDatabase
import tqdm as tqdm

def get_sorted_table(metric_dict, metric, topk=10):
    records = [{'Service No.':k, metric:v[metric]} for k, v in metric_dict.items()]
    temp_df = pd.DataFrame.from_records(records)
    temp_df.sort_values(metric, ascending=False, ignore_index=True, inplace=True)
    return temp_df.iloc[:topk, :]

def get_route_coords(stops, stop_details):
    coords = []
    names = []
    for stop in stops:
        try:
            coords.append([stop_details[stop]['Latitude'], stop_details[stop]['Longitude']])
            names.append(stop_details[stop]['Description'])
        except:
            continue
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

def get_top_links_map(top_links_df, full_stop_info, topk):
    fig = folium.Figure(height=600,width=1200)
    map = folium.Map(location=[1.36, 103.83], zoom_start=11.5, tiles='cartodbpositron', zoomSnap=0.5)
    fig.add_child(map)
    color_options = px.colors.sample_colorscale('Reds_r', np.linspace(0.2, 0.6, topk))
    for i, row in top_links_df.iterrows():
        if i==topk:
            break
        n1, n2 = re.findall("[0-9]+", row['pair'])
        try:
            temp_coords, temp_names = get_route_coords([n1, n2], full_stop_info)
            temp_f = folium.FeatureGroup(f"Pred score: {row['prob']}")
            folium.vector_layers.PolyLine(temp_coords, tooltip=f"Pred score: {row['prob']}", color=color_options[i], weight=3).add_to(temp_f)
        except:
            continue
        temp_f.add_to(map)
        for j in range(len(temp_coords)):
            try:
                folium.Circle(location=temp_coords[j], color='black', radius=20, weight=0.7, 
                        fillcolor='black', fill=True, fill_opacity=0.7, tooltip=temp_names[j]).add_to(map)
            except:
                continue
    return fig

def plot_hist_percentiles_bus(busno, bus_ttt_contributions, metrics=['ttt_contribution', 'ttt_pm', 'num_routes', 'trips_influenced']):
    params = {
        "text.color" : "w",
        "ytick.color" : "w",
        "xtick.color" : "w",
        "axes.labelcolor" : "w",
        "axes.edgecolor" : "w"
    }
    mpl.rcParams.update(params)
    fig, ax = plt.subplots(len(metrics), figsize=(12, 8))
    fig.patch.set_alpha(0)
    for i, metric in enumerate(metrics):
        full_list = sorted([v[metric] for v in bus_ttt_contributions.values()], reverse=True)
        pos = full_list.index(bus_ttt_contributions[busno][metric])
        perc = round((1 - pos/len(full_list))*100, 2)
        ax[i].hist(full_list, bins=20, color='coral')
        ax[i].axvline(bus_ttt_contributions[busno][metric], color='white')
        ax[i].set_title(f"Ranked #{pos+1} for {metric} - {perc}%ile")
        ax[i].set_xlim((0, full_list[int(len(full_list)*0.01)]))
        ax[i].patch.set_alpha(0)
    fig.tight_layout()
    return fig


def get_link_predictions(model, model_type, new_link_feat, multiplier):
    new_link_feat['n1_avg_flow']=new_link_feat.n1_avg_flow.mul(multiplier)
    new_link_feat['n1_pop_estimate']=new_link_feat.n1_pop_estimate.mul(multiplier)
    new_link_feat['n2_pop_estimate']=new_link_feat.n2_pop_estimate.mul(multiplier)
    new_link_feat['n2_avg_flow']=new_link_feat.n2_avg_flow.mul(multiplier)
    if model_type==1:
        pred_df_cols=new_link_feat[['dist_m', 'n1_latitude', 'n1_longitude', 'n2_latitude', 'n2_longitude', 'n1_pop_estimate', 'n2_pop_estimate']]
    elif model_type==2:
        pred_df_cols=new_link_feat[['dist_m', 'n1_latitude', 'n1_longitude', 'n2_latitude', 'n2_longitude', 'n1_avg_flow', 'n2_avg_flow']]
    elif model_type==3:
        pred_df_cols=new_link_feat[['dist_m', 'n1_pop_estimate', 'n2_pop_estimate']]
    elif model_type==4:
        pred_df_cols=new_link_feat[['dist_m', 'n1_avg_flow', 'n2_avg_flow']]
    prediction_probs=model.predict_proba(pred_df_cols)
    output_df=pd.DataFrame({'pair':new_link_feat["pair"], 'prob':prediction_probs[:,1]})
    output_df.sort_values(by=["prob"], ascending=False, inplace=True, ignore_index=True)
    output_df=output_df[:1000]
    return output_df

driver = GraphDatabase.driver("neo4j+s://7be14e4d.databases.neo4j.io", auth=("neo4j", "Wm9lnnu0db4fD_g9IOAf67zKNk8O6mCrpgk7lq2j3uI"))
def get_planning_areas():
    query = """
    MATCH (n) 
    RETURN DISTINCT n.planningArea
    """
    result = run_query(query)
    res = [i['n.planningArea'] for i in result]
    return res

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return result.data()

def query_planningArea(planningArea):
    ## period = ['AM_Offpeak_Freq', 'AM_Peak_Freq', 'PM_Offpeak_Freq', 'PM_Peak_Freq']
    if planningArea:
        query = ("""
        MATCH (n1),(n2) MATCH (n1)-[r]-(n2) 
        WHERE n1.planningArea IN """+str(planningArea)+""" OR n2.planningArea IN """+str(planningArea)+"""
        RETURN n1.busstop_id, n2.busstop_id""")
        
    else:
        query = ("""
        MATCH (n1),(n2) MATCH (n1)-[r]-(n2) 
        RETURN n1.busstop_id, n2.busstop_id""")
    result = run_query(query)
    res = []
    for i in result:
        res.extend([i['n1.busstop_id'],i['n2.busstop_id']])
    return res

def process_new_links_features(res,new_links_feat,multiplier=1):
    link_feat_copy = new_links_feat.copy()
    for i in (range(len(link_feat_copy))):
        if(link_feat_copy.iloc[i]['pair'][0] in res):
            link_feat_copy.iloc[i]['n1_pop_estimate'] = link_feat_copy.iloc[i]['n1_pop_estimate']*multiplier
            link_feat_copy.iloc[i]['n1_avg_flow'] = link_feat_copy.iloc[i]['n1_avg_flow']*multiplier
        if(link_feat_copy.iloc[i]['pair'][1] in res):
            link_feat_copy.iloc[i]['n2_pop_estimate'] = link_feat_copy.iloc[i]['n2_pop_estimate']*multiplier
            link_feat_copy.iloc[i]['n2_avg_flow'] = link_feat_copy.iloc[i]['n2_avg_flow']*multiplier
            
    return link_feat_copy

driver.close()

# def plot_hist_percentiles_bus(busno, bus_ttt_contributions, metrics=['ttt_contribution', 'ttt_pm', 'num_routes', 'trips_influenced']):
#     temp_df = pd.DataFrame()
#     for metric in metrics:
#         temp_df[metric] = [v[metric] for v in bus_ttt_contributions.values()]
#     fig = make_subplots(rows=len(metrics), cols=1, specs=[[{'type': 'histogram'}]]*len(metrics))
#     for i, metric in enumerate(metrics):
#         full_list = sorted([v[metric] for v in bus_ttt_contributions.values()], reverse=True)
#         pos = full_list.index(bus_ttt_contributions[busno][metric])
#         perc = round((1 - pos/len(full_list))*100, 2)
#         # ax[i].hist([i[metric] for i in bus_ttt_contributions.values()], bins=20)
#         # ax[i].axvline(bus_ttt_contributions[busno][metric], color='black')
#         # ax[i].set_title(f"Ranked #{pos+1} for {metric} - {perc}%ile")
#         fig.add_trace(px.histogram(temp_df, metric, nbins=20), row=i+1, col=1)
#     # fig.tight_layout()
#     return fig
