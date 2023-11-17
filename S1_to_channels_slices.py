import argparse
import shapely
from shapely.geometry import Point, Polygon
import math
import numpy as np
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
import plotly.io as pio   
pio.kaleido.scope.mathjax = None

import Tools as tools
from S1_to_channels import extract_data

colors = {0  : 'white',
          1  : 'cornflowerblue',
          2  : 'orange',
          3 : 'yellow'}
 
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

def create_custom_legend(fig):
    custom_legend_traces = [
        go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=10, color=color), name=label)
        for label, color in colors.items()
    ]
    
    for trace in custom_legend_traces:
        fig.add_trace(trace)

def create_slice_plot(df, layer):
    fig = go.Figure()
    center = Point(0,0)
    radius = df['hex_x'].apply(lambda x: max(x)).max() + 300
    annotations = []

    for module in df.Module.unique():
        df_module = df[df.Module == module]
        hexagon = create_hexagon(df_module) 
        for i in range(-10,85):
            sector = create_sector(center, math.radians(i*120/84), math.radians((i+1)*120/84), radius)
            module = hexagon.intersection(sector)
            if module.is_empty or isinstance(module, Point): continue
            x, y = module.exterior.coords.xy

            TCs = df_module['occurrence'][df_module.Column == i]
            color = colors[int(TCs)] if not TCs.empty else 'white'
            fig.add_trace(go.Scatter(x=np.array(x), y=np.array(y), fill="toself", fillcolor=color,
                          line=dict(color='rgba(0,0,0)', width=0.5), mode='lines', showlegend=False))

        module_info = df_module.iloc[0]
        text = '('+str(module_info['u'])+','+str(module_info['v'])+')'
        annotations.append(go.layout.Annotation(x=module_info['x0'], y=module_info['y0'], text=text, showarrow=False, font=dict(color='black')))

    create_custom_legend(fig)
    fig.update_layout(annotations=annotations, title='TCs distribution in each frame*column in layer '+str(layer))
    
    fig.write_image("slice_plot_layer_"+str(layer)+".pdf")
    fig.write_image("slice_plot_layer_"+str(layer)+".png")
    
if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
    #parser.add_argument("--sector120", action="store_true", help="Display 60 or 120 sector")
    #args = parser.parse_args()
   
    tree = ET.parse('xml/S1toChannels.SeparateTD.120.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'
    df = extract_data(tree, geometry_file)

    df['occurrence'] = df.groupby(['Module','Column']).cumcount().add(1).astype(str)
    df = df.sort_values(by=['Module', 'Column']).drop_duplicates(['Module', 'Column'], 'last')

    for plane in df['plane'].unique():
        print("Processing layer ", str(plane))
        df_layer = df[df['plane'] == plane]
        create_slice_plot(df_layer, plane)
    
