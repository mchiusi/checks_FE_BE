import numpy as np
import pandas as pd
import math
import ast
import plotly.express as px
import plotly.graph_objects as go
import shapely
from shapely.geometry import Point, Polygon

import xml.etree.ElementTree as ET

colors = {0  : 'white',
          1  : 'cornflowerblue',
          2  : 'orange',
          3 : 'yellow'}

# Define a class to represent the Region objects
class Region:
    def __init__(self, id, section, plane, ud, lr, TriggerLpGbts, DaqLpGbts, DaqRate, TCcount, Motherboards):
        self.id = id
        self.section = section
        self.plane = plane
        self.ud = ud
        self.lr = lr
        self.TriggerLpGbts = TriggerLpGbts
        self.DaqLpGbts = DaqLpGbts
        self.DaqRate = DaqRate
        self.TCcount = TCcount
        self.MBs = Motherboards

def read_regions_xml_file():
    # Parse the XML file content
    tree = ET.parse("../xml/Regions.120.NoSplit.xml")
    root = tree.getroot()

    # Create Region objects for each Region element
    regions = []
    for region_elem in root.findall(".//Region"):
        id = region_elem.get("id")
        section = region_elem.get("section")
        plane = region_elem.get("plane")
        ud = region_elem.get("ud")
        lr = region_elem.get("lr")
        TriggerLpGbts = region_elem.get("TriggerLpGbts")
        DaqLpGbts = region_elem.get("DaqLpGbts")
        DaqRate = region_elem.get("DaqRate")
        TCcount = region_elem.get("TCcount")
        Motherboards = region_elem.get("Motherboards")

        region = Region(id, section, plane, ud, lr, TriggerLpGbts, DaqLpGbts, DaqRate, TCcount, Motherboards)
        regions.append(region)
    return regions

def get_modules_per_S1(regions):
    all_regions = read_regions_xml_file()
    geometry_file = '../xml/Geometry.xml'
    geometry = extract_module_info_from_xml(geometry_file)

    modules = 0
    for region in regions:
        #if region.lr =='0': continue
        print(f"Region ID: {region}")
        MB_ids_for_region = get_MB_ids(all_regions, region)

        df_region = pd.DataFrame(columns=['MB', 'plane'])
        for MB_id in MB_ids_for_region:
            MB, plane = extract_MB_plane_from_MBid(MB_id)
            # assert plane != region.plane, f"Planes from region and from MBs are different ({region.plane}, {plane})."

            df_region = df_region.append({'MB': MB, 'plane': plane}, ignore_index=True)
     
        modmap_region = pd.merge(df_region, geometry, on=['plane', 'MB'])
        modules += modmap_region.shape[0]

    return modules
#    scatter, annotations = plot_modules(modmap_region, 'MB')
#    set_figure(scatter, annotations, region.plane, region.section)

def create_sector(center, start_angle, end_angle, radius, steps=2):
    def polar_point(origin_point, angle,  distance):
        return [origin_point.x + math.cos(angle) * distance, origin_point.y + math.sin(angle) * distance]

    if start_angle > end_angle:
        start_angle = start_angle - 2*math.pi
    else:
        pass
    step_angle_width = (end_angle-start_angle) / steps
    sector_width = (end_angle-start_angle) 
    segment_vertices = []

    segment_vertices.append(polar_point(center, 0,0))
    segment_vertices.append(polar_point(center, start_angle,radius))

    for z in range(1, steps):
        segment_vertices.append((polar_point(center, start_angle + z * step_angle_width,radius)))
    segment_vertices.append(polar_point(center, start_angle+sector_width,radius))
    segment_vertices.append(polar_point(center, 0,0))
    return Polygon(segment_vertices)

def create_hexagon(df):
    x_vertices = df['hex_x'].iloc[0]
    y_vertices = df['hex_y'].iloc[0]
    vertices = vertices = [(x, y) for x, y in zip(x_vertices, y_vertices)]
    return Polygon(vertices)

def phi_calculator(df):
    df['x0'] = df['hex_x'].apply(np.mean)
    df['y0'] = df['hex_y'].apply(np.mean)
    return np.arctan2(df['y0'], df['x0'])

