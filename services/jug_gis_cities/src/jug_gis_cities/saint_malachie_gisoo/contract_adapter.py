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

finalized_layer_name = 'saint_malachie_gisoo_with_fsa'
finalized_layer_suffix = '.shp'
finalized_layer_path = paths.output_paths_dir + finalized_layer_name + \
  finalized_layer_suffix

field_schema_manager = FieldSchemaManager(
    qgis_path=paths.qgis_path,
    layer_path=finalized_layer_path,
    layer_name='saint_malachie_gisoo_with_fsa'
)

