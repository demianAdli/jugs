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
  'mtl_nrcan_preserved':
  os.path.join(
    input_data_dir,
    'mtl_auto_with_heights_preserved',
    'mtl_auto_with_heights_preserved.gpkg'),
  'mtl_mahm_usage_2026_gpkg':
  os.path.join(
    input_data_dir,
    'mamh_usage_predo_2026_gpkg',
    'mamh_usage_predo_2026_s_poly.gpkg'),
  'mtl_usage_dup':
  os.path.join(
    input_data_dir,
    'mamh_usage_predo_2026_gpkg_dup',
    'mamh_usage_predo_2026_dup.gpkg'),
  'fsa':
  os.path.join(
    input_data_dir,
    'mtl_island_fsa_boundaries',
    'mtl_island_fsa_boundaries_dmti_2025.gpkg')
}
fsa_field_name = 'g_fsa'

nrcan_usage_roll_unnecessary_fields = [
  'layer',
  'path',
  'area_ratio',
  'sum_restore_group',
  'sum_restore_reason',
  'sum_number_parts',
  'sum_min_inter_area',
  'sum_max_inter_area',
  'sum_max_area_ratio',
  'restore_group',
  'restore_reason',
  'ur_area_ex',
  'ur_ro_fid',
  'ur_ro_OBJECTID',
  'ur_ro_id_provinc',
  'ur_ro_code_mun',
  'ur_ro_arrond',
  'ur_ro_rejet',
  'ur_ro_date_entre',
  'ur_ro_mat18',
  'ur_ro_ueid_provinc',
  'ur_ro_uecode_mun',
  'ur_ro_uerl0102a',
  'ur_ro_uerl0105a',
  'ur_ro_uerl0301a',
  'ur_ro_uerl0302a',
  'ur_ro_uerl0304a',
  'ur_ro_uerl0305a',
  'ur_ro_uerl0306a',
  'ur_ro_uerl0307a',
  'ur_ro_uerl0307b',
  'ur_ro_uerl0308a',
  'ur_ro_uerl0309a',
  'ur_ro_uerl0311a',
  'ur_ro_uerl0313a',
  'ur_ro_uerl0310a',
  'ur_ro_ad_addr_count',
  'ur_ro_ad_addr_all',
  'ur_ro_roll_id',
  'ur_layer',
  'ur_path',
  'area_ex',
  'ro_fid',
  'ro_OBJECTID',
  'ro_id_provinc',
  'ro_code_mun',
  'ro_arrond',
  'ro_rejet',
  'ro_date_entre',
  'ro_mat18',
  'ro_ueid_provinc',
  'ro_uecode_mun',
  'ro_uerl0102a',
  'ro_uerl0105a',
  'ro_uerl0301a',
  'ro_uerl0302a',
  'ro_uerl0304a',
  'ro_uerl0305a',
  'ro_uerl0306a',
  'ro_uerl0307a',
  'ro_uerl0307b',
  'ro_uerl0308a',
  'ro_uerl0309a',
  'ro_uerl0311a',
  'ro_uerl0313a',
  'ro_uerl0310a',
  'ro_ad_addr_count',
  'ro_ad_addr_all',
]

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
  'nrcan_preserved': '',
  'usage_dup': '',
  'nrcan': '',
  'usage': '',
  'roll': '',
  'nrcan_fixed': '',
  'nrcan_preserved_fixed': '',
  'usage_fixed': '',
  'usage_dup_fixed': '',
  'usage_margin_san': '',
  'usage_clean': '',
  'usage_margin': '',
  'usage_only': '',
  'roll_only': '',
  'usage_roll_only_all': '',
  'usage_roll_only': '',
  'usage_roll_only_unique': '',
  'roll_clean': '',
  'usage_roll': '',
  'usage_roll_all': '',
  'usage_dup_clean': '',
  'inter_nrcan': '',
  'inter_summary': '',
  'summary_joined': '',
  'inter_kept': '',
  'nrcan_joined_summary': '',
  'nrcan_restored': '',
  'dominant_parts': '',
  'nrcan_restored_with_usage_id': '',
  'nrcan_intersected': '',
  'nrcan_intersected_points': '',
  'nrcan_in_usage_roll_points': '',
  'nrcan_usage_roll_with_missing': '',
  'usage_roll_all_only': '',
  'nrcan_usage_roll': '',
  'mtl_fsa_gisoo': '',
}
