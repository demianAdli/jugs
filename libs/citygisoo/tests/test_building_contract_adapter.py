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
    'QgsDistanceArea',
    'QgsExpression',
    'QgsExpressionContext',
    'QgsExpressionContextUtils',
    'QgsFeatureRequest',
    'QgsFeature',
    'QgsField',
    'QgsProcessingFeedback',
    'QgsProcessingFeatureSourceDefinition',
    'QgsProject',
    'QgsVectorDataProvider',
    'QgsVectorFileWriter',
    'QgsVectorLayer',
    'QgsVectorLayerJoinInfo',
    'QgsWkbTypes',
    'edit',
  ]
  for name in qgis_core_names:
    setattr(qgis_core_module, name, _Dummy)
  qgis_core_module.NULL = None

  qgis_analysis_module.QgsNativeAlgorithms = _Dummy
  qgis_qtcore_module.QVariant = _Dummy

  processing_module = sys.modules.setdefault(
    'processing', types.ModuleType('processing'))
  if not hasattr(processing_module, 'run'):
    processing_module.run = Mock()
  sys.modules.setdefault('qgis', qgis_module)
  sys.modules.setdefault('qgis.core', qgis_core_module)
  sys.modules.setdefault('qgis.analysis', qgis_analysis_module)
  sys.modules.setdefault('qgis.PyQt', qgis_pyqt_module)
  sys.modules.setdefault('qgis.PyQt.QtCore', qgis_qtcore_module)


_install_qgis_stubs()

from src.citygisoo.building_contract_adapter import BuildingContractAdapter
from src.citygisoo.field_schema_manager import FieldSchemaManager


class _FakeField:
  def __init__(self, field_type=10, length=80, precision=0):
    self._type = field_type
    self._length = length
    self._precision = precision

  def type(self):
    return self._type

  def length(self):
    return self._length

  def precision(self):
    return self._precision


class _FakeFields:
  def __init__(self, names):
    self._fields = {name: _FakeField() for name in names}

  def field(self, name):
    return self._fields[name]


class _FakeLayer:
  def __init__(self, names):
    self._fields = _FakeFields(names)

  def fields(self):
    return self._fields


class TestFieldSchemaManagerRefactor(unittest.TestCase):
  @patch(
    'src.citygisoo.field_schema_manager.QgsApplication'
    '.processingRegistry',
    create=True)
  @patch('src.citygisoo.field_schema_manager.os.path.exists',
         return_value=True)
  @patch('src.citygisoo.field_schema_manager.processing.run', create=True)
  def test_output_standardization_refactors_and_exports_once(
      self, processing_run_mock, _exists_mock, registry_mock):
    manager = object.__new__(FieldSchemaManager)
    manager.scrub_layer = Mock(
      layer_name='source',
      layer_path='input/source.gpkg',
      layer=_FakeLayer(['raw_name', 'raw_height', 'unused']))
    manager._field_names = Mock(
      return_value=['raw_name', 'raw_height', 'unused'])
    manager._layer_name = Mock(return_value='source')
    standardized_layer = Mock(layer_name='standardized')
    manager._new_scrub_layer = Mock(return_value=standardized_layer)
    processing_run_mock.return_value = {
      'OUTPUT': 'standardized.geojson'}

    result = manager.standardize_fields(
      field_rename_map={
        'raw_name': 'name',
        'raw_height': 'height',
      },
      fields_to_keep=['name', 'height'],
      field_order=['height', 'name'],
      output_path='standardized.geojson',
      output_layer_name='standardized')

    self.assertIs(result, standardized_layer)
    processing_run_mock.assert_called_once()
    algorithm, params = processing_run_mock.call_args.args
    self.assertEqual(algorithm, 'native:refactorfields')
    self.assertIs(params['INPUT'], manager.layer)
    self.assertEqual(params['OUTPUT'], 'standardized.geojson')
    self.assertEqual(
      [(item['name'], item['expression'])
       for item in params['FIELDS_MAPPING']],
      [('height', '"raw_height"'), ('name', '"raw_name"')])
    registry_mock.return_value.addProvider.assert_called_once()

  def test_output_standardization_rejects_duplicate_targets(self):
    manager = object.__new__(FieldSchemaManager)
    manager.scrub_layer = Mock(
      layer_name='source',
      layer_path='input/source.gpkg',
      layer=_FakeLayer(['first', 'second']))
    manager._field_names = Mock(return_value=['first', 'second'])

    with self.assertRaisesRegex(ValueError, 'duplicate target'):
      manager.standardize_fields(
        field_rename_map={'first': 'name', 'second': 'name'},
        fields_to_keep=['name'],
        output_path='standardized.geojson')


