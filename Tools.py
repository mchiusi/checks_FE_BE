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

def get_MB_ids(regions, region_id):
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

def colorscale(df, variable, scale):
    #norm_points = (df[variable]-df[variable].min())/(0.1+df[variable].max()-df[variable].min())
    norm_points = (df[variable].rank()-df[variable].rank().min()) / (df[variable].rank().max()-df[variable].rank().min())
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
        if len(i[0]) < 6: x1, y1 = np.append(i[0], i[0][:1]), np.append(i[1], i[1][:1])
        else: x1, y1 = np.append(i[0], i[0][0]), np.append(i[1], i[1][0])
        text = '('+str(i[5])+','+str(i[6])+')'+'<br>'+' MB: '+str(i[7])
         
        datum = go.Scatter(x=x1, y=y1, mode="lines", fill='toself', fillcolor=i[4], opacity=opacity,
                           line_color='black', marker_line_color="black", text=text)
        listmodule.append(datum)
        
        x_offset, y_offset = i[2], i[3]
        text = 'MB:'+str(i[7])+'<br>'+'lpGBT:'+str(int(i[8])) if isinstance(variable, str) else text
        annotations.append(go.layout.Annotation(x=x_offset, y=y_offset, text=text, showarrow=False, font=dict(color='black')))
    
    return listmodule, annotations

def set_figure(scatter, annotations, local_plane, section='0'):
    layer = local_plane if section == '0' else (str(int(local_plane) + 27) if section == '1' else '999')
    fig = go.Figure(scatter)
    fig.update_layout(width=800, height=900)

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
                if motherboard.get('TriggerLpGbts') == '0': continue
                data_list.append({
                    'plane' : int(plane_id),
                    'Module': str(int(module.get('id'))),
                    'MB'    : extract_MB_plane_from_MBid(motherboard.get('id'))[0],
                    'u'     : int(module.get('u')),
                    'v'     : int(module.get('v')),
                    'hex_x' : list(float(x.split(',')[0]) for x in module.get('Vertices').split(';')),
                    'hex_y' : list(float(x.split(',')[1]) for x in module.get('Vertices').split(';')),
                    'TriggerLpGbts' : motherboard.get('TriggerLpGbts'),
                })

    df = pd.DataFrame(data_list)
    return df

def extract_60regions_MB_from_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    regions = []
    for region_elem in root.findall(".//Region"):
        regions.append({
            'section': region_elem.get("section"),
            'plane'  : region_elem.get("plane"),
            'lr'     : region_elem.get("lr"),
            'MB'     : region_elem.get("Motherboards")
        })

    df = pd.DataFrame(regions)
    df['MB'] = df['MB'].str.split(';')
    df = df.explode('MB', ignore_index=True)
    df['MB'] = df['MB'].apply(extract_MB_plane_from_MBid).apply(lambda x: x[0])
    return df

