"""
CityGISOO
test_geopackage_feature_processor module
"""

import os
import sys
import types
import unittest
from unittest.mock import Mock, patch


_REPO_ROOT = os.path.abspath(
  os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
  sys.path.insert(0, _SABU_CHASSIS_SRC)


class _Dummy:
  AddAttributes = 1
  ChangeAttributeValues = 2
  Double = 6
  String = 10
  NoError = 0
  CreateOrOverwriteFile = 1
  NoGeometry = 1

  def __init__(self, *args, **kwargs):
    pass

  def __call__(self, *args, **kwargs):
    return self

  def __getattr__(self, name):
    return _Dummy()


def _install_qgis_stubs():
  qgis_module = types.ModuleType('qgis')
  qgis_core_module = types.ModuleType('qgis.core')
  qgis_analysis_module = types.ModuleType('qgis.analysis')
  qgis_pyqt_module = types.ModuleType('qgis.PyQt')
  qgis_qtcore_module = types.ModuleType('qgis.PyQt.QtCore')
  processing_module = types.ModuleType('processing')

  qgis_core_names = [
    'QgsApplication',
    'QgsCoordinateReferenceSystem',
    'QgsExpression',
    'QgsExpressionContext',
    'QgsExpressionContextUtils',
    'QgsFeature',
    'QgsFeatureRequest',
    'QgsField',
    'QgsProcessingFeatureSourceDefinition',
    'QgsProcessingFeedback',
    'QgsProject',
    'QgsVectorDataProvider',
    'QgsVectorFileWriter',
    'QgsVectorLayerJoinInfo',
    'QgsVectorLayer',
    'QgsWkbTypes',
    'edit',
  ]
  for name in qgis_core_names:
    setattr(qgis_core_module, name, _Dummy)

  qgis_analysis_module.QgsNativeAlgorithms = _Dummy
  qgis_qtcore_module.QVariant = _Dummy
  processing_module.run = Mock()

  sys.modules['qgis'] = qgis_module
  sys.modules['qgis.core'] = qgis_core_module
  sys.modules['qgis.analysis'] = qgis_analysis_module
  sys.modules['qgis.PyQt'] = qgis_pyqt_module
  sys.modules['qgis.PyQt.QtCore'] = qgis_qtcore_module
  sys.modules['processing'] = processing_module


_install_qgis_stubs()

from src.citygisoo import geopackage_feature_processor as processor_module
from src.citygisoo.geopackage_feature_processor import (
  FieldSpec,
  GeoPackageFeatureProcessor,
)


class _FakeQVariant:
  Double = 6
  String = 10


class _FakeQgsVectorDataProvider:
  AddAttributes = 1
  ChangeAttributeValues = 2


class _FakeQgsField:
  def __init__(self, name, field_type, len=0, prec=0):
    self.name_value = name
    self.type_value = field_type
    self.length_value = len
    self.precision_value = prec

  def name(self):
    return self.name_value

  def type(self):
    return self.type_value

  def length(self):
    return self.length_value

  def precision(self):
    return self.precision_value


class _FakeFields:
  def __init__(self, field_names):
    self.field_names = field_names

  def indexFromName(self, field_name):
    try:
      return self.field_names.index(field_name)
    except ValueError:
      return -1

  def __getitem__(self, idx):
    return _FakeQgsField(self.field_names[idx], _FakeQVariant.String)

  def __iter__(self):
    for field_name in self.field_names:
      yield _FakeQgsField(field_name, _FakeQVariant.String)


class _FakeFeature:
  def __init__(self, fid, attributes):
    self.fid = fid
    self.attributes_by_name = dict(attributes)

  def id(self):
    return self.fid

  def __getitem__(self, field_name):
    return self.attributes_by_name.get(field_name)

  def attributes(self):
    return list(self.attributes_by_name.values())


class _FakeProvider:
  def __init__(self, layer):
    self.layer = layer
    self.added_fields = []
    self.change_maps = []

  def capabilities(self):
    return (
      _FakeQgsVectorDataProvider.AddAttributes
      | _FakeQgsVectorDataProvider.ChangeAttributeValues)

  def addAttributes(self, fields):
    self.added_fields.extend(fields)
    for field in fields:
      self.layer.field_names.append(field.name())
    return True

  def changeAttributeValues(self, change_map):
    self.change_maps.append(change_map)
    return True


class _FakeLayer:
  def __init__(self, layer_path, field_names, features):
    self.layer_path = layer_path
    self.field_names = list(field_names)
    self.features = list(features)
    self.provider = _FakeProvider(self)

  def fields(self):
    return _FakeFields(self.field_names)

  def getFeatures(self, request=None):
    return iter(self.features)

  def dataProvider(self):
    return self.provider

  def updateFields(self):
    return None


class _FakeScrubLayer:
  def __init__(self, layer_path, layer_name, layer):
    self.layer_path = layer_path
    self.layer_name = layer_name
    self.layer = layer


class _FakeFeatureRequestWithNameFallback:
  NoGeometry = 1

  def __init__(self):
    self.subset_attributes = None
    self.flags = None

  def setSubsetOfAttributes(self, attributes, fields):
    if attributes and isinstance(attributes[0], int):
      raise TypeError("index 0 has type 'int' but 'str' is expected")
    self.subset_attributes = list(attributes)

  def setFlags(self, flags):
    self.flags = flags


class GeoPackageFeatureProcessorTest(unittest.TestCase):
  def setUp(self):
    processor_module.QVariant = _FakeQVariant
    processor_module.QgsField = _FakeQgsField
    processor_module.QgsVectorDataProvider = _FakeQgsVectorDataProvider

  def test_extract_by_membership_writes_non_matching_features(self):
    processor = GeoPackageFeatureProcessor()
    source_layer = _FakeLayer(
      'usage.gpkg',
      ['g_id_provi'],
      [
        _FakeFeature(1, {'g_id_provi': 'A'}),
        _FakeFeature(2, {'g_id_provi': 'C'}),
      ])
    lookup_layer = _FakeLayer(
      'roll.gpkg',
      ['id_provinc'],
      [
        _FakeFeature(10, {'id_provinc': 'A'}),
        _FakeFeature(11, {'id_provinc': 'B'}),
      ])
    source = _FakeScrubLayer('usage.gpkg', 'usage', source_layer)
    lookup = _FakeScrubLayer('roll.gpkg', 'roll', lookup_layer)

    with patch.object(
            processor,
            '_write_features_like_source',
            return_value='usage_missing.gpkg') as write_mock:
      result = processor.extract_by_membership(
        source_layer=source,
        lookup_layer=lookup,
        source_field='g_id_provi',
        lookup_field='id_provinc',
        output_path='usage_missing.gpkg',
        include_matches=False)

    self.assertEqual(result, 'usage_missing.gpkg')
    written_features = write_mock.call_args.args[1]
    self.assertEqual([feature.id() for feature in written_features], [2])

  def test_extract_by_membership_rejects_non_geopackage_inputs(self):
    processor = GeoPackageFeatureProcessor()
    layer = _FakeLayer('usage.shp', ['g_id_provi'], [])
    source = _FakeScrubLayer('usage.shp', 'usage', layer)

    with self.assertRaises(ValueError):
      processor.extract_by_membership(
        source_layer=source,
        lookup_layer=source,
        source_field='g_id_provi',
        lookup_field='g_id_provi',
        output_path='usage_missing.gpkg')

  def test_add_ratio_field_adds_double_field_and_handles_zero_denominator(self):
    processor = GeoPackageFeatureProcessor()
    feature_with_ratio = _FakeFeature(
      1,
      {
        'numerator': 8,
        'denominator': 2,
      })
    feature_with_zero_denominator = _FakeFeature(
      2,
      {
        'numerator': 8,
        'denominator': 0,
      })
    layer = _FakeLayer(
      'ratios.gpkg',
      ['numerator', 'denominator'],
      [
        feature_with_ratio,
        feature_with_zero_denominator,
      ])
    scrub_layer = _FakeScrubLayer('ratios.gpkg', 'ratios', layer)

    result = processor.add_ratio_field(
      scrub_layer,
      target_field='ratio',
      numerator_field='numerator',
      denominator_field='denominator')

    self.assertEqual(result, 'ratio')
    self.assertEqual(layer.provider.added_fields[0].name(), 'ratio')
    self.assertEqual(
      layer.provider.added_fields[0].type(),
      _FakeQVariant.Double)
    self.assertEqual(
      layer.provider.change_maps,
      [
        {
          1: {2: 4.0},
          2: {2: None},
        }
      ])

  def test_add_calculated_field_rejects_existing_field_without_overwrite(self):
    processor = GeoPackageFeatureProcessor()
    layer = _FakeLayer('layer.gpkg', ['status'], [])
    scrub_layer = _FakeScrubLayer('layer.gpkg', 'layer', layer)

    with self.assertRaises(ValueError):
      processor.add_calculated_field(
        scrub_layer,
        FieldSpec('status', _FakeQVariant.String),
        lambda feature: 'x')

  def test_request_for_fields_falls_back_to_name_subset_overload(self):
    processor = GeoPackageFeatureProcessor()
    layer = _FakeLayer('layer.gpkg', ['status'], [])

    with patch.object(
            processor_module,
            'QgsFeatureRequest',
            _FakeFeatureRequestWithNameFallback):
      request = processor._request_for_fields(
        layer,
        ['status'],
        include_geometry=False)

    self.assertEqual(request.subset_attributes, ['status'])
    self.assertEqual(
      request.flags,
      _FakeFeatureRequestWithNameFallback.NoGeometry)


if __name__ == '__main__':
  unittest.main()
