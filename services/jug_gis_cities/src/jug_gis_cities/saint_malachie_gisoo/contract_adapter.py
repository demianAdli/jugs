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
from time import perf_counter

from citygisoo import BuildingContractAdapter
from sabu_chassis.logging import configure_logging, get_logger

try:
    from . import workflow_config as paths
except ImportError:
    import workflow_config as paths


logger = get_logger(__name__)

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
    """Run the Saint-Malachie building contract adaptation workflow."""
    adapter_t0 = perf_counter()
    logger.info(
        'Starting Saint-Malachie contract adapter. Input=%s Output=%s',
        workflow_output_layer_path,
        output_layer_path)

    adapter = BuildingContractAdapter(
        qgis_path=paths.qgis_path,
        input_layer_path=workflow_output_layer_path,
        input_layer_name=workflow_output_layer_name,
        output_geojson_path=output_layer_path,
        field_rename_map=rename_fields,
        required_fields=required_fields,
        non_null_required_fields=required_fields,
        id_field_name=id_field_name,
        id_start_value=id_start_value,
        output_layer_name='standardized_saint_malachie')

    try:
        standardized_output_path = adapter.run()
    except Exception:
        logger.exception('Saint-Malachie contract adapter failed.')
        raise

    logger.info(
        'Completed Saint-Malachie contract adapter. Output=%s Elapsed=%.3fs',
        standardized_output_path,
        perf_counter() - adapter_t0)
    return standardized_output_path


if __name__ == '__main__':
    configure_logging()
    run_contract_adapter()
