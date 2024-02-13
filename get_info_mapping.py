import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np 
import matplotlib.pyplot as plt

import Tools as tools

def produce_plot(df):
    unique_s1_values = df['S1'].unique()

    for s1_value in unique_s1_values:
        subset_data = df[df['S1'] == s1_value]
        grouped_data = subset_data.groupby('Module').agg(
                       {'Column': 'nunique', 'TCcount': 'max'}).reset_index()
   
        print(f'Analying {s1_value} containing {len(grouped_data)} modules/MB..')
        plt.figure(figsize=(10, 6))
        plt.scatter(grouped_data['Column'], grouped_data['TCcount']/grouped_data['Column'], alpha=0.4)
        
        plt.xlabel('Number of columns in each module')
        plt.ylabel('Max TCs / Number of columns')
        plt.title(f'Modules processed by S1 {s1_value}')
        plt.savefig('plots/TCmax_vs_ncols'+s1_value+'.pdf')
    
# main
tree = ET.parse('xml/ChannelAllocation_SeparateTD-120-MixedTypes-NoSplit.xml')
geometry_file = 'xml/Geometry.xml'

df = tools.extract_data(tree, geometry_file)
#print(df.columns)

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

produce_plot(result_df.reset_index(name='TCcount'))
# result_df.to_excel("xlsx/tc_per_column_mod_S1.xlsx")
