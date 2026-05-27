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

from citygisoo import BuildingContractAdapter
import workflow_config as paths


workflow_output_layer_name = 'saint_malachie_gisoo_with_fsa'
workflow_output_layer_suffix = '.shp'
workflow_output_layer_path = \
    os.path.join(
        paths.output_paths_dir,
        workflow_output_layer_name,
        workflow_output_layer_name + workflow_output_layer_suffix)

output_layer_name = 'saint_malachie_standardized'
output_layer_suffix = '.geojson'
output_layer_path = os.path.join(
    paths.output_paths_dir,
    output_layer_name,
    output_layer_name + output_layer_suffix)

contract_source_layer_name = 'saint_malachie_contract_source'
contract_source_layer_path = os.path.join(
    paths.output_paths_dir,
    output_layer_name,
    contract_source_layer_name + '.geojson')

id_field_name = 'id'
id_start_value = 100000

rename_fields = {
    'g_id_provi': 'name',
    'heightmax': 'height',
    'g_utilisat': 'function',
    'rl_ad_ad_1': 'address',
    'rl_uerl0_6': 'year_of_construction'
}

required_fields = list(rename_fields.values())


def run_contract_adapter():
    adapter = BuildingContractAdapter(
        qgis_path=paths.qgis_path,
        input_layer_path=workflow_output_layer_path,
        input_layer_name=workflow_output_layer_name,
        output_geojson_path=output_layer_path,
        field_rename_map=rename_fields,
        required_fields=required_fields,
        id_field_name=id_field_name,
        id_start_value=id_start_value,
        source_geojson_path=contract_source_layer_path,
        source_geojson_layer_name=contract_source_layer_name,
        output_layer_name='standardized_saint_malachie')
    return adapter.run()


standardized_output_path = run_contract_adapter()
