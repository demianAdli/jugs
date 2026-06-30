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
from unittest.mock import Mock, patch


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


class TestScrubLayerExtraction(unittest.TestCase):
  def setUp(self):
    scrub_layer_module.QgsApplication = _FakeQgsApplication

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

  def test_extract_by_attribute_rejects_unknown_operator(self):
    with self.assertRaises(ValueError):
      ScrubLayer._normalize_extract_attribute_operator('near')


if __name__ == '__main__':
  unittest.main()
