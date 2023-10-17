# HGCAL FE to BE mapping
In this repository, part of the code written by me is for understanding how the front-end to back-end mapping of the HGCAL detector has been optimized. The XML files have been copied from the repository at [this link](https://gitlab.cern.ch/hgcal-tpg/mapping/-/tree/master/).

In the xml/ folder:
 - Regions.60.NoSplit.xml contains the regions obtained re-writing the HGCAL front-end geometry from Pedro (v15.3). For each region it is associated a list of motherboards id.
 - S1.SeparateTD.Identical60.SingleTypes.NoSplit.xml contains mapping of regions to S1 FPGA, in a specifc configuration. More information in Andy's repo.
 - S1toChannels.SeparateTD.Identical60.SingleTypes.NoSplit.xml contains, for every S1 FPGA, the output channels and frames.

Python files:
 - FE_to_regions.py: reads the first xml files and produces maps of 60 degree sectors representing the fron-end mapping (how motherboards are mapped into a sector / region). A map is produced per layer (right sector only).
 - regions_to_S1.py: reads the second xml file and produces the region to S1 FPGA map for the whole detector, in this particular configuration.

Some first results are available [here](https://mchiusi.web.cern.ch/BEmapping/).
