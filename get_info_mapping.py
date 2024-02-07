import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np 

import Tools as tools

# tree = ET.parse('xml/S1toChannels.SeparateTD.120.MixedTypes.NoSplit.xml')
tree = ET.parse('xml/ChannelAllocation_SeparateTD-120-MixedTypes-NoSplit.xml')
geometry_file = 'xml/Geometry.xml'

df = tools.extract_data(tree, geometry_file)
#print(df.columns)

# # number of columns per module
# col_per_module = df[['Module', 'S1', 'plane', 'u', 'v', 'Column', 'MB']].sort_values(by=['S1', 'Module']).drop_duplicates(subset=['Module','Column'])
# col_per_module = col_per_module.groupby(['S1','Module']).agg({
#                      'Column': 'nunique',
#                      'u': 'first', 
#                      'v': 'first',
#                      'plane': 'first',
#                      'MB': 'first' 
#                  }).reset_index()
# col_per_module.to_excel("xlsx/cols_per_module.xlsx", index=False)

# number of TCs per columns
for det in df.keys():
    if det == 'si':
        df_det = df[det].rename(columns={'Frame': 'TC_per_cols'})
    else:
        df_det = df[det].rename(columns={'Frame': 'TC_per_cols', 'Module': 'Module_true', 'MB': 'Module'})
    
    df_det['module_label'] = df_det[['TC_per_cols','Module','S1']].groupby(['S1','Module'])['TC_per_cols'].transform('count')
 
    conditions = [
       (df_det['module_label'] <= 7) & (df_det['plane'] < 27),
       ((df_det['module_label'] == 8) | (df_det['module_label'] == 9)) & (df_det['plane'] < 27),
       (df_det['module_label'] <= 3) & (df_det['plane'] >= 27),
       (df_det['module_label'] >= 6) & (df_det['plane'] >= 27),
    ]
    labels = ['BC_LOW', 'BC_HIGH', 'STC_16', 'STC_4']
    df_det['module_label'] = np.select(conditions, labels, default=None)

    tc_per_column = df_det[['Column','TC_per_cols','Module','module_label','S1']].groupby(['S1','Module','module_label','Column'])['TC_per_cols'].count()
    if det == 'sci': result_df = pd.concat([result_df, tc_per_column])
    if det == 'si':  result_df = tc_per_column

result_df.to_excel("xlsx/tc_per_column_mod_S1.xlsx")
