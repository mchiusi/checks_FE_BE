import argparse
import pandas as pd
import numpy as np
import plotly.express as px
import xml.etree.ElementTree as ET
import plotly.io as pio   
pio.kaleido.scope.mathjax = None
pd.options.plotting.backend = "plotly"

import Tools as tools

def plotting_frames(df, S1):
    ''' generic plotting function to create different scatter
        plots based on the options in args '''

    fig = px.scatter(df, y="Column", x="Frame", color='Channel', color_discrete_sequence=px.colors.qualitative.Light24)

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
    ''' crates a dictionary: keys == Stage1 FPGAs,
        values == dataframes containing frames '''

    df_devices = {}
    for S1 in df['S1'].unique():
        df_devices[S1] = df[df['S1'] == S1].reset_index(drop=True)
        df_device = df_devices[S1]

        fig = plotting_frames(df_device, S1) 
        tools.save_figure(fig, S1)


if __name__ == "__main__":
    ''' python S1_to_channels.py --channel --layer 11 '''

    tree = ET.parse('xml/S1toChannels.SeparateTD.Identical60.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'

    df = tools.extract_data(tree, geometry_file)
    create_scatter_plot(df)

