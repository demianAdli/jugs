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
from contextlib import contextmanager
from time import perf_counter

from citygisoo.scrub_layer_class import ScrubLayer
from citygisoo import basic_functions
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


def run_workflow(fsa):
  """Run the Montreal FSA GISOO cleaning workflow."""
  normalized_fsa = paths.normalize_fsa(fsa)
  output_paths = dict(paths.output_paths)
  output_paths_dir = paths.get_fsa_output_paths_dir(normalized_fsa)
  workflow_t0 = perf_counter()
  logger.info(
    'Starting Montreal FSA GISOO workflow. FSA=%s Output directory=%s',
    normalized_fsa,
    output_paths_dir)

  try:
    with _workflow_step('prepare output folders', normalized_fsa):
      basic_functions.create_output_folders(
        output_paths, output_paths_dir)

    with _workflow_step('load input layers', normalized_fsa):
      roll_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_property_roll_2025'],
        'roll_mtl')
      nrcan_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_nrcan_heights'],
        'nrcan_mtl')
      usage_mtl = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['mtl_mahm_usage_2026'],
        'usage_mtl')
      fsa_layer = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['fsa'],
        'fsa_boundaries')
      _log_layer_summary(roll_mtl)
      _log_layer_summary(nrcan_mtl)
      _log_layer_summary(usage_mtl)
      _log_layer_summary(fsa_layer)

    with _workflow_step('add UUID fields', normalized_fsa):
      roll_mtl.add_uuid_field('roll_id', overwrite=True)
      nrcan_mtl.add_uuid_field('nrcan_id', overwrite=True)
      usage_mtl.add_uuid_field('usage_id', overwrite=True)

    with _workflow_step('extract FSA boundary', normalized_fsa):
      fsa_layer.extract_by_attribute(
        paths.fsa_field_name,
        '=',
        normalized_fsa,
        output_paths['fsa_boundary'])
      fsa_boundary = ScrubLayer(
        paths.qgis_path,
        output_paths['fsa_boundary'],
        f'fsa_boundary_{normalized_fsa}')
      fsa_boundary.create_spatial_index()
      _log_layer_summary(fsa_boundary)
      if fsa_boundary.data_count != 1:
        raise ValueError(
          f'Expected exactly one Montreal FSA boundary for {normalized_fsa}; '
          f'found {fsa_boundary.data_count}.')

    with _workflow_step('clip input layers to FSA boundary', normalized_fsa):
      nrcan_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['nrcan'])
      nrcan = ScrubLayer(
        paths.qgis_path,
        output_paths['nrcan'],
        f'nrcan_clipped_{normalized_fsa}')
      nrcan.create_spatial_index()
      _log_layer_summary(nrcan)
      roll_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['roll'])
      roll = ScrubLayer(
        paths.qgis_path,
        output_paths['roll'],
        f'roll_clipped_{normalized_fsa}')
      roll.create_spatial_index()
      _log_layer_summary(roll)
      usage_mtl.clip_layer(
        fsa_boundary.layer_path,
        output_paths['usage'])
      usage = ScrubLayer(
        paths.qgis_path,
        output_paths['usage'],
        f'usage_clipped_{normalized_fsa}')
      usage.create_spatial_index()
      _log_layer_summary(usage)

    with _workflow_step('fix nrcan geometries', normalized_fsa):
      nrcan.fix_geometries(output_paths['nrcan_fixed'])
      nrcan_fixed = ScrubLayer(
        paths.qgis_path,
        output_paths['nrcan_fixed'],
        f'nrcan_fixed_{normalized_fsa}')
      nrcan_fixed.create_spatial_index()
      _log_layer_summary(nrcan_fixed)

    with _workflow_step('fix usage geometries', normalized_fsa):
      usage.fix_geometries(output_paths['usage_fixed'])
      usage_fixed = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_fixed'],
        f'usage_fixed_{normalized_fsa}')
      usage_fixed.create_spatial_index()
      _log_layer_summary(usage_fixed)

    with _workflow_step('extract usage records missing from roll',
                        normalized_fsa):
      usage_fixed.extract_by_aggregate_membership(
        lookup_layer=roll,
        lookup_field='id_provinc',
        target_field='g_id_provi',
        output_path=output_paths['usage_margin_sans'],
        include_matches=False)
      usage_margin_sans = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_margin_sans'],
        f'usage_margin_sans_{normalized_fsa}')
      usage_margin_sans.create_spatial_index()
      _log_layer_summary(usage_margin_sans)

  except Exception:
    logger.exception(
      'Montreal FSA GISOO workflow failed. FSA=%s',
      normalized_fsa)
    raise

  output_path = output_paths['mtl_fsa_gisoo']
  logger.info(
    'Completed Montreal FSA GISOO workflow. FSA=%s Output=%s Elapsed=%.3fs',
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