def extract_data(tree, geometry_file):
    ''' takes data from the xml and adds some useful information
        like the module id and cartesian coords and phi '''
    
    root = tree.getroot()
    data_list_si = []
    data_list_sci = []

    # reading the xml configuration file
    for s1 in root.findall('.//S1'):
        for channel in s1.findall('.//Channel'):
            for frame in channel.findall('.//Frame'):
                module = frame.get('Module')
                MB = frame.get('Motherboard')
                if module:
                    data_list_si.append({
                        'Module': str(int(frame.get('Module'))),
                        'idx': int(frame.get('index')),
                        'Column': int(frame.get('column')),
                        'Frame':  int(frame.get('id')),
                        'S1': s1.get('id'),
                        'Channel': channel.get('id'),
                    })
                if MB:
                    data_list_sci.append({
                        'MB': int(frame.get('Motherboard'),16),
                        'idx': int(frame.get('index')),
                        'Column': int(frame.get('column')),
                        'Frame':  int(frame.get('id')),
                        'S1': s1.get('id'),
                        'Channel': channel.get('id'),
                    })
                else:
                    continue 

    # adding additional information using geometry xml
    geometry = extract_module_info_from_xml(geometry_file)
   
    df_si  = pd.merge(pd.DataFrame(data_list_si),  geometry, on='Module', how='inner')
    df_sci = pd.merge(pd.DataFrame(data_list_sci), geometry, on='MB', how='inner')
    
    df = pd.concat([df_si, df_sci])
    df['phi'] = phi_calculator(df)
    return df

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

def get_MB_ids(regions, region):
    MB_ids = []

    region_class = [_region for _region in regions if _region.id == region][0]
    MB_ids.extend(region_class.MBs.split(';'))
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
        if len(i[0]) == 6 and i[0][5] == 0.0: x1, y1 = np.append(i[0][:-1], i[0][:-1]), np.append(i[1][:-1], i[1][:-1])
        else: x1, y1 = np.append(i[0], i[0][0]), np.append(i[1], i[1][0])
        text = '('+str(i[5])+','+str(i[6])+')'+'<br>'+' MB: '+str(i[7])
         
        datum = go.Scatter(x=x1, y=y1, mode="lines", fill='toself', fillcolor=i[4], opacity=opacity,
                           line_color='black', marker_line_color="black", text=text)
        listmodule.append(datum)
        
        x_offset, y_offset = (np.mean(x1), np.mean(y1)) if len(i[0]) == 6 and i[0][5] == 0.0 else (i[2], i[3])
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
        plane_id = int(plane.get('id'))
        if plane_id%2==0 and plane_id < 27: continue
        for motherboard in plane.findall(".//Motherboard"):
            for module in motherboard.findall(".//Module"):
                data_list.append({
                    'plane' : plane_id,
                    'Module': str(int(module.get('id'))),
                    'MB'    : int(motherboard.get('id'),16), #extract_MB_plane_from_MBid(motherboard.get('id'))[0],
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
        section = region_elem.get("section")
        local_plane = region_elem.get("plane")
        regions.append({
            'section': region_elem.get("section"),
            'plane'  : int(local_plane) if section == '0' else (int(local_plane) + 27 if section == '1' else 999),
            'lr'     : region_elem.get("lr"),
            'MB'     : region_elem.get("Motherboards")
        })

    df = pd.DataFrame(regions)
    df['MB'] = df['MB'].str.split(';')
    df = df.explode('MB', ignore_index=True)
    df['MB'] = df['MB'].apply(extract_MB_plane_from_MBid).apply(lambda x: x[0])
    return df

def prepare_geometry_txt():
    ''' old but working version, it reads the geometry 
        file from Pedro's txt '''
    geometry_file = 'geometries/v15.3/geometry.15.3.txt'
    geometry_df = pd.read_csv(geometry_file,sep=' ')

    geometry_df['hex_x'] = geometry_df[['vx_0','vx_1','vx_2','vx_3','vx_4','vx_5']].apply(list, axis=1)
    geometry_df['hex_y'] = geometry_df[['vy_0','vy_1','vy_2','vy_3','vy_4','vy_5']].apply(list, axis=1)
    
    return geometry_df[['plane','u','v','MB','x0','y0','hex_x','hex_y','trigLinks']]

def save_figure(fig, layer, args):
    if args.channel: title = "S1toChannels_channel_layer_"+str(layer)
    if args.module:  title = "S1toChannels_module_layer_" +str(layer)
    if args.frame:   title = "S1toChannels_frame_layer_"  +str(layer)
    title += "_sector60" if args.sector60 else "_sector120"
    title += "_phi" if args.phi else ""

    fig.write_image(title+".pdf")
    fig.write_image(title+".png")
    
def save_csv(df, layer, args):
    df = df.sort_values(by=['Module','Module_idx']).drop_duplicates(['Module'], 'last')
    df['Module_idx'] = df['Module_idx'].astype(int) + 1

    title = "frames_per_module_layer" + str(layer)
    df[['plane','u','v','Module_idx']].to_csv(title+'.csv', index=False)    
