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

workflow_output_layer_name = 'mtl_{fsa}_gisoo'
workflow_output_layer_suffix = '.gpkg'

output_layer_name = 'mtl_fsa_standardized'
output_layer_suffix = '.geojson'

id_field_name = 'id'
id_start_value = 100000

rename_fields = {
    'citygisoo_id': 'citygisoo_id',
    'processing_tool': 'processing_tool',
    'processed_by': 'processed_by',
    'FSA': 'FSA',
    'citygisoo_area': 'citygisoo_area',
    '_max': 'height',
    'ur_r_uerl0105a': 'function',
    'ur_r_uerl0307a': 'year_of_construction',
    'ur_g_id_provi': 'usage_provincial_id',
    'ur_r_ueid_provinc': 'roll_provincial_id',
    'bldgarea': 'nrcan_building_area',
    'ur_r_uerl0302a': 'roll_area',
    'ur_g_sup_tota': 'usage_area',
    'ur_ro_uerl0308a': 'main_floor_area',
    'ur_ro_uerl0306a': 'floor_num',
    'ur_ro_uerl0311a': 'unit_num',
    'ur_g_utilisat': 'usage_function',
    '_mean': 'mean_height',
}

required_fields = list(rename_fields.values())
field_order = list(required_fields)


def _build_adapter_paths(fsa):
    output_paths_dir = paths.get_fsa_output_paths_dir(fsa)
    resolved_workflow_output_layer_name = workflow_output_layer_name.format(
        fsa=fsa)
    workflow_output_layer_path = os.path.join(
        output_paths_dir,
        resolved_workflow_output_layer_name,
        resolved_workflow_output_layer_name + workflow_output_layer_suffix)
    output_layer_path = os.path.join(
        output_paths_dir,
        output_layer_name,
        output_layer_name + output_layer_suffix)
    return (
        workflow_output_layer_path,
        output_layer_path,
    )


def run_contract_adapter(fsa, non_null_required_fields=None):
    """Run the Montreal FSA building contract adaptation workflow."""
    normalized_fsa = paths.normalize_fsa(fsa)
    (
        workflow_output_layer_path,
        output_layer_path,
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
        input_layer_name=workflow_output_layer_name.format(
            fsa=normalized_fsa),
        output_geojson_path=output_layer_path,
        field_rename_map=rename_fields,
        required_fields=required_fields,
        non_null_required_fields=non_null_required_fields,
        id_field_name=id_field_name,
        id_start_value=id_start_value,
        output_layer_name='standardized_mtl_fsa',
        field_order=field_order)

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
    parser.add_argument(
        '--drop-null-fields',
        nargs='+',
        default=None,
        metavar='FIELD',
        help=(
            'Optional standardized field names that must be non-null. '
            'Features with null or empty values in any listed field are '
            'deleted. By default, no features are deleted based on null '
            'attributes.'))
    args = parser.parse_args()
    run_contract_adapter(
        args.fsa,
        non_null_required_fields=args.drop_null_fields)
