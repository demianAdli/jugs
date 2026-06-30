"""
Sabu project
Service jug_gis_cities
Municipality: Montreal FSA
contract_adapter module
This prepares the given geojson file for building LCA.
Project Developer: Alireza Adli 
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""

import argparse
import os
from time import perf_counter

from citygisoo import BuildingContractAdapter
from sabu_chassis.logging import configure_logging, get_logger

try:
    from . import workflow_config as paths
except ImportError:
    import workflow_config as paths


logger = get_logger(__name__)

workflow_output_layer_name = 'mtl_fsa_gisoo'
workflow_output_layer_suffix = '.shp'

output_layer_name = 'mtl_fsa_standardized'
output_layer_suffix = '.geojson'

contract_source_layer_name = 'mtl_fsa_contract_source'

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


def _build_adapter_paths(fsa):
    output_paths_dir = paths.get_fsa_output_paths_dir(fsa)
    workflow_output_layer_path = os.path.join(
        output_paths_dir,
        workflow_output_layer_name,
        workflow_output_layer_name + workflow_output_layer_suffix)
    output_layer_path = os.path.join(
        output_paths_dir,
        output_layer_name,
        output_layer_name + output_layer_suffix)
    contract_source_layer_path = os.path.join(
        output_paths_dir,
        output_layer_name,
        contract_source_layer_name + '.geojson')
    return (
        workflow_output_layer_path,
        output_layer_path,
        contract_source_layer_path,
    )


def run_contract_adapter(fsa):
    """Run the Montreal FSA building contract adaptation workflow."""
    normalized_fsa = paths.normalize_fsa(fsa)
    (
        workflow_output_layer_path,
        output_layer_path,
        contract_source_layer_path,
    ) = _build_adapter_paths(normalized_fsa)
    adapter_t0 = perf_counter()
    logger.info(
        'Starting Montreal FSA contract adapter. FSA=%s Input=%s Output=%s',
        normalized_fsa,
        workflow_output_layer_path,
        output_layer_path)

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
        output_layer_name='standardized_mtl_fsa')

    try:
        standardized_output_path = adapter.run()
    except Exception:
        logger.exception(
            'Montreal FSA contract adapter failed. FSA=%s',
            normalized_fsa)
        raise

    logger.info(
        'Completed Montreal FSA contract adapter. FSA=%s Output=%s '
        'Elapsed=%.3fs',
        normalized_fsa,
        standardized_output_path,
        perf_counter() - adapter_t0)
    return standardized_output_path


if __name__ == '__main__':
    configure_logging()
    parser = argparse.ArgumentParser(
        description='Run the Montreal FSA contract adapter directly.')
    parser.add_argument(
        '--fsa',
        required=True,
        help='Three-character Montreal FSA, for example H3H.')
    args = parser.parse_args()
    run_contract_adapter(args.fsa)
