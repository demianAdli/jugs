"""
Municipality: Saint-Malachie
workflow_config module
Project Developer: Alireza Adli 
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""

import os


default_data_dir = 'D:/GIS/saint_malachie_gisoo_data'
data_dir = os.getenv(
  'JUG_GIS_CITIES_SAINT_MALACHIE_DATA_DIR',
  default_data_dir)
input_data_dir = os.path.join(data_dir, 'input_data')

# Application's path
qgis_path = os.getenv(
  'JUG_GIS_CITIES_QGIS_PATH',
  'C:/Program Files/QGIS 3.34.1/apps/qgis')

# Gathering input data layers paths 
input_paths = {
  'qc_property_roll_2025':
  os.path.join(
    input_data_dir,
    'saint_malachie_role_2025_unit_eval_et_address_geopackage',
    'role_2025_unit_eval_et_address_geopackage_quebec.gpkg'),
  'nrcan_heights':
  os.path.join(
    input_data_dir,
    'saint_malachie_auto_with_heights',
    'saint_malachie_auto_with_heights.gpkg'),
  'qc_geoindex':
  os.path.join(
    input_data_dir,
    'saint_malachie_mahm_usage_2025',
    'mamh_usage_predo_2025_s_poly.shp'),
  'fsa':
  os.path.join(
    input_data_dir,
    'forward_sortation_areas',
    'dmti_forwardsortationareas_2025_s_poly.shp')
}

# Defining a directory for all the output data layers
output_paths_dir = os.getenv(
  'JUG_GIS_CITIES_SAINT_MALACHIE_OUTPUT_DIR',
  os.path.join(data_dir, 'output_data'))

# Preparing a bedding for output data layers paths
output_paths = {
  'nrcan_fixed': '',
  'geoindex_fixed': '',
  'geoindex_field_join_roll': '',
  'nrcan_spatial_join_geoindex': '',
  'saint_malachie_gisoo_with_fsa': ''
}
