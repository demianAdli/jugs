"""
Direct Python execution entrypoint for jug_gis_cities.
"""
from __future__ import annotations

import argparse
import sys

from sabu_chassis.logging import get_logger

from .application import GISCitiesApplicationService, GisComponentRunMode
from .logging_setup import configure_service_logging


logger = get_logger(__name__)


def _build_parser():
    parser = argparse.ArgumentParser(
        description='Run a jug_gis_cities component directly.')
    parser.add_argument(
        '--component',
        required=True,
        help=(
            'Component package name, for example saint_malachie_gisoo.'))
    parser.add_argument(
        '--mode',
        default=GisComponentRunMode.STANDARDIZE.value,
        choices=[mode.value for mode in GisComponentRunMode],
        help=(
            'Execution mode. independent runs only workflow.py; '
            'standardize runs workflow.py and contract_adapter.py.'))
    parser.add_argument(
        '--fsa',
        help=(
            'Three-character FSA for components that require district '
            'selection, for example H3H.'))
    parser.add_argument(
        '--drop-null-fields',
        nargs='+',
        default=None,
        metavar='FIELD',
        help=(
            'Optional standardized field names that must be non-null when '
            'running standardize mode. Features with null or empty values in '
            'any listed field are deleted. By default, no features are '
            'deleted based on null attributes.'))
    parser.add_argument(
        '--cleanup-outputs',
        action='store_true',
        help=(
            'Delete unretained intermediate datasets after a successful '
            'component run. By default, every generated output is kept.'))
    parser.add_argument(
        '--keep-output',
        action='append',
        default=None,
        metavar='OUTPUT_KEY',
        help=(
            'Additional workflow output key to retain when cleanup is '
            'enabled. Repeat this option to retain multiple outputs.'))
    return parser


def main(argv=None):
    configure_service_logging('gis_cities-direct')
    args = _build_parser().parse_args(argv)

    try:
        result = GISCitiesApplicationService.run_component(
            component_name=args.component,
            mode=args.mode,
            fsa=args.fsa,
            non_null_required_fields=args.drop_null_fields,
            cleanup_outputs=args.cleanup_outputs,
            keep_outputs=args.keep_output)
    except Exception as exc:
        logger.error(
            'Direct jug_gis_cities execution failed. Component=%s Mode=%s '
            'FSA=%s Error=%s',
            args.component,
            args.mode,
            args.fsa,
            exc)
        return 1

    print(f'Component: {result.component_name}')
    print(f'Mode: {result.mode.value}')
    if result.fsa is not None:
        print(f'FSA: {result.fsa}')
    print(f'Workflow output: {result.workflow_output_path}')
    if result.standardized_output_path is not None:
        print(f'Standardized output: {result.standardized_output_path}')
    if result.cleaned_output_paths:
        print(f'Cleaned outputs: {len(result.cleaned_output_paths)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
