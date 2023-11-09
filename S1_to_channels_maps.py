import argparse
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
import plotly.io as pio   
pio.kaleido.scope.mathjax = None

import Tools as tools
from S1_to_channels import extract_data

def create_plot(df, layer):
    offset = -4 # including the negative columns
    radius = df['hex_x'].apply(lambda x: max(x)).max()
    x_slice, y_slice = tools.create_slices(radius, offset=-4)

    for column in range(84+offset):
        column = column + offset
        df = df.sort_values(by='Column', key=lambda x: x != column)
        df_layer = df.drop_duplicates('Module').copy()
        scatter, annotations = tools.plot_modules(df_layer, column)
        fig = go.Figure(scatter)
        fig.update_layout(width=1100, height=900)
        fig.update_layout(annotations=annotations, showlegend=False, title='Display layer '+str(layer)+', Column'+str(column))
  
        fig.add_trace(go.Scatter(x=x_slice[column-offset],   y=y_slice[column-offset],   mode='lines', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=x_slice[column-offset+1], y=y_slice[column-offset+1], mode='lines', line=dict(color='blue')))
    
        title = "S1toChannels_module_layer_" +str(layer)+"_Column"+str(column)
        fig.write_image(title+".pdf")
        fig.write_image(title+".png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
    parser.add_argument("--sector120", action="store_true", help="Display 60 or 120 sector")
    args = parser.parse_args()

    tree = ET.parse('xml/S1toChannels.SeparateTD.120.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'

    df = extract_data(tree, geometry_file)
    for plane in df['plane'].unique():
        print("Processing layer ", str(plane))
        df_layer = df[df['plane'] == plane].reset_index(drop=True)
        create_plot(df_layer, plane)
