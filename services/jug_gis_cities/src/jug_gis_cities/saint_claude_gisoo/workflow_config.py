"""
Municipality: Saint-Claude
workflow_config module
Project Developer: Alireza Adli 
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
# Application's path
qgis_path = 'C:/Program Files/QGIS 3.34.1/apps/qgis'

# Gathering input data layers paths
input_paths = {
  'CERC Boundary':
  'C:/Users/a_adli/PycharmProjects/mtl_gis_oo/input_data/'
  'cerc_district_111/layer_111.shp'
}

# Defining a directory for all the output data layers
output_paths_dir = \
  'C:/Users/a_adli/PycharmProjects/saint_claude/' \
  'output_data'

# Preparing a bedding for output data layers paths
output_paths = {
  'Fixed NRCan': '',
  'NRCan CERC Fixed': '',
  'Fixed GeoIndex': '',
  'Clipped Fixed GeoIndex': '',
  'CERC Property Assessment': '',
  'Splitted CERC NRCans': '',
  'Pairwise Clipped Property Assessment Partitions': '',
  'Pairwise Clipped Merged Property Assessment': '',
  'Property Assessment and NRCan': '',
  'Property Assessment and NRCan and GeoIndex': '',
  'Deleted Duplicates Layer': '',
  'Single Parts Layer': ''
}
