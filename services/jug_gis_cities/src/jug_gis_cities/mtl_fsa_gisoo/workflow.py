"""
Municipality: Montreal FSA
workflow module
The workflow of cleaning and updating Montreal buildings by FSA district.
Project Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""

import argparse
import os
from contextlib import contextmanager
from time import perf_counter

from citygisoo import GeoPackageFeatureProcessor
from citygisoo.scrub_layer_class import ScrubLayer
from sabu_chassis.logging import configure_logging, get_logger

try:
  from . import workflow_config as paths
except ImportError:
  import workflow_config as paths


logger = get_logger(__name__)


@contextmanager
def _workflow_step(step_name, fsa):
  step_t0 = perf_counter()
  logger.info('Starting Montreal %s workflow step: %s.', fsa, step_name)
  try:
    yield
  except Exception:
    logger.error(
      'Failed Montreal %s workflow step: %s after %.3fs.',
      fsa,
      step_name,
      perf_counter() - step_t0)
    raise
  logger.info(
    'Completed Montreal %s workflow step: %s in %.3fs.',
    fsa,
    step_name,
    perf_counter() - step_t0)


def _log_layer_summary(layer):
  logger.info('%s', layer)


def _create_geopackage_output_paths(output_paths, output_paths_dir):
  for output_key in output_paths:
    output_folder = os.path.join(output_paths_dir, output_key)
    os.makedirs(output_folder, exist_ok=True)
    output_paths[output_key] = os.path.join(
      output_folder,
      f'{output_key}.gpkg')


def _load_output_layer(output_paths, output_key, fsa, layer_name=None):
  loaded_layer = ScrubLayer(
    paths.qgis_path,
    output_paths[output_key],
    layer_name or f'{output_key}_{fsa}')
  loaded_layer.create_spatial_index()
  _log_layer_summary(loaded_layer)
  return loaded_layer


def run_workflow(fsa):
  """Run the Montreal FSA GISOO cleaning workflow through usage_san_san."""
  normalized_fsa = paths.normalize_fsa(fsa)
  output_paths = dict(paths.output_paths)
  output_paths_dir = paths.get_fsa_output_paths_dir(normalized_fsa)
  processor = GeoPackageFeatureProcessor()
  workflow_t0 = perf_counter()
  logger.info(
    'Starting Montreal FSA GISOO workflow. FSA=%s Output directory=%s',
    normalized_fsa,
    output_paths_dir)

  try:
    with _workflow_step('prepare output folders', normalized_fsa):
      _create_geopackage_output_paths(output_paths, output_paths_dir)

    with _workflow_step('load input layers', normalized_fsa):
      roll_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_property_roll_2025'],
        'roll_mtl')
      nrcan_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_nrcan_heights'],
        'nrcan_mtl')
      nrcan_preserved_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_nrcan_preserved'],
        'nrcan_preserved_mtl')
      usage_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_mahm_usage_2026_gpkg'],
        'usage_mtl')
      usage_dup_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_usage_dup'],
        'usage_dup_mtl')
      fsa_layer = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['fsa'],
        'fsa_boundaries')
      _log_layer_summary(roll_mtl)
      _log_layer_summary(nrcan_mtl)
      _log_layer_summary(nrcan_preserved_mtl)
      _log_layer_summary(usage_mtl)
      _log_layer_summary(usage_dup_mtl)
      _log_layer_summary(fsa_layer)

    with _workflow_step('extract FSA boundary', normalized_fsa):
      fsa_layer.extract_by_attribute(
        paths.fsa_field_name,
        '=',
        normalized_fsa,
        output_paths['fsa_boundary'])
      fsa_boundary = _load_output_layer(
        output_paths,
        'fsa_boundary',
        normalized_fsa)
      if fsa_boundary.data_count != 1:
        raise ValueError(
          f'Expected exactly one Montreal FSA boundary for {normalized_fsa}; '
          f'found {fsa_boundary.data_count}.')

    with _workflow_step('clip input layers to FSA boundary', normalized_fsa):
      nrcan_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['nrcan'])
      nrcan = _load_output_layer(
        output_paths,
        'nrcan',
        normalized_fsa,
        layer_name=f'nrcan_clipped_{normalized_fsa}')

      nrcan_preserved_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['nrcan_preserved'])
      nrcan_preserved = _load_output_layer(
        output_paths,
        'nrcan_preserved',
        normalized_fsa)

      roll_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['roll'])
      roll = _load_output_layer(
        output_paths,
        'roll',
        normalized_fsa,
        layer_name=f'roll_clipped_{normalized_fsa}')

      usage_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['usage'])
      usage = _load_output_layer(
        output_paths,
        'usage',
        normalized_fsa,
        layer_name=f'usage_clipped_{normalized_fsa}')

      usage_dup_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['usage_dup'])
      usage_dup = _load_output_layer(
        output_paths,
        'usage_dup',
        normalized_fsa)

    with _workflow_step('fix nrcan geometries', normalized_fsa):
      nrcan.fix_geometries(output_paths['nrcan_fixed'])
      nrcan_fixed = _load_output_layer(
        output_paths,
        'nrcan_fixed',
        normalized_fsa)

    with _workflow_step('assign nrcan area field', normalized_fsa):
      nrcan_fixed.add_field('nrcan_area')
      nrcan_fixed.assign_area('nrcan_area')

    with _workflow_step('fix nrcan preserved geometries', normalized_fsa):
      nrcan_preserved.fix_geometries(output_paths['nrcan_preserved_fixed'])
      nrcan_preserved_fixed = _load_output_layer(
        output_paths,
        'nrcan_preserved_fixed',
        normalized_fsa)

    with _workflow_step('assign nrcan preserved area field', normalized_fsa):
      nrcan_preserved_fixed.add_field('nrcan_area')
      nrcan_preserved_fixed.assign_area('nrcan_area')

    with _workflow_step('fix usage geometries', normalized_fsa):
      usage.fix_geometries(output_paths['usage_fixed'])
      usage_fixed = _load_output_layer(
        output_paths,
        'usage_fixed',
        normalized_fsa)

    with _workflow_step('fix usage duplicate geometries', normalized_fsa):
      usage_dup.fix_geometries(output_paths['usage_dup_fixed'])
      _load_output_layer(
        output_paths,
        'usage_dup_fixed',
        normalized_fsa)

    with _workflow_step('extract usage records missing from roll',
                        normalized_fsa):
      processor.extract_by_membership(
        source_layer=usage_fixed,
        lookup_layer=roll,
        source_field='g_id_provi',
        lookup_field='id_provinc',
        output_path=output_paths['usage_margin_san'],
        include_matches=False,
        layer_name=f'usage_margin_san_{normalized_fsa}')
      usage_margin_san = _load_output_layer(
        output_paths,
        'usage_margin_san',
        normalized_fsa)

    with _workflow_step('difference usage with usage margin san',
                        normalized_fsa):
      usage.difference_layer(
        overlay_layer=usage_margin_san,
        output_path=output_paths['usage_san_san'])
      usage_san_san = _load_output_layer(
        output_paths,
        'usage_san_san',
        normalized_fsa)

  except Exception:
    logger.exception(
      'Montreal FSA GISOO workflow failed. FSA=%s',
      normalized_fsa)
    raise

  output_path = usage_san_san.layer_path
  logger.info(
    'Completed Montreal FSA GISOO partial workflow. '
    'FSA=%s Output=%s Elapsed=%.3fs',
    normalized_fsa,
    output_path,
    perf_counter() - workflow_t0)
  return output_path


def _build_parser():
  parser = argparse.ArgumentParser(
    description='Run the Montreal FSA GISOO workflow directly.')
  parser.add_argument(
    '--fsa',
    required=True,
    help='Three-character Montreal FSA, for example H3H.')
  return parser


if __name__ == '__main__':
  configure_logging()
  args = _build_parser().parse_args()
  run_workflow(args.fsa)
