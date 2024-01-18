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

region_degree = '120'

if region_degree != '120': tree = ET.parse("xml/S1.SeparateTD.Identical60.SingleTypes.NoSplit.xml")
else: tree = ET.parse("xml/S1.SeparateTD.120.MixedTypes.NoSplit.xml")
root = tree.getroot()

S1_FPGAs = {}
df_S1 = pd.DataFrame(columns=['S1', 'modules'])

for S1_FPGA in root.findall(".//S1"):
    id_S1 = S1_FPGA.get("id")
    S1_regions = S1_FPGA.get("Regions")

    print(f"S1: {id_S1}")
    
    regions = []
    regions.extend(S1_regions.split(';'))
    
    modules = tools.get_modules_per_S1(regions) 
    df_S1 = df_S1.append({'S1': id_S1, 'modules': modules}, ignore_index=True)

print(df_S1)
df_S1.to_excel("xlsx/modules_per_S1.xlsx")
