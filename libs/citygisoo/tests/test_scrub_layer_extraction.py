"""
CityGISOO
test_scrub_layer_extraction module
Project Developer: Alireza Adli
alireza.adli@concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import os
import sys
import types
import unittest
from unittest.mock import ANY, Mock, patch


_REPO_ROOT = os.path.abspath(
  os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
  sys.path.insert(0, _SABU_CHASSIS_SRC)


class _Dummy:
  NoError = 0

  @staticmethod
  def processingRegistry():
    return _Dummy()

  def __init__(self, *args, **kwargs):
    pass

  def __call__(self, *args, **kwargs):
    return self

  def addProvider(self, *args, **kwargs):
    return None

  def __getattr__(self, name):
    return _Dummy()


def _install_qgis_stubs():
  qgis_module = types.ModuleType('qgis')
  qgis_core_module = types.ModuleType('qgis.core')
  qgis_analysis_module = types.ModuleType('qgis.analysis')
  qgis_pyqt_module = types.ModuleType('qgis.PyQt')
  qgis_qtcore_module = types.ModuleType('qgis.PyQt.QtCore')

  qgis_core_names = [
    'QgsApplication',
    'QgsCoordinateReferenceSystem',
    'QgsExpression',
    'QgsExpressionContext',
    'QgsExpressionContextUtils',
    'QgsFeatureRequest',
    'QgsField',
    'QgsProcessingFeedback',
    'QgsProject',
    'QgsVectorDataProvider',
    'QgsVectorFileWriter',
    'QgsVectorLayer',
    'QgsVectorLayerJoinInfo',
    'edit',
  ]
  for name in qgis_core_names:
    setattr(qgis_core_module, name, _Dummy)

  qgis_analysis_module.QgsNativeAlgorithms = _Dummy
  qgis_qtcore_module.QVariant = _Dummy

  processing_module = sys.modules.get('processing')
  if processing_module is None:
    processing_module = types.ModuleType('processing')
  if not hasattr(processing_module, 'run'):
    processing_module.run = Mock()
  sys.modules['processing'] = processing_module
  sys.modules['qgis'] = qgis_module
  sys.modules['qgis.core'] = qgis_core_module
  sys.modules['qgis.analysis'] = qgis_analysis_module
  sys.modules['qgis.PyQt'] = qgis_pyqt_module
  sys.modules['qgis.PyQt.QtCore'] = qgis_qtcore_module


_install_qgis_stubs()

from src.citygisoo import scrub_layer_class as scrub_layer_module
from src.citygisoo.scrub_layer_class import ScrubLayer


class _FakeQgsApplication:
  @staticmethod
  def processingRegistry():
    return _Dummy()


def _build_scrub_layer():
  scrub_layer = ScrubLayer.__new__(ScrubLayer)
  scrub_layer.layer = object()
  scrub_layer.layer_name = 'fsa_boundaries'
  scrub_layer.layer_path = 'fsa_boundaries.gpkg'
  scrub_layer.qgis_path = 'C:/QGIS'
  return scrub_layer


def _build_lookup_layer(layer_name):
  lookup_layer = ScrubLayer.__new__(ScrubLayer)
  lookup_layer.layer_name = layer_name
  lookup_layer.layer_path = f'{layer_name}.shp'
  return lookup_layer


class _FakeFeature:
  def __init__(self, feature_id, attributes):
    self._feature_id = feature_id
    self._attributes = attributes

  def id(self):
    return self._feature_id

  def __getitem__(self, field_name):
    return self._attributes[field_name]


class _FakeVectorLayer:
  def __init__(self, features):
    self._features = features
    self.selected_ids = None
    self.selection_removed = False

  def getFeatures(self):
    return iter(self._features)

  def selectByIds(self, selected_ids):
    self.selected_ids = selected_ids

  def removeSelection(self):
    self.selection_removed = True


class _FakeQgsVectorDataProvider:
  AddAttributes = 1
  ChangeAttributeValues = 2


class _FakeQVariant:
  String = 'String'


class _FakeQgsField:
  def __init__(self, name, field_type, len=None):
    self.name = name
    self.field_type = field_type
    self.length = len


class _FakeFields:
  def __init__(self, names):
    self.names = names

  def indexFromName(self, field_name):
    try:
      return self.names.index(field_name)
    except ValueError:
      return -1


class _FakeProvider:
  def __init__(self, layer):
    self.layer = layer
    self.added_fields = []
    self.changed_attributes = []

  def capabilities(self):
    return (
      _FakeQgsVectorDataProvider.AddAttributes
      | _FakeQgsVectorDataProvider.ChangeAttributeValues)

  def addAttributes(self, fields):
    self.added_fields.extend(fields)
    for field in fields:
      self.layer.field_names.append(field.name)
    return True

  def changeAttributeValues(self, change_map):
    self.changed_attributes.append(change_map)
    return True


class _FakeAttributeLayer:
  def __init__(self, field_names, features):
    self.field_names = list(field_names)
    self._features = features
    self.provider = _FakeProvider(self)

  def fields(self):
    return _FakeFields(self.field_names)

  def dataProvider(self):
    return self.provider

  def updateFields(self):
    return None

  def getFeatures(self):
    return iter(self._features)


class _FakeJoinMainLayer:
  def __init__(self):
    self.added_join = None

  def addJoin(self, join_info):
    self.added_join = join_info
    return True


class _FakeJoiningLayer:
  def __init__(self, layer_path, layer_name, provider):
    self.layer_path = layer_path
    self.layer_name = layer_name
    self.provider = provider

  def isValid(self):
    return True


class _FakeQgsVectorLayerJoinInfo:
  def __init__(self):
    self.joining_layer = None
    self.join_field = None
    self.target_field = None
    self.prefix = None
    self.using_memory_cache = None
    self.join_fields = None

  def setJoinLayer(self, joining_layer):
    self.joining_layer = joining_layer

  def setJoinFieldName(self, join_field):
    self.join_field = join_field

  def setTargetFieldName(self, target_field):
    self.target_field = target_field

  def setPrefix(self, prefix):
    self.prefix = prefix

  def setUsingMemoryCache(self, using_memory_cache):
    self.using_memory_cache = using_memory_cache

  def setJoinFieldNamesSubset(self, join_fields):
    self.join_fields = join_fields


class _FakeQgsProject:
  added_layers = []

  @classmethod
  def instance(cls):
    return cls

  @classmethod
  def addMapLayer(cls, layer):
    cls.added_layers.append(layer)


class TestScrubLayerExtraction(unittest.TestCase):
  def setUp(self):
    scrub_layer_module.QgsApplication = _FakeQgsApplication
    scrub_layer_module.QgsField = _FakeQgsField
    scrub_layer_module.QgsVectorDataProvider = _FakeQgsVectorDataProvider
    scrub_layer_module.QVariant = _FakeQVariant
    _FakeQgsProject.added_layers = []

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_extract_by_attribute_runs_qgis_algorithm(self, processing_run_mock):
    scrub_layer = _build_scrub_layer()

    result = scrub_layer.extract_by_attribute(
      field_name='g_fsa',
      operator='=',
      value='H3H',
      output_path='output/fsa_boundary.shp')

    self.assertEqual(result, 'output/fsa_boundary.shp')
    processing_run_mock.assert_called_once_with(
      'native:extractbyattribute',
      {
        'INPUT': scrub_layer.layer,
        'FIELD': 'g_fsa',
        'OPERATOR': 0,
        'VALUE': 'H3H',
        'OUTPUT': 'output/fsa_boundary.shp',
      })

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_extract_by_expression_runs_qgis_algorithm(self, processing_run_mock):
    scrub_layer = _build_scrub_layer()

    result = scrub_layer.extract_by_expression(
      expression='"g_fsa" = \'H3H\'',
      output_path='output/fsa_boundary.shp')

    self.assertEqual(result, 'output/fsa_boundary.shp')
    processing_run_mock.assert_called_once_with(
      'native:extractbyexpression',
      {
        'INPUT': scrub_layer.layer,
        'EXPRESSION': '"g_fsa" = \'H3H\'',
        'OUTPUT': 'output/fsa_boundary.shp',
      })

  @patch.object(ScrubLayer, 'extract_by_expression')
  def test_extract_by_aggregate_membership_extracts_matches(
          self, extract_by_expression_mock):
    scrub_layer = _build_scrub_layer()
    lookup_layer = _build_lookup_layer('roll_clipped_H3H')

    result = scrub_layer.extract_by_aggregate_membership(
      lookup_layer=lookup_layer,
      lookup_field='id_provinc',
      target_field='g_id_provi',
      output_path='output/usage_margin_sans.shp')

    self.assertEqual(result, extract_by_expression_mock.return_value)
    extract_by_expression_mock.assert_called_once_with(
      'array_contains('
      'aggregate('
      "layer:='roll_clipped_H3H',"
      "aggregate:='array_agg',"
      'expression:="id_provinc"'
      '),'
      '"g_id_provi"'
      ')',
      'output/usage_margin_sans.shp')

  @patch.object(ScrubLayer, 'extract_by_expression')
  def test_extract_by_aggregate_membership_extracts_non_matches(
          self, extract_by_expression_mock):
    scrub_layer = _build_scrub_layer()

    result = scrub_layer.extract_by_aggregate_membership(
      lookup_layer='roll',
      lookup_field='id_provinc',
      target_field='g_id_provi',
      output_path='output/usage_margin_sans.shp',
      include_matches=False)

    self.assertEqual(result, extract_by_expression_mock.return_value)
    extract_by_expression_mock.assert_called_once_with(
      'NOT array_contains('
      'aggregate('
      "layer:='roll',"
      "aggregate:='array_agg',"
      'expression:="id_provinc"'
      '),'
      '"g_id_provi"'
      ')',
      'output/usage_margin_sans.shp')

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_difference_layer_runs_qgis_algorithm(self, processing_run_mock):
    scrub_layer = _build_scrub_layer()

    result = scrub_layer.difference_layer(
      overlay_layer='output/roll.shp',
      output_path='output/usage_only.shp')

    self.assertEqual(result, 'output/usage_only.shp')
    processing_run_mock.assert_called_once_with(
      'native:difference',
      {
        'INPUT': 'fsa_boundaries.gpkg',
        'OVERLAY': 'output/roll.shp',
        'OUTPUT': 'output/usage_only.shp',
      })

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_difference_layer_accepts_scrub_layer_overlay_and_grid_size(
          self, processing_run_mock):
    scrub_layer = _build_scrub_layer()
    overlay_layer = _build_lookup_layer('roll_clipped_H3H')

    result = scrub_layer.difference_layer(
      overlay_layer=overlay_layer,
      output_path='output/usage_only.shp',
      grid_size=0.001)

    self.assertEqual(result, 'output/usage_only.shp')
    processing_run_mock.assert_called_once_with(
      'native:difference',
      {
        'INPUT': 'fsa_boundaries.gpkg',
        'OVERLAY': 'roll_clipped_H3H.shp',
        'OUTPUT': 'output/usage_only.shp',
        'GRID_SIZE': 0.001,
      })

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_extract_unique_by_field_saves_first_feature_per_value(
          self, processing_run_mock):
    scrub_layer = _build_scrub_layer()
    scrub_layer.layer = _FakeVectorLayer([
      _FakeFeature(10, {'ro_id_provinc': 'A'}),
      _FakeFeature(11, {'ro_id_provinc': 'B'}),
      _FakeFeature(12, {'ro_id_provinc': 'A'}),
      _FakeFeature(13, {'ro_id_provinc': None}),
    ])

    result = scrub_layer.extract_unique_by_field(
      field_name='ro_id_provinc',
      output_path='output/usage_roll_only_unique.shp')

    self.assertEqual(result, 'output/usage_roll_only_unique.shp')
    self.assertEqual(scrub_layer.layer.selected_ids, [10, 11])
    self.assertTrue(scrub_layer.layer.selection_removed)
    processing_run_mock.assert_called_once_with(
      'native:saveselectedfeatures',
      {
        'INPUT': scrub_layer.layer,
        'OUTPUT': 'output/usage_roll_only_unique.shp',
      })

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_extract_unique_by_field_can_include_one_null_value(
          self, processing_run_mock):
    scrub_layer = _build_scrub_layer()
    scrub_layer.layer = _FakeVectorLayer([
      _FakeFeature(10, {'ro_id_provinc': None}),
      _FakeFeature(11, {'ro_id_provinc': None}),
    ])

    scrub_layer.extract_unique_by_field(
      field_name='ro_id_provinc',
      output_path='output/usage_roll_only_unique.shp',
      include_null=True)

    self.assertEqual(scrub_layer.layer.selected_ids, [10])
    processing_run_mock.assert_called_once()

  def test_duplicate_text_field_adds_string_field_and_copies_values_intact(
          self):
    scrub_layer = _build_scrub_layer()
    scrub_layer.layer = _FakeAttributeLayer(
      ['id_provinc'],
      [
        _FakeFeature(10, {'id_provinc': 'Évaluation-123'}),
        _FakeFeature(11, {'id_provinc': 'Apostrophe O\'Neil'}),
        _FakeFeature(12, {'id_provinc': None}),
      ])

    result = scrub_layer.duplicate_text_field(
      source_field='id_provinc',
      target_field='r_id_provinc',
      field_length=36)

    self.assertEqual(result, 'r_id_provinc')
    self.assertEqual(scrub_layer.layer.field_names,
                     ['id_provinc', 'r_id_provinc'])
    added_field = scrub_layer.layer.provider.added_fields[0]
    self.assertEqual(added_field.name, 'r_id_provinc')
    self.assertEqual(added_field.field_type, _FakeQVariant.String)
    self.assertEqual(added_field.length, 36)
    self.assertEqual(
      scrub_layer.layer.provider.changed_attributes,
      [{10: {1: 'Évaluation-123'},
        11: {1: 'Apostrophe O\'Neil'},
        12: {1: None}}])

  def test_duplicate_text_field_rejects_existing_target_by_default(self):
    scrub_layer = _build_scrub_layer()
    scrub_layer.layer = _FakeAttributeLayer(
      ['id_provinc', 'r_id_provinc'],
      [_FakeFeature(10, {'id_provinc': 'A'})])

    with self.assertRaises(ValueError):
      scrub_layer.duplicate_text_field(
        source_field='id_provinc',
        target_field='r_id_provinc',
        field_length=36)

  def test_duplicate_text_field_rejects_missing_source(self):
    scrub_layer = _build_scrub_layer()
    scrub_layer.layer = _FakeAttributeLayer(
      ['id_provinc'],
      [_FakeFeature(10, {'id_provinc': 'A'})])

    with self.assertRaises(KeyError):
      scrub_layer.duplicate_text_field(
        source_field='missing',
        target_field='r_id_provinc',
        field_length=36)

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_spatial_join_with_predicate_runs_qgis_algorithm(
          self, processing_run_mock):
    scrub_layer = _build_scrub_layer()

    result = scrub_layer.spatial_join_with_predicate(
      joining_layer_path='output/property_assessment.shp',
      joined_layer_path='output/property_usage_joined.shp',
      predicate='within',
      join_method='one-to-one-first',
      prefix='pa_')

    self.assertEqual(result, 'output/property_usage_joined.shp')
    processing_run_mock.assert_called_once_with(
      'native:joinattributesbylocation',
      {
        'INPUT': scrub_layer.layer,
        'PREDICATE': [5],
        'JOIN': 'output/property_assessment.shp',
        'JOIN_FIELDS': [],
        'METHOD': 1,
        'DISCARD_NONMATCHING': False,
        'PREFIX': 'pa_',
        'OUTPUT': 'output/property_usage_joined.shp',
      },
      feedback=ANY)

  def test_spatial_join_with_predicate_accepts_multiple_predicates(self):
    self.assertEqual(
      ScrubLayer._normalize_spatial_join_predicate(['intersects', 'within']),
      [0, 5])

  def test_spatial_join_with_predicate_defaults_to_one_to_many(self):
    self.assertEqual(
      ScrubLayer._normalize_spatial_join_method('one-to-many'),
      0)

  def test_spatial_join_with_predicate_accepts_largest_overlap_method(self):
    self.assertEqual(
      ScrubLayer._normalize_spatial_join_method('largest overlap'),
      2)

  def test_spatial_join_with_predicate_rejects_unknown_predicate(self):
    with self.assertRaises(ValueError):
      ScrubLayer._normalize_spatial_join_predicate('near')

  def test_spatial_join_with_predicate_rejects_unknown_method(self):
    with self.assertRaises(ValueError):
      ScrubLayer._normalize_spatial_join_method('nearest')

  def test_add_layer_join_adds_qgis_layer_properties_join(self):
    scrub_layer = _build_scrub_layer()
    scrub_layer.layer = _FakeJoinMainLayer()

    with patch(
            'src.citygisoo.scrub_layer_class.QgsVectorLayer',
            _FakeJoiningLayer), \
        patch(
            'src.citygisoo.scrub_layer_class.QgsVectorLayerJoinInfo',
            _FakeQgsVectorLayerJoinInfo), \
        patch('src.citygisoo.scrub_layer_class.QgsProject', _FakeQgsProject):
      join_info = scrub_layer.add_layer_join(
        joining_layer_path='output/roll.shp',
        joining_layer_name='roll',
        join_field='id_provinc',
        target_field='g_id_provi',
        prefix='roll_',
        join_fields=['usage'])

    self.assertIs(scrub_layer.layer.added_join, join_info)
    self.assertEqual(join_info.joining_layer.layer_path, 'output/roll.shp')
    self.assertEqual(join_info.joining_layer.layer_name, 'roll')
    self.assertEqual(join_info.join_field, 'id_provinc')
    self.assertEqual(join_info.target_field, 'g_id_provi')
    self.assertEqual(join_info.prefix, 'roll_')
    self.assertTrue(join_info.using_memory_cache)
    self.assertEqual(join_info.join_fields, ['usage'])
    self.assertEqual(_FakeQgsProject.added_layers, [join_info.joining_layer])

  @patch.object(ScrubLayer, 'field_join')
  def test_add_layer_join_with_output_path_persists_join(
          self, field_join_mock):
    scrub_layer = _build_scrub_layer()

    result = scrub_layer.add_layer_join(
      joining_layer_path='output/roll.shp',
      joining_layer_name='roll',
      join_field='id_provinc',
      target_field='g_id_provi',
      prefix='roll_',
      output_path='output/joined.shp',
      join_fields=['usage'])

    self.assertEqual(result, 'output/joined.shp')
    field_join_mock.assert_called_once_with(
      joining_layer_path='output/roll.shp',
      joining_layer_name='roll',
      target_field='g_id_provi',
      join_field='id_provinc',
      join_fields=['usage'],
      prefix='roll_',
      output_path='output/joined.shp')

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_merge_layer_paths_runs_qgis_algorithm_for_explicit_paths(
          self, processing_run_mock):
    result = ScrubLayer.merge_layer_paths(
      layer_paths=[
        'input/usage_a.gpkg',
        'input/usage_b.gpkg',
        'input/usage_c.gpkg',
      ],
      output_path='output/merged_usage.gpkg',
      crs='EPSG:2950')

    self.assertEqual(result, 'output/merged_usage.gpkg')
    processing_run_mock.assert_called_once_with(
      'native:mergevectorlayers',
      {
        'LAYERS': [
          'input/usage_a.gpkg',
          'input/usage_b.gpkg',
          'input/usage_c.gpkg',
        ],
        'CRS': 'EPSG:2950',
        'OUTPUT': 'output/merged_usage.gpkg',
      })

  @patch('src.citygisoo.scrub_layer_class.processing.run')
  def test_merge_layer_paths_accepts_scrub_layer_instances(
          self, processing_run_mock):
    first_layer = _build_lookup_layer('first')
    second_layer = _build_lookup_layer('second')

    ScrubLayer.merge_layer_paths(
      layer_paths=[first_layer, second_layer],
      output_path='output/merged.shp')

    processing_run_mock.assert_called_once_with(
      'native:mergevectorlayers',
      {
        'LAYERS': ['first.shp', 'second.shp'],
        'CRS': None,
        'OUTPUT': 'output/merged.shp',
      })

  def test_merge_layer_paths_rejects_plain_string_layer_paths(self):
    with self.assertRaises(ValueError):
      ScrubLayer.merge_layer_paths(
        layer_paths='input/usage_a.gpkg',
        output_path='output/merged_usage.gpkg')

  def test_extract_by_attribute_rejects_unknown_operator(self):
    with self.assertRaises(ValueError):
      ScrubLayer._normalize_extract_attribute_operator('near')


if __name__ == '__main__':
  unittest.main()
