"""
Sabu project
jug_gis_cities package
test_mtl_fsa_workflow module
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)


def _fake_create_output_folders(paths_dict, output_dir):
    for key in paths_dict:
        paths_dict[key] = os.path.join(output_dir, key, key + '.shp')


class _FakeScrubLayer:
    calls = []
    instances = []

    def __init__(self, qgis_path, layer_path, layer_name):
        self.qgis_path = qgis_path
        self.layer_path = layer_path
        self.layer_name = layer_name
        self.data_count = 1 if layer_name.startswith('fsa_boundary_') else 7
        self.calls.append(('init', qgis_path, layer_path, layer_name))
        self.instances.append(self)

    def extract_by_attribute(self, field_name, operator, value, output_path):
        self.calls.append((
            'extract_by_attribute',
            self.layer_name,
            field_name,
            operator,
            value,
            output_path))
        return output_path

    def extract_by_expression(self, expression, output_path):
        self.calls.append((
            'extract_by_expression',
            self.layer_name,
            expression,
            output_path))
        return output_path

    def add_uuid_field(self, field_name='uuid', field_length=36,
                       overwrite=False):
        self.calls.append((
            'add_uuid_field',
            self.layer_name,
            field_name,
            field_length,
            overwrite))
        return field_name

    def clip_layer(self, overlay_layer, clipped_layer):
        self.calls.append((
            'clip_layer',
            self.layer_name,
            overlay_layer,
            clipped_layer))

    def fix_geometries(self, output_path):
        self.calls.append((
            'fix_geometries',
            self.layer_name,
            output_path))
        return output_path

    def extract_by_aggregate_membership(
            self, lookup_layer, lookup_field, target_field, output_path,
            aggregate='array_agg', include_matches=True):
        self.calls.append((
            'extract_by_aggregate_membership',
            self.layer_name,
            lookup_layer.layer_name,
            lookup_field,
            target_field,
            output_path,
            aggregate,
            include_matches))
        return output_path

    def difference_layer(self, overlay_layer, output_path, grid_size=None):
        self.calls.append((
            'difference_layer',
            self.layer_name,
            overlay_layer.layer_name,
            output_path,
            grid_size))
        return output_path

    def spatial_join_with_predicate(
            self, joining_layer_path, joined_layer_path,
            predicate='intersect', join_method='one-to-many', prefix=''):
        self.calls.append((
            'spatial_join_with_predicate',
            self.layer_name,
            joining_layer_path,
            joined_layer_path,
            predicate,
            join_method,
            prefix))
        return joined_layer_path

    def extract_unique_by_field(
            self, field_name, output_path, include_null=False):
        self.calls.append((
            'extract_unique_by_field',
            self.layer_name,
            field_name,
            output_path,
            include_null))
        return output_path

    def duplicate_text_field(
            self, source_field, target_field, field_length,
            overwrite=False, batch_size=10000):
        self.calls.append((
            'duplicate_text_field',
            self.layer_name,
            source_field,
            target_field,
            field_length,
            overwrite,
            batch_size))
        return target_field

    def add_layer_join(
            self, joining_layer_path, joining_layer_name, join_field,
            target_field, prefix='', output_path=None, join_fields=None):
        self.calls.append((
            'add_layer_join',
            self.layer_name,
            joining_layer_path,
            joining_layer_name,
            join_field,
            target_field,
            prefix,
            output_path,
            join_fields))
        return output_path

    def add_field(self, new_field_name):
        self.calls.append((
            'add_field',
            self.layer_name,
            new_field_name))
        return new_field_name

    def assign_area(self, field_name):
        self.calls.append((
            'assign_area',
            self.layer_name,
            field_name))
        return field_name

    def create_spatial_index(self):
        self.calls.append(('create_spatial_index', self.layer_name))

    def __str__(self):
        return f'The {self.layer_name} has {self.data_count} records.'


def _import_mtl_fsa_workflow(data_dir, output_dir):
    fake_citygisoo = types.ModuleType('citygisoo')
    fake_basic_functions = types.SimpleNamespace(
        create_output_folders=_fake_create_output_folders)
    fake_scrub_layer_module = types.ModuleType('citygisoo.scrub_layer_class')
    fake_scrub_layer_module.ScrubLayer = _FakeScrubLayer
    fake_citygisoo.basic_functions = fake_basic_functions

    module_names = [
        'src.jug_gis_cities.mtl_fsa_gisoo.workflow',
        'src.jug_gis_cities.mtl_fsa_gisoo.workflow_config',
    ]
    with patch.dict(
            os.environ,
            {
                'JUG_GIS_CITIES_MTL_FSA_DATA_DIR': data_dir,
                'JUG_GIS_CITIES_MTL_FSA_OUTPUT_DIR': output_dir,
                'JUG_GIS_CITIES_QGIS_PATH': 'C:/QGIS',
            }):
        with patch.dict(
                sys.modules,
                {
                    'citygisoo': fake_citygisoo,
                    'citygisoo.scrub_layer_class': fake_scrub_layer_module,
                }):
            for module_name in module_names:
                sys.modules.pop(module_name, None)
            return importlib.import_module(module_names[0])


class TestMtlFsaWorkflow(unittest.TestCase):
    def setUp(self):
        _FakeScrubLayer.calls = []
        _FakeScrubLayer.instances = []

    def test_run_workflow_extracts_fsa_boundary_and_clips_input_layers(self):
        workflow = _import_mtl_fsa_workflow(
            data_dir='D:/GIS/mtl_gisoo_fsa_data',
            output_dir='D:/GIS/mtl_gisoo_fsa_data/output_data')

        workflow.run_workflow('h3h')

        fsa_boundary_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'fsa_boundary',
            'fsa_boundary.shp')
        nrcan_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'nrcan',
            'nrcan.shp')
        roll_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'roll',
            'roll.shp')
        usage_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage',
            'usage.shp')
        nrcan_fixed_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'nrcan_fixed',
            'nrcan_fixed.shp')
        usage_fixed_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_fixed',
            'usage_fixed.shp')
        usage_margin_san_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_margin_san',
            'usage_margin_san.shp')
        usage_san_san_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_san_san',
            'usage_san_san.shp')
        usage_margin_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_margin',
            'usage_margin.shp')
        usage_only_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_only',
            'usage_only.shp')
        roll_only_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'roll_only',
            'roll_only.shp')
        usage_roll_only_all_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_roll_only_all',
            'usage_roll_only_all.shp')
        usage_roll_only_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_roll_only',
            'usage_roll_only.shp')
        usage_roll_only_unique_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_roll_only_unique',
            'usage_roll_only_unique.shp')
        roll_clean_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'roll_clean',
            'roll_clean.shp')
        usage_roll_path = os.path.join(
            'D:/GIS/mtl_gisoo_fsa_data/output_data',
            'H3H',
            'usage_roll',
            'usage_roll.shp')

        self.assertIn(
            (
                'extract_by_attribute',
                'fsa_boundaries',
                'g_fsa',
                '=',
                'H3H',
                fsa_boundary_path,
            ),
            _FakeScrubLayer.calls)
        for layer_name, id_field_name in [
                ('roll_mtl', 'roll_id'),
                ('nrcan_mtl', 'nrcan_id'),
                ('usage_mtl', 'usage_id')]:
            self.assertIn(
                (
                    'add_uuid_field',
                    layer_name,
                    id_field_name,
                    36,
                    True,
                ),
                _FakeScrubLayer.calls)

        extract_call_index = _FakeScrubLayer.calls.index((
            'extract_by_attribute',
            'fsa_boundaries',
            'g_fsa',
            '=',
            'H3H',
            fsa_boundary_path,
        ))
        for layer_name, id_field_name in [
                ('roll_mtl', 'roll_id'),
                ('nrcan_mtl', 'nrcan_id'),
                ('usage_mtl', 'usage_id')]:
            uuid_call_index = _FakeScrubLayer.calls.index((
                'add_uuid_field',
                layer_name,
                id_field_name,
                36,
                True,
            ))
            self.assertLess(uuid_call_index, extract_call_index)

        for layer_name, output_path in [
                ('nrcan_mtl', nrcan_path),
                ('roll_mtl', roll_path),
                ('usage_mtl', usage_path)]:
            self.assertIn(
                (
                    'clip_layer',
                    layer_name,
                    fsa_boundary_path,
                    output_path,
                ),
                _FakeScrubLayer.calls)

        for layer_name, output_path in [
                ('nrcan_clipped_H3H', nrcan_fixed_path),
                ('usage_clipped_H3H', usage_fixed_path)]:
            self.assertIn(
                (
                    'fix_geometries',
                    layer_name,
                    output_path,
                ),
                _FakeScrubLayer.calls)

        self.assertIn(
            (
                'extract_by_aggregate_membership',
                'usage_fixed_H3H',
                'roll_clipped_H3H',
                'id_provinc',
                'g_id_provi',
                usage_margin_san_path,
                'array_agg',
                False,
            ),
            _FakeScrubLayer.calls)

        self.assertIn(
            (
                'difference_layer',
                'usage_clipped_H3H',
                'usage_margin_san_H3H',
                usage_san_san_path,
                None,
            ),
            _FakeScrubLayer.calls)

        self.assertIn(
            (
                'extract_by_expression',
                'usage_margin_san_H3H',
                '"g_id_provi" != \'Sans correspondance\'',
                usage_margin_path,
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'add_field',
                'usage_margin_H3H',
                'area_ex',
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'assign_area',
                'usage_margin_H3H',
                'area_ex',
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'extract_by_expression',
                'usage_margin_H3H',
                '"area_ex" > 0.9 * "g_sup_tota"',
                usage_only_path,
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'extract_by_aggregate_membership',
                'roll_clipped_H3H',
                'usage_clipped_H3H',
                'g_id_provi',
                'id_provinc',
                roll_only_path,
                'array_agg',
                False,
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'spatial_join_with_predicate',
                'usage_clipped_H3H',
                roll_only_path,
                usage_roll_only_all_path,
                'contains',
                'one-to-many',
                'ro_',
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'extract_by_expression',
                'usage_roll_only_all_H3H',
                '"ro_roll_id" IS NOT NULL',
                usage_roll_only_path,
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'extract_unique_by_field',
                'usage_roll_only_H3H',
                'ro_id_provinc',
                usage_roll_only_unique_path,
                False,
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'difference_layer',
                'roll_clipped_H3H',
                'roll_only_H3H',
                roll_clean_path,
                None,
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'duplicate_text_field',
                'roll_clean_H3H',
                'id_provinc',
                'r_id_provinc',
                36,
                False,
                10000,
            ),
            _FakeScrubLayer.calls)
        self.assertIn(
            (
                'add_layer_join',
                'usage_margin_san_H3H',
                roll_clean_path,
                'roll_clean_H3H',
                'r_id_provinc',
                'g_id_provi',
                'r_',
                usage_roll_path,
                None,
            ),
            _FakeScrubLayer.calls)

        for output_path, layer_name in [
                (fsa_boundary_path, 'fsa_boundary_H3H'),
                (nrcan_path, 'nrcan_clipped_H3H'),
                (roll_path, 'roll_clipped_H3H'),
                (usage_path, 'usage_clipped_H3H'),
                (nrcan_fixed_path, 'nrcan_fixed_H3H'),
                (usage_fixed_path, 'usage_fixed_H3H'),
                (usage_margin_san_path, 'usage_margin_san_H3H'),
                (usage_san_san_path, 'usage_san_san_H3H'),
                (usage_margin_path, 'usage_margin_H3H'),
                (usage_only_path, 'usage_only_H3H'),
                (roll_only_path, 'roll_only_H3H'),
                (usage_roll_only_all_path, 'usage_roll_only_all_H3H'),
                (usage_roll_only_path, 'usage_roll_only_H3H'),
                (usage_roll_only_unique_path,
                 'usage_roll_only_unique_H3H'),
                (roll_clean_path, 'roll_clean_H3H'),
                (usage_roll_path, 'usage_roll_H3H')]:
            self.assertIn(
                ('init', 'C:/QGIS', output_path, layer_name),
                _FakeScrubLayer.calls)
            self.assertIn(
                ('create_spatial_index', layer_name),
                _FakeScrubLayer.calls)


if __name__ == '__main__':
    unittest.main()
