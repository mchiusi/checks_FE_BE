import pandas as pd
import xml.etree.ElementTree as ET

import Tools as tools

tree = ET.parse('xml/S1toChannels.SeparateTD.120.MixedTypes.NoSplit.xml')
geometry_file = 'xml/Geometry.xml'

df = tools.extract_data(tree, geometry_file)
print(df.columns)

# number of columns per module
col_per_module = df[['Module', 'idx', 'S1', 'plane', 'u', 'v']].sort_values(by=['S1', 'Module', 'idx']).drop_duplicates(subset=['S1','Module'], keep='last')
col_per_module['idx'] = col_per_module['idx'].astype(int) + 1
col_per_module = col_per_module.rename(columns={'idx':'Number_cols'})
col_per_module.to_excel("xlsx/cols_per_module.xlsx", index=False)

# number of TCs per columns
df = df.rename(columns={'Frame':'TC_per_cols'})
tc_per_column = df[['TC_per_cols', 'Column', 'S1']].groupby(['S1','Column'])['TC_per_cols'].nunique().mul(3)
tc_per_column.to_excel("xlsx/tc_per_column.xlsx")
