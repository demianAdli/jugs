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

from citygisoo.field_schema_manager import FieldSchemaManager
import workflow_config as paths

workflow_output_layer_name = 'saint_malachie_gisoo_with_fsa'
workflow_output_layer_suffix = '.shp'
workflow_output_layer_path = \
    paths.output_paths_dir + \
    workflow_output_layer_name + \
    workflow_output_layer_suffix

output_layer_relative_path = 'saint_malachie_standardized.shp'
output_layer_path = paths.output_paths_dir + output_layer_relative_path

rename_fields = {
    'g_id_provi': 'name',
    'heightmax': 'height',
    'g_utilisat': 'function',
    'rl_ad_ad_1': 'address',
    'rl_uerl0_6': 'year_of_construction'
}

keep_set = rename_fields.keys()

saint_malachie_schema_manager = FieldSchemaManager(
    qgis_path=paths.qgis_path,
    layer_path=workflow_output_layer_path,
    layer_name='saint_malachie_gisoo_with_fsa'
)

standardized_saint_malachie = \
    saint_malachie_schema_manager.standardize_fields(
        field_rename_map=rename_fields,
        fields_to_keep=keep_set,
        output_path=output_layer_path,
        output_layer_name='standardized_saint_malachie'
    )

