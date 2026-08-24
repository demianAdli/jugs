"""Direct Python execution entrypoint for jug_gis_validation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sabu_chassis.logging import get_logger

from .application import (
    GISValidationApplicationService,
    GISValidationOutputMode,
    GISValidationPlotMetric,
)
from .application.jug_gis_validation import (
    DEFAULT_AREA_KEY,
    DEFAULT_CENSUS_CODE_FIELD_TITLE,
    DEFAULT_CENSUS_DATA_CSV,
    DEFAULT_CENSUS_UNITS_NUM_TITLE,
    DEFAULT_DISTRICT_NAME,
    DEFAULT_FLOOR_NUM_KEY,
    DEFAULT_FUNCTION_KEY,
    DEFAULT_FUNCTION_VALUE,
    DEFAULT_HEIGHT_KEY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POSTAL_CODE_KEY,
)
from .logging_setup import configure_service_logging


logger = get_logger(__name__)


def _build_parser():
    parser = argparse.ArgumentParser(
        description='Run a jug_gis_validation workflow directly.')
    parser.add_argument(
        '--buildings-set',
        required=True,
        help='Path to a buildings_set GeoJSON file.')
    parser.add_argument(
        '--census-data-csv',
        default=DEFAULT_CENSUS_DATA_CSV,
        help='Census CSV path or packaged default data/filtered_census.csv.')
    parser.add_argument(
        '--census-code-field-title',
        default=DEFAULT_CENSUS_CODE_FIELD_TITLE,
        help='Census field containing FSA/code values.')
    parser.add_argument(
        '--census-units-num-title',
        default=DEFAULT_CENSUS_UNITS_NUM_TITLE,
        help='Census field containing count values.')
    parser.add_argument(
        '--postal-code-key',
        default=DEFAULT_POSTAL_CODE_KEY,
        help='buildings_set field containing FSA/postal-code values.')
    parser.add_argument(
        '--function-key',
        default=DEFAULT_FUNCTION_KEY,
        help='buildings_set field containing building function values.')
    parser.add_argument(
        '--function-value',
        default=DEFAULT_FUNCTION_VALUE,
        help='Function value to keep during validation.')
    parser.add_argument(
        '--area-key',
        default=DEFAULT_AREA_KEY,
        help='buildings_set field containing area values.')
    parser.add_argument(
        '--floor-num-key',
        default=DEFAULT_FLOOR_NUM_KEY,
        help='buildings_set field containing floor-number values.')
    parser.add_argument(
        '--height-key',
        default=DEFAULT_HEIGHT_KEY,
        help='buildings_set field containing height values for proxy output.')
    parser.add_argument(
        '--census-avg-area-json',
        help=(
            'Optional JSON object or path to a JSON file with average area '
            'values by census dwelling type.'))
    parser.add_argument(
        '--output-mode',
        default=GISValidationOutputMode.CONSOLE.value,
        choices=[mode.value for mode in GISValidationOutputMode],
        help='How to output the comparison table.')
    parser.add_argument(
        '--district-name',
        default=DEFAULT_DISTRICT_NAME,
        help='Name used for default CSV and plot filenames.')
    parser.add_argument(
        '--output-dir',
        default=DEFAULT_OUTPUT_DIR,
        help='Directory used for default CSV and plot outputs.')
    parser.add_argument(
        '--csv-path',
        help='Optional explicit CSV output path.')
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Save a comparison plot.')
    parser.add_argument(
        '--plot-metric',
        default=GISValidationPlotMetric.AREA.value,
        choices=[metric.value for metric in GISValidationPlotMetric],
        help='Metric to compare in the plot (default: area).')
    parser.add_argument(
        '--plot-path',
        help='Optional explicit plot output path.')
    parser.add_argument(
        '--plot-title',
        help='Optional plot title.')
    return parser


def _load_census_avg_area(raw_value):
    if not raw_value:
        return None

    candidate_path = Path(raw_value)
    if candidate_path.exists():
        raw_value = candidate_path.read_text(encoding='utf-8')

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError(
            '--census-avg-area-json must be a JSON object or a JSON file path.'
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError('--census-avg-area-json must resolve to a JSON object.')
    return parsed


def main(argv=None):
    configure_service_logging('gis_validation-direct')
    args = _build_parser().parse_args(argv)

    try:
        result = GISValidationApplicationService.run_validation(
            buildings_set=args.buildings_set,
            census_data_csv=args.census_data_csv,
            census_code_field_title=args.census_code_field_title,
            census_units_num_title=args.census_units_num_title,
            postal_code_key=args.postal_code_key,
            function_key=args.function_key,
            function_value=args.function_value,
            area_key=args.area_key,
            floor_num_key=args.floor_num_key,
            height_key=args.height_key,
            census_avg_area_by_type=_load_census_avg_area(
                args.census_avg_area_json),
            output_mode=args.output_mode,
            district_name=args.district_name,
            output_dir=args.output_dir,
            csv_path=args.csv_path,
            include_plot=args.plot,
            plot_path=args.plot_path,
            plot_title=args.plot_title,
            plot_metric=args.plot_metric)
    except Exception as exc:
        logger.error('Direct jug_gis_validation execution failed. Error=%s',
                     exc)
        return 1

    print(f'District codes: {len(result.codes)}')
    if result.csv_path is not None:
        print(f'CSV output: {result.csv_path}')
    if result.plot_path is not None:
        print(f'Plot output: {result.plot_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
