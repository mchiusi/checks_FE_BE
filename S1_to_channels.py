import xml.etree.ElementTree as ET
import Tools as tools
import pandas as pd

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
                'Column'    : frame.get('column'),
                'Frame'     : frame.get('id'),
                'S1'        : s1.get('id'),
                'Channel'   : channel.get('id'),
                'Frame'     : frame.get('id'),
            })

df = pd.DataFrame(data_list)
df = df.sort_values(by=['Module', 'Module_idx'])
df = pd.merge(df, tools.extract_module_info_from_xml(geometry_file),
              on='Module', how='inner')

dfs_by_s1 = {}
unique_s1_values = df['S1'].unique()

for s1_value in unique_s1_values:
    dfs_by_s1[s1_value] = df[df['S1'] == s1_value].reset_index(drop=True)
 
print(dfs_by_s1['X00'].Plane.unique())#[dfs_by_s1['X00'].Plane == 3])


