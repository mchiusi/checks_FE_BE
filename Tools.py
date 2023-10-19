import numpy as np
import pandas as pd
import ast
import plotly.express as px
import plotly.graph_objects as go

import xml.etree.ElementTree as ET

def convert_to_float_list(string):
    return [float(num) for num in ast.literal_eval(string)]

def prepare_geometry():
    geometry = pd.read_csv('geometry/module_MB_geometry.csv')
    geometry['hex_x'] = geometry['hex_x'].apply(convert_to_float_list)
    geometry['hex_y'] = geometry['hex_y'].apply(convert_to_float_list)
    return geometry

def colorscale(df, variable, scale):
    if variable=='MB':
        df[variable] = df[variable].rank(method='dense').astype(int) - 1
    norm_points = (df[variable]-df[variable].min())/(0.1+df[variable].max()-df[variable].min())
    colorscale = px.colors.sample_colorscale(scale, norm_points)
    colorscale = ['rgb(255, 255, 255)' if value == 'rgb(48, 18, 59)' else value for value in colorscale]
    return colorscale

def plot_modules(df,variable):
    if variable=='trigLinks':
        df['Color'] = colorscale(df, 'trigLinks', 'Viridis')
    else:
        df['Color'] = colorscale(df, 'MB', 'Turbo')
    array_data = df[['hex_x','hex_y','Color','u','v','MB','TriggerLpGbts']].to_numpy()
    listmodule = []
    annotations = []
    for j,i in enumerate(array_data):
        x1 = np.append(i[0],i[0][0])
        y1 = np.append(i[1],i[1][0])
        datum = go.Scatter(x=-x1, y=y1, mode="lines",fill='toself', fillcolor=i[2],
                           line_color='black',marker_line_color="black",
                           text='(u,v)=('+str(i[3])+','+str(i[4])+')'+'<br>'+' MB: '+str(i[5]))
        listmodule.append(datum)
        annotations.append(go.layout.Annotation(x=-sum(x1[:-1])/6, y=sum(y1[:-1])/6,
                                    text='MB:'+str(i[5])+'<br>'+'lpGBT:'+str(int(i[6])), 
                                    showarrow=False,font=dict(color='black')))
        
    return listmodule, annotations

def set_figure(scatter, annotations, local_plane, section):
    layer = local_plane if section == '0' else (str(int(local_plane) + 27) if section != '3' else '999')
    fig = go.Figure(scatter)
    fig.update_layout(width=800, height=900)
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_xaxes(showline=False, showticklabels=False)
    fig.update_yaxes(showline=False, showticklabels=False)

    fig.update_layout(annotations=annotations, showlegend=False,
                 title='Display layer '+layer)
    #if layer=='3':
    fig.write_image("layer"+layer+"_MB_60sector.pdf")
    fig.write_image("layer"+str(layer)+"_MB_60sector.png")

def extract_module_info_from_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    data_list = []
    for plane in root.findall(".//Plane"):
        plane_id = plane.get('id')
        for motherboard in plane.findall(".//Motherboard"):
            for module in motherboard.findall(".//Module"):
                data_list.append({
                    'plane' : int(plane_id),
                    'Module': str(int(module.get('id'))),
                    'u': int(module.get('u')),
                    'v': int(module.get('v'))
                })

    df = pd.DataFrame(data_list)
    return df

