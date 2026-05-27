"""
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
      return

    if qgis_path is None or layer_path is None:
      raise ValueError(
        'FieldSchemaManager requires either a ScrubLayer instance or both '
        'qgis_path and layer_path.')

    if layer_name is None:
      layer_name = os.path.splitext(os.path.basename(layer_path))[0]

    from .scrub_layer_class import ScrubLayer

    self.scrub_layer = ScrubLayer(qgis_path, layer_path, layer_name)

  @property
  def layer(self):
    """Return the managed QGIS vector layer."""
    return self.scrub_layer.layer

  def _field_names(self):
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
  def _same_path(first_path, second_path):
    return os.path.abspath(first_path) == os.path.abspath(second_path)

  @staticmethod
  def _is_geojson_path(path):
    return os.path.splitext(path)[1].lower() in ('.geojson', '.json')

  def _write_layer(self, output_path, field_order=None):
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = self._driver_name(output_path)
    options.fileEncoding = 'utf-8'

    if field_order is not None:
      options.attributes = [
        self.layer.fields().indexFromName(field_name)
        for field_name in field_order
      ]

    writer_result = QgsVectorFileWriter.writeAsVectorFormat(
      self.layer, output_path, options)
    error_code = self._writer_error_code(writer_result)
    if error_code != QgsVectorFileWriter.NoError:
      raise RuntimeError(
        f'Failed to write layer {self.scrub_layer.layer_name} '
        f'to {output_path}: {writer_result}')

  def _replace_current_layer(self, replacement_path):
    self._reload_without_source()
    self.scrub_layer._replace_layer_files(
      replacement_path, self.scrub_layer.layer_path)
    self.scrub_layer.layer = self.scrub_layer.load_layer()
    self.scrub_layer.data_count = self.scrub_layer.layer.featureCount()

  def _reload_without_source(self):
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

    with edit(self.layer):
      idx = self.layer.fields().indexFromName(source_field)
      if idx == -1:
        raise KeyError(f'Cannot rename missing field {source_field}.')
      if not self.layer.renameAttribute(idx, target_field):
        raise RuntimeError(
          f'Failed to rename field {source_field} to {target_field}.')
      self.layer.updateFields()

    logger.info('Renamed field %s to %s.', source_field, target_field)
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

    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    with edit(self.layer):
      idx = self.layer.fields().indexFromName(field_name)
      if idx == -1:
        raise KeyError(f'Cannot drop missing field {field_name}.')
      if not self.layer.deleteAttribute(idx):
        raise RuntimeError(f'Failed to drop field {field_name}.')
      self.layer.updateFields()

    logger.info('Dropped field %s.', field_name)
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

    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    with edit(self.layer):
      for idx in indexes_to_drop:
        if idx == -1:
          raise KeyError('Cannot drop a field with index -1.')
        if not self.layer.deleteAttribute(idx):
          field_name = self.layer.fields()[idx].name()
          raise RuntimeError(f'Failed to drop field {field_name}.')
      self.layer.updateFields()

    for field_name in existing_fields_to_drop:
      logger.info('Dropped field %s.', field_name)
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
      capabilities = self.layer.dataProvider().capabilities()
      if not capabilities & QgsVectorDataProvider.AddAttributes:
        raise RuntimeError(
          f'Layer {self.scrub_layer.layer_name} does not support '
          f'adding fields.')

      new_field = QgsField(field_name, QVariant.Int)
      if not self.layer.dataProvider().addAttributes([new_field]):
        raise RuntimeError(f'Failed to add ID field {field_name}.')
      self.layer.updateFields()

    field_idx = self.layer.fields().indexFromName(field_name)
    if field_idx == -1:
      raise RuntimeError(f'Failed to locate ID field {field_name}.')

    with edit(self.layer):
      for feature, id_value in zip(self.layer.getFeatures(), id_list):
        if not self.layer.changeAttributeValue(
                feature.id(), field_idx, id_value):
          raise RuntimeError(
            f'Failed to assign ID value for feature {feature.id()}.')

    logger.info(
      'Assigned %s ID values to field %s on layer %s.',
      len(id_list),
      field_name,
      self.scrub_layer.layer_name)
    return self.scrub_layer

  def promote_property_id_to_feature_id(self, field_name='id'):
    """Move a GeoJSON property ID to the feature-level id member.

    This is useful after add_id_field() when a downstream GeoJSON contract
    expects "id" beside "geometry" and "properties", not inside properties.
    """
    self._validate_field_name(field_name, 'field_name')

    layer_path = self.scrub_layer.layer_path
    if not self._is_geojson_path(layer_path):
      raise ValueError(
        'promote_property_id_to_feature_id only supports GeoJSON layers.')

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
      json.dump(geojson_data, geojson_file, indent=2)
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
          id_field_name=None,
          id_start_value=None,
          output_layer_name=None):
    """Apply final field cleanup operations in a safe order.

    The operation order is: rename fields, keep only selected fields or drop
    selected fields, optionally reorder fields, then optionally add and promote
    a GeoJSON feature ID.

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
    if (id_field_name is None) != (id_start_value is None):
      raise ValueError(
        'id_field_name and id_start_value must be provided together.')
    if id_field_name is not None:
      self._validate_field_name(id_field_name, 'id_field_name')
    if id_start_value is not None and not isinstance(id_start_value, int):
      raise TypeError('id_start_value must be an integer.')
    if id_field_name is not None:
      id_target_path = output_path or self.scrub_layer.layer_path
      if not self._is_geojson_path(id_target_path):
        raise ValueError(
          'Feature-level IDs require a GeoJSON output path.')

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

    if id_field_name is not None:
      feature_count = target_manager.layer.featureCount()
      target_manager.add_id_field(
        id_values=range(id_start_value, id_start_value + feature_count),
        field_name=id_field_name)
      target_manager.promote_property_id_to_feature_id(id_field_name)

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
