import xml.etree.ElementTree as ET
import os

import plotly.io as pio   
pio.kaleido.scope.mathjax = None
import pandas as pd
import Tools as tools

# Define a class to represent the Region objects
class Region:
    def __init__(self, id, section, plane, ud, lr, TriggerLpGbts, DaqLpGbts, DaqRate, TCcount, Motherboards):
        self.id = id
        self.section = section
        self.plane = plane
        self.ud = ud
        self.lr = lr
        self.TriggerLpGbts = TriggerLpGbts
        self.DaqLpGbts = DaqLpGbts
        self.DaqRate = DaqRate
        self.TCcount = TCcount
        self.MBs = Motherboards

def get_MB_ids(region_id):
    MB_ids = []

    for region in regions:
        if region.id == region_id:
            MB_ids.extend(region.MBs.split(';'))
    return MB_ids

def extract_MB_plane_from_MBid(id):
    id_int = int(id, 16) # hexadecimal 'id' to integer

    MotherboardId = id_int & 0x1FFF  # binary: 0001 1111 1111 1111
    PlaneId = (id_int >> 13) & 0xFFFF  

    return MotherboardId, PlaneId


# main function

# Parse the XML file content
tree = ET.parse("xml/Regions.60.NoSplit.xml")
root = tree.getroot()

# Create Region objects for each Region element
regions = []
for region_elem in root.findall(".//Region"):
    id = region_elem.get("id")
    section = region_elem.get("section")
    plane = region_elem.get("plane")
    ud = region_elem.get("ud")
    lr = region_elem.get("lr")
    TriggerLpGbts = region_elem.get("TriggerLpGbts")
    DaqLpGbts = region_elem.get("DaqLpGbts")
    DaqRate = region_elem.get("DaqRate")
    TCcount = region_elem.get("TCcount")
    Motherboards = region_elem.get("Motherboards")

    region = Region(id, section, plane, ud, lr, TriggerLpGbts, DaqLpGbts, DaqRate, TCcount, Motherboards)
    regions.append(region)


geometry = tools.prepare_geometry()

for region in regions:
    if region.lr =='0': continue
    if region.plane != '8': continue
    print(f"Region ID: {region.id}, Plane: {region.plane}, LR: {region.lr}")
    MB_ids_for_region = get_MB_ids(region.id)

    df_region = pd.DataFrame(columns=['MB', 'plane', 'TriggerLpGbts'])
    for MB_id in MB_ids_for_region:
        MB, plane = extract_MB_plane_from_MBid(MB_id)
        assert plane != region.plane, f"Planes from region and from MBs are different ({region.plane}, {plane})."

        df_region = df_region.append({'MB': MB, 'plane': plane, 'TriggerLpGbts' : region.TriggerLpGbts}, ignore_index=True)

    modmap_region = pd.merge(df_region, geometry, on=['plane', 'MB'])
    scatter, annotations = tools.plot_modules(modmap_region, 'MB')
    tools.set_figure(scatter, annotations, region.plane, region.section)

