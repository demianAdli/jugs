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
      property_roll = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['qc_property_roll_2025'],
        'roll')
      nrcan = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['nrcan_heights'],
        'nrcan')
      geoindex = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['qc_geoindex'],
        'geoindex')
      fsa = ScrubLayer(
        paths.qgis_path,
        paths.input_paths['fsa'],
        'fsa')
      _log_layer_summary(property_roll)
      _log_layer_summary(nrcan)
      _log_layer_summary(geoindex)
      _log_layer_summary(fsa)

    with _workflow_step('process NRCan layer'):
      nrcan.create_spatial_index()
      nrcan.fix_geometries(paths.output_paths['nrcan_fixed'])
      nrcan_fixed = ScrubLayer(
        paths.qgis_path,
        paths.output_paths['nrcan_fixed'],
        'nrcan_fixed')
      nrcan_fixed.create_spatial_index()
      _log_layer_summary(nrcan_fixed)

    with _workflow_step('process GeoIndex layer'):
      geoindex.create_spatial_index()
      geoindex.fix_geometries(paths.output_paths['geoindex_fixed'])
      geoindex_fixed = ScrubLayer(
        paths.qgis_path,
        paths.output_paths['geoindex_fixed'],
        'geoindex_fixed')
      geoindex_fixed.create_spatial_index()
      _log_layer_summary(geoindex_fixed)

    with _workflow_step('remove GeoIndex records without provincial id'):
      geoindex_fixed.conditional_delete_record(
        'g_id_provi', '=', 'Sans correspondance')

    with _workflow_step('join GeoIndex with property roll fields'):
      geoindex_fixed.field_join(
        joining_layer_path=paths.input_paths['qc_property_roll_2025'],
        joining_layer_name='roll',
        target_field='g_id_provi',
        join_field='ueid_provinc',
        join_fields=None,
        prefix='rl_',
        output_path=paths.output_paths['geoindex_field_join_roll'])
      geoindex_field_join_roll = ScrubLayer(
        paths.qgis_path,
        paths.output_paths['geoindex_field_join_roll'],
        'geoindex_field_join_roll')
      geoindex_field_join_roll.create_spatial_index()
      _log_layer_summary(geoindex_field_join_roll)

    with _workflow_step('spatial join NRCan with GeoIndex'):
      nrcan_fixed.spatial_join(
        geoindex_field_join_roll.layer_path,
        paths.output_paths['nrcan_spatial_join_geoindex'])
      nrcan_spatial_join_geoindex = ScrubLayer(
        paths.qgis_path,
        paths.output_paths['nrcan_spatial_join_geoindex'],
        'nrcan_spatial_join_geoindex')
      nrcan_spatial_join_geoindex.create_spatial_index()
      _log_layer_summary(nrcan_spatial_join_geoindex)

    with _workflow_step('spatial join Saint-Malachie with FSA'):
      nrcan_spatial_join_geoindex.spatial_join(
        fsa.layer_path,
        paths.output_paths['saint_malachie_gisoo_with_fsa'])
      saint_malachie_gisoo_with_fsa = ScrubLayer(
        paths.qgis_path,
        paths.output_paths['saint_malachie_gisoo_with_fsa'],
        'saint_malachie_gisoo_with_fsa')
      saint_malachie_gisoo_with_fsa.create_spatial_index()
      _log_layer_summary(saint_malachie_gisoo_with_fsa)

    with _workflow_step('remove records missing address'):
      saint_malachie_gisoo_with_fsa.conditional_delete_record(
        'rl_ad_ad_1', 'IS', 'NULL')

  except Exception:
    logger.exception('Saint-Malachie GISOO workflow failed.')
    raise

  output_path = paths.output_paths['saint_malachie_gisoo_with_fsa']
  logger.info(
    'Completed Saint-Malachie GISOO workflow. Output=%s Elapsed=%.3fs',
    output_path,
    perf_counter() - workflow_t0)
  return output_path


if __name__ == '__main__':
  configure_logging()
  run_workflow()
