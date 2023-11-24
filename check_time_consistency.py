import argparse
import pandas as pd
import numpy as np
import plotly.express as px
import xml.etree.ElementTree as ET
import plotly.io as pio   
pio.kaleido.scope.mathjax = None
pd.options.plotting.backend = "plotly"

import Tools as tools

def plotting_frames(df, variable):
    ''' generic plotting function to create different scatter
        plots based on the options in args '''

    print(variable)
    y="S1" if args.column else "Column"
    color="S1"
    fig = px.scatter(df, y=y, x="Frame", color=color, color_discrete_sequence=px.colors.qualitative.Light24)
    title_text = 'Channel allocation algorithm'
    title_text += 'in S1 FPGA '+str(variable) if args.fpga else 'for column '+str(variable)
    legend_title_text = 'channels' if args.fpga else 'S1'

    fig.update_layout(
        title_text=title_text,
        legend_title_text=legend_title_text,
        width=1200,
        height=850,
        xaxis_title='time [frame]',
        yaxis_title='columns',
    )
    return fig

def create_scatter_plot(df, variable):
    ''' crates a dictionary: keys == Stage1 FPGAs,
        values == dataframes containing frames '''

    df_split = {}
    for var in df[variable].unique():
        df_split[var] = df[df[variable] == var].reset_index(drop=True)

        fig = plotting_frames(df_split[var], var) 
        if args.fpga:    title = "Channel_allocation_device_" +str(var)
        if args.column:  title = "Channel_allocation_column_" +str(var)
        fig.write_image(title+".pdf")
        fig.write_image(title+".png")

if __name__ == "__main__":
    ''' python check_time_consistency.py '''
    parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
    parser.add_argument("--fpga",     action="store_true", help="Create scatter plots phi vs columns. Each marker is a frame", default=True)
    parser.add_argument("--column", action="store_true", help="Create HGCAL maps per layer and per columns highliting modules selected")
    args = parser.parse_args()

    tree = ET.parse('xml/S1toChannels.SeparateTD.Identical60.SingleTypes.NoSplit.xml')
    geometry_file = 'xml/Geometry.xml'

    df = tools.extract_data(tree, geometry_file)
    variable = 'Column' if args.column else 'S1'
    create_scatter_plot(df, variable)

