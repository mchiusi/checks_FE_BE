import numpy as np
import pandas as pd
import math
import ast
import plotly.express as px
import plotly.graph_objects as go

import xml.etree.ElementTree as ET

def create_slices(radius, total_angle_degrees=120, offset=0):
    central_angle_degrees = total_angle_degrees / 84
    x_coordinates = []
    y_coordinates = []

    for i in range(offset,85):
        angle_degrees = i * central_angle_degrees
        angle_radians = math.radians(angle_degrees)
        x = radius * math.cos(angle_radians)
        y = radius * math.sin(angle_radians)
        x_coordinates.append([0, x])
        y_coordinates.append([0, y])

    return x_coordinates, y_coordinates

def get_MB_ids(region_id):
    MB_ids = []

    for region in regions:
        if region.id == region_id:
            MB_ids.extend(region.MBs.split(';'))
    return MB_ids

def extract_MB_plane_from_MBid(id):
    id_int = int(id, 16) # hexadecimal 'id' to integer

    MotherboardId = id_int & 0x1FFF  # binary: 0001 1111 1111 1111
    PlaneId = (id_int >> 13) & 0xFFFF

    return MotherboardId, PlaneId

def shift_dataframe(df, x_center, y_center):
    ''' operates the dataframe shift '''
    for i in range(len(df)):
        x_vertices = df['hex_x'].iloc[i]
        y_vertices = df['hex_y'].iloc[i]
        shifted_x = [x + x_center for x in x_vertices]
        shifted_y = [y + y_center for y in y_vertices]

        df['hex_x'].iloc[i] = shifted_x
        df['hex_y'].iloc[i] = shifted_y

def define_center(df, plane):
    ''' prepare the shift of each dataframe '''
    x_center = sum(df['hex_x'][(df.u == 3)&(df.v == 6)].iloc[0])/6
    if plane <= 32: y_center = sum(df['hex_y'][df['v'] == 0].iloc[0]) / 6
    elif plane > 32 and plane % 2 == 1: y_center = (df['hex_y'][df['v'] == 0].iloc[0])[0]
    else: y_center = (df['hex_y'][df['v'] == 1].iloc[0])[0]
    return x_center, -y_center

def convert_to_float_list(string):
    ''' to be used with the visualization geometry
        since float in csv become strings '''
    return [float(num) for num in ast.literal_eval(string)]

def prepare_geometry_txt():
    ''' old but working version, it reads the geometry 
        file from Pedro's txt '''
    geometry_file = 'geometry/geometry.hgcal.txt'
    geometry_df = pd.read_csv(geometry_file,sep=' ')

    geometry_df['hex_x'] = geometry_df[['vx_0','vx_1','vx_2','vx_3','vx_4','vx_5']].apply(list, axis=1)
    geometry_df['hex_y'] = geometry_df[['vy_0','vy_1','vy_2','vy_3','vy_4','vy_5']].apply(list, axis=1)
    return geometry_df[['plane','u','v','MB','x0','y0','hex_x','hex_y']]

# def prepare_geometry():
#     ''' to be used with the visualisation geometry '''
#     geometry = pd.read_csv('geometry/module_MB_geometry.csv')
#     geometry['hex_x'] = geometry['hex_x'].apply(convert_to_float_list)
#     geometry['hex_y'] = geometry['hex_y'].apply(convert_to_float_list)
#     return geometry

def colorscale(df, variable, scale):
    #if variable=='MB':
    #    df[variable] = df[variable].rank(method='dense').astype(int) - 1
    norm_points = (df[variable]-df[variable].min())/(0.1+df[variable].max()-df[variable].min())
    colorscale = px.colors.sample_colorscale(scale, norm_points)
    colorscale = ['rgb(255, 255, 255)' if value == 'rgb(48, 18, 59)' else value for value in colorscale]
    return colorscale

def plot_modules(df, variable):
    if isinstance(variable, str):
        opacity = 1
        df['Color'] = colorscale(df, variable, 'Viridis' if variable == 'trigLinks' else 'Turbo')
        array_data = df[['hex_x', 'hex_y', 'x0', 'y0', 'Color', 'u', 'v', 'MB', 'TriggerLpGbts']].to_numpy()
    else:
        opacity = 0.4
        df['Color'] = ['rgb(0, 0, 255)' if value==variable else 'rgb(255, 255, 255)' for value in df['Column']]
        array_data = df[['hex_x', 'hex_y', 'x0', 'y0', 'Color', 'u', 'v', 'MB']].to_numpy()
    
    listmodule = []
    annotations = []

    for i in array_data:
        #if i[0][5] == 0.0: x1, y1 = np.append(i[0][:-1], i[0][:1]), np.append(i[1][:-1], i[1][:1])
        if len(i[0]) < 6: x1, y1 = np.append(i[0], i[0][:1]), np.append(i[1], i[1][:1])
        else: x1, y1 = np.append(i[0], i[0][0]), np.append(i[1], i[1][0])
        text = '('+str(i[5])+','+str(i[6])+')'+'<br>'+' MB: '+str(i[7])
         
        datum = go.Scatter(x=x1, y=y1, mode="lines", fill='toself', fillcolor=i[4], opacity=opacity,
                           line_color='black', marker_line_color="black", text=text)
        listmodule.append(datum)
        
        x_offset, y_offset = i[2], i[3]
        #x_offset, y_offset = sum(x1[:-1])/6, sum(y1[:-1])/6
        text = 'MB:'+str(i[7])+'<br>'+'lpGBT:'+str(int(i[8])) if isinstance(variable, str) else text
        annotations.append(go.layout.Annotation(x=x_offset, y=y_offset, text=text, showarrow=False, font=dict(color='black')))
    
    return listmodule, annotations

def set_figure(scatter, annotations, local_plane, section):
    layer = local_plane if section == '0' else (str(int(local_plane) + 27) if section == '1' else '999')
    if int(layer) <= 27: return
    print(layer) 
    fig = go.Figure(scatter)
    fig.update_layout(width=900, height=900)
    
    #fig.update_layout(
    #    paper_bgcolor='rgba(0,0,0,0)',
    #    plot_bgcolor='rgba(0,0,0,0)'
    #)
    #fig.update_xaxes(showline=False, showticklabels=False)
    #fig.update_yaxes(showline=False, showticklabels=False)

    fig.update_layout(annotations=annotations, showlegend=False,
                 title='Display layer '+layer)
    
    fig.write_image("layer"+layer+"_MB_60sector.pdf")
    fig.write_image("layer"+str(layer)+"_MB_60sector.png")

def extract_module_info_from_xml(xml_file):
    ''' geometry is read from xml geometry file '''
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
                    'MB'    : extract_MB_plane_from_MBid(motherboard.get('id'))[0],
                    'u'     : int(module.get('u')),
                    'v'     : int(module.get('v')),
                    'hex_x' : list(float(x.split(',')[0]) for x in module.get('Vertices').split(';')),
                    'hex_y' : list(float(x.split(',')[1]) for x in module.get('Vertices').split(';'))
                })

    df = pd.DataFrame(data_list)
    return df

