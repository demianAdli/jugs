"""
CityGISOO
Object-Oriented Geographic Information System for Cities
building_contract_adapter module
Reusable building contract GeoJSON adaptation workflow for PyQGIS layers.
Project Developer: Alireza Adli
alireza.adli@concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
from __future__ import annotations

import os
from pathlib import Path

from sabu_chassis.logging import get_logger

from .field_schema_manager import FieldSchemaManager


logger = get_logger(__name__)


class BuildingContractAdapter:
  """Adapt a building layer to a standard GeoJSON contract schema.

  This class handles workflow orchestration only. Field/schema operations are
  delegated to FieldSchemaManager so provider-specific behavior stays in one
  reusable place.
  """

  def __init__(
          self,
          qgis_path,
          input_layer_path,
          input_layer_name,
          output_geojson_path,
          field_rename_map,
          required_fields=None,
          non_null_required_fields=None,
          id_field_name='id',
          id_start_value=1,
          output_layer_name=None,
          field_order=None,
          output_geopackage_path=None):
    self.qgis_path = qgis_path
    self.input_layer_path = input_layer_path
    self.input_layer_name = input_layer_name
    self.output_geojson_path = output_geojson_path
    self.output_geopackage_path = output_geopackage_path
    self.field_rename_map = field_rename_map
    if required_fields is None and isinstance(field_rename_map, dict):
      self.required_fields = list(field_rename_map.values())
    elif required_fields is None:
      self.required_fields = []
    else:
      self.required_fields = list(required_fields)
    if non_null_required_fields is None:
      self.non_null_required_fields = None
    elif isinstance(non_null_required_fields, (str, bytes)):
      raise TypeError(
        'non_null_required_fields must be a list, tuple, set, or None.')
    else:
      self.non_null_required_fields = list(non_null_required_fields)
    if field_order is None:
      self.field_order = None
    else:
      self.field_order = list(field_order)
    self.id_field_name = id_field_name
    self.id_start_value = id_start_value

    self.output_layer_name = (
      output_layer_name
      or (
        Path(output_geojson_path).stem
        if output_geojson_path
        else None))

    self._validate_config()

  @staticmethod
  def _is_geojson_path(path):
    return Path(path).suffix.lower() in ('.geojson', '.json')

  @staticmethod
  def _is_geopackage_path(path):
    return Path(path).suffix.lower() == '.gpkg'

  def _validate_config(self):
    if not self.qgis_path:
      raise ValueError('qgis_path is required.')
    if not self.input_layer_name:
      raise ValueError('input_layer_name is required.')
    if not self.output_geojson_path:
      raise ValueError('output_geojson_path is required.')
    if not self._is_geojson_path(self.output_geojson_path):
      raise ValueError(
        'BuildingContractAdapter output_geojson_path must end with '
        '.geojson or .json.')
    if self.output_geopackage_path:
      if not self._is_geopackage_path(self.output_geopackage_path):
        raise ValueError(
          'BuildingContractAdapter output_geopackage_path must end with '
          '.gpkg.')
      if os.path.abspath(self.output_geopackage_path) == os.path.abspath(
              self.output_geojson_path):
        raise ValueError(
          'output_geopackage_path must differ from output_geojson_path.')
    if not isinstance(self.field_rename_map, dict) or not self.field_rename_map:
      raise ValueError('field_rename_map must be a non-empty dictionary.')
    if not isinstance(self.required_fields, (list, tuple, set)):
      raise TypeError('required_fields must be a list, tuple, or set.')
    if not self.required_fields:
      raise ValueError('required_fields must not be empty.')
    if self.non_null_required_fields is not None:
      if not isinstance(self.non_null_required_fields, (list, tuple, set)):
        raise TypeError(
          'non_null_required_fields must be a list, tuple, set, or None.')
      unknown_non_null_fields = [
        field_name for field_name in self.non_null_required_fields
        if field_name not in self.required_fields
      ]
      if unknown_non_null_fields:
        raise ValueError(
          'non_null_required_fields contains fields outside required_fields: '
          f'{unknown_non_null_fields}')
    if self.field_order is not None:
      if not self.field_order:
        raise ValueError('field_order must not be empty when provided.')
      if len(set(self.field_order)) != len(self.field_order):
        raise ValueError('field_order must not contain duplicate fields.')
      unknown_fields = [
        field_name for field_name in self.field_order
        if field_name not in self.required_fields
      ]
      if unknown_fields:
        raise ValueError(
          'field_order contains fields outside required_fields: '
          f'{unknown_fields}')
    if not isinstance(self.id_start_value, int):
      raise TypeError('id_start_value must be an integer.')

  @property
  def source_required_fields(self):
    return list(self.field_rename_map.keys())

  def run(self):
    """Run the full contract adaptation workflow and return output path."""
    logger.info(
      'Starting building contract adapter. Input=%s Output=%s',
      self.input_layer_path,
      self.output_geojson_path)

    self._prepare_output_directories()
    self._require_existing_input_layer()

    input_manager = self._load_layer(
      self.input_layer_path,
      self.input_layer_name)
    self._ensure_source_fields(input_manager)

    standardized_manager = self._standardize_contract_fields(
      input_manager)
    if self.non_null_required_fields:
      self._drop_null_contract_features(standardized_manager)
    else:
      logger.info(
        'Skipping null-feature deletion because no non-null contract fields '
        'were configured.')
    self._add_feature_ids(standardized_manager)
    if self.output_geopackage_path:
      self._finalize_geopackage_and_geojson(standardized_manager)
    else:
      self._promote_geojson_feature_id(standardized_manager)

    logger.info(
      'Completed building contract adapter. GeoJSON output=%s '
      'GeoPackage output=%s',
      self.output_geojson_path,
      self.output_geopackage_path)
    return self.output_geojson_path

  def _prepare_output_directories(self):
    output_paths = [self.output_geojson_path]
    if self.output_geopackage_path:
      output_paths.append(self.output_geopackage_path)
    for output_path in output_paths:
      output_dir = os.path.dirname(output_path)
      if output_dir:
        os.makedirs(output_dir, exist_ok=True)

  def _require_existing_input_layer(self):
    if not self.input_layer_path:
      message = 'Missing input layer path.'
      logger.error(message)
      raise ValueError(message)

    if not os.path.exists(self.input_layer_path):
      message = f'Input layer path does not exist: {self.input_layer_path}'
      logger.error(message)
      raise FileNotFoundError(message)

  def _load_layer(self, layer_path, layer_name):
    try:
      schema_manager = FieldSchemaManager(
        qgis_path=self.qgis_path,
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

  def _ensure_source_fields(self, schema_manager):
    missing_fields = schema_manager.find_missing_fields(
      self.source_required_fields)
    if missing_fields:
      message = (
        'Input layer is missing fields required before contract renaming: '
        f'{missing_fields}')
      logger.error(message)
      raise KeyError(message)

  def _standardize_contract_fields(self, input_manager):
    try:
      self._ensure_source_fields(input_manager)
      standardized_scrub_layer = input_manager.standardize_fields(
        field_rename_map=self.field_rename_map,
        fields_to_keep=list(self.required_fields),
        field_order=self.field_order,
        output_path=(
          self.output_geopackage_path or self.output_geojson_path),
        output_layer_name=self.output_layer_name)
      standardized_manager = FieldSchemaManager(standardized_scrub_layer)
      missing_standard_fields = standardized_manager.find_missing_fields(
        self.required_fields)
      if missing_standard_fields:
        raise KeyError(
          'Standardized layer is missing required contract fields: '
          f'{missing_standard_fields}')
      return standardized_manager
    except Exception as exc:
      logger.exception(
        'Failed field standardization for contract output %s.',
        self.output_geopackage_path or self.output_geojson_path)
      raise RuntimeError(
        'Failed field standardization: '
        f'{self.output_geopackage_path or self.output_geojson_path}') from exc

  def _drop_null_contract_features(self, schema_manager):
    try:
      schema_manager.drop_null_features(self.non_null_required_fields)
      remaining_null_feature_ids = schema_manager.find_null_feature_ids(
        self.non_null_required_fields)
      if remaining_null_feature_ids:
        raise RuntimeError(
          'Null-feature removal left required-field nulls in feature IDs: '
          f'{remaining_null_feature_ids[:20]}')
    except Exception as exc:
      logger.exception(
        'Failed null-feature removal for contract fields %s.',
        self.non_null_required_fields)
      raise RuntimeError('Failed null-feature removal.') from exc

  def _add_feature_ids(self, schema_manager):
    try:
      feature_count = schema_manager.layer.featureCount()
      schema_manager.add_id_field(
        id_values=range(
          self.id_start_value,
          self.id_start_value + feature_count),
        field_name=self.id_field_name)
    except Exception as exc:
      logger.exception('Failed id-field creation.')
      raise RuntimeError('Failed id-field creation.') from exc

  def _finalize_geopackage_and_geojson(self, geopackage_manager):
    try:
      geopackage_manager.scrub_layer.create_spatial_index()
      geopackage_manager.export_to_geojson(self.output_geojson_path)
      geojson_manager = self._load_layer(
        self.output_geojson_path,
        self.output_layer_name)
      self._promote_geojson_feature_id(geojson_manager)
    except Exception as exc:
      logger.exception(
        'Failed GeoPackage finalization or GeoJSON export. '
        'GeoPackage=%s GeoJSON=%s',
        self.output_geopackage_path,
        self.output_geojson_path)
      raise RuntimeError(
        'Failed GeoPackage finalization or GeoJSON export.') from exc

  def _promote_geojson_feature_id(self, geojson_manager):
    try:
      geojson_manager.promote_feature_id(self.id_field_name)
    except Exception as exc:
      logger.exception('Failed GeoJSON feature id promotion.')
      raise RuntimeError('Failed GeoJSON feature id promotion.') from exc
