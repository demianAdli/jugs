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

    with _workflow_step('duplicate nrcan layer with UUIDs',
                        normalized_fsa):
      nrcan_mtl.duplicate_layer(output_paths['nrcan_preserved'])
      nrcan_preserved = ScrubLayer(
        paths.qgis_path,
        output_paths['nrcan_preserved'],
        f'nrcan_preserved_{normalized_fsa}')
      nrcan_preserved.create_spatial_index()
      _log_layer_summary(nrcan_preserved)

    with _workflow_step('duplicate usage layer with UUIDs',
                        normalized_fsa):
      usage_mtl.duplicate_layer(output_paths['usage_dup'])
      usage_dup = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_dup'],
        f'usage_dup_{normalized_fsa}')
      usage_dup.create_spatial_index()
      _log_layer_summary(usage_dup)

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

    with _workflow_step('assign nrcan area field', normalized_fsa):
      nrcan.add_field('nrcan_area')
      nrcan.assign_area('nrcan_area')

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
        output_path=output_paths['usage_margin_san'],
        include_matches=False)
      usage_margin_san = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_margin_san'],
        f'usage_margin_san_{normalized_fsa}')
      usage_margin_san.create_spatial_index()
      _log_layer_summary(usage_margin_san)

    with _workflow_step('difference usage with usage margin san',
                        normalized_fsa):
      usage.difference_layer(
        overlay_layer=usage_margin_san,
        output_path=output_paths['usage_san_san'])
      usage_san_san = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_san_san'],
        f'usage_san_san_{normalized_fsa}')
      usage_san_san.create_spatial_index()
      _log_layer_summary(usage_san_san)

    with _workflow_step('extract usage margin records with provincial id',
                        normalized_fsa):
      usage_margin_san.extract_by_expression(
        '"g_id_provi" != \'Sans correspondance\'',
        output_paths['usage_margin'])
      usage_margin = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_margin'],
        f'usage_margin_{normalized_fsa}')
      usage_margin.create_spatial_index()
      _log_layer_summary(usage_margin)

    with _workflow_step('assign usage margin area field', normalized_fsa):
      usage_margin.add_field('area_ex')
      usage_margin.assign_area('area_ex')

    with _workflow_step('extract usage-only records by area',
                        normalized_fsa):
      usage_margin.extract_by_expression(
        '"area_ex" > 0.9 * "g_sup_tota"',
        output_paths['usage_only'])
      usage_only = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_only'],
        f'usage_only_{normalized_fsa}')
      usage_only.create_spatial_index()
      _log_layer_summary(usage_only)

    with _workflow_step('extract roll records missing from usage',
                        normalized_fsa):
      roll.extract_by_aggregate_membership(
        lookup_layer=usage,
        lookup_field='g_id_provi',
        target_field='id_provinc',
        output_path=output_paths['roll_only'],
        include_matches=False)
      roll_only = ScrubLayer(
        paths.qgis_path,
        output_paths['roll_only'],
        f'roll_only_{normalized_fsa}')
      roll_only.create_spatial_index()
      _log_layer_summary(roll_only)

    with _workflow_step('spatial join usage with roll-only',
                        normalized_fsa):
      usage.spatial_join_with_predicate(
        joining_layer_path=roll_only.layer_path,
        joined_layer_path=output_paths['usage_roll_only_all'],
        predicate='contains',
        join_method='one-to-many',
        prefix='ro_')
      usage_roll_only_all = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_roll_only_all'],
        f'usage_roll_only_all_{normalized_fsa}')
      usage_roll_only_all.create_spatial_index()
      _log_layer_summary(usage_roll_only_all)

    with _workflow_step('extract usage-roll-only matched records',
                        normalized_fsa):
      usage_roll_only_all.extract_by_expression(
        '"ro_roll_id" IS NOT NULL',
        output_paths['usage_roll_only'])
      usage_roll_only = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_roll_only'],
        f'usage_roll_only_{normalized_fsa}')
      usage_roll_only.create_spatial_index()
      _log_layer_summary(usage_roll_only)

    with _workflow_step('extract unique usage-roll-only records',
                        normalized_fsa):
      usage_roll_only.extract_unique_by_field(
        field_name='ro_id_provinc',
        output_path=output_paths['usage_roll_only_unique'])
      usage_roll_only_unique = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_roll_only_unique'],
        f'usage_roll_only_unique_{normalized_fsa}')
      usage_roll_only_unique.create_spatial_index()
      _log_layer_summary(usage_roll_only_unique)

    with _workflow_step('difference roll with roll-only', normalized_fsa):
      roll.difference_layer(
        overlay_layer=roll_only,
        output_path=output_paths['roll_clean'])
      roll_clean = ScrubLayer(
        paths.qgis_path,
        output_paths['roll_clean'],
        f'roll_clean_{normalized_fsa}')
      roll_clean.create_spatial_index()
      _log_layer_summary(roll_clean)

    with _workflow_step('duplicate roll provincial id field',
                        normalized_fsa):
      roll_clean.duplicate_text_field(
        source_field='id_provinc',
        target_field='r_id_provinc',
        field_length=36)

    with _workflow_step('join usage margin san with roll clean',
                        normalized_fsa):
      usage_margin_san.add_layer_join(
        joining_layer_path=roll_clean.layer_path,
        joining_layer_name=roll_clean.layer_name,
        join_field='r_id_provinc',
        target_field='g_id_provi',
        prefix='r_',
        output_path=output_paths['usage_roll'])
      usage_roll = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_roll'],
        f'usage_roll_{normalized_fsa}')
      usage_roll.create_spatial_index()
      _log_layer_summary(usage_roll)

    with _workflow_step('merge usage roll layers', normalized_fsa):
      ScrubLayer.merge_layer_paths(
        layer_paths=[
          usage_roll.layer_path,
          usage_only.layer_path,
          usage_roll_only_unique.layer_path,
        ],
        output_path=output_paths['usage_roll_all'])
      usage_roll_all = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_roll_all'],
        f'usage_roll_all_{normalized_fsa}')
      usage_roll_all.create_spatial_index()
      _log_layer_summary(usage_roll_all)

    with _workflow_step('delete duplicate usage geometries', normalized_fsa):
      usage_dup.delete_duplicate_geometries(output_paths['usage_dup_clean'])
      clean_usage_dup = ScrubLayer(
        paths.qgis_path,
        output_paths['usage_dup_clean'],
        f'clean_usage_dup_{normalized_fsa}')
      clean_usage_dup.create_spatial_index()
      _log_layer_summary(clean_usage_dup)

    with _workflow_step('intersect nrcan with clean usage duplicate',
                        normalized_fsa):
      nrcan.intersection_layer(
        overlay_layer=clean_usage_dup,
        output_path=output_paths['inter_nrcan'],
        overlay_fields=['usagedup_id'])
      inter_nrcan = ScrubLayer(
        paths.qgis_path,
        output_paths['inter_nrcan'],
        f'inter_nrcan_{normalized_fsa}')
      inter_nrcan.create_spatial_index()
      _log_layer_summary(inter_nrcan)

    with _workflow_step('assign inter nrcan area field', normalized_fsa):
      inter_nrcan.add_field('inter_area')
      inter_nrcan.assign_area('inter_area')

    with _workflow_step('assign inter nrcan area ratio field',
                        normalized_fsa):
      inter_nrcan.add_field('area_ratio')
      inter_nrcan.assign_field_ratio(
        target_field='area_ratio',
        numerator_field='inter_area',
        denominator_field='nrcan_area')

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
