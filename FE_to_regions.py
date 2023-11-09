import argparse
import numpy as np
import pandas as pd
import Tools as tools

parser = argparse.ArgumentParser(description="A script that chooses between --channel and --module.")
parser.add_argument("--sector120", action="store_true", help="Display 60 or 120 sector")
args = parser.parse_args()

geometry_file = 'xml/Geometry.xml'
geometry = tools.extract_module_info_from_xml(geometry_file)

geometry['x0'] = geometry['hex_x'].apply(np.mean)
geometry['y0'] = geometry['hex_y'].apply(np.mean)

if not args.sector120:
    regions = tools.extract_60regions_MB_from_xml("xml/Regions.60.NoSplit.xml")
    df = pd.merge(geometry, regions[regions.lr==0], on='MB', how='inner')

for plane in geometry.plane.unique():
    print("Processing layer ", plane)

    df_layer = geometry[geometry.plane == plane].copy()
    df_layer = df_layer[df_layer.MB < 100].copy()
    scatter, annotations = tools.plot_modules(df_layer, 'MB')
    tools.set_figure(scatter, annotations, str(plane))

