import pandas as pd
import xml.etree.ElementTree as ET

import Tools as tools

tree = ET.parse('xml/S1toChannels.SeparateTD.120.MixedTypes.NoSplit.xml')
geometry_file = 'xml/Geometry.xml'

df = tools.extract_data(tree, geometry_file)
print(df.columns)

# number of columns per module
col_per_module = df[['Module', 'S1', 'plane', 'u', 'v', 'Column', 'MB']].sort_values(by=['S1', 'Module']).drop_duplicates(subset=['Module','Column'])
col_per_module = col_per_module.groupby(['S1','Module']).agg({
                     'Column': 'nunique',
                     'u': 'first', 
                     'v': 'first',
                     'plane': 'first',
                     'MB': 'first' 
                 }).reset_index()
col_per_module.to_excel("xlsx/cols_per_module.xlsx", index=False)

# number of TCs per columns
df = df.rename(columns={'Frame':'TC_per_cols'})
tc_per_column = df[['TC_per_cols', 'Column', 'Module', 'S1']].groupby(['Column','Module','S1'])['TC_per_cols'].nunique().mul(3)
tc_per_column.to_excel("xlsx/tc_per_column_mod_S1.xlsx")
