"""
Tests for the Montreal FSA batch runner.
"""
import os
import sys
import unittest
from unittest.mock import Mock


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SERVICE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)

from src.jug_gis_cities.application.mtl_fsa_batch_runner import (
    MTL_FSA_COMPONENT_NAME,
    MtlFsaBatchRunner,
    normalize_mtl_fsas,
    run_mtl_fsa_batch,
    run_one_mtl_fsa,
)


class _ComponentResult:
    def __init__(
            self,
            workflow_output_path,
            standardized_output_path=None):
        self.workflow_output_path = workflow_output_path
        self.standardized_output_path = standardized_output_path


class TestMtlFsaBatchRunner(unittest.TestCase):
    def test_normalize_mtl_fsas_preserves_order_and_removes_duplicates(self):
        self.assertEqual(
            normalize_mtl_fsas([' h3h ', 'H2X', 'h3h']),
            ('H3H', 'H2X'))

    def test_run_one_mtl_fsa_passes_component_mode_and_fsa(self):
        component_runner = Mock(
            return_value=_ComponentResult(
                workflow_output_path='workflow_H3H.gpkg',
                standardized_output_path='standard_H3H.geojson'))

        result = run_one_mtl_fsa(
            fsa=' h3h ',
            mode='raw',
            component_runner=component_runner)

        self.assertTrue(result.succeeded)
        self.assertEqual(result.fsa, 'H3H')
        self.assertEqual(result.workflow_output_path, 'workflow_H3H.gpkg')
        self.assertEqual(result.standardized_output_path, 'standard_H3H.geojson')
        component_runner.assert_called_once_with(
            component_name=MTL_FSA_COMPONENT_NAME,
            mode='raw',
            fsa='H3H',
            non_null_required_fields=None)

    def test_run_one_mtl_fsa_passes_non_null_required_fields(self):
        component_runner = Mock(
            return_value=_ComponentResult(
                workflow_output_path='workflow_H3H.gpkg',
                standardized_output_path='standard_H3H.geojson'))

        run_one_mtl_fsa(
            fsa='h3h',
            mode='standardize',
            non_null_required_fields=['citygisoo_id', 'FSA'],
            component_runner=component_runner)

        component_runner.assert_called_once_with(
            component_name=MTL_FSA_COMPONENT_NAME,
            mode='standardize',
            fsa='H3H',
            non_null_required_fields=['citygisoo_id', 'FSA'])

    def test_run_mtl_fsa_batch_uses_provider_when_fsas_not_supplied(self):
        component_runner = Mock(
            side_effect=[
                _ComponentResult('workflow_H3H.gpkg'),
                _ComponentResult('workflow_H2X.gpkg'),
            ])

        result = run_mtl_fsa_batch(
            fsa_provider=lambda: ['h3h', 'h2x'],
            mode='standardize',
            component_runner=component_runner)

        self.assertTrue(result.succeeded)
        self.assertEqual(result.fsas, ('H3H', 'H2X'))
        self.assertEqual(result.succeeded_count, 2)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(component_runner.call_count, 2)

    def test_runner_stores_configuration_and_runs_selected_fsas(self):
        component_runner = Mock(
            side_effect=[
                _ComponentResult('workflow_H3H.gpkg'),
                _ComponentResult('workflow_H2X.gpkg'),
            ])
        runner = MtlFsaBatchRunner(
            mode='standard',
            max_workers=1,
            component_runner=component_runner)

        result = runner.run_fsas(['h3h', 'h2x'])

        self.assertEqual(runner.mode, 'standard')
        self.assertTrue(result.succeeded)
        self.assertEqual(result.fsas, ('H3H', 'H2X'))
        self.assertEqual(result.mode, 'standard')
        self.assertEqual(result.max_workers, 1)
        self.assertEqual(component_runner.call_count, 2)

    def test_runner_stores_non_null_fields_and_runs_selected_fsas(self):
        component_runner = Mock(
            return_value=_ComponentResult('workflow_H3H.gpkg'))
        runner = MtlFsaBatchRunner(
            non_null_required_fields=['citygisoo_id'],
            component_runner=component_runner)

        runner.run_fsas(['h3h'])

        component_runner.assert_called_once_with(
            component_name=MTL_FSA_COMPONENT_NAME,
            mode='standardize',
            fsa='H3H',
            non_null_required_fields=['citygisoo_id'])

    def test_runner_run_all_uses_configured_provider(self):
        component_runner = Mock(
            return_value=_ComponentResult('workflow_H3H.gpkg'))
        runner = MtlFsaBatchRunner(
            fsa_provider=lambda: ['h3h'],
            component_runner=component_runner)

        result = runner.run_all()

        self.assertTrue(result.succeeded)
        self.assertEqual(result.fsas, ('H3H',))

    def test_run_mtl_fsa_batch_records_failure_and_continues(self):
        component_runner = Mock(
            side_effect=[
                RuntimeError('boom'),
                _ComponentResult('workflow_H2X.gpkg'),
            ])

        result = run_mtl_fsa_batch(
            fsas=['H3H', 'H2X'],
            mode='standardize',
            component_runner=component_runner)

        self.assertFalse(result.succeeded)
        self.assertEqual(result.succeeded_count, 1)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.results[0].fsa, 'H3H')
        self.assertFalse(result.results[0].succeeded)
        self.assertIn('RuntimeError: boom', result.results[0].error)
        self.assertTrue(result.results[1].succeeded)

    def test_parallel_batch_rejects_injected_component_runner(self):
        with self.assertRaises(ValueError):
            MtlFsaBatchRunner(
                max_workers=2,
                component_runner=Mock())

    def test_runner_passes_cleanup_options_to_each_fsa(self):
        component_runner = Mock(
            return_value=_ComponentResult('workflow_H3H.gpkg'))
        runner = MtlFsaBatchRunner(
            cleanup_outputs=True,
            keep_outputs=['usage_clean'],
            component_runner=component_runner)

        runner.run_fsas(['h3h'])

        component_runner.assert_called_once_with(
            component_name=MTL_FSA_COMPONENT_NAME,
            mode='standardize',
            fsa='H3H',
            non_null_required_fields=None,
            cleanup_outputs=True,
            keep_outputs=('usage_clean',))


if __name__ == '__main__':
    unittest.main()
