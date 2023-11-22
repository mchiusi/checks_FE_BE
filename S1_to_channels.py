import argparse
import pandas as pd
import numpy as np
import math
import plotly.express as px
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
import plotly.io as pio   
pio.kaleido.scope.mathjax = None
pd.options.plotting.backend = "plotly"
import shapely
from shapely.geometry import Point, Polygon

import Tools as tools

def plotting_frames(df, layer, args):
    ''' generic plotting function to create different scatter
        plots based on the options in args '''

    color = 'Channel' if args.channel else 'coord' if args.module else 'occurrence' if args.frame else None
    showlegend = args.channel or args.module or args.frame

    fig_text = px.scatter(df, y="rank", x="Column", color=color, color_discrete_sequence=px.colors.qualitative.Light24)
    fig = px.scatter(df.drop_duplicates('Module'), y="rank", x="Column", text='coord', opacity=0)
    fig.add_traces(fig_text.data)

    text_size = 12 if args.sector60 else 8 
    fig.update_traces(textposition='middle left', textfont=dict(size=text_size))
    fig.update_layout(
        title_text='layer '+str(layer)+', modules to columns mapping',
        legend_title_text='channels' if args.channel else 'tcs',
        width=1200,
        height=850,
        showlegend=showlegend,
        xaxis_title='column',
        yaxis_title='φ coordinate' if args.phi else 'φ-ordered modules',
    )
    return fig

def plotting_histo(df, layer, args):
    fig = df['coord'].plot(kind = 'hist')

    fig.update_layout(
        title_text='layer '+str(layer)+', frames per module histogram',
        width=1200,
        height=850,
        xaxis_title='φ-ordered module coordinates',
        yaxis_title='frames',
    )

    tools.save_csv(df, layer, args)
    return fig

def create_maps(df, layer):
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

def create_scatter_plot(scatter_df, layer, args):
    if args.sector60: scatter_df = scatter_df[scatter_df['MB'] < 100].copy()
    
    scatter_df['coord'] = "(" + scatter_df['u'].astype(str) + "," + scatter_df['v'].astype(str) + ")"
    scatter_df['rank'] = scatter_df['phi'] if args.phi else scatter_df['phi'].rank(method='dense')
    
    if args.frame: scatter_df['occurrence'] = scatter_df.groupby(['Module','Column']).cumcount().add(1).mul(3).astype(str)
    if args.histo: scatter_df = scatter_df.sort_values(by=['phi'])
    else: scatter_df = scatter_df.sort_values(by=['Module', 'Column']).drop_duplicates(['Module', 'Column'], 'last')

    fig = plotting_histo(scatter_df, layer, args) if args.histo else plotting_frames(scatter_df, layer, args) 
    tools.save_figure(fig, layer, args)

def create_custom_legend(fig):
    custom_legend_traces = [
        go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=10, color=color), name=label)
        for label, color in tools.colors.items()
    ]
    
    for trace in custom_legend_traces:
        fig.add_trace(trace)

def create_slice_plot(df, layer):
    fig = go.Figure()
    center = Point(0,0)
    radius = df['hex_x'].apply(lambda x: max(x)).max() + 300
    annotations = []

    df['occurrence'] = df.groupby(['Module','Column']).cumcount().add(1).astype(str)
    df = df.sort_values(by=['Module', 'Column']).drop_duplicates(['Module', 'Column'], 'last')
    for module in df.Module.unique():
        df_module = df[df.Module == module]
        hexagon = tools.create_hexagon(df_module) 
        for i in range(-10,85):
            sector = tools.create_sector(center, math.radians(i*120/84), math.radians((i+1)*120/84), radius)
            module = hexagon.intersection(sector)
            if module.is_empty or isinstance(module, Point): continue
            x, y = module.exterior.coords.xy

            TCs = df_module['occurrence'][df_module.Column == i]
            color = tools.colors[int(TCs)] if not TCs.empty else 'white'
            fig.add_trace(go.Scatter(x=np.array(x), y=np.array(y), fill="toself", fillcolor=color,
                          line=dict(color='rgba(0,0,0)', width=0.5), mode='lines', showlegend=False))

        module_info = df_module.iloc[0]
        text = '('+str(module_info['u'])+','+str(module_info['v'])+')'
        annotations.append(go.layout.Annotation(x=module_info['x0'], y=module_info['y0'], text=text, showarrow=False, font=dict(color='black')))

    create_custom_legend(fig)
    fig.update_layout(annotations=annotations, title='TCs distribution in each frame*column in layer '+str(layer))
    
    fig.write_image("slice_plot_layer_"+str(layer)+".pdf")
    fig.write_image("slice_plot_layer_"+str(layer)+".png")

def create_plot(df, args):
    ''' crates a dictionary: keys == HGCAL layers,
        values == dataframes containing frames '''
    
    df_layer = {}
    for plane in df['plane'].unique():
        print("Processing layer ", str(plane))
        df_layer[plane] = df[df['plane'] == plane].reset_index(drop=True)

        if args.scatter:     create_scatter_plot(df_layer[plane], plane, args)
        if args.module_maps: create_maps(df_layer[plane], plane)
        if args.frame_maps:  create_slice_plot(df_layer[plane], plane)

if __name__ == "__main__":
    ''' python S1_to_channels.py '''

    parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
    parser.add_argument("--scatter",     action="store_true", help="Create scatter plots phi vs columns. Each marker is a frame", default=True)
    parser.add_argument("--module_maps", action="store_true", help="Create HGCAL maps per layer and per columns highliting modules selected")
    parser.add_argument("--frame_maps",  action="store_true", help="Create HGCAL maps per layer showing the frames")
    parser.add_argument("--sector60",    action="store_true", help="Display 60 or 120 sector")
    parser.add_argument("--phi",         action="store_true", help="Display phi or ordered numbers")
    parser.add_argument("--channel",     action="store_true", help="Color based on the channel numeration", default=True)
    parser.add_argument("--module",      action="store_true", help="Color based on the module ids")
    parser.add_argument("--frame",       action="store_true", help="Color based on the number of frames in each module x column")
    parser.add_argument("--histo",       action="store_true", help="produce histograms")
    args = parser.parse_args()

    tree = ET.parse('xml/S1toChannels.SeparateTD.120.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'

    df = tools.extract_data(tree, geometry_file)
    create_plot(df, args)

