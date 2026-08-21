"""Tests for direct single and generic FSA batch CLI execution."""
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SERVICE_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'src'))
if _SERVICE_SRC not in sys.path:
    sys.path.insert(0, _SERVICE_SRC)
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)

from jug_gis_cities import __main__ as cli
from jug_gis_cities.application import (
    FsaBatchItemResult,
    FsaBatchRunResult,
    GisComponentRunMode,
    GisComponentRunResult,
)


class TestGisCitiesCli(unittest.TestCase):
    @staticmethod
    def _run_cli(arguments):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return cli.main(arguments)

    @patch.object(cli, 'configure_service_logging')
    @patch.object(cli, 'run_fsa_batch')
    def test_all_fsa_batch_with_three_workers_and_cleanup(
            self,
            run_fsa_batch_mock,
            configure_logging_mock):
        run_fsa_batch_mock.return_value = FsaBatchRunResult(
            component_name='mtl_fsa_gisoo',
            mode='standardize',
            max_workers=3,
            results=(
                FsaBatchItemResult(fsa='H2X', succeeded=True),
                FsaBatchItemResult(fsa='H3H', succeeded=True),
            ))

        exit_code = self._run_cli([
            '--component', 'mtl_fsa_gisoo',
            '--mode', 'standardize',
            '--all-fsas',
            '--max-workers', '3',
            '--cleanup-outputs',
            '--keep-output', 'usage_clean',
            '--keep-output', 'inter_summary',
        ])

        self.assertEqual(exit_code, 0)
        run_fsa_batch_mock.assert_called_once_with(
            component_name='mtl_fsa_gisoo',
            fsas=None,
            mode='standardize',
            max_workers=3,
            non_null_required_fields=None,
            cleanup_outputs=True,
            keep_outputs=['usage_clean', 'inter_summary'])

    @patch.object(cli, 'configure_service_logging')
    @patch.object(cli, 'run_fsa_batch')
    def test_selected_fsa_batch_preserves_cli_selection(
            self,
            run_fsa_batch_mock,
            configure_logging_mock):
        run_fsa_batch_mock.return_value = FsaBatchRunResult(
            component_name='future_fsa_gisoo',
            mode='independent',
            max_workers=3,
            results=(FsaBatchItemResult(fsa='H3H', succeeded=True),))

        exit_code = self._run_cli([
            '--component', 'future_fsa_gisoo',
            '--mode', 'independent',
            '--fsas', 'h3h', 'H2X',
            '--max-workers', '3',
        ])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            run_fsa_batch_mock.call_args.kwargs['fsas'],
            ['h3h', 'H2X'])

    @patch.object(cli, 'configure_service_logging')
    @patch.object(cli.GISCitiesApplicationService, 'run_component')
    def test_existing_single_fsa_execution_is_unchanged(
            self,
            run_component_mock,
            configure_logging_mock):
        run_component_mock.return_value = GisComponentRunResult(
            component_name='mtl_fsa_gisoo',
            mode=GisComponentRunMode.STANDARDIZE,
            fsa='H3H',
            workflow_output_path='workflow.gpkg',
            standardized_output_path='standardized.geojson')

        exit_code = self._run_cli([
            '--component', 'mtl_fsa_gisoo',
            '--mode', 'standardize',
            '--fsa', 'H3H',
        ])

        self.assertEqual(exit_code, 0)
        run_component_mock.assert_called_once_with(
            component_name='mtl_fsa_gisoo',
            mode='standardize',
            fsa='H3H',
            non_null_required_fields=None,
            cleanup_outputs=False,
            keep_outputs=None)

    @patch.object(cli, 'configure_service_logging')
    def test_max_workers_requires_batch_selection(
            self,
            configure_logging_mock):
        with self.assertRaises(SystemExit):
            self._run_cli([
                '--component', 'mtl_fsa_gisoo',
                '--fsa', 'H3H',
                '--max-workers', '3',
            ])


if __name__ == '__main__':
    unittest.main()
