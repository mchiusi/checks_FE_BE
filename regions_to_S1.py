import xml.etree.ElementTree as ET
import os

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import Tools as tools
import plotly.io as pio
pio.kaleido.scope.mathjax = None

def get_MB_ids(region_id):
    MB_ids = []

    for region in regions:
        if region.id == region_id:
            MB_ids.extend(region.MBs.split(';'))
    return MB_ids

def extract_plane_from_region(id):
    RegionId = int(id, 16) # hexadecimal 'id' to integer

    lr = RegionId & 1
    ud = (RegionId >> 1) & 1
    plane = (RegionId >> 2) & 0b11111
    section = (RegionId >> 7)

    return lr, ud, plane, section 


# main function

region_degree = '60'

if region_degree != '120': tree = ET.parse("xml/S1.SeparateTD.Identical60.SingleTypes.NoSplit.xml")
else: tree = ET.parse("xml/S1.SeparateTD.120.SingleTypes.NoSplit.xml")
root = tree.getroot()

S1_FPGAs = {}
df_S1 = pd.DataFrame(columns=['S1', 'plane', 'section', 'lr'])

for S1_FPGA in root.findall(".//S1"):
    id_S1 = S1_FPGA.get("id")
    S1_regions = S1_FPGA.get("Regions")

    print(f"S1: {id_S1}")
    
    regions = []
    regions.extend(S1_regions.split(';'))
    
    for region in regions:
        lr, ud, local_plane, section = extract_plane_from_region(region)
        lr = lr + 0.1 if section == 2 and lr == 0 else lr - 0.1 if section == 2 else lr
        plane = local_plane if section == 0 else (local_plane + 27 if section != 3 else None)

        df_S1 = df_S1.append({'S1': id_S1, 'plane': plane, 'section' : section,'lr': lr}, ignore_index=True)

if region_degree != '120':
    fig  = px.scatter(df_S1[df_S1.lr>=0.9], x='plane', y='lr', color='S1', symbol='S1', title='60 regions to S1 FPGA Mapping', width=840)
    fig2 = px.scatter(df_S1[df_S1.lr<=0.1], x='plane', y='lr', color='S1', symbol='S1', title='60 regions to S1 FPGA Mapping', width=840)
    fig.add_traces(fig2.data)
else:
    fig = px.scatter(df_S1, x='plane', y='lr', color='S1', symbol='S1', title='120 regions to S1 FPGA Mapping', width=840)


fig.update_traces(marker=dict(size=12, opacity=0.7), selector=dict(mode='markers'))

fig.add_shape(type='line', x0=27, x1=27, y0=-0.2, y1=1.2, line=dict(color='red', width=2, dash='dash'))
labels = [('CE-H CE-S', 'right', 0.5, 40), ('CE-E', 'left', 0.5, 10)]
for text, xanchor, y, x in labels:
    fig.add_annotation(x=x, y=y, text=text, showarrow=False, font=dict(size=14), xanchor=xanchor)

fig.update_xaxes(title_text='HGCAL layers')
fig.update_yaxes(title_text='left and right sectors')

fig.update_layout(
    legend_title_text='',
    legend=dict(
        orientation='h',
        bordercolor='gray',
        borderwidth=1,
        yanchor = "bottom", 
        y = -0.4,
        xanchor = "center",
        x =  0.5,
    )
)

title = "S1_mapping"
title += "_60" if region_degree == '60' else "_120"
fig.write_image(title + ".png")
fig.write_image(title + ".pdf")
