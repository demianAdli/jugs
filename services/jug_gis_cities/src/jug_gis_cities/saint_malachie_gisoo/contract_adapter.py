"""
Sabu project
Service jug_gis_cities
Municipality: Saint-Malachie
contract_adapter module
This prepares the given geojson file for building LCA.
Project Developer: Alireza Adli 
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""

import os
import sys


def _add_repo_libs_to_path():
    """Support running this file directly with pyqgis from its folder."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = current_dir
    while repo_root and os.path.basename(repo_root) != 'sabu':
        parent_dir = os.path.dirname(repo_root)
        if parent_dir == repo_root:
            return
        repo_root = parent_dir

    for relative_path in (
            os.path.join('libs', 'citygisoo', 'src'),
            os.path.join('libs', 'sabu_chassis', 'src')):
        absolute_path = os.path.join(repo_root, relative_path)
        if os.path.isdir(absolute_path) and absolute_path not in sys.path:
            sys.path.insert(0, absolute_path)


_add_repo_libs_to_path()

from citygisoo.field_schema_manager import FieldSchemaManager
import workflow_config as paths

workflow_output_layer_name = 'saint_malachie_gisoo_with_fsa'
workflow_output_layer_suffix = '.shp'
workflow_output_layer_path = \
    os.path.join(
        paths.output_paths_dir,
        workflow_output_layer_name,
        workflow_output_layer_name + workflow_output_layer_suffix)

output_layer_name = 'saint_malachie_standardized'
output_layer_suffix = '.shp'
output_layer_path = os.path.join(
    paths.output_paths_dir,
    output_layer_name,
    output_layer_name + output_layer_suffix)
os.makedirs(os.path.dirname(output_layer_path), exist_ok=True)

id_field_name = 'id'
id_start_value = 100000

rename_fields = {
    'g_id_provi': 'name',
    'heightmax': 'height',
    'g_utilisat': 'function',
    'rl_ad_ad_1': 'address',
    'rl_uerl0_6': 'year_of_construction'
}

keep_set = list(rename_fields.keys())
required_fields = list(rename_fields.values())

saint_malachie_schema_manager = FieldSchemaManager(
    qgis_path=paths.qgis_path,
    layer_path=workflow_output_layer_path,
    layer_name='saint_malachie_gisoo_with_fsa'
)

standardized_saint_malachie = FieldSchemaManager(
    saint_malachie_schema_manager.standardize_fields(
        field_rename_map=rename_fields,
        fields_to_keep=keep_set,
        output_path=output_layer_path,
        output_layer_name='standardized_saint_malachie'
    ))

standardized_saint_malachie.drop_null_features(required_fields)

feature_count = standardized_saint_malachie.layer.featureCount()
standardized_saint_malachie.add_id_field(
    id_values=range(
        id_start_value,
        id_start_value + feature_count),
    field_name=id_field_name)

if output_layer_suffix.lower() in ('.geojson', '.json'):
    standardized_saint_malachie.promote_feature_id(id_field_name)
