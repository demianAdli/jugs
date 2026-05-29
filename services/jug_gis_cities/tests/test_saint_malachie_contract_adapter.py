"""
Sabu project
jug_gis_cities package
test_saint_malachie_contract_adapter module
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)


def _import_contract_adapter(adapter_cls, output_dir, qgis_path):
    fake_citygisoo = types.ModuleType('citygisoo')
    fake_citygisoo.BuildingContractAdapter = adapter_cls
    module_names = [
        'src.jug_gis_cities.saint_malachie_gisoo.contract_adapter',
        'src.jug_gis_cities.saint_malachie_gisoo.workflow_config',
    ]
    with patch.dict(
            os.environ,
            {
                'JUG_GIS_CITIES_SAINT_MALACHIE_OUTPUT_DIR': output_dir,
                'JUG_GIS_CITIES_QGIS_PATH': qgis_path,
            }):
        with patch.dict(sys.modules, {'citygisoo': fake_citygisoo}):
            for module_name in module_names:
                sys.modules.pop(module_name, None)
            return importlib.import_module(module_names[0])


class TestSaintMalachieContractAdapter(unittest.TestCase):
    def test_run_contract_adapter_uses_saint_malachie_finalize_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter_cls_mock = Mock()
            adapter_cls_mock.return_value.run.return_value = (
                'standardized_output.geojson')
            contract_adapter = _import_contract_adapter(
                adapter_cls=adapter_cls_mock,
                output_dir=tmp_dir,
                qgis_path='C:/QGIS')

            result = contract_adapter.run_contract_adapter()

        self.assertEqual(result, 'standardized_output.geojson')
        expected_workflow_output_path = os.path.join(
            tmp_dir,
            'saint_malachie_gisoo_with_fsa',
            'saint_malachie_gisoo_with_fsa.shp')
        expected_output_path = os.path.join(
            tmp_dir,
            'saint_malachie_standardized',
            'saint_malachie_standardized.geojson')
        expected_source_path = os.path.join(
            tmp_dir,
            'saint_malachie_standardized',
            'saint_malachie_contract_source.geojson')

        adapter_cls_mock.assert_called_once_with(
            qgis_path='C:/QGIS',
            input_layer_path=expected_workflow_output_path,
            input_layer_name='saint_malachie_gisoo_with_fsa',
            output_geojson_path=expected_output_path,
            field_rename_map={
                'g_id_provi': 'name',
                'heightmax': 'height',
                'g_utilisat': 'function',
                'rl_ad_ad_1': 'address',
                'rl_uerl0_6': 'year_of_construction',
            },
            required_fields=[
                'name',
                'height',
                'function',
                'address',
                'year_of_construction',
            ],
            id_field_name='id',
            id_start_value=100000,
            source_geojson_path=expected_source_path,
            source_geojson_layer_name='saint_malachie_contract_source',
            output_layer_name='standardized_saint_malachie')
        adapter_cls_mock.return_value.run.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
