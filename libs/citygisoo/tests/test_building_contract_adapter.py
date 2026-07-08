"""
CityGISOO
test_building_contract_adapter module
Project Developer: Alireza Adli
alireza.adli@concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, call, patch


_REPO_ROOT = os.path.abspath(
  os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
  sys.path.insert(0, _SABU_CHASSIS_SRC)


class _Dummy:
  Int = 2
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

  sys.modules.setdefault('processing', types.ModuleType('processing'))
  sys.modules.setdefault('qgis', qgis_module)
  sys.modules.setdefault('qgis.core', qgis_core_module)
  sys.modules.setdefault('qgis.analysis', qgis_analysis_module)
  sys.modules.setdefault('qgis.PyQt', qgis_pyqt_module)
  sys.modules.setdefault('qgis.PyQt.QtCore', qgis_qtcore_module)


_install_qgis_stubs()

from src.citygisoo.building_contract_adapter import BuildingContractAdapter


class TestBuildingContractAdapter(unittest.TestCase):
  def test_default_required_fields_and_source_path(self):
    adapter = BuildingContractAdapter(
      qgis_path='C:/QGIS',
      input_layer_path='input.shp',
      input_layer_name='input_layer',
      output_geojson_path='output/standardized.geojson',
      field_rename_map={'old_name': 'name', 'old_height': 'height'})

    self.assertEqual(adapter.required_fields, ['name', 'height'])
    self.assertEqual(
      adapter.source_geojson_path,
      os.path.join('output', 'standardized_source.geojson'))
    self.assertEqual(adapter.source_required_fields,
                     ['old_name', 'old_height'])
    self.assertEqual(adapter.output_layer_name, 'standardized')
    self.assertIsNone(adapter.field_order)

  def test_rejects_invalid_output_geojson_path(self):
    with self.assertRaises(ValueError):
      BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path='input.shp',
        input_layer_name='input_layer',
        output_geojson_path='output/standardized.shp',
        field_rename_map={'old_name': 'name'})

  def test_rejects_empty_required_fields(self):
    with self.assertRaises(ValueError):
      BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path='input.shp',
        input_layer_name='input_layer',
        output_geojson_path='output/standardized.geojson',
        field_rename_map={'old_name': 'name'},
        required_fields=[])

  def test_run_requires_existing_input_layer_before_loading(self):
    adapter = BuildingContractAdapter(
      qgis_path='C:/QGIS',
      input_layer_path='missing_input.shp',
      input_layer_name='input_layer',
      output_geojson_path='output/standardized.geojson',
      field_rename_map={'old_name': 'name'})

    with patch(
        'src.citygisoo.building_contract_adapter.FieldSchemaManager'
    ) as manager_cls_mock:
      with self.assertRaises(FileNotFoundError):
        adapter.run()

    manager_cls_mock.assert_not_called()

  @patch('src.citygisoo.building_contract_adapter.FieldSchemaManager')
  def test_run_orchestrates_contract_standardization(self, manager_cls_mock):
    with tempfile.TemporaryDirectory() as tmp_dir:
      input_layer_path = os.path.join(tmp_dir, 'input.shp')
      with open(input_layer_path, 'w', encoding='utf-8') as input_layer_file:
        input_layer_file.write('')

      output_geojson_path = os.path.join(
        tmp_dir, 'standardized', 'buildings.geojson')
      source_geojson_path = os.path.join(
        tmp_dir, 'standardized', 'buildings_source.geojson')

      input_manager = Mock()
      input_manager.layer.isValid.return_value = True
      input_manager.find_missing_fields.return_value = []
      input_manager.export_to_geojson.return_value = source_geojson_path

      source_manager = Mock()
      source_manager.layer.isValid.return_value = True
      source_manager.find_missing_fields.return_value = []
      standardized_scrub_layer = Mock()
      source_manager.standardize_fields.return_value = standardized_scrub_layer

      standardized_manager = Mock()
      standardized_manager.find_missing_fields.return_value = []
      standardized_manager.find_null_feature_ids.return_value = []
      standardized_manager.layer.featureCount.return_value = 3

      manager_cls_mock.side_effect = [
        input_manager,
        source_manager,
        standardized_manager,
      ]

      adapter = BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path=input_layer_path,
        input_layer_name='input_layer',
        output_geojson_path=output_geojson_path,
        field_rename_map={'raw_name': 'name', 'raw_height': 'height'},
        required_fields=['name', 'height'],
        id_field_name='id',
        id_start_value=100,
        output_layer_name='standardized_buildings',
        field_order=['height', 'name'])

      result = adapter.run()

    self.assertEqual(result, output_geojson_path)
    manager_cls_mock.assert_has_calls([
      call(
        qgis_path='C:/QGIS',
        layer_path=input_layer_path,
        layer_name='input_layer'),
      call(
        qgis_path='C:/QGIS',
        layer_path=source_geojson_path,
        layer_name='buildings_source'),
      call(standardized_scrub_layer),
    ])
    input_manager.find_missing_fields.assert_called_once_with(
      ['raw_name', 'raw_height'])
    input_manager.export_to_geojson.assert_called_once_with(
      source_geojson_path)
    source_manager.standardize_fields.assert_called_once_with(
      field_rename_map={'raw_name': 'name', 'raw_height': 'height'},
      fields_to_keep=['name', 'height'],
      field_order=['height', 'name'],
      output_path=output_geojson_path,
      output_layer_name='standardized_buildings')
    standardized_manager.drop_null_features.assert_called_once_with(
      ['name', 'height'])
    standardized_manager.add_id_field.assert_called_once()
    id_values = standardized_manager.add_id_field.call_args.kwargs[
      'id_values']
    self.assertEqual(list(id_values), [100, 101, 102])
    standardized_manager.promote_feature_id.assert_called_once_with('id')


if __name__ == '__main__':
  unittest.main()
