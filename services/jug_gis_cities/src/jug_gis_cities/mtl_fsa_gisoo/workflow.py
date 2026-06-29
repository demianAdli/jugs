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
        'fsa')
      _log_layer_summary(roll_mtl)
      _log_layer_summary(nrcan_mtl)
      _log_layer_summary(usage_mtl)
      _log_layer_summary(fsa_layer)

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
