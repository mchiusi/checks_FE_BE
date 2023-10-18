import xml.etree.ElementTree as ET
import Tools as tools
import pandas as pd
import numpy as np

import plotly.express as px

tree = ET.parse('xml/S1toChannels.SeparateTD.120.SingleTypes.NoSplit.xml')
geometry_file = 'xml/Geometry.xml'
root = tree.getroot()

data_list = []

for s1 in root.findall('.//S1'):
    for channel in s1.findall('.//Channel'):
        for frame in channel.findall('.//Frame'):
            module = frame.get('Module') 
            if module is not None: module = int(module)
            else: continue
            data_list.append({
                'Module'    : int(frame.get('Module')),
                'Module_idx': frame.get('index'),
                'Column'    : int(frame.get('column')),
                'Frame'     : frame.get('id'),
                'S1'        : s1.get('id'),
                'Channel'   : channel.get('id'),
                'Frame'     : frame.get('id'),
            })

df = pd.DataFrame(data_list)
df = df.sort_values(by=['Module', 'Module_idx'])
df = pd.merge(df, tools.extract_module_info_from_xml(geometry_file),
              on='Module', how='inner')

geometry = tools.prepare_geometry()
df = pd.merge(df, geometry, on=['plane','u','v'])
df['phi'] = np.arctan2(df['hex_y'].apply(lambda y: y[3]), -df['hex_x'].apply(lambda x: x[3]))

df_layer = {}
for plane in df['plane'].unique():
    df_layer[plane] = df[df['plane'] == plane].reset_index(drop=True)
 
scatter_df = df_layer[3][df_layer[3].MB < 20]
scatter_df['coord'] = "(" + scatter_df['u'].astype(str) + "," + scatter_df['v'].astype(str) + ")"
scatter_df["Module"] = scatter_df["Module"].astype(str)
fig = px.scatter(scatter_df, y="phi", x="Column", color="coord")
fig.update_traces(marker_size=10)

fig.write_image("layer_3.pdf")

