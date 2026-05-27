"""
CityGISOO
Object-Oriented Geographic Information System for Cities
field_schema_manager module
Attribute-field schema management helpers for PyQGIS layers.
Project Developer: Alireza Adli
alireza.adli@concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from sabu_chassis.logging import get_logger
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import (
  QgsApplication,
  QgsField,
  QgsProject,
  QgsVectorDataProvider,
  QgsVectorFileWriter,
  edit,
)
from qgis.PyQt.QtCore import QVariant


logger = get_logger(__name__)


class FieldSchemaManager:
  """Manage attribute-field schema operations for a ScrubLayer.

  The manager is intentionally limited to attribute schema changes. It does
  not transform CRS, repair geometries, or change feature geometries. These
  operations help prepare cleaned layers for expected downstream schemas.
  It can receive an existing ScrubLayer or create one from layer path inputs.
  """

  _DRIVERS_BY_EXTENSION = {
    '.shp': 'ESRI Shapefile',
    '.geojson': 'GeoJSON',
    '.json': 'GeoJSON',
    '.gpkg': 'GPKG',
  }

  _WRITER_NO_ERROR = getattr(QgsVectorFileWriter, 'NoError', 0)

  def __init__(
          self,
          scrub_layer=None,
          layer_path=None,
          layer_name=None,
          qgis_path=None):
    """Create a manager from a ScrubLayer or direct layer path inputs.

    Supported forms:
      FieldSchemaManager(scrub_layer)
      FieldSchemaManager(qgis_path, layer_path, layer_name)
      FieldSchemaManager(qgis_path='...', layer_path='...', layer_name='...')
    """
    if isinstance(scrub_layer, str):
      if qgis_path is not None:
        raise ValueError(
          'qgis_path was provided twice. Use either positional arguments '
          'or keyword arguments.')
      qgis_path = scrub_layer
      scrub_layer = None

    if scrub_layer is not None:
      direct_args_provided = (
        layer_path is not None
        or layer_name is not None
        or qgis_path is not None
      )
      if direct_args_provided:
        raise ValueError(
          'Provide either scrub_layer or direct path arguments, not both.')
      self.scrub_layer = scrub_layer
      self._validate_layer()
      return

    if qgis_path is None or layer_path is None:
      raise ValueError(
        'FieldSchemaManager requires either a ScrubLayer instance or both '
        'qgis_path and layer_path.')

    if layer_name is None:
      layer_name = os.path.splitext(os.path.basename(layer_path))[0]

    from .scrub_layer_class import ScrubLayer

    self.scrub_layer = ScrubLayer(qgis_path, layer_path, layer_name)
    self._validate_layer()

  @property
  def layer(self):
    """Return the managed QGIS vector layer."""
    layer = getattr(self.scrub_layer, 'layer', None)
    if layer is None:
      raise RuntimeError('FieldSchemaManager has no QGIS layer attached.')
    return layer

  def _field_names(self):
    self._validate_layer()
    return [field.name() for field in self.layer.fields()]

  def list_fields(self):
    """Return the current layer field names."""
    return self._field_names()

  def has_field(self, field_name):
    """Return True when field_name exists on the current layer."""
    self._validate_field_name(field_name, 'field_name')
    return field_name in self._field_names()

  @staticmethod
  def _validate_field_name(field_name, parameter_name):
    if not isinstance(field_name, str) or not field_name:
      raise ValueError(f'{parameter_name} must be a non-empty string.')

  @staticmethod
  def _validate_field_collection(fields, parameter_name):
    if not isinstance(fields, (list, tuple, set)):
      raise TypeError(f'{parameter_name} must be a list, tuple, or set.')

    field_list = list(fields)
    for field_name in field_list:
      FieldSchemaManager._validate_field_name(field_name, parameter_name)
    return field_list

  @staticmethod
  def _driver_name(output_path):
    extension = os.path.splitext(output_path)[1].lower()
    return FieldSchemaManager._DRIVERS_BY_EXTENSION.get(
      extension, 'ESRI Shapefile')

  @staticmethod
  def _writer_error_code(writer_result):
    if isinstance(writer_result, tuple):
      return writer_result[0]
    return writer_result

  @staticmethod
  def _writer_error_message(writer_result):
    if isinstance(writer_result, tuple) and len(writer_result) > 1:
      return writer_result[1]
    return writer_result

  @staticmethod
  def _same_path(first_path, second_path):
    return os.path.abspath(first_path) == os.path.abspath(second_path)

  @staticmethod
  def _is_geojson_path(path):
    return os.path.splitext(path)[1].lower() in ('.geojson', '.json')

  def _layer_name(self):
    scrub_layer = getattr(self, 'scrub_layer', None)
    layer_name = getattr(scrub_layer, 'layer_name', None)
    if layer_name:
      return layer_name
    layer = getattr(scrub_layer, 'layer', None)
    layer_name_func = getattr(layer, 'name', None)
    if callable(layer_name_func):
      return layer_name_func()
    return '<unknown>'

  def _layer_path(self):
    return getattr(getattr(self, 'scrub_layer', None), 'layer_path', None)

  def _provider(self):
    self._validate_layer(require_provider=False)
    provider = self.layer.dataProvider()
    if provider is None:
      message = f'Layer {self._layer_name()} has no data provider.'
      logger.error(message)
      raise RuntimeError(message)
    return provider

  def _provider_name(self):
    try:
      provider = self.layer.dataProvider()
    except RuntimeError:
      return 'unknown'
    if provider is None:
      return 'none'
    for attribute in ('name', 'storageType'):
      provider_value = getattr(provider, attribute, None)
      if callable(provider_value):
        try:
          value = provider_value()
        except Exception:
          continue
        if value:
          return value
    provider_type = getattr(self.layer, 'providerType', None)
    if callable(provider_type):
      try:
        return provider_type()
      except Exception:
        pass
    return provider.__class__.__name__

  def _validate_layer(self, require_provider=True):
    layer = getattr(getattr(self, 'scrub_layer', None), 'layer', None)
    layer_name = getattr(
      getattr(self, 'scrub_layer', None),
      'layer_name',
      '<unknown>')
    if layer is None:
      message = f'Layer {layer_name} is not available.'
      logger.error(message)
      raise RuntimeError(message)

    is_valid = getattr(layer, 'isValid', None)
    if callable(is_valid) and not is_valid():
      message = f'Layer {layer_name} is invalid.'
      logger.error(message)
      raise ValueError(message)

    if require_provider and layer.dataProvider() is None:
      message = f'Layer {layer_name} has no data provider.'
      logger.error(message)
      raise RuntimeError(message)

    return layer

  def _require_provider_capability(self, capability_name, operation):
    provider = self._provider()
    capability = getattr(QgsVectorDataProvider, capability_name, None)
    if capability is None:
      logger.debug(
        'QGIS capability %s is not available; attempting %s on layer %s '
        'with provider %s.',
        capability_name,
        operation,
        self._layer_name(),
        self._provider_name())
      return

    capabilities = provider.capabilities()
    if not capabilities & capability:
      message = (
        f'Provider {self._provider_name()} for layer {self._layer_name()} '
        f'does not support {operation}.')
      logger.error(message)
      raise RuntimeError(message)

  def _raise_provider_operation_failed(self, operation):
    message = (
      f'Provider operation failed while attempting {operation} on layer '
      f'{self._layer_name()} using provider {self._provider_name()}.')
    logger.error(message)
    raise RuntimeError(message)

  def _write_layer(self, output_path, field_order=None, driver_name=None):
    self._validate_layer()
    if not isinstance(output_path, (str, os.PathLike)) or not str(output_path):
      raise ValueError('output_path must be a non-empty path.')
    output_path = str(output_path)

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = driver_name or self._driver_name(output_path)
    options.fileEncoding = 'utf-8'
    if hasattr(options, 'actionOnExistingFile'):
      overwrite_action = getattr(
        QgsVectorFileWriter, 'CreateOrOverwriteFile', None)
      if overwrite_action is not None:
        options.actionOnExistingFile = overwrite_action

    if field_order is not None:
      options.attributes = [
        self.layer.fields().indexFromName(field_name)
        for field_name in field_order
      ]
      if any(attribute_idx == -1 for attribute_idx in options.attributes):
        missing_fields = [
          field_name
          for field_name, attribute_idx in zip(field_order, options.attributes)
          if attribute_idx == -1
        ]
        raise KeyError(
          f'Cannot export missing fields from layer {self._layer_name()}: '
          f'{missing_fields}')

    logger.info(
      'Writing layer %s to %s with driver %s using provider %s.',
      self._layer_name(),
      output_path,
      options.driverName,
      self._provider_name())
    try:
      writer_v3 = getattr(QgsVectorFileWriter, 'writeAsVectorFormatV3', None)
      if callable(writer_v3):
        writer_result = writer_v3(
          self.layer,
          output_path,
          QgsProject.instance().transformContext(),
          options)
      else:
        writer_result = QgsVectorFileWriter.writeAsVectorFormat(
          self.layer, output_path, options)
    except Exception:
      logger.exception(
        'Failed exporting layer %s to %s with driver %s.',
        self._layer_name(),
        output_path,
        options.driverName)
      raise
    error_code = self._writer_error_code(writer_result)
    if error_code != self._WRITER_NO_ERROR:
      message = (
        f'Failed to write layer {self._layer_name()} to {output_path} '
        f'with driver {options.driverName}: '
        f'{self._writer_error_message(writer_result)}')
      logger.error(message)
      raise RuntimeError(message)

    if not os.path.exists(output_path):
      message = (
        f'Export reported success but output was not created: {output_path}')
      logger.error(message)
      raise RuntimeError(message)
    logger.info('Exported layer %s to %s.', self._layer_name(), output_path)

  def export_to_geojson(self, output_path):
    """Export the managed layer to GeoJSON.

    The export delegates to QGIS/GDAL so geometry, CRS, attributes, and field
    order are preserved as far as the active QGIS version and GeoJSON driver
    support them.
    """
    self._validate_layer()
    if not isinstance(output_path, (str, os.PathLike)) or not str(output_path):
      raise ValueError('output_path must be a non-empty path.')

    output_path = str(output_path)
    if not self._is_geojson_path(output_path):
      raise ValueError(
        'export_to_geojson output_path must end with .geojson or .json.')

    output_parent = Path(output_path).parent
    if output_parent and not output_parent.exists():
      message = f'GeoJSON export directory does not exist: {output_parent}'
      logger.error(message)
      raise FileNotFoundError(message)

    current_path = self._layer_path()
    if current_path and self._same_path(output_path, current_path):
      raise ValueError(
        'export_to_geojson output_path must differ from the current layer '
        'path.')

    field_order = self._field_names()
    logger.info(
      'Exporting layer %s to GeoJSON at %s with %s fields, %s features, '
      'CRS %s, provider %s.',
      self._layer_name(),
      output_path,
      len(field_order),
      self.layer.featureCount(),
      self.layer.crs().authid(),
      self._provider_name())
    self._write_layer(
      output_path,
      field_order=field_order,
      driver_name='GeoJSON')
    return output_path

  def _replace_current_layer(self, replacement_path):
    self._reload_without_source()
    self.scrub_layer._replace_layer_files(
      replacement_path, self.scrub_layer.layer_path)
    self.scrub_layer.layer = self.scrub_layer.load_layer()
    self.scrub_layer.data_count = self.scrub_layer.layer.featureCount()
    self._validate_layer()

  def _reload_without_source(self):
    self._validate_layer(require_provider=False)
    old_layer_id = self.layer.id()
    QgsProject.instance().removeMapLayer(old_layer_id)

  def rename_field(self, source_field, target_field, strict=True):
    """Rename one field on the current layer.

    Args:
      source_field: Existing field name.
      target_field: New field name.
      strict: Raise an error when source_field is missing. If False, log a
        warning and leave the layer unchanged.
    """
    self._validate_field_name(source_field, 'source_field')
    self._validate_field_name(target_field, 'target_field')

    field_names = self._field_names()
    if source_field not in field_names:
      message = (
        f'Cannot rename missing field {source_field} '
        f'on layer {self.scrub_layer.layer_name}.')
      if strict:
        raise KeyError(message)
      logger.warning(message)
      return self.scrub_layer

    if source_field == target_field:
      logger.info(
        'Field rename skipped because source and target match: %s',
        source_field)
      return self.scrub_layer

    if target_field in field_names:
      raise ValueError(
        f'Cannot rename {source_field} to {target_field}; '
        f'target field already exists.')

    self._require_provider_capability('RenameAttributes', 'renaming fields')
    try:
      with edit(self.layer):
        idx = self.layer.fields().indexFromName(source_field)
        if idx == -1:
          raise KeyError(f'Cannot rename missing field {source_field}.')
        if not self.layer.renameAttribute(idx, target_field):
          self._raise_provider_operation_failed(
            f'renaming field {source_field} to {target_field}')
        self.layer.updateFields()
    except Exception:
      logger.exception(
        'Failed to rename field %s to %s on layer %s.',
        source_field,
        target_field,
        self._layer_name())
      raise

    logger.info(
      'Renamed field %s to %s on layer %s.',
      source_field,
      target_field,
      self._layer_name())
    return self.scrub_layer

  def rename_fields(self, field_rename_map, strict=True):
    """Rename multiple fields from a dictionary of old_name -> new_name."""
    if not isinstance(field_rename_map, dict):
      raise TypeError('field_rename_map must be a dictionary.')

    field_names = self._field_names()
    targets = []

    for source_field, target_field in field_rename_map.items():
      self._validate_field_name(source_field, 'field_rename_map key')
      self._validate_field_name(target_field, 'field_rename_map value')
      targets.append(target_field)

    duplicate_targets = {
      target_field for target_field in targets
      if targets.count(target_field) > 1
    }
    if duplicate_targets:
      raise ValueError(
        f'Cannot rename fields to duplicate target names: '
        f'{sorted(duplicate_targets)}')

    missing_fields = [
      source_field for source_field in field_rename_map
      if source_field not in field_names
    ]
    if missing_fields:
      message = (
        f'Cannot rename missing fields on layer '
        f'{self.scrub_layer.layer_name}: {missing_fields}')
      if strict:
        raise KeyError(message)
      logger.warning(message)

    target_conflicts = [
      target_field
      for source_field, target_field in field_rename_map.items()
      if target_field in field_names and target_field != source_field
    ]
    if target_conflicts:
      raise ValueError(
        f'Cannot rename fields because target fields already exist: '
        f'{target_conflicts}')

    for source_field, target_field in field_rename_map.items():
      if source_field in field_names:
        self.rename_field(source_field, target_field, strict=strict)
    return self.scrub_layer

  def drop_field(self, field_name, strict=True):
    """Drop one attribute field from the current layer."""
    self._validate_field_name(field_name, 'field_name')

    if field_name not in self._field_names():
      message = (
        f'Cannot drop missing field {field_name} '
        f'on layer {self.scrub_layer.layer_name}.')
      if strict:
        raise KeyError(message)
      logger.warning(message)
      return self.scrub_layer

    self._require_provider_capability('DeleteAttributes', 'dropping fields')
    try:
      QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
      with edit(self.layer):
        idx = self.layer.fields().indexFromName(field_name)
        if idx == -1:
          raise KeyError(f'Cannot drop missing field {field_name}.')
        if not self.layer.deleteAttribute(idx):
          self._raise_provider_operation_failed(f'dropping field {field_name}')
        self.layer.updateFields()
    except Exception:
      logger.exception(
        'Failed to drop field %s from layer %s.',
        field_name,
        self._layer_name())
      raise

    logger.info(
      'Dropped field %s from layer %s.', field_name, self._layer_name())
    return self.scrub_layer

  def drop_fields(self, fields_to_drop, strict=True):
    """Drop multiple attribute fields from the current layer."""
    fields_to_drop = self._validate_field_collection(
      fields_to_drop, 'fields_to_drop')
    field_names = self._field_names()

    missing_fields = [
      field_name for field_name in fields_to_drop
      if field_name not in field_names
    ]
    if missing_fields:
      message = (
        f'Cannot drop missing fields on layer '
        f'{self.scrub_layer.layer_name}: {missing_fields}')
      if strict:
        raise KeyError(message)
      logger.warning(message)

    existing_fields_to_drop = [
      field_name for field_name in fields_to_drop
      if field_name in field_names
    ]
    if not existing_fields_to_drop:
      return self.scrub_layer

    indexes_to_drop = sorted(
      [
        self.layer.fields().indexFromName(field_name)
        for field_name in existing_fields_to_drop
      ],
      reverse=True,
    )

    self._require_provider_capability('DeleteAttributes', 'dropping fields')
    try:
      QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
      with edit(self.layer):
        for idx in indexes_to_drop:
          if idx == -1:
            raise KeyError('Cannot drop a field with index -1.')
          field_name = self.layer.fields()[idx].name()
          if not self.layer.deleteAttribute(idx):
            self._raise_provider_operation_failed(
              f'dropping field {field_name}')
        self.layer.updateFields()
    except Exception:
      logger.exception(
        'Failed to drop fields %s from layer %s.',
        existing_fields_to_drop,
        self._layer_name())
      raise

    for field_name in existing_fields_to_drop:
      logger.info(
        'Dropped field %s from layer %s.', field_name, self._layer_name())
    return self.scrub_layer

  def keep_only_fields(self, fields_to_keep, strict=True):
    """Keep only selected attribute fields and remove all others."""
    fields_to_keep = self._validate_field_collection(
      fields_to_keep, 'fields_to_keep')
    field_names = self._field_names()

    missing_fields = [
      field_name for field_name in fields_to_keep
      if field_name not in field_names
    ]
    if missing_fields:
      message = (
        f'Cannot keep missing fields on layer '
        f'{self.scrub_layer.layer_name}: {missing_fields}')
      if strict:
        raise KeyError(message)
      logger.warning(message)

    keep_set = set(fields_to_keep)
    fields_to_drop = [
      field_name for field_name in field_names
      if field_name not in keep_set
    ]

    logger.info('Keeping fields: %s.', fields_to_keep)
    logger.info('Dropping fields outside keep list: %s.', fields_to_drop)
    if fields_to_drop:
      self.drop_fields(fields_to_drop, strict=strict)
    return self.scrub_layer

  def drop_null_features(self, required_fields):
    """Drop features where any required field is null or an empty string."""
    required_fields = self._validate_field_collection(
      required_fields, 'required_fields')
    feature_ids_to_delete = self.find_null_feature_ids(required_fields)

    if not feature_ids_to_delete:
      logger.info(
        'No null features found on layer %s for fields %s.',
        self._layer_name(),
        required_fields)
      return self.scrub_layer

    deleted_count = 0
    self._require_provider_capability('DeleteFeatures', 'deleting features')
    try:
      with edit(self.layer):
        for feature_id in feature_ids_to_delete:
          if self.layer.deleteFeature(feature_id):
            deleted_count += 1
          else:
            logger.warning(
              'Failed to delete feature %s from %s using provider %s.',
              feature_id,
              self._layer_name(),
              self._provider_name())
    except Exception:
      logger.exception(
        'Failed deleting null features from layer %s.',
        self._layer_name())
      raise

    self.scrub_layer.data_count = self.layer.featureCount()
    logger.info(
      'Deleted %s null features from layer %s for fields %s.',
      deleted_count,
      self._layer_name(),
      required_fields)
    return self.scrub_layer

  def add_id_field(
          self,
          id_values,
          field_name='id',
          overwrite=False):
    """Add an ID field and assign one provided value to each feature.

    Args:
      id_values: Iterable of ID values, commonly a range. The number of
        values must match the layer feature count.
      field_name: Name of the ID field to add.
      overwrite: If True, reuse an existing field_name and replace its
        values. If False, raise an error when field_name already exists.
    """
    self._validate_field_name(field_name, 'field_name')
    if isinstance(id_values, (str, bytes)):
      raise TypeError('id_values must be an iterable of ID values.')

    try:
      id_list = list(id_values)
    except TypeError as exc:
      raise TypeError('id_values must be an iterable of ID values.') from exc

    feature_count = self.layer.featureCount()
    if len(id_list) != feature_count:
      raise ValueError(
        f'id_values must contain exactly {feature_count} values; '
        f'got {len(id_list)}.')
    if any(not isinstance(id_value, int) for id_value in id_list):
      raise TypeError('id_values must contain only integer values.')

    field_names = self._field_names()
    if field_name in field_names and not overwrite:
      raise ValueError(
        f'Cannot add ID field {field_name}; field already exists.')

    if field_name not in field_names:
      self._require_provider_capability('AddAttributes', 'adding fields')

      new_field = QgsField(field_name, QVariant.Int)
      if not self._provider().addAttributes([new_field]):
        self._raise_provider_operation_failed(f'adding ID field {field_name}')
      self.layer.updateFields()

    field_idx = self.layer.fields().indexFromName(field_name)
    if field_idx == -1:
      raise RuntimeError(f'Failed to locate ID field {field_name}.')

    self._require_provider_capability(
      'ChangeAttributeValues',
      'changing attribute values')
    try:
      with edit(self.layer):
        for feature, id_value in zip(self.layer.getFeatures(), id_list):
          if not self.layer.changeAttributeValue(
                  feature.id(), field_idx, id_value):
            self._raise_provider_operation_failed(
              f'assigning ID value for feature {feature.id()}')
    except Exception:
      logger.exception(
        'Failed assigning ID values to field %s on layer %s.',
        field_name,
        self._layer_name())
      raise

    logger.info(
      'Assigned %s ID values to field %s on layer %s.',
      len(id_list),
      field_name,
      self._layer_name())
    return self.scrub_layer

  def promote_feature_id(self, field_name='id'):
    """Move a GeoJSON property ID to the feature-level id member.

    This is useful after add_id_field() when a downstream GeoJSON contract
    expects "id" beside "geometry" and "properties", not inside properties.
    """
    self._validate_field_name(field_name, 'field_name')

    layer_path = self.scrub_layer.layer_path
    if not self._is_geojson_path(layer_path):
      raise ValueError(
        'promote_feature_id only supports GeoJSON layers.')

    with open(layer_path, 'r', encoding='utf-8') as geojson_file:
      geojson_data = json.load(geojson_file)

    features = geojson_data.get('features')
    if not isinstance(features, list):
      raise ValueError('GeoJSON data must contain a features list.')

    for feature in features:
      properties = feature.get('properties')
      if not isinstance(properties, dict):
        raise ValueError('Each GeoJSON feature must contain properties.')

      if field_name in properties:
        feature_id = properties.pop(field_name)
      elif field_name in feature:
        feature_id = feature[field_name]
      else:
        raise KeyError(
          f'GeoJSON feature is missing generated {field_name} value.')

      reordered_feature = {
        'type': feature.get('type', 'Feature'),
        'geometry': feature.get('geometry'),
        field_name: feature_id,
        'properties': properties,
      }

      for key, value in feature.items():
        if key not in reordered_feature:
          reordered_feature[key] = value

      feature.clear()
      feature.update(reordered_feature)

    with open(layer_path, 'w', encoding='utf-8') as geojson_file:
      json.dump(geojson_data, geojson_file, indent=2, ensure_ascii=False)
      geojson_file.write('\n')

    logger.info(
      'Promoted property %s to feature-level ID for layer %s.',
      field_name,
      self.scrub_layer.layer_name)
    return self.scrub_layer

  def find_missing_fields(self, required_fields):
    """Return required fields that are not present on the layer."""
    required_fields = self._validate_field_collection(
      required_fields, 'required_fields')
    field_names = set(self._field_names())
    return [
      field_name for field_name in required_fields
      if field_name not in field_names
    ]

  def find_extra_fields(self, allowed_fields):
    """Return layer fields that are not included in allowed_fields."""
    allowed_fields = self._validate_field_collection(
      allowed_fields, 'allowed_fields')
    allowed_field_set = set(allowed_fields)
    return [
      field_name for field_name in self._field_names()
      if field_name not in allowed_field_set
    ]

  @staticmethod
  def _is_null_attribute_value(value):
    if value is None:
      return True

    is_null = getattr(value, 'isNull', None)
    if callable(is_null):
      try:
        if is_null():
          return True
      except Exception:
        pass

    is_valid = getattr(value, 'isValid', None)
    if callable(is_valid):
      try:
        if not is_valid():
          return True
      except Exception:
        pass

    if isinstance(value, str):
      stripped_value = value.strip()
      return stripped_value == '' or stripped_value.upper() in (
        'NULL',
        '<NULL>',
      )

    return False

  def find_null_feature_ids(self, required_fields):
    """Return feature IDs where any required field has a null-like value."""
    required_fields = self._validate_field_collection(
      required_fields, 'required_fields')
    field_names = self._field_names()

    missing_fields = [
      field_name for field_name in required_fields
      if field_name not in field_names
    ]
    if missing_fields:
      raise KeyError(
        f'Cannot find null features because required fields are missing '
        f'on layer {self._layer_name()}: {missing_fields}')

    feature_ids = []
    for feature in self.layer.getFeatures():
      for field_name in required_fields:
        value = feature[field_name]
        if self._is_null_attribute_value(value):
          feature_ids.append(feature.id())
          break
    return feature_ids

  def reorder_fields(
          self,
          field_order,
          append_unlisted=True,
          strict=True,
          output_path=None):
    """Reorder attribute fields while preserving feature values.

    Args:
      field_order: Desired leading field order.
      append_unlisted: Append fields not listed in field_order after the
        ordered fields. If False, unlisted fields are omitted.
      strict: Raise an error when field_order includes missing fields. If
        False, missing fields are ignored.
      output_path: Optional path for a new reordered layer. If omitted, the
        current layer dataset is replaced in place.
    """
    field_order = self._validate_field_collection(
      field_order, 'field_order')
    if len(set(field_order)) != len(field_order):
      raise ValueError('field_order must not contain duplicate field names.')

    field_names = self._field_names()
    missing_fields = [
      field_name for field_name in field_order
      if field_name not in field_names
    ]
    if missing_fields:
      message = (
        f'Cannot reorder missing fields on layer '
        f'{self.scrub_layer.layer_name}: {missing_fields}')
      if strict:
        raise KeyError(message)
      logger.warning(message)

    ordered_fields = [
      field_name for field_name in field_order
      if field_name in field_names
    ]
    if append_unlisted:
      ordered_fields.extend([
        field_name for field_name in field_names
        if field_name not in ordered_fields
      ])

    logger.info('Final field order: %s.', ordered_fields)

    if output_path:
      if self._same_path(output_path, self.scrub_layer.layer_path):
        raise ValueError(
          'output_path must differ from the current layer path. '
          'Omit output_path to reorder the current layer in place.')
      self._write_layer(output_path, field_order=ordered_fields)
      return self._new_scrub_layer(output_path)

    if ordered_fields == field_names:
      return self.scrub_layer

    temp_dir = tempfile.mkdtemp(prefix='reorder_fields_')
    try:
      layer_extension = os.path.splitext(self.scrub_layer.layer_path)[1]
      temp_path = os.path.join(
        temp_dir, f'{self.scrub_layer.layer_name}{layer_extension}')
      self._write_layer(temp_path, field_order=ordered_fields)
      self._replace_current_layer(temp_path)
    finally:
      shutil.rmtree(temp_dir, ignore_errors=True)

    return self.scrub_layer

  def standardize_fields(
          self,
          field_rename_map=None,
          fields_to_drop=None,
          fields_to_keep=None,
          field_order=None,
          output_path=None,
          strict=True,
          append_unlisted=True,
          in_place=False,
          output_layer_name=None):
    """Apply final field cleanup operations in a safe order.

    The operation order is: rename fields, keep only selected fields or drop
    selected fields, then optionally reorder fields.

    By default this method requires output_path and returns a new ScrubLayer,
    preserving the current layer dataset. Set in_place=True to modify the
    current layer instead.
    """
    if fields_to_keep is not None and fields_to_drop is not None:
      raise ValueError(
        'fields_to_keep and fields_to_drop cannot both be provided.')
    if output_path and in_place:
      raise ValueError('output_path and in_place=True cannot both be used.')
    if output_path is None and not in_place:
      raise ValueError(
        'standardize_fields requires output_path unless in_place=True.')
    if output_path and self._same_path(output_path, self.scrub_layer.layer_path):
      raise ValueError(
        'output_path must differ from the current layer path. '
        'Use in_place=True to standardize the current layer.')

    target_manager = self
    target_scrub_layer = self.scrub_layer

    if output_path:
      self._write_layer(output_path)
      target_scrub_layer = self._new_scrub_layer(
        output_path, layer_name=output_layer_name)
      target_manager = FieldSchemaManager(target_scrub_layer)

    if field_rename_map:
      target_manager.rename_fields(field_rename_map, strict=strict)

    if fields_to_keep is not None:
      target_manager.keep_only_fields(fields_to_keep, strict=strict)
    elif fields_to_drop is not None:
      target_manager.drop_fields(fields_to_drop, strict=strict)

    if field_order is not None:
      target_manager.reorder_fields(
        field_order,
        append_unlisted=append_unlisted,
        strict=strict)

    logger.info(
      'Standardized fields for layer %s.', target_scrub_layer.layer_name)
    return target_scrub_layer

  def _new_scrub_layer(self, output_path, layer_name=None):
    from .scrub_layer_class import ScrubLayer

    final_layer_name = layer_name
    if final_layer_name is None:
      final_layer_name = os.path.splitext(os.path.basename(output_path))[0]
    return ScrubLayer(
      self.scrub_layer.qgis_path, output_path, final_layer_name)
