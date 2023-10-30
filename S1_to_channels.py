import argparse
import pandas as pd
import numpy as np
import plotly.express as px
import xml.etree.ElementTree as ET
import plotly.io as pio   
pio.kaleido.scope.mathjax = None
pd.options.plotting.backend = "plotly"

import Tools as tools

def phi_calculator(df):
    mean_x, mean_y = np.zeros(len(df)), np.zeros(len(df))
    for vertix in range(6):
        mean_x += df['hex_x'].apply(lambda x: x[vertix])/6
        mean_y += df['hex_y'].apply(lambda y: y[vertix])/6

    return np.arctan2(mean_y, -mean_x)

def extract_data(tree, geometry_file):
    ''' takes data from the xml and adds some useful information
        like the module id and cartesian coords and phi '''
    
    root = tree.getroot()
    data_list = []

    for s1 in root.findall('.//S1'):
        for channel in s1.findall('.//Channel'):
            for frame in channel.findall('.//Frame'):
                module = frame.get('Module')
                if module is not None:
                    module = int(module)
                else:
                    continue
                data_list.append({
                    'Module': str(int(frame.get('Module'))),
                    'Module_idx': frame.get('index'),
                    'Column': int(frame.get('column')),
                    'Frame': frame.get('id'),
                    'S1': s1.get('id'),
                    'Channel': channel.get('id'),
                    'Frame': frame.get('id'),
                })

    df = pd.DataFrame(data_list)
    df = pd.merge(df, tools.extract_module_info_from_xml(geometry_file), on='Module', how='inner')

    geometry = tools.prepare_geometry()
    df = pd.merge(df, geometry, on=['plane', 'u', 'v'])
    df['phi'] = phi_calculator(df)

    return df

def save_figure(fig, args):
    if args.channel: title = "S1toChannels_channel_layer_"+str(args.layer)
    if args.module:  title = "S1toChannels_module_layer_" +str(args.layer)
    else:            title = "S1toChannels_frame_layer_"  +str(args.layer)
    title += "_sector60" if args.sector60 else "_sector120"
    title += "_phi" if args.phi else ""

    fig.write_image(title+".pdf")
    fig.write_image(title+".png")
    
def save_csv(df, args):
    df = df.sort_values(by=['Module','Module_idx']).drop_duplicates(['Module'], 'last')
    df['Module_idx'] = df['Module_idx'].astype(int) + 1

    title = "frames_per_module_layer" + str(args.layer)
    df[['plane','u','v','Module_idx']].to_csv(title+'.csv', index=False)    

def plotting_frames(df, args):
    ''' generic plotting function to create different scatter
        plots based on the options in args '''

    text = "coord" if args.layer != -1 else None
    text_size = 12 if args.sector60 else 8
   
    color = 'Channel' if args.channel else 'coord' if args.module else 'occurrence' if args.frame else None
    showlegend = args.channel or (args.module and not args.layer == -1) or args.frame

    fig_text = px.scatter(df, y="rank", x="Column", color=color, color_discrete_sequence=px.colors.qualitative.Light24)
    fig = px.scatter(df.drop_duplicates('Module'), y="rank", x="Column", text=text, opacity=0)
    fig.add_traces(fig_text.data)

    fig.update_traces(textposition='middle left', textfont=dict(size=text_size))
    fig.update_layout(
        title_text='layer '+str(args.layer)+', modules to columns mapping',
        legend_title_text='channels' if args.channel else 'tcs',
        width=1200,
        height=850,
        showlegend=showlegend,
        xaxis_title='column',
        yaxis_title='φ coordinate' if args.phi else 'φ-ordered modules',
    )
    return fig

def plotting_histo(df, args):
    fig = df['coord'].plot(kind = 'hist')

    fig.update_layout(
        title_text='layer '+str(args.layer)+', frames per module histogram',
        width=1200,
        height=850,
        xaxis_title='φ-ordered module coordinates',
        yaxis_title='frames',
    )

    save_csv(df, args)
    return fig


def create_scatter_plot(df, args):
    ''' crates a dictionary: keys == HGCAL layers,
        values == dataframes containing frames '''
    
    df_layer = {}
    for plane in df['plane'].unique():
        df_layer[plane] = df[df['plane'] == plane].reset_index(drop=True)

    #for plane in df['plane'].unique():
    #args.layer = plane
    scatter_df = df_layer[args.layer] if args.layer != -1 else df
    if args.sector60: scatter_df = scatter_df[scatter_df['MB'] < 100].copy()
    scatter_df['coord'] = "(" + scatter_df['u'].astype(str) + "," + scatter_df['v'].astype(str) + ")"
    scatter_df['rank'] = scatter_df['phi'] if args.phi else scatter_df['phi'].rank(method='dense')
    if args.frame: scatter_df['occurrence'] = scatter_df.groupby(['Module','Column']).cumcount().add(1).mul(4).astype(str)
    if args.histo: scatter_df = scatter_df.sort_values(by=['phi'])
    else: scatter_df = scatter_df.sort_values(by=['Module', 'Column']).drop_duplicates(['Module', 'Column'], 'last')

    fig = plotting_histo(scatter_df, args) if args.histo else plotting_frames(scatter_df, args) 
    save_figure(fig, args)


if __name__ == "__main__":
    ''' python S1_to_channels.py --channel --layer 11 '''

    parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
    parser.add_argument("--layer", type=int, default=3, help="Choose the layer to display, -1 means all layers")
    parser.add_argument("--sector60",  action="store_true", help="Display 60 or 120 sector")
    parser.add_argument("--phi",       action="store_true", help="Display phi or ordered numbers")
    parser.add_argument("--channel",   action="store_true", help="Color based on the channel numeration")
    parser.add_argument("--module",    action="store_true", help="Color based on the module ids")
    parser.add_argument("--frame",     action="store_true", help="Color based on the number of frames in each module x column")
    parser.add_argument("--histo",     action="store_true", help="produce histograms")
    args = parser.parse_args()

    tree = ET.parse('xml/S1toChannels.SeparateTD.120.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'

    df = extract_data(tree, geometry_file)
    create_scatter_plot(df, args)

