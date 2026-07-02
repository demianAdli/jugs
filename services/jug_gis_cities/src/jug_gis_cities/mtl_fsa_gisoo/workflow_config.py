"""
Municipality: Montreal FSA
workflow_config module
Project Developer: Alireza Adli 
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""

import os
import re


_FSA_PATTERN = re.compile(r'^[A-Z][0-9][A-Z]$')

default_data_dir = 'D:/GIS/mtl_gisoo_fsa_data'
data_dir = os.getenv(
  'JUG_GIS_CITIES_MTL_FSA_DATA_DIR',
  default_data_dir)
input_data_dir = os.path.join(data_dir, 'input_data')

# Application's path
qgis_path = os.getenv(
  'JUG_GIS_CITIES_QGIS_PATH',
  'C:/Program Files/QGIS 3.34.1/apps/qgis')

# Gathering input data layers paths 
input_paths = {
  'mtl_property_roll_2025':
  os.path.join(
    input_data_dir,
    'mtl_role_2025_unit_eval_et_address_geopackage',
    'mtl_island_role_2025_unit_eval_et_address.gpkg'),
  'mtl_nrcan_heights':
  os.path.join(
    input_data_dir,
    'mtl_auto_with_heights',
    'mtl_auto_with_heights.gpkg'),
  'mtl_mahm_usage_2026':
  os.path.join(
    input_data_dir,
    'mtl_mahm_usage_2026',
    'mamh_usage_predo_2026_s_poly.shp'),
  'fsa':
  os.path.join(
    input_data_dir,
    'mtl_island_fsa_boundaries',
    'mtl_island_fsa_boundaries_dmti_2025.gpkg')
}
fsa_field_name = 'g_fsa'

# Defining a directory for all the output data layers
output_paths_dir = os.getenv(
  'JUG_GIS_CITIES_MTL_FSA_OUTPUT_DIR',
  os.path.join(data_dir, 'output_data'))


def normalize_fsa(fsa):
  if fsa is None:
    raise ValueError('fsa is required for the Montreal FSA workflow.')
  if not isinstance(fsa, str):
    raise TypeError('fsa must be a string.')

  normalized_fsa = fsa.strip().upper()
  if not _FSA_PATTERN.match(normalized_fsa):
    raise ValueError(
      'fsa must be a three-character Canadian FSA, for example H3H.')
  return normalized_fsa


def get_fsa_output_paths_dir(fsa):
  return os.path.join(output_paths_dir, normalize_fsa(fsa))


# Preparing a bedding for output data layers paths
output_paths = {
  'fsa_boundary': '',
  'nrcan': '',
  'usage': '',
  'roll': '',
  'nrcan_fixed': '',
  'usage_fixed': '',
  'usage_margin_san': '',
  'usage_san_san': '',
  'usage_margin': '',
  'usage_only': '',
  'roll_only': '',
  'usage_roll_only_all': '',
  'usage_roll_only': '',
  'usage_roll_only_unique': '',
  'roll_clean': '',
  'usage_roll': '',
  'usage_roll_all': '',
  'nrcan_preserved': '',
  'usage_dup': '',
  'usage_dup_clean': '',
  'inter_nrcan': '',
  'nrcan_inter': '',
  'inter_summary': '',
  'summary_joined': '',
  'inter_kept': '',
  'nrcan_joined_summary': '',
  'nrcan_restored': '',
  'dominant_parts': '',
  'nrcan_restored_with_usage_id': '',
  'nrcan_intersected': '',
  'nrcan_spatial_join_usage': '',
  'mtl_fsa_gisoo': ''
}
