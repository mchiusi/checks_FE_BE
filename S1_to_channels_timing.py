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
    df['x0'] = df['hex_x'].apply(np.mean)
    df['y0'] = df['hex_y'].apply(np.mean)
    return np.arctan2(df['y0'], df['x0'])

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
                    'Frame': int(frame.get('id')),
                    'S1': s1.get('id'),
                    'Channel': channel.get('id'),
                })

    df = pd.DataFrame(data_list)
    df = pd.merge(df, tools.extract_module_info_from_xml(geometry_file), on='Module', how='inner')
    df['phi'] = phi_calculator(df)
    return df

def save_figure(fig, S1):
    #if args.channel: title = "S1toChannels_channel_layer_"+str(args.layer)
    #if args.module:  title = "S1toChannels_module_layer_" +str(args.layer)
    #else:            title = "S1toChannels_frame_layer_"  +str(args.layer)
    #title += "_sector60" if args.sector60 else "_sector120"
    #title += "_phi" if args.phi else ""

    title = 'Channel_allocation_'+S1
    fig.write_image(title+".pdf")
    fig.write_image(title+".png")
    
def plotting_frames(df, S1):
    ''' generic plotting function to create different scatter
        plots based on the options in args '''

    color = 'Channel' #if args.channel else 'coord' if args.module else 'occurrence' if args.frame else None

    fig = px.scatter(df, y="Column", x="Frame", color=color, color_discrete_sequence=px.colors.qualitative.Light24)
    # fig = px.scatter(df.drop_duplicates('Module'), y="rank", x="Column", text=text, opacity=0)
    # fig.add_traces(fig_text.data)

    #fig.update_traces(textposition='middle left', textfont=dict(size=text_size))
    fig.update_layout(
        title_text='Channel allocation algorithm in S1 FPGA, ' + S1,
        legend_title_text='channels',
        width=1200,
        height=850,
        xaxis_title='time [frame]',
        yaxis_title='columns',
    )
    return fig

def create_scatter_plot(df):
    ''' crates a dictionary: keys == HGCAL layers,
        values == dataframes containing frames '''

    df_devices = {}
    for S1 in df['S1'].unique():
        df_devices[S1] = df[df['S1'] == S1].reset_index(drop=True)
        df_device = df_devices[S1]

        fig = plotting_frames(df_device, S1) 
        save_figure(fig, S1)


if __name__ == "__main__":
    ''' python S1_to_channels.py --channel --layer 11 '''

    #parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
    #parser.add_argument("--sector60",  action="store_true", help="Display 60 or 120 sector")
    #parser.add_argument("--channel",   action="store_true", help="Color based on the channel numeration")
    #args = parser.parse_args()

    tree = ET.parse('xml/S1toChannels.SeparateTD.Identical60.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'

    df = extract_data(tree, geometry_file)
    create_scatter_plot(df)

