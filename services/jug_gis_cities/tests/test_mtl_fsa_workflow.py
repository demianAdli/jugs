"""
Sabu project
jug_gis_cities package
test_mtl_fsa_workflow module
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
"""
import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


_REPO_ROOT = os.path.abspath(
  os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
_JUG_GIS_CITIES_SRC = os.path.join(_REPO_ROOT, 'services', 'jug_gis_cities')
for _path in [_SABU_CHASSIS_SRC, _JUG_GIS_CITIES_SRC]:
  if _path not in sys.path:
    sys.path.insert(0, _path)


class _FakeGeoPackageFeatureProcessor:
  calls = []

  def add_area_field(self, layer, field_name, overwrite=False,
                     batch_size=10000):
    self.calls.append((
      'add_area_field',
      layer.layer_name,
      field_name,
      overwrite,
      batch_size))
    return field_name

  def extract_by_membership(
          self,
          source_layer,
          lookup_layer,
          source_field,
          lookup_field,
          output_path,
          include_matches=True,
          layer_name=None):
    self.calls.append((
      'extract_by_membership',
      source_layer.layer_name,
      lookup_layer.layer_name,
      source_field,
      lookup_field,
      output_path,
      include_matches,
      layer_name))
    return output_path


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

  def add_uuid_field(self, field_name='uuid', field_length=36,
                     overwrite=False):
    self.calls.append((
      'add_uuid_field',
      self.layer_name,
      field_name,
      field_length,
      overwrite))
    return field_name

  def duplicate_layer(self, output_path):
    self.calls.append(('duplicate_layer', self.layer_name, output_path))
    return output_path

  def clip_layer(self, overlay_layer, clipped_layer):
    self.calls.append((
      'clip_layer',
      self.layer_name,
      overlay_layer,
      clipped_layer))
    return clipped_layer

  def fix_geometries(self, output_path):
    self.calls.append(('fix_geometries', self.layer_name, output_path))
    return output_path

  def add_field(self, new_field_name):
    self.calls.append(('add_field', self.layer_name, new_field_name))
    return new_field_name

  def assign_area(self, field_name):
    self.calls.append(('assign_area', self.layer_name, field_name))
    return field_name

  def difference_layer(self, overlay_layer, output_path, grid_size=None):
    self.calls.append((
      'difference_layer',
      self.layer_name,
      overlay_layer.layer_name,
      output_path,
      grid_size))
    return output_path

  def create_spatial_index(self):
    self.calls.append(('create_spatial_index', self.layer_name))

  def __str__(self):
    return f'The {self.layer_name} has {self.data_count} records.'


def _import_mtl_fsa_workflow(data_dir, output_dir):
  fake_citygisoo = types.ModuleType('citygisoo')
  fake_scrub_layer_module = types.ModuleType('citygisoo.scrub_layer_class')
  fake_scrub_layer_module.ScrubLayer = _FakeScrubLayer
  fake_citygisoo.GeoPackageFeatureProcessor = _FakeGeoPackageFeatureProcessor

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
    _FakeGeoPackageFeatureProcessor.calls = []
    _FakeScrubLayer.calls = []
    _FakeScrubLayer.instances = []

  def test_run_workflow_stops_after_difference_usage_with_margin_san(self):
    with tempfile.TemporaryDirectory() as temp_dir:
      data_dir = os.path.join(temp_dir, 'data')
      output_dir = os.path.join(temp_dir, 'output')
      workflow = _import_mtl_fsa_workflow(data_dir, output_dir)

      result = workflow.run_workflow('h3h')

    def _output_path(output_key):
      return os.path.join(
        output_dir,
        'H3H',
        output_key,
        f'{output_key}.gpkg')

    fsa_boundary_path = _output_path('fsa_boundary')
    nrcan_preserved_path = _output_path('nrcan_preserved')
    usage_dup_path = _output_path('usage_dup')
    nrcan_path = _output_path('nrcan')
    roll_path = _output_path('roll')
    usage_path = _output_path('usage')
    nrcan_fixed_path = _output_path('nrcan_fixed')
    nrcan_preserved_fixed_path = _output_path('nrcan_preserved_fixed')
    usage_fixed_path = _output_path('usage_fixed')
    usage_dup_fixed_path = _output_path('usage_dup_fixed')
    usage_margin_san_path = _output_path('usage_margin_san')
    usage_san_san_path = _output_path('usage_san_san')

    self.assertEqual(result, usage_san_san_path)
    self.assertNotIn(
      'add_uuid_field',
      [call[0] for call in _FakeScrubLayer.calls])
    self.assertNotIn(
      'duplicate_layer',
      [call[0] for call in _FakeScrubLayer.calls])

    self.assertIn(
      (
        'init',
        'C:/QGIS',
        os.path.join(
          data_dir,
          'input_data',
          'mamh_usage_predo_2026_gpkg',
          'mamh_usage_predo_2026_s_poly.gpkg'),
        'usage_mtl',
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'init',
        'C:/QGIS',
        os.path.join(
          data_dir,
          'input_data',
          'mtl_auto_with_heights_preserved',
          'mtl_auto_with_heights_preserved.gpkg'),
        'nrcan_preserved_mtl',
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'init',
        'C:/QGIS',
        os.path.join(
          data_dir,
          'input_data',
          'mamh_usage_predo_2026_gpkg_dup',
          'mamh_usage_predo_2026_dup.gpkg'),
        'usage_dup_mtl',
      ),
      _FakeScrubLayer.calls)
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

    for layer_name, output_path in [
            ('nrcan_mtl', nrcan_path),
            ('nrcan_preserved_mtl', nrcan_preserved_path),
            ('roll_mtl', roll_path),
            ('usage_mtl', usage_path),
            ('usage_dup_mtl', usage_dup_path)]:
      self.assertIn(
        (
          'clip_layer',
          layer_name,
          fsa_boundary_path,
          output_path,
        ),
        _FakeScrubLayer.calls)

    self.assertIn(
      (
        'fix_geometries',
        'nrcan_clipped_H3H',
        nrcan_fixed_path,
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'add_area_field',
        'nrcan_fixed_H3H',
        'nrcan_area',
        False,
        10000,
      ),
      _FakeGeoPackageFeatureProcessor.calls)
    self.assertIn(
      (
        'init',
        'C:/QGIS',
        nrcan_fixed_path,
        'nrcan_fixed_H3H',
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'fix_geometries',
        'nrcan_preserved_H3H',
        nrcan_preserved_fixed_path,
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'add_area_field',
        'nrcan_preserved_fixed_H3H',
        'nrcan_area',
        False,
        10000,
      ),
      _FakeGeoPackageFeatureProcessor.calls)
    self.assertIn(
      (
        'init',
        'C:/QGIS',
        nrcan_preserved_fixed_path,
        'nrcan_preserved_fixed_H3H',
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'fix_geometries',
        'usage_clipped_H3H',
        usage_fixed_path,
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'fix_geometries',
        'usage_dup_H3H',
        usage_dup_fixed_path,
      ),
      _FakeScrubLayer.calls)
    self.assertIn(
      (
        'extract_by_membership',
        'usage_fixed_H3H',
        'roll_clipped_H3H',
        'g_id_provi',
        'id_provinc',
        usage_margin_san_path,
        False,
        'usage_margin_san_H3H',
      ),
      _FakeGeoPackageFeatureProcessor.calls)
    self.assertIn(
      (
        'difference_layer',
        'usage_clipped_H3H',
        'usage_margin_san_H3H',
        usage_san_san_path,
        None,
      ),
      _FakeScrubLayer.calls)


if __name__ == '__main__':
  unittest.main()