class TestBuildingContractAdapter(unittest.TestCase):
  def test_default_required_fields_and_output_layer_name(self):
    adapter = BuildingContractAdapter(
      qgis_path='C:/QGIS',
      input_layer_path='input.shp',
      input_layer_name='input_layer',
      output_geojson_path='output/standardized.geojson',
      field_rename_map={'old_name': 'name', 'old_height': 'height'})

    self.assertEqual(adapter.required_fields, ['name', 'height'])
    self.assertEqual(adapter.source_required_fields,
                     ['old_name', 'old_height'])
    self.assertEqual(adapter.output_layer_name, 'standardized')
    self.assertIsNone(adapter.field_order)
    self.assertIsNone(adapter.non_null_required_fields)

  def test_rejects_invalid_output_geojson_path(self):
    with self.assertRaises(ValueError):
      BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path='input.shp',
        input_layer_name='input_layer',
        output_geojson_path='output/standardized.shp',
        field_rename_map={'old_name': 'name'})

  def test_rejects_invalid_output_geopackage_path(self):
    with self.assertRaises(ValueError):
      BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path='input.shp',
        input_layer_name='input_layer',
        output_geojson_path='output/standardized.geojson',
        field_rename_map={'old_name': 'name'},
        output_geopackage_path='output/standardized.shp')

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
      input_manager = Mock()
      input_manager.layer.isValid.return_value = True
      input_manager.find_missing_fields.return_value = []
      standardized_scrub_layer = Mock()
      input_manager.standardize_fields.return_value = standardized_scrub_layer

      standardized_manager = Mock()
      standardized_manager.find_missing_fields.return_value = []
      standardized_manager.find_null_feature_ids.return_value = []
      standardized_manager.layer.featureCount.return_value = 3

      manager_cls_mock.side_effect = [
        input_manager,
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
      call(standardized_scrub_layer),
    ])
    self.assertEqual(
      input_manager.find_missing_fields.call_args_list,
      [call(['raw_name', 'raw_height']),
       call(['raw_name', 'raw_height'])])
    input_manager.standardize_fields.assert_called_once_with(
      field_rename_map={'raw_name': 'name', 'raw_height': 'height'},
      fields_to_keep=['name', 'height'],
      field_order=['height', 'name'],
      output_path=output_geojson_path,
      output_layer_name='standardized_buildings')
    input_manager.export_to_geojson.assert_not_called()
    standardized_manager.drop_null_features.assert_not_called()
    standardized_manager.find_null_feature_ids.assert_not_called()
    standardized_manager.add_id_field.assert_called_once()
    id_values = standardized_manager.add_id_field.call_args.kwargs[
      'id_values']
    self.assertEqual(list(id_values), [100, 101, 102])
    standardized_manager.promote_feature_id.assert_called_once_with('id')

  @patch('src.citygisoo.building_contract_adapter.FieldSchemaManager')
  def test_run_drops_null_features_when_explicitly_configured(
          self,
          manager_cls_mock):
    with tempfile.TemporaryDirectory() as tmp_dir:
      input_layer_path = os.path.join(tmp_dir, 'input.shp')
      with open(input_layer_path, 'w', encoding='utf-8') as input_layer_file:
        input_layer_file.write('')

      output_geojson_path = os.path.join(
        tmp_dir, 'standardized', 'buildings.geojson')
      input_manager = Mock()
      input_manager.layer.isValid.return_value = True
      input_manager.find_missing_fields.return_value = []
      standardized_scrub_layer = Mock()
      input_manager.standardize_fields.return_value = standardized_scrub_layer

      standardized_manager = Mock()
      standardized_manager.find_missing_fields.return_value = []
      standardized_manager.find_null_feature_ids.return_value = []
      standardized_manager.layer.featureCount.return_value = 2

      manager_cls_mock.side_effect = [
        input_manager,
        standardized_manager,
      ]

      adapter = BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path=input_layer_path,
        input_layer_name='input_layer',
        output_geojson_path=output_geojson_path,
        field_rename_map={'raw_name': 'name', 'raw_height': 'height'},
        required_fields=['name', 'height'],
        non_null_required_fields=['name'])

      adapter.run()

    standardized_manager.drop_null_features.assert_called_once_with(['name'])
    standardized_manager.find_null_feature_ids.assert_called_once_with(
      ['name'])

  @patch('src.citygisoo.building_contract_adapter.FieldSchemaManager')
  def test_run_creates_geopackage_then_exports_geojson(
          self,
          manager_cls_mock):
    with tempfile.TemporaryDirectory() as tmp_dir:
      input_layer_path = os.path.join(tmp_dir, 'input.gpkg')
      with open(input_layer_path, 'w', encoding='utf-8') as input_layer_file:
        input_layer_file.write('')

      output_geojson_path = os.path.join(
        tmp_dir, 'standardized', 'buildings.geojson')
      output_geopackage_path = os.path.join(
        tmp_dir, 'standardized', 'buildings.gpkg')
      input_manager = Mock()
      input_manager.layer.isValid.return_value = True
      input_manager.find_missing_fields.return_value = []
      standardized_scrub_layer = Mock()
      input_manager.standardize_fields.return_value = standardized_scrub_layer

      geopackage_manager = Mock()
      geopackage_manager.find_missing_fields.return_value = []
      geopackage_manager.layer.featureCount.return_value = 2
      geojson_manager = Mock()
      geojson_manager.layer.isValid.return_value = True
      manager_cls_mock.side_effect = [
        input_manager,
        geopackage_manager,
        geojson_manager,
      ]

      adapter = BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path=input_layer_path,
        input_layer_name='input_layer',
        output_geojson_path=output_geojson_path,
        output_geopackage_path=output_geopackage_path,
        field_rename_map={'raw_name': 'name'},
        required_fields=['name'],
        id_start_value=100)

      result = adapter.run()

    self.assertEqual(result, output_geojson_path)
    input_manager.standardize_fields.assert_called_once_with(
      field_rename_map={'raw_name': 'name'},
      fields_to_keep=['name'],
      field_order=None,
      output_path=output_geopackage_path,
      output_layer_name='buildings')
    geopackage_manager.add_id_field.assert_called_once()
    id_values = geopackage_manager.add_id_field.call_args.kwargs['id_values']
    self.assertEqual(list(id_values), [100, 101])
    geopackage_manager.scrub_layer.create_spatial_index.assert_called_once_with()
    geopackage_manager.export_to_geojson.assert_called_once_with(
      output_geojson_path)
    geojson_manager.promote_feature_id.assert_called_once_with('id')
    geopackage_manager.promote_feature_id.assert_not_called()

  def test_rejects_non_null_fields_outside_required_fields(self):
    with self.assertRaisesRegex(ValueError, 'outside required_fields'):
      BuildingContractAdapter(
        qgis_path='C:/QGIS',
        input_layer_path='input.shp',
        input_layer_name='input_layer',
        output_geojson_path='output/standardized.geojson',
        field_rename_map={'old_name': 'name'},
        required_fields=['name'],
        non_null_required_fields=['height'])


if __name__ == '__main__':
  unittest.main()
