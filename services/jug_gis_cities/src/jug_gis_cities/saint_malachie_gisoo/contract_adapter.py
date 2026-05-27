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

from sabu_chassis.logging import get_logger
from citygisoo.field_schema_manager import FieldSchemaManager
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
os.makedirs(os.path.dirname(output_layer_path), exist_ok=True)

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

source_required_fields = list(rename_fields.keys())
required_fields = list(rename_fields.values())


def _require_existing_input_layer(layer_path):
    if not layer_path:
        message = 'Missing workflow output layer path.'
        logger.error(message)
        raise ValueError(message)

    if not os.path.exists(layer_path):
        message = f'Workflow output layer path does not exist: {layer_path}'
        logger.error(message)
        raise FileNotFoundError(message)


def _load_layer(layer_path, layer_name):
    try:
        schema_manager = FieldSchemaManager(
            qgis_path=paths.qgis_path,
            layer_path=layer_path,
            layer_name=layer_name)
        if not schema_manager.layer.isValid():
            raise ValueError(f'Layer is invalid: {layer_path}')
        return schema_manager
    except Exception as exc:
        logger.exception(
            'Failed to load layer %s from %s.',
            layer_name,
            layer_path)
        raise RuntimeError(
            f'Invalid or unloaded layer {layer_name} at {layer_path}') from exc


def _ensure_source_fields(schema_manager):
    missing_fields = schema_manager.find_missing_fields(source_required_fields)
    if missing_fields:
        message = (
            'Workflow output is missing fields required before contract '
            f'renaming: {missing_fields}')
        logger.error(message)
        raise KeyError(message)


def _export_workflow_output_to_geojson(schema_manager):
    try:
        exported_path = schema_manager.export_to_geojson(
            contract_source_layer_path)
    except Exception as exc:
        logger.exception(
            'Failed to export workflow output layer %s to GeoJSON at %s.',
            workflow_output_layer_path,
            contract_source_layer_path)
        raise RuntimeError(
            f'Failed GeoJSON export: {contract_source_layer_path}') from exc

    logger.info('Workflow output exported to GeoJSON: %s', exported_path)
    return exported_path


def _standardize_contract_fields(source_geojson_manager):
    try:
        _ensure_source_fields(source_geojson_manager)
        standardized_scrub_layer = source_geojson_manager.standardize_fields(
            field_rename_map=rename_fields,
            fields_to_keep=required_fields,
            output_path=output_layer_path,
            output_layer_name='standardized_saint_malachie')
        standardized_manager = FieldSchemaManager(standardized_scrub_layer)
        missing_standard_fields = standardized_manager.find_missing_fields(
            required_fields)
        if missing_standard_fields:
            raise KeyError(
                'Standardized layer is missing required contract fields: '
                f'{missing_standard_fields}')
        return standardized_manager
    except Exception as exc:
        logger.exception(
            'Failed field standardization for contract GeoJSON %s.',
            output_layer_path)
        raise RuntimeError(
            f'Failed field standardization: {output_layer_path}') from exc


def _drop_null_contract_features(schema_manager):
    try:
        schema_manager.drop_null_features(required_fields)
        remaining_null_feature_ids = schema_manager.find_null_feature_ids(
            required_fields)
        if remaining_null_feature_ids:
            raise RuntimeError(
                'Null-feature removal left required-field nulls in feature '
                f'IDs: {remaining_null_feature_ids[:20]}')
    except Exception as exc:
        logger.exception(
            'Failed null-feature removal for contract fields %s.',
            required_fields)
        raise RuntimeError('Failed null-feature removal.') from exc


def _add_and_promote_feature_ids(schema_manager):
    try:
        feature_count = schema_manager.layer.featureCount()
        schema_manager.add_id_field(
            id_values=range(id_start_value, id_start_value + feature_count),
            field_name=id_field_name)
        schema_manager.promote_feature_id(id_field_name)
    except Exception as exc:
        logger.exception(
            'Failed id-field creation or GeoJSON feature id promotion.')
        raise RuntimeError(
            'Failed id-field creation or GeoJSON feature id promotion.'
        ) from exc


def run_contract_adapter():
    logger.info(
        'Starting Saint-Malachie contract adapter. Input=%s Output=%s',
        workflow_output_layer_path,
        output_layer_path)

    _require_existing_input_layer(workflow_output_layer_path)

    workflow_manager = _load_layer(
        workflow_output_layer_path,
        workflow_output_layer_name)
    _ensure_source_fields(workflow_manager)

    source_geojson_path = _export_workflow_output_to_geojson(workflow_manager)
    source_geojson_manager = _load_layer(
        source_geojson_path,
        contract_source_layer_name)

    standardized_manager = _standardize_contract_fields(source_geojson_manager)
    _drop_null_contract_features(standardized_manager)
    _add_and_promote_feature_ids(standardized_manager)

    logger.info(
        'Completed Saint-Malachie contract adapter. GeoJSON output=%s',
        output_layer_path)
    return output_layer_path


standardized_output_path = run_contract_adapter()
