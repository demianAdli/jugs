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
          id_field_name='id',
          id_start_value=1,
          output_layer_name=None,
          field_order=None):
    self.qgis_path = qgis_path
    self.input_layer_path = input_layer_path
    self.input_layer_name = input_layer_name
    self.output_geojson_path = output_geojson_path
    self.field_rename_map = field_rename_map
    if required_fields is None and isinstance(field_rename_map, dict):
      self.required_fields = list(field_rename_map.values())
    elif required_fields is None:
      self.required_fields = []
    else:
      self.required_fields = list(required_fields)
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
    if not isinstance(self.field_rename_map, dict) or not self.field_rename_map:
      raise ValueError('field_rename_map must be a non-empty dictionary.')
    if not isinstance(self.required_fields, (list, tuple, set)):
      raise TypeError('required_fields must be a list, tuple, or set.')
    if not self.required_fields:
      raise ValueError('required_fields must not be empty.')
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
    self._drop_null_contract_features(standardized_manager)
    self._add_and_promote_feature_ids(standardized_manager)

    logger.info(
      'Completed building contract adapter. GeoJSON output=%s',
      self.output_geojson_path)
    return self.output_geojson_path

  def _prepare_output_directories(self):
    output_dir = os.path.dirname(self.output_geojson_path)
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
        output_path=self.output_geojson_path,
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
        'Failed field standardization for contract GeoJSON %s.',
        self.output_geojson_path)
      raise RuntimeError(
        f'Failed field standardization: {self.output_geojson_path}') from exc

  def _drop_null_contract_features(self, schema_manager):
    try:
      schema_manager.drop_null_features(self.required_fields)
      remaining_null_feature_ids = schema_manager.find_null_feature_ids(
        self.required_fields)
      if remaining_null_feature_ids:
        raise RuntimeError(
          'Null-feature removal left required-field nulls in feature IDs: '
          f'{remaining_null_feature_ids[:20]}')
    except Exception as exc:
      logger.exception(
        'Failed null-feature removal for contract fields %s.',
        self.required_fields)
      raise RuntimeError('Failed null-feature removal.') from exc

  def _add_and_promote_feature_ids(self, schema_manager):
    try:
      feature_count = schema_manager.layer.featureCount()
      schema_manager.add_id_field(
        id_values=range(
          self.id_start_value,
          self.id_start_value + feature_count),
        field_name=self.id_field_name)
      schema_manager.promote_feature_id(self.id_field_name)
    except Exception as exc:
      logger.exception(
        'Failed id-field creation or GeoJSON feature id promotion.')
      raise RuntimeError(
        'Failed id-field creation or GeoJSON feature id promotion.') from exc
