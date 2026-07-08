"""
CityGISOO
Object-Oriented Geographic Information System for Cities
scrub_layer_class module
PyQGIS functionalities that are needed in the cleaning and updating
Montreal Buildings dataset project, gathered in one class.
Project Developer: Alireza Adli
alireza.adli@concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import glob
import os
import shutil
import tempfile
import uuid

import processing

from sabu_chassis.logging import get_logger
from qgis.core import QgsApplication, QgsField, QgsProject, \
  QgsProcessingFeedback, QgsVectorLayer, QgsVectorDataProvider, \
  QgsExpressionContext, QgsExpressionContextUtils, edit, QgsFeatureRequest, \
  QgsExpression, QgsVectorFileWriter, QgsCoordinateReferenceSystem, \
  QgsVectorLayerJoinInfo, QgsProcessingFeatureSourceDefinition
from qgis.PyQt.QtCore import QVariant
from qgis.analysis import QgsNativeAlgorithms

from .basic_functions import create_folders, find_shp_files
from .field_schema_manager import FieldSchemaManager


logger = get_logger(__name__)


class ScrubLayer:
  def __init__(self, qgis_path, layer_path, layer_name):

    self.qgis_path = qgis_path
    # Set the path to QGIS installation
    QgsApplication.setPrefixPath(self.qgis_path, True)

    self.layer_path = layer_path
    self.layer_name = layer_name
    self.layer = self.load_layer()
    self.data_count = self.layer.featureCount()

  @property
  def field_schema_manager(self):
    return FieldSchemaManager(self)

  def duplicate_layer(self, output_path):
    output_extension = os.path.splitext(output_path)[1].lower()
    driver_name = {
      '.geojson': 'GeoJSON',
      '.json': 'GeoJSON',
      '.gpkg': 'GPKG',
      '.shp': 'ESRI Shapefile'
    }.get(output_extension, 'ESRI Shapefile')

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = driver_name
    options.fileEncoding = 'utf-8'

    if hasattr(options, 'actionOnExistingFile'):
      overwrite_action = getattr(
        QgsVectorFileWriter, 'CreateOrOverwriteFile', None)
      if overwrite_action is not None:
        options.actionOnExistingFile = overwrite_action

    writer_v3 = getattr(QgsVectorFileWriter, 'writeAsVectorFormatV3', None)
    if callable(writer_v3):
      duplication = writer_v3(
        self.layer,
        output_path,
        QgsProject.instance().transformContext(),
        options
      )
    else:
      duplication = QgsVectorFileWriter.writeAsVectorFormat(
        self.layer,
        output_path,
        options
      )

    duplication_error = duplication[0] if isinstance(
      duplication, tuple) else duplication

    if duplication_error == QgsVectorFileWriter.NoError:
      logger.info('Layer successfully duplicated to %s', output_path)
    else:
      logger.error('Error duplicating shapefile: %s', duplication)

  def get_cell(self, fid, field_name):
    return self.layer.getFeature(fid)[field_name]

  def select_cells(
          self,
          field_name, field_value, required_field,
          return_one_value=False):
    """Returns the value of a field
    based on the value of another field in the same record"""
    expression = QgsExpression(f'{field_name} = {field_value}')
    request = QgsFeatureRequest(expression)
    features = self.layer.getFeatures(request)
    field_field_values = []
    for feature in features:
      field_field_values.append(feature[required_field])
      if return_one_value and field_field_values:
        return field_field_values[0]
    return field_field_values

  def load_layer(self):
    the_layer = QgsVectorLayer(self.layer_path, self.layer_name, 'ogr')
    if not the_layer.isValid():
      logger.error(
        'Failed to load layer %s from %s.',
        self.layer_name,
        self.layer_path)
      raise ValueError(
        f'Failed to load layer {self.layer_name} from {self.layer_path}')
    else:
      QgsProject.instance().addMapLayer(the_layer)
      logger.info(
        'Loaded layer %s from %s.', self.layer_name, self.layer_path)
    return the_layer

  def features_to_layers(self, layers_dir, crs):
    create_folders(layers_dir, self.data_count)
    target_crs = QgsCoordinateReferenceSystem(crs)
    for feature in self.layer.getFeatures():
      new_layer = QgsVectorLayer(
        f'Polygon?crs={crs}', "feature_layer", "memory")
      new_layer.setCrs(target_crs)

      new_provider = new_layer.dataProvider()
      new_provider.addFeatures([feature])

      feature_id = feature.id()
      output_path = f'{layers_dir}layer_{feature_id}/layer_{feature_id}.shp'

      QgsVectorFileWriter.writeAsVectorFormat(
        new_layer,
        output_path,
        'utf-8',
        new_layer.crs(),
        'ESRI Shapefile'
      )
    logger.info('Shapefiles created for each feature in %s', layers_dir)

  def fix_geometries(self, fixed_layer):
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    fix_geometries_params = {
      'INPUT': self.layer,
      'METHOD': 0,
      'OUTPUT': fixed_layer
    }
    processing.run("native:fixgeometries", fix_geometries_params)
    logger.info(
      'Fixed geometries for %s into %s.', self.layer_name, fixed_layer)

  def create_spatial_index(self):
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    create_spatial_index_params = {
      'INPUT': self.layer,
      'OUTPUT': 'Output'
    }
    processing.run("native:createspatialindex", create_spatial_index_params)
    logger.info('Creating spatial index for %s is completed.', self.layer_name)

  def spatial_join(self, joining_layer_path, joined_layer_path):
    """In QGIS, it is called 'Join attributes by Location'"""
    params = {'INPUT': self.layer,
              'PREDICATE': [0],
              'JOIN': joining_layer_path,
              'JOIN_FIELDS': [],
              'METHOD': 0,
              'DISCARD_NONMATCHING': False,
              'PREFIX': '',
              'OUTPUT': joined_layer_path}

    feedback = QgsProcessingFeedback()
    processing.run(
      'native:joinattributesbylocation', params, feedback=feedback)
    logger.info(
      'Spatial join with input layer %s is completed.', self.layer_name)

  @staticmethod
  def _normalize_spatial_join_predicate(predicate):
    if isinstance(predicate, int):
      return [predicate]

    if isinstance(predicate, (list, tuple)):
      predicate_codes = []
      for predicate_item in predicate:
        predicate_codes.extend(
          ScrubLayer._normalize_spatial_join_predicate(predicate_item))
      return predicate_codes

    normalized_predicate = str(predicate).strip().lower()
    predicate_codes = {
      'intersect': 0,
      'intersects': 0,
      'contain': 1,
      'contains': 1,
      'equal': 2,
      'equals': 2,
      'touch': 3,
      'touches': 3,
      'overlap': 4,
      'overlaps': 4,
      'within': 5,
      'are within': 5,
      'cross': 6,
      'crosses': 6,
    }
    if normalized_predicate not in predicate_codes:
      raise ValueError(f'Unsupported spatial join predicate: {predicate}')
    return [predicate_codes[normalized_predicate]]

  @staticmethod
  def _normalize_spatial_join_method(join_method):
    if isinstance(join_method, int):
      return join_method

    normalized_method = str(join_method).strip().lower()
    method_codes = {
      'one-to-many': 0,
      'create separate feature for each matching feature': 0,
      'separate feature for each matching feature': 0,
      'all matches': 0,
      'one-to-one-first': 1,
      'first match': 1,
      'take attributes of the first matching feature only': 1,
      'one-to-one-largest-overlap': 2,
      'largest overlap': 2,
      'take attributes of the feature with largest overlap only': 2,
    }
    if normalized_method not in method_codes:
      raise ValueError(f'Unsupported spatial join method: {join_method}')
    return method_codes[normalized_method]

  def spatial_join_with_predicate(
          self,
          joining_layer_path,
          joined_layer_path,
          predicate='intersect',
          join_method='one-to-many',
          prefix=''):
    """Join attributes by location with caller-selected predicate and method."""
    params = {
      'INPUT': self.layer,
      'PREDICATE': self._normalize_spatial_join_predicate(predicate),
      'JOIN': joining_layer_path,
      'JOIN_FIELDS': [],
      'METHOD': self._normalize_spatial_join_method(join_method),
      'DISCARD_NONMATCHING': False,
      'PREFIX': prefix,
      'OUTPUT': joined_layer_path
    }

    feedback = QgsProcessingFeedback()
    processing.run(
      'native:joinattributesbylocation', params, feedback=feedback)
    logger.info(
      'Spatial join with input layer %s, predicate %s, method %s, and '
      'prefix %s is completed.',
      self.layer_name,
      predicate,
      join_method,
      prefix)
    return joined_layer_path

  @staticmethod
  def _replace_layer_files(source_path, destination_path):
    source_base, source_ext = os.path.splitext(source_path)
    destination_base, destination_ext = os.path.splitext(destination_path)

    if source_ext.lower() != destination_ext.lower():
      raise ValueError(
        f'Cannot replace layer {destination_path} with {source_path} '
        f'because their formats differ.')

    if destination_ext.lower() == '.shp':
      for existing_file in glob.glob(f'{destination_base}.*'):
        os.remove(existing_file)

      for source_file in glob.glob(f'{source_base}.*'):
        extension = os.path.splitext(source_file)[1]
        shutil.move(source_file, f'{destination_base}{extension}')
      return

    if os.path.exists(destination_path):
      os.remove(destination_path)
    shutil.move(source_path, destination_path)

  def field_join(
          self,
          joining_layer_path,
          joining_layer_name,
          target_field,
          join_field,
          join_fields=None,
          prefix='',
          output_path=None,
          selected_features_only=False,
          joining_selected_features_only=False,
          join_method=1,
          discard_nonmatching=False,
          unjoinable_output_path=None):
    """Joins fields from another layer and persists the result.

    If output_path is None, the current layer dataset is replaced in place.
    If join_fields is None, all fields from the joining layer are added.
    """
    joining_layer = QgsVectorLayer(
      joining_layer_path, joining_layer_name, 'ogr')
    if not joining_layer.isValid():
      raise ValueError(
        f'Failed to load layer {joining_layer_name} '
        f'from {joining_layer_path}')

    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    final_output_path = output_path or self.layer_path
    temp_dir = None
    processing_output_path = final_output_path

    if final_output_path == self.layer_path:
      temp_dir = tempfile.mkdtemp(prefix='field_join_')
      layer_extension = os.path.splitext(self.layer_path)[1]
      processing_output_path = os.path.join(
        temp_dir, f'{self.layer_name}{layer_extension}')

    input_layer = self.layer
    if selected_features_only:
      layer_source = (
        self.layer.id()
        if callable(getattr(self.layer, 'id', None))
        else self.layer_path)
      input_layer = QgsProcessingFeatureSourceDefinition(
        layer_source,
        selectedFeaturesOnly=True)

    input_layer_2 = joining_layer
    if joining_selected_features_only:
      joining_layer_source = (
        joining_layer.id()
        if callable(getattr(joining_layer, 'id', None))
        else joining_layer_path)
      input_layer_2 = QgsProcessingFeatureSourceDefinition(
        joining_layer_source,
        selectedFeaturesOnly=True)

    params = {
      'INPUT': input_layer,
      'FIELD': target_field,
      'INPUT_2': input_layer_2,
      'FIELD_2': join_field,
      'FIELDS_TO_COPY': join_fields or [],
      'METHOD': self._normalize_field_join_method(join_method),
      'DISCARD_NONMATCHING': discard_nonmatching,
      'PREFIX': prefix,
      'OUTPUT': processing_output_path
    }
    if unjoinable_output_path is not None:
      params['NON_MATCHING'] = unjoinable_output_path

    processing.run('native:joinattributestable', params)

    if final_output_path == self.layer_path:
      old_layer_id = self.layer.id()
      QgsProject.instance().removeMapLayer(old_layer_id)
      self._replace_layer_files(processing_output_path, self.layer_path)
      shutil.rmtree(temp_dir)
      self.layer = self.load_layer()
      self.data_count = self.layer.featureCount()

    logger.info(
      'Field join of %s with input layer %s is completed.',
      self.layer_name,
      joining_layer_name)

  @staticmethod
  def _normalize_field_join_method(join_method):
    if isinstance(join_method, int):
      return join_method

    normalized_method = str(join_method).strip().lower()
    method_codes = {
      'one-to-many': 0,
      'create separate feature for each matching feature': 0,
      'separate feature for each matching feature': 0,
      'all matches': 0,
      'one-to-one-first': 1,
      'first match': 1,
      'take attributes of the first matching feature only': 1,
    }
    if normalized_method not in method_codes:
      raise ValueError(f'Unsupported field join method: {join_method}')
    return method_codes[normalized_method]

  def add_layer_join(
          self,
          joining_layer_path,
          joining_layer_name,
          join_field,
          target_field,
          prefix='',
          output_path=None,
          join_fields=None,
          selected_features_only=False,
          joining_selected_features_only=False,
          join_method=1,
          discard_nonmatching=False,
          unjoinable_output_path=None):
    """Add a QGIS layer-properties join or persist it to output_path.

    Without output_path, this creates a live join on this layer, equivalent to
    adding a join from Layer Properties > Joins in QGIS. With output_path, it
    writes a joined dataset using QGIS processing.
    """
    if output_path is not None:
      self.field_join(
        joining_layer_path=joining_layer_path,
        joining_layer_name=joining_layer_name,
        target_field=target_field,
        join_field=join_field,
        join_fields=join_fields,
        prefix=prefix,
        output_path=output_path,
        selected_features_only=selected_features_only,
        joining_selected_features_only=joining_selected_features_only,
        join_method=join_method,
        discard_nonmatching=discard_nonmatching,
        unjoinable_output_path=unjoinable_output_path)
      return output_path

    joining_layer = QgsVectorLayer(
      joining_layer_path, joining_layer_name, 'ogr')
    if not joining_layer.isValid():
      raise ValueError(
        f'Failed to load layer {joining_layer_name} '
        f'from {joining_layer_path}')

    QgsProject.instance().addMapLayer(joining_layer)

    join_info = QgsVectorLayerJoinInfo()
    join_info.setJoinLayer(joining_layer)
    join_info.setJoinFieldName(join_field)
    join_info.setTargetFieldName(target_field)
    join_info.setPrefix(prefix)
    join_info.setUsingMemoryCache(True)
    if join_fields is not None:
      join_info.setJoinFieldNamesSubset(join_fields)

    if not self.layer.addJoin(join_info):
      raise RuntimeError(
        f'Failed to add join from {joining_layer_name} to {self.layer_name}.')

    logger.info(
      'Added layer join to %s from %s on %s = %s with prefix %s.',
      self.layer_name,
      joining_layer_name,
      target_field,
      join_field,
      prefix)
    return join_info

  def clip_layer(self, overlay_layer, clipped_layer):
    """This must be tested"""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    clip_layer_params = {
      'INPUT': self.layer_path,
      'OVERLAY': overlay_layer,
      'FILTER_EXPRESSION': '',
      'FILTER_EXTENT': None,
      'OUTPUT': clipped_layer
    }
    processing.run("native:clip", clip_layer_params)
    logger.info('Clipping of %s is completed.', self.layer_name)

  def difference_layer(self, overlay_layer, output_path, grid_size=None):
    """Run QGIS vector overlay difference and persist the result."""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    overlay_input = getattr(overlay_layer, 'layer_path', overlay_layer)
    params = {
      'INPUT': self.layer_path,
      'OVERLAY': overlay_input,
      'OUTPUT': output_path
    }
    if grid_size is not None:
      params['GRID_SIZE'] = grid_size

    processing.run('native:difference', params)
    logger.info(
      'Difference of %s with overlay %s is completed into %s.',
      self.layer_name,
      overlay_input,
      output_path)
    return output_path

  @staticmethod
  def _normalize_field_selection(fields):
    if fields is None:
      return []
    if isinstance(fields, str):
      return [fields]
    return list(fields)

  def intersection_layer(
          self,
          overlay_layer,
          output_path,
          input_fields=None,
          overlay_fields=None,
          overlay_fields_prefix=''):
    """Run QGIS vector overlay intersection and persist the result."""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    overlay_input = getattr(overlay_layer, 'layer_path', overlay_layer)
    params = {
      'INPUT': self.layer_path,
      'OVERLAY': overlay_input,
      'INPUT_FIELDS': self._normalize_field_selection(input_fields),
      'OVERLAY_FIELDS': self._normalize_field_selection(overlay_fields),
      'OVERLAY_FIELDS_PREFIX': overlay_fields_prefix,
      'OUTPUT': output_path
    }

    processing.run('native:intersection', params)
    logger.info(
      'Intersection of %s with overlay %s is completed into %s.',
      self.layer_name,
      overlay_input,
      output_path)
    return output_path

  @staticmethod
  def _normalize_extract_attribute_operator(operator):
    if isinstance(operator, int):
      return operator

    normalized_operator = str(operator).strip().lower()
    operator_codes = {
      '=': 0,
      '==': 0,
      'equals': 0,
      '!=': 1,
      '<>': 1,
      'not equals': 1,
      '>': 2,
      'greater than': 2,
      '>=': 3,
      'greater than or equal to': 3,
      '<': 4,
      'less than': 4,
      '<=': 5,
      'less than or equal to': 5,
      'begins with': 6,
      'contains': 7,
      'is null': 8,
      'is not null': 9,
      'does not contain': 10,
    }
    if normalized_operator not in operator_codes:
      raise ValueError(f'Unsupported extract-by-attribute operator: {operator}')
    return operator_codes[normalized_operator]

  def extract_by_attribute(self, field_name, operator, value, output_path):
    """Extract features by attribute value and persist them to output_path."""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    params = {
      'INPUT': self.layer,
      'FIELD': field_name,
      'OPERATOR': self._normalize_extract_attribute_operator(operator),
      'VALUE': value,
      'OUTPUT': output_path
    }
    processing.run('native:extractbyattribute', params)
    logger.info(
      'Extracted features from %s where %s %s %s into %s.',
      self.layer_name,
      field_name,
      operator,
      value,
      output_path)
    return output_path

  def extract_by_expression(self, expression, output_path):
    """Extract features by QGIS expression and persist them to output_path."""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    params = {
      'INPUT': self.layer,
      'EXPRESSION': expression,
      'OUTPUT': output_path
    }
    processing.run('native:extractbyexpression', params)
    logger.info(
      'Extracted features from %s using expression %s into %s.',
      self.layer_name,
      expression,
      output_path)
    return output_path

  @staticmethod
  def _quote_qgis_identifier(identifier):
    return f'"{str(identifier).replace(chr(34), chr(34) * 2)}"'

  @staticmethod
  def _quote_qgis_string(value):
    return f"'{str(value).replace(chr(39), chr(39) * 2)}'"

  def extract_by_aggregate_membership(
          self,
          lookup_layer,
          lookup_field,
          target_field,
          output_path,
          aggregate='array_agg',
          include_matches=True):
    """Extract features by testing target_field membership in another layer.

    Builds a QGIS expression using array_contains(aggregate(...)) and delegates
    execution to extract_by_expression().
    """
    lookup_layer_name = getattr(lookup_layer, 'layer_name', lookup_layer)
    expression = (
      'array_contains('
      'aggregate('
      f'layer:={self._quote_qgis_string(lookup_layer_name)},'
      f'aggregate:={self._quote_qgis_string(aggregate)},'
      f'expression:={self._quote_qgis_identifier(lookup_field)}'
      '),'
      f'{self._quote_qgis_identifier(target_field)}'
      ')')

    if not include_matches:
      expression = f'NOT {expression}'

    return self.extract_by_expression(expression, output_path)

  @staticmethod
  def _normalize_aggregate_definition(aggregate_definition):
    """Normalize one QGIS aggregate table row.

    The QGIS aggregate algorithm expects dict keys named like the processing
    internals. This accepts those keys and clearer caller-facing aliases.
    """
    if not isinstance(aggregate_definition, dict):
      raise TypeError('Each aggregate definition must be a dictionary.')

    output_field = (
      aggregate_definition.get('output_field')
      or aggregate_definition.get('name'))
    aggregate_function = (
      aggregate_definition.get('aggregate_function')
      or aggregate_definition.get('aggregate'))
    input_expression = (
      aggregate_definition.get('input_expression')
      or aggregate_definition.get('input'))
    field_type = (
      aggregate_definition.get('field_type')
      if 'field_type' in aggregate_definition
      else aggregate_definition.get('type'))

    missing_fields = [
      field_name
      for field_name, field_value in [
        ('output_field', output_field),
        ('aggregate_function', aggregate_function),
        ('input_expression', input_expression),
        ('field_type', field_type),
      ]
      if field_value is None
    ]
    if missing_fields:
      raise ValueError(
        f'Aggregate definition is missing {missing_fields}.')

    return {
      'name': output_field,
      'aggregate': aggregate_function,
      'input': input_expression,
      'type': field_type,
      'length': aggregate_definition.get('length', 0),
      'precision': aggregate_definition.get('precision', 0),
      'delimiter': aggregate_definition.get('delimiter', ','),
    }

  def aggregate_table(
          self,
          group_by_expression,
          aggregates,
          output_path,
          selected_features_only=False,
          template_layer=None):
    """Run Processing Toolbox > Vector table > Aggregate.

    Args:
      group_by_expression: QGIS group-by expression.
      aggregates: Sequence of aggregate table rows. Each row must define
        output_field, aggregate_function, input_expression, and field_type.
        QGIS processing aliases name, aggregate, input, and type are also
        accepted. Optional length, precision, and delimiter are passed through.
      output_path: Destination output layer/table path.
      selected_features_only: Match QGIS's input "selected features only"
        checkbox. Defaults to False.
      template_layer: Kept as an explicit option matching the QGIS dialog.
        The native processing algorithm uses AGGREGATES, so this remains empty
        by default and is not sent as a processing parameter.
    """
    if template_layer not in (None, ''):
      logger.warning(
        'Template layer %s was provided for aggregate_table, but QGIS '
        'native:aggregate expects aggregate definitions directly.',
        template_layer)

    normalized_aggregates = [
      self._normalize_aggregate_definition(aggregate_definition)
      for aggregate_definition in aggregates
    ]
    if not normalized_aggregates:
      raise ValueError('At least one aggregate definition is required.')

    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    input_layer = self.layer
    if selected_features_only:
      layer_source = (
        self.layer.id()
        if callable(getattr(self.layer, 'id', None))
        else self.layer_path)
      input_layer = QgsProcessingFeatureSourceDefinition(
        layer_source,
        selectedFeaturesOnly=True)

    params = {
      'INPUT': input_layer,
      'GROUP_BY': group_by_expression,
      'AGGREGATES': normalized_aggregates,
      'OUTPUT': output_path
    }
    processing.run('native:aggregate', params)
    logger.info(
      'Aggregated table for %s by %s into %s.',
      self.layer_name,
      group_by_expression,
      output_path)
    return output_path

  def clip_by_predefined_zones(self):
    pass

  def clip_by_multiple(
          self, number_of_partitions, overlay_layers_dir, clipped_layers_dir):
    create_folders(clipped_layers_dir, number_of_partitions)
    logger.info(
      'Started clipping %s by %s partitions.',
      self.layer_name,
      number_of_partitions)
    for layer in range(number_of_partitions):
      overlay = overlay_layers_dir + f'/layer_{layer}/layer_{layer}.shp'
      clipped = clipped_layers_dir + f'/layer_{layer}/layer_{layer}.shp'
      self.clip_layer(overlay, clipped)
      clipped_layer = ScrubLayer(self.qgis_path, clipped, 'Temp Layer')
      clipped_layer.create_spatial_index()
    logger.info(
      'Completed clipping %s by multiple overlays into %s.',
      self.layer_name,
      clipped_layers_dir)

  def split_layer(self, number_of_layers, splitted_layers_dir):
    number_of_layers -= 1
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    create_folders(splitted_layers_dir, number_of_layers)
    intervals = self.data_count // number_of_layers
    logger.info(
      'Started splitting %s into %s layer partitions.',
      self.layer_name,
      number_of_layers + 1)
    for part in range(number_of_layers):
      output_layer_path = \
        splitted_layers_dir + f'/layer_{part}/layer_{part}.shp'
      params = {'INPUT': self.layer,
                'EXPRESSION': f'$id >= {part * intervals} '
                              f'AND $id < {(part + 1) * intervals}\r\n',
                'OUTPUT': output_layer_path}

      processing.run("native:extractbyexpression", params)

      new_layer = ScrubLayer(self.qgis_path, output_layer_path, 'Temp Layer')
      new_layer.create_spatial_index()

    # Adding a folder for the remaining features

    os.makedirs(splitted_layers_dir + f'/layer_{number_of_layers}')
    output_layer_path = splitted_layers_dir + \
        f'/layer_{number_of_layers}/layer_{number_of_layers}.shp'
    params = {'INPUT': self.layer,
              'EXPRESSION': f'$id >= {number_of_layers * intervals}\r\n',
              'OUTPUT': output_layer_path}

    processing.run("native:extractbyexpression", params)
    new_layer = ScrubLayer(self.qgis_path, output_layer_path, 'Temp Layer')
    new_layer.create_spatial_index()
    logger.info(
      'Completed splitting %s into %s.',
      self.layer_name,
      splitted_layers_dir)

  @staticmethod
  def merge_layers(layers_path, mergeded_layer_path):
    merging_layers = find_shp_files(layers_path)
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    params = {'LAYERS': merging_layers,
              'CRS': None,
              'OUTPUT': mergeded_layer_path}

    processing.run("native:mergevectorlayers", params)
    logger.info(
      'Merged %s layers from %s into %s.',
      len(merging_layers),
      layers_path,
      mergeded_layer_path)

  @staticmethod
  def merge_layer_paths(layer_paths, output_path, crs=None):
    """Merge explicitly provided vector layers into output_path.

    layer_paths can contain file paths or ScrubLayer instances. This avoids the
    folder shapefile discovery used by merge_layers() and supports formats such
    as GeoPackage when QGIS can read them.
    """
    if isinstance(layer_paths, (str, bytes)) or not layer_paths:
      raise ValueError('layer_paths must be a non-empty list or tuple.')

    merging_layers = [
      getattr(layer_path, 'layer_path', layer_path)
      for layer_path in layer_paths
    ]

    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    params = {
      'LAYERS': merging_layers,
      'CRS': crs,
      'OUTPUT': output_path
    }

    processing.run('native:mergevectorlayers', params)
    logger.info(
      'Merged %s explicit layers into %s.',
      len(merging_layers),
      output_path)
    return output_path

  def multipart_to_singleparts(self, singleparts_layer_path):
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    params = {'INPUT': self.layer,
              'OUTPUT': singleparts_layer_path}
    processing.run("native:multiparttosingleparts", params)
    logger.info(
      'Converted multipart layer %s to singleparts at %s.',
      self.layer_name,
      singleparts_layer_path)

  def point_on_surface(self, output_path, all_parts=False):
    """Create point features guaranteed to be on each input surface."""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    params = {
      'INPUT': self.layer,
      'ALL_PARTS': all_parts,
      'OUTPUT': output_path
    }
    processing.run('native:pointonsurface', params)
    logger.info(
      'Created point-on-surface layer from %s into %s.',
      self.layer_name,
      output_path)
    return output_path

  def delete_duplicate_geometries(self, output_path):
    """Delete duplicate geometries using QGIS native processing."""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    params = {
      'INPUT': self.layer,
      'OUTPUT': output_path
    }
    processing.run('native:deleteduplicategeometries', params)
    logger.info(
      'Deleted duplicate geometries from %s into %s.',
      self.layer_name,
      output_path)
    return output_path

  def delete_duplicates(self, deleted_duplicates_layer):
    """Backward-compatible alias for delete_duplicate_geometries()."""
    return self.delete_duplicate_geometries(deleted_duplicates_layer)

  def extract_unique_by_field(
          self,
          field_name,
          output_path,
          include_null=False):
    """Extract the first feature for each unique value in an attribute field."""
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    selected_feature_ids = []
    seen_values = set()

    for feature in self.layer.getFeatures():
      field_value = feature[field_name]
      if field_value is None and not include_null:
        continue
      if field_value in seen_values:
        continue

      seen_values.add(field_value)
      selected_feature_ids.append(feature.id())

    self.layer.selectByIds(selected_feature_ids)
    params = {
      'INPUT': self.layer,
      'OUTPUT': output_path
    }
    try:
      processing.run('native:saveselectedfeatures', params)
    finally:
      self.layer.removeSelection()

    logger.info(
      'Extracted %s unique %s values from %s into %s.',
      len(selected_feature_ids),
      field_name,
      self.layer_name,
      output_path)
    return output_path

  def delete_field(self, field_name):
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    with edit(self.layer):
      # Get the index of the column to delete
      idx = self.layer.fields().indexFromName(field_name)
      if idx == -1:
        logger.warning(
          'Field %s was not found on %s.', field_name, self.layer_name)
        return

      # Delete the field
      deleted = self.layer.deleteAttribute(idx)

      # Update layer fields
      self.layer.updateFields()
    if deleted:
      logger.info('Deleted field %s from %s.', field_name, self.layer_name)
    else:
      logger.error(
        'Failed to delete field %s from %s.',
        field_name,
        self.layer_name)

  def rename_field(self, source_field, target_field, strict=True):
    """Rename one attribute field."""
    return self.field_schema_manager.rename_field(
      source_field, target_field, strict=strict)

  def rename_fields(self, field_rename_map, strict=True):
    """Rename multiple attribute fields from old_name -> new_name."""
    return self.field_schema_manager.rename_fields(
      field_rename_map, strict=strict)

  def drop_field(self, field_name, strict=True):
    """Drop one attribute field."""
    return self.field_schema_manager.drop_field(
      field_name, strict=strict)

  def drop_fields(self, fields_to_drop, strict=True):
    """Drop multiple attribute fields."""
    return self.field_schema_manager.drop_fields(
      fields_to_drop, strict=strict)

  def keep_only_fields(self, fields_to_keep, strict=True):
    """Keep only selected attribute fields and drop all other fields."""
    return self.field_schema_manager.keep_only_fields(
      fields_to_keep, strict=strict)

  def find_missing_fields(self, required_fields):
    """Return required fields that are missing from the layer."""
    return self.field_schema_manager.find_missing_fields(required_fields)

  def find_extra_fields(self, allowed_fields):
    """Return current layer fields that are not allowed."""
    return self.field_schema_manager.find_extra_fields(allowed_fields)

  def reorder_fields(
          self,
          field_order,
          append_unlisted=True,
          strict=True,
          output_path=None):
    """Reorder attribute fields while preserving feature values."""
    return self.field_schema_manager.reorder_fields(
      field_order,
      append_unlisted=append_unlisted,
      strict=strict,
      output_path=output_path)

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
    """Apply final field cleanup operations to this layer or a copy."""
    return self.field_schema_manager.standardize_fields(
      field_rename_map=field_rename_map,
      fields_to_drop=fields_to_drop,
      fields_to_keep=fields_to_keep,
      field_order=field_order,
      output_path=output_path,
      strict=strict,
      append_unlisted=append_unlisted,
      in_place=in_place,
      output_layer_name=output_layer_name)

  def delete_record_by_index(self, record_index):
    self.layer.startEditing()

    if self.layer.deleteFeature(record_index):
      logger.info(
        'Feature with ID %s has been successfully removed.', record_index)
    else:
      logger.error('Failed to remove feature with ID %s.', record_index)

    self.layer.commitChanges()

  def conditional_delete_record(self, field_name, operator, condition):
    if isinstance(condition, str) and condition.upper() != 'NULL':
      condition = f"'{condition}'"
    else:
      condition = str(condition)

    request = QgsFeatureRequest().setFilterExpression(
      f'"{field_name}" {operator} {condition}')
    deleted_count = 0
    with edit(self.layer):
      for feature in self.layer.getFeatures(request):
        if self.layer.deleteFeature(feature.id()):
          deleted_count += 1
        else:
          logger.warning(
            'Failed to delete feature %s from %s.',
            feature.id(),
            self.layer_name)
    logger.info(
      'Deleted %s records from %s where %s %s %s.',
      deleted_count,
      self.layer_name,
      field_name,
      operator,
      condition)

  def add_field(self, new_field_name):
    functionalities = self.layer.dataProvider().capabilities()

    if functionalities & QgsVectorDataProvider.AddAttributes:
      new_field = QgsField(new_field_name, QVariant.Double)
      added = self.layer.dataProvider().addAttributes([new_field])
      self.layer.updateFields()
      if added:
        logger.info('Added field %s to %s.', new_field_name, self.layer_name)
      else:
        logger.error(
          'Failed to add field %s to %s.',
          new_field_name,
          self.layer_name)
    else:
      logger.warning(
        'Layer %s does not support adding field %s.',
        self.layer_name,
        new_field_name)

  def assign_area(self, field_name):
    idx = self.layer.fields().indexFromName(field_name)
    if idx == -1:
      raise KeyError(
        f'Field {field_name} was not found on {self.layer_name}.')

    area_expression = QgsExpression('$area')
    if area_expression.hasParserError():
      raise ValueError(
        f'Invalid area expression: '
        f'{area_expression.parserErrorString()}')

    context = QgsExpressionContext()
    context.appendScopes(
      QgsExpressionContextUtils.globalProjectLayerScopes(self.layer))

    self.layer.startEditing()
    for feature in self.layer.getFeatures():
      context.setFeature(feature)
      area = area_expression.evaluate(context)
      if area_expression.hasEvalError():
        self.layer.commitChanges()
        raise ValueError(
          f'Failed to evaluate area for feature {feature.id()} on '
          f'{self.layer_name}: {area_expression.evalErrorString()}')
      feature[idx] = area
      self.layer.updateFeature(feature)

    self.layer.commitChanges()
    logger.info(
      'Assigned area values to field %s on %s.',
      field_name,
      self.layer_name)

  def assign_field_ratio(
          self,
          target_field,
          numerator_field,
          denominator_field):
    target_idx = self.layer.fields().indexFromName(target_field)
    numerator_idx = self.layer.fields().indexFromName(numerator_field)
    denominator_idx = self.layer.fields().indexFromName(denominator_field)
    missing_fields = [
      field_name
      for field_name, field_idx in [
        (target_field, target_idx),
        (numerator_field, numerator_idx),
        (denominator_field, denominator_idx),
      ]
      if field_idx == -1
    ]
    if missing_fields:
      raise KeyError(
        f'Fields {missing_fields} were not found on {self.layer_name}.')

    self.layer.startEditing()
    for feature in self.layer.getFeatures():
      numerator = feature[numerator_field]
      denominator = feature[denominator_field]
      if denominator in (None, 0):
        ratio = None
      else:
        ratio = float(numerator) / float(denominator)
      feature[target_idx] = ratio
      self.layer.updateFeature(feature)

    self.layer.commitChanges()
    logger.info(
      'Assigned %s / %s values to field %s on %s.',
      numerator_field,
      denominator_field,
      target_field,
      self.layer_name)

  def assign_field_expression(
          self,
          target_field,
          expression,
          field_type=None,
          field_length=0,
          field_precision=0):
    """Add or update a field using a QGIS expression evaluated per feature."""
    if not target_field:
      raise ValueError('target_field is required.')
    if not expression:
      raise ValueError('expression is required.')
    if field_type is None:
      field_type = QVariant.Double

    provider = self.layer.dataProvider()
    target_idx = self.layer.fields().indexFromName(target_field)
    if target_idx == -1:
      functionalities = provider.capabilities()
      if not functionalities & QgsVectorDataProvider.AddAttributes:
        raise ValueError(
          f'Layer {self.layer_name} does not support adding fields.')

      new_field = QgsField(
        target_field,
        field_type,
        len=field_length,
        prec=field_precision)
      added = provider.addAttributes([new_field])
      self.layer.updateFields()
      if not added:
        raise RuntimeError(
          f'Failed to add expression field {target_field} to '
          f'{self.layer_name}.')
      target_idx = self.layer.fields().indexFromName(target_field)

    qgis_expression = QgsExpression(expression)
    if qgis_expression.hasParserError():
      raise ValueError(
        f'Invalid expression for {target_field}: '
        f'{qgis_expression.parserErrorString()}')

    context = QgsExpressionContext()
    context.appendScopes(
      QgsExpressionContextUtils.globalProjectLayerScopes(self.layer))

    self.layer.startEditing()
    updated_count = 0
    for feature in self.layer.getFeatures():
      context.setFeature(feature)
      value = qgis_expression.evaluate(context)
      if qgis_expression.hasEvalError():
        self.layer.commitChanges()
        raise ValueError(
          f'Failed to evaluate expression for feature {feature.id()} on '
          f'{self.layer_name}: {qgis_expression.evalErrorString()}')
      feature[target_idx] = value
      self.layer.updateFeature(feature)
      updated_count += 1

    self.layer.commitChanges()
    logger.info(
      'Assigned expression values to field %s on %s for %s features.',
      target_field,
      self.layer_name,
      updated_count)
    return target_field

  def duplicate_text_field(
          self,
          source_field,
          target_field,
          field_length,
          overwrite=False,
          batch_size=10000):
    """Copy source_field values intact into a text target_field."""
    if batch_size <= 0:
      raise ValueError('batch_size must be greater than zero.')

    source_idx = self.layer.fields().indexFromName(source_field)
    if source_idx == -1:
      raise KeyError(
        f'Field {source_field} was not found on {self.layer_name}.')

    target_idx = self.layer.fields().indexFromName(target_field)
    if target_idx != -1 and not overwrite:
      raise ValueError(
        f'Field {target_field} already exists on {self.layer_name}.')

    provider = self.layer.dataProvider()
    if target_idx == -1:
      functionalities = provider.capabilities()
      if not functionalities & QgsVectorDataProvider.AddAttributes:
        raise ValueError(
          f'Layer {self.layer_name} does not support adding fields.')

      new_field = QgsField(target_field, QVariant.String, len=field_length)
      added = provider.addAttributes([new_field])
      self.layer.updateFields()
      if not added:
        raise RuntimeError(
          f'Failed to add duplicate text field {target_field} to '
          f'{self.layer_name}.')
      target_idx = self.layer.fields().indexFromName(target_field)

    can_bulk_update = (
      provider.capabilities() & QgsVectorDataProvider.ChangeAttributeValues)
    if not can_bulk_update:
      raise ValueError(
        f'Layer {self.layer_name} does not support changing attributes.')

    updated_count = 0
    change_map = {}
    for feature in self.layer.getFeatures():
      source_value = feature[source_field]
      if source_value is None:
        target_value = None
      elif isinstance(source_value, str):
        target_value = source_value
      else:
        target_value = str(source_value)

      change_map[feature.id()] = {target_idx: target_value}
      if len(change_map) >= batch_size:
        if not provider.changeAttributeValues(change_map):
          raise RuntimeError(
            f'Failed to copy {source_field} to {target_field} on '
            f'{self.layer_name}.')
        updated_count += len(change_map)
        change_map = {}

    if change_map:
      if not provider.changeAttributeValues(change_map):
        raise RuntimeError(
          f'Failed to copy {source_field} to {target_field} on '
          f'{self.layer_name}.')
      updated_count += len(change_map)

    logger.info(
      'Copied %s values from %s to text field %s on %s.',
      updated_count,
      source_field,
      target_field,
      self.layer_name)
    return target_field

  def add_uuid_field(
          self,
          field_name='uuid',
          field_length=36,
          overwrite=False,
          batch_size=10000):
    """Add and populate a text UUID field for every feature.

    Values match the QGIS expression:
    replace(replace(uuid(), '{', ''), '}', '')
    """
    idx = self.layer.fields().indexFromName(field_name)
    if idx != -1 and not overwrite:
      raise ValueError(
        f'Field {field_name} already exists on {self.layer_name}.')

    provider = self.layer.dataProvider()
    if idx == -1:
      functionalities = provider.capabilities()
      if not functionalities & QgsVectorDataProvider.AddAttributes:
        raise ValueError(
          f'Layer {self.layer_name} does not support adding fields.')

      new_field = QgsField(field_name, QVariant.String, len=field_length)
      added = provider.addAttributes([new_field])
      self.layer.updateFields()
      if not added:
        raise RuntimeError(
          f'Failed to add UUID field {field_name} to {self.layer_name}.')
      idx = self.layer.fields().indexFromName(field_name)

    if batch_size <= 0:
      raise ValueError('batch_size must be greater than zero.')

    updated_count = 0
    can_bulk_update = (
      provider.capabilities() & QgsVectorDataProvider.ChangeAttributeValues)
    if can_bulk_update:
      change_map = {}
      for feature in self.layer.getFeatures():
        change_map[feature.id()] = {idx: str(uuid.uuid4())}
        if len(change_map) >= batch_size:
          if not provider.changeAttributeValues(change_map):
            raise RuntimeError(
              f'Failed to update UUID field {field_name} on '
              f'{self.layer_name}.')
          updated_count += len(change_map)
          change_map = {}

      if change_map:
        if not provider.changeAttributeValues(change_map):
          raise RuntimeError(
            f'Failed to update UUID field {field_name} on {self.layer_name}.')
        updated_count += len(change_map)

      logger.info(
        'Assigned UUID values to field %s on %s for %s features.',
        field_name,
        self.layer_name,
        updated_count)
      return field_name

    with edit(self.layer):
      for feature in self.layer.getFeatures():
        feature[idx] = str(uuid.uuid4())
        if self.layer.updateFeature(feature):
          updated_count += 1
        else:
          logger.warning(
            'Failed to update UUID field for feature %s on %s.',
            feature.id(),
            self.layer_name)

    logger.info(
      'Assigned UUID values to field %s on %s for %s features.',
      field_name,
      self.layer_name,
      updated_count)
    return field_name

  def __str__(self):
    return f'The {self.layer_name} has {self.data_count} records.'

  @staticmethod
  def cleanup():
    QgsApplication.exitQgis()
    logger.info('QGIS application cleanup completed.')
