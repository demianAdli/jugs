"""
CityGISOO
test_scrub_layer_uuid module
Project Developer: Alireza Adli
alireza.adli@concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import os
import sys
import types
import unittest
from contextlib import contextmanager


_REPO_ROOT = os.path.abspath(
  os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
  sys.path.insert(0, _SABU_CHASSIS_SRC)


class _Dummy:
  AddAttributes = 1
  ChangeAttributeValues = 2
  String = 10
  NoError = 0

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

  qgis_core_names = [
    'QgsApplication',
    'QgsCoordinateReferenceSystem',
    'QgsExpression',
    'QgsExpressionContext',
    'QgsExpressionContextUtils',
    'QgsFeatureRequest',
    'QgsField',
    'QgsProcessingFeedback',
    'QgsProcessingFeatureSourceDefinition',
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

  sys.modules['processing'] = types.ModuleType('processing')
  sys.modules['qgis'] = qgis_module
  sys.modules['qgis.core'] = qgis_core_module
  sys.modules['qgis.analysis'] = qgis_analysis_module
  sys.modules['qgis.PyQt'] = qgis_pyqt_module
  sys.modules['qgis.PyQt.QtCore'] = qgis_qtcore_module


_install_qgis_stubs()

from src.citygisoo import scrub_layer_class as scrub_layer_module
from src.citygisoo.scrub_layer_class import ScrubLayer


class _FakeQVariant:
  String = 10


class _FakeQgsVectorDataProvider:
  AddAttributes = 1
  ChangeAttributeValues = 2


class _FakeQgsField:
  def __init__(self, name, field_type, len=0):
    self.name = name
    self.field_type = field_type
    self.length = len


class _FakeFields:
  def __init__(self, field_names):
    self.field_names = field_names

  def indexFromName(self, field_name):
    try:
      return self.field_names.index(field_name)
    except ValueError:
      return -1


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
    for field in fields:
      self.layer.field_names.append(field.name)
      self.added_fields.append(field)
    return True

  def changeAttributeValues(self, change_map):
    self.change_maps.append(change_map)
    for feature_id, field_values in change_map.items():
      feature = self.layer.feature_by_id[feature_id]
      for field_index, value in field_values.items():
        feature[field_index] = value
    return True


class _FakeFeature:
  def __init__(self, feature_id):
    self.feature_id = feature_id
    self.values = {}

  def id(self):
    return self.feature_id

  def __setitem__(self, key, value):
    self.values[key] = value


class _FakeLayer:
  def __init__(self, field_names=None, features=None):
    self.field_names = field_names or []
    self.features = features or []
    self.feature_by_id = {feature.id(): feature for feature in self.features}
    self.provider = _FakeProvider(self)
    self.updated_features = []

  def fields(self):
    return _FakeFields(self.field_names)

  def dataProvider(self):
    return self.provider

  def updateFields(self):
    return None

  def getFeatures(self):
    return self.features

  def updateFeature(self, feature):
    self.updated_features.append(feature)
    return True


@contextmanager
def _fake_edit(layer):
  yield


def _build_scrub_layer(layer):
  scrub_layer = ScrubLayer.__new__(ScrubLayer)
  scrub_layer.layer = layer
  scrub_layer.layer_name = 'buildings'
  return scrub_layer


class TestScrubLayerUuid(unittest.TestCase):
  def setUp(self):
    scrub_layer_module.QgsField = _FakeQgsField
    scrub_layer_module.QgsVectorDataProvider = _FakeQgsVectorDataProvider
    scrub_layer_module.QVariant = _FakeQVariant
    scrub_layer_module.edit = _fake_edit

  def test_add_uuid_field_adds_string_field_and_populates_features(self):
    features = [_FakeFeature(1), _FakeFeature(2)]
    layer = _FakeLayer(features=features)
    scrub_layer = _build_scrub_layer(layer)

    result = scrub_layer.add_uuid_field('uid')

    self.assertEqual(result, 'uid')
    self.assertEqual(layer.field_names, ['uid'])
    self.assertEqual(layer.provider.added_fields[0].length, 36)
    self.assertEqual(len(features[0].values[0]), 36)
    self.assertEqual(len(features[1].values[0]), 36)
    self.assertNotIn('{', features[0].values[0])
    self.assertNotIn('}', features[0].values[0])
    self.assertEqual(len(layer.provider.change_maps), 1)
    self.assertEqual(layer.updated_features, [])

  def test_add_uuid_field_rejects_existing_field_by_default(self):
    layer = _FakeLayer(field_names=['uid'])
    scrub_layer = _build_scrub_layer(layer)

    with self.assertRaises(ValueError):
      scrub_layer.add_uuid_field('uid')

  def test_add_uuid_field_can_overwrite_existing_field(self):
    feature = _FakeFeature(3)
    layer = _FakeLayer(field_names=['uid'], features=[feature])
    scrub_layer = _build_scrub_layer(layer)

    scrub_layer.add_uuid_field('uid', overwrite=True)

    self.assertEqual(len(feature.values[0]), 36)
    self.assertEqual(layer.provider.added_fields, [])

  def test_add_uuid_field_rejects_invalid_batch_size(self):
    layer = _FakeLayer(features=[_FakeFeature(1)])
    scrub_layer = _build_scrub_layer(layer)

    with self.assertRaises(ValueError):
      scrub_layer.add_uuid_field('uid', batch_size=0)


if __name__ == '__main__':
  unittest.main()
