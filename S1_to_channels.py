import argparse
import pandas as pd
import numpy as np
import plotly.express as px
import xml.etree.ElementTree as ET
import plotly.io as pio   
pio.kaleido.scope.mathjax = None

import Tools as tools

def phi_calculator(df):
    phi_values = np.zeros(len(df))
    for vertix in range(6):
        phi_values += np.arctan2(df['hex_y'].apply(lambda y: y[vertix]), -df['hex_x'].apply(lambda x: x[vertix]))

    return phi_values/6

def extract_data(tree, geometry_file):
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

def create_scatter_plot(df, args):
    df_layer = {}
    for plane in df['plane'].unique():
        df_layer[plane] = df[df['plane'] == plane].reset_index(drop=True)

    scatter_df = df_layer[args.layer] if args.layer != -1 else df
    if not args.sector120: scatter_df = scatter_df[scatter_df['MB'] < 100].copy()
    scatter_df['coord'] = "(" + scatter_df['u'].astype(str) + "," + scatter_df['v'].astype(str) + ")"
    scatter_df['rank'] = scatter_df['phi'] if args.phi else scatter_df['phi'].rank(method='dense')
    scatter_df = scatter_df.sort_values(by=['Module', 'Column'])

    text = "coord" if args.layer != -1 else None
    text_size = 8 if args.sector120 else 12
    if args.channel:
        color = 'Channel'
        showlegend = True
    else:
        color = 'coord'
        showlegend = False

    fig_text = px.scatter(scatter_df, y="rank", x="Column", color=color, color_discrete_sequence=px.colors.qualitative.Light24)
    fig = px.scatter(scatter_df.drop_duplicates('Module'), y="rank", x="Column", text=text, opacity=0)
    fig.add_traces(fig_text.data)

    fig.update_traces(textposition='middle left', textfont=dict(size=text_size))
    fig.update_layout(
        title_text='Layer '+str(args.layer)+', modules to columns mapping',
        legend_title_text='Channels',
        width=1200,
        height=850,
        showlegend=showlegend,
        xaxis_title='Column',
        yaxis_title='φ-ordered modules',
    )

    return fig

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
    parser.add_argument("--layer", type=int, default=3, help="Choose the layer to display, -1 means all layers")
    parser.add_argument("--sector120", action="store_true", help="Display 60 or 120 sector")
    parser.add_argument("--phi",       action="store_true", help="Display phi or ordered numbers")
    parser.add_argument("--channel",   action="store_true", help="Color based on the channel numeration")
    parser.add_argument("--module",    action="store_true", help="Color based on the module ids")
    args = parser.parse_args()

    tree = ET.parse('xml/S1toChannels.SeparateTD.120.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'

    df = extract_data(tree, geometry_file)
    fig = create_scatter_plot(df, args)

    if args.channel: title = "S1toChannels_channel_layer_"+str(args.layer)
    else:            title = "S1toChannels_module_layer_" +str(args.layer)
    title += "_sector120" if args.sector120 else "_sector60"
    fig.write_image(title+".pdf")
    fig.write_image(title+".png")
