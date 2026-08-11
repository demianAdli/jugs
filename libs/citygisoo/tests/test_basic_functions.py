"""Tests for CityGISOO basic functions."""

import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


_REPO_ROOT = os.path.abspath(
  os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
  sys.path.insert(0, _SABU_CHASSIS_SRC)


def _load_basic_functions_module():
  module_names = ('processing', 'qgis', 'qgis.core', 'qgis.analysis')
  missing = object()
  previous_modules = {
    name: sys.modules.get(name, missing) for name in module_names
  }

  processing_module = types.ModuleType('processing')
  qgis_module = types.ModuleType('qgis')
  qgis_core_module = types.ModuleType('qgis.core')
  qgis_analysis_module = types.ModuleType('qgis.analysis')

  qgis_core_module.QgsApplication = object
  qgis_analysis_module.QgsNativeAlgorithms = object

  sys.modules['processing'] = processing_module
  sys.modules['qgis'] = qgis_module
  sys.modules['qgis.core'] = qgis_core_module
  sys.modules['qgis.analysis'] = qgis_analysis_module

  module_path = (
    Path(__file__).parent.parent
    / 'src'
    / 'citygisoo'
    / 'basic_functions.py')
  spec = importlib.util.spec_from_file_location(
    'citygisoo_basic_functions_under_test',
    module_path)
  module = importlib.util.module_from_spec(spec)
  try:
    spec.loader.exec_module(module)
  finally:
    for name, previous_module in previous_modules.items():
      if previous_module is missing:
        sys.modules.pop(name, None)
      else:
        sys.modules[name] = previous_module
  return module


basic_functions = _load_basic_functions_module()
gather_district_geojson_files = (
  basic_functions.gather_district_geojson_files)


def _create_standardized_geojson(
        root: Path,
        district_name: str,
        subdistrict_name: str,
        content: str) -> Path:
  standardized_name = (
    f'{district_name}_{subdistrict_name}_gisoo_standardized')
  source_directory = root / subdistrict_name / standardized_name
  source_directory.mkdir(parents=True)
  source_file = source_directory / f'{standardized_name}.geojson'
  source_file.write_text(content, encoding='utf-8')
  return source_file


class TestGatherDistrictGeojsonFiles(unittest.TestCase):
  def test_gathers_files_using_names_discovered_from_subdirectories(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      root = Path(temporary_directory) / 'results'
      output = Path(temporary_directory) / 'district_geojson'
      root.mkdir()
      _create_standardized_geojson(root, 'mtl', 'alpha', '{"id": 1}')
      _create_standardized_geojson(root, 'mtl', 'beta', '{"id": 2}')

      result = gather_district_geojson_files(root, 'mtl', output)

      self.assertIsNone(result)
      self.assertEqual(
        sorted(path.name for path in output.iterdir()),
        [
          'mtl_alpha_gisoo_standardized.geojson',
          'mtl_beta_gisoo_standardized.geojson',
        ])
      self.assertEqual(
        (output / 'mtl_alpha_gisoo_standardized.geojson').read_text(
          encoding='utf-8'),
        '{"id": 1}')

  def test_validates_all_sources_before_creating_output(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      root = Path(temporary_directory) / 'results'
      output = Path(temporary_directory) / 'district_geojson'
      root.mkdir()
      _create_standardized_geojson(root, 'mtl', 'alpha', '{"id": 1}')
      (root / 'beta').mkdir()

      with self.assertRaises(FileNotFoundError) as context:
        gather_district_geojson_files(root, 'mtl', output)

      self.assertIn(
        'mtl_beta_gisoo_standardized.geojson',
        str(context.exception))
      self.assertFalse(output.exists())

  def test_existing_output_inside_input_is_excluded_and_files_are_updated(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      root = Path(temporary_directory) / 'results'
      output = root / 'gathered_geojson'
      root.mkdir()
      source_file = _create_standardized_geojson(
        root,
        'quebec',
        'centre',
        '{"version": 1}')

      gather_district_geojson_files(root, 'quebec', output)
      source_file.write_text('{"version": 2}', encoding='utf-8')
      gather_district_geojson_files(root, 'quebec', output)

      copied_file = output / 'quebec_centre_gisoo_standardized.geojson'
      self.assertEqual(
        copied_file.read_text(encoding='utf-8'),
        '{"version": 2}')

  def test_rejects_invalid_district_names(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      root = Path(temporary_directory)
      invalid_names = ['', '   ', 'mtl/centre', r'mtl\centre']

      for district_name in invalid_names:
        with self.subTest(district_name=district_name):
          with self.assertRaises(ValueError):
            gather_district_geojson_files(
              root,
              district_name,
              root / 'output')

      with self.assertRaises(TypeError):
        gather_district_geojson_files(root, 123, root / 'output')

  def test_rejects_invalid_input_and_output_paths(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      root = Path(temporary_directory)
      input_file = root / 'input.txt'
      output_file = root / 'output.txt'
      input_file.write_text('input', encoding='utf-8')
      output_file.write_text('output', encoding='utf-8')

      with self.assertRaises(FileNotFoundError):
        gather_district_geojson_files(
          root / 'missing',
          'mtl',
          root / 'output')
      with self.assertRaises(NotADirectoryError):
        gather_district_geojson_files(
          input_file,
          'mtl',
          root / 'output')
      with self.assertRaises(NotADirectoryError):
        gather_district_geojson_files(root, 'mtl', output_file)
      with self.assertRaises(ValueError):
        gather_district_geojson_files(root, 'mtl', root)


if __name__ == '__main__':
  unittest.main()
