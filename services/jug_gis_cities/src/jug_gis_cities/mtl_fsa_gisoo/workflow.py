"""
Municipality: Saint-Malachie
workflow module
The workflow of cleaning and updating the Saint-Malachie Buildings dataset.
Project Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""

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
def _workflow_step(step_name):
  step_t0 = perf_counter()
  logger.info('Starting Saint-Malachie workflow step: %s.', step_name)
  try:
    yield
  except Exception:
    logger.error(
      'Failed Saint-Malachie workflow step: %s after %.3fs.',
      step_name,
      perf_counter() - step_t0)
    raise
  logger.info(
    'Completed Saint-Malachie workflow step: %s in %.3fs.',
    step_name,
    perf_counter() - step_t0)


def _log_layer_summary(layer):
  logger.info('%s', layer)


def run_workflow():
  """Run the Saint-Malachie GISOO cleaning workflow."""
  workflow_t0 = perf_counter()
  logger.info(
    'Starting Saint-Malachie GISOO workflow. Output directory=%s',
    paths.output_paths_dir)

  try:
    with _workflow_step('prepare output folders'):
      basic_functions.create_output_folders(
        paths.output_paths, paths.output_paths_dir)

    with _workflow_step('load input layers'):
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
      fsa = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['fsa'],
        'fsa')
      _log_layer_summary(roll_mtl)
      _log_layer_summary(nrcan_mtl)
      _log_layer_summary(usage_mtl)
      _log_layer_summary(fsa)






if __name__ == '__main__':
  configure_logging()
  run_workflow()
