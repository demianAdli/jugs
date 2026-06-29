"""
Sabu project
jug_gis_cities package
test_gis_cities_application module
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import unittest
import os
import sys
from unittest.mock import Mock, call, patch


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)

from src.jug_gis_cities.application.jug_gis_cities import (
    GisComponentContractError,
    GisComponentError,
    GisComponentRunMode,
    GISCitiesApplicationService,
)


class TestGISCitiesApplicationService(unittest.TestCase):
    def test_normalize_mode_accepts_strings_and_enum(self):
        self.assertEqual(
            GISCitiesApplicationService._normalize_mode(' STANDARDIZE '),
            GisComponentRunMode.STANDARDIZE)
        self.assertEqual(
            GISCitiesApplicationService._normalize_mode(
                GisComponentRunMode.INDEPENDENT),
            GisComponentRunMode.INDEPENDENT)

    def test_normalize_mode_rejects_unsupported_mode(self):
        with self.assertRaises(ValueError):
            GISCitiesApplicationService._normalize_mode('finalize')

    @patch.object(GISCitiesApplicationService, '_import_component_callable')
    @patch.object(GISCitiesApplicationService, '_ensure_component_callable')
    @patch.object(GISCitiesApplicationService, '_normalize_component_name')
    def test_run_component_independent_runs_workflow_only(
            self,
            normalize_component_name_mock,
            ensure_component_callable_mock,
            import_component_callable_mock):
        normalize_component_name_mock.return_value = 'saint_malachie_gisoo'
        workflow_runner = Mock(return_value='workflow_output.shp')
        import_component_callable_mock.return_value = workflow_runner

        result = GISCitiesApplicationService.run_component(
            ' saint_malachie_gisoo ',
            mode='independent')

        self.assertEqual(result.component_name, 'saint_malachie_gisoo')
        self.assertEqual(result.mode, GisComponentRunMode.INDEPENDENT)
        self.assertEqual(result.workflow_output_path, 'workflow_output.shp')
        self.assertIsNone(result.fsa)
        self.assertIsNone(result.standardized_output_path)
        ensure_component_callable_mock.assert_called_once_with(
            component_name='saint_malachie_gisoo',
            module_name='workflow',
            callable_name='run_workflow')
        import_component_callable_mock.assert_called_once_with(
            component_name='saint_malachie_gisoo',
            module_name='workflow',
            callable_name='run_workflow')
        workflow_runner.assert_called_once_with()

    @patch.object(GISCitiesApplicationService, '_import_component_callable')
    @patch.object(GISCitiesApplicationService, '_ensure_component_callable')
    @patch.object(GISCitiesApplicationService, '_normalize_component_name')
    def test_run_component_standardize_runs_workflow_and_contract_adapter(
            self,
            normalize_component_name_mock,
            ensure_component_callable_mock,
            import_component_callable_mock):
        normalize_component_name_mock.return_value = 'saint_malachie_gisoo'
        workflow_runner = Mock(return_value='workflow_output.shp')
        contract_adapter_runner = Mock(return_value='standardized.geojson')
        import_component_callable_mock.side_effect = [
            workflow_runner,
            contract_adapter_runner,
        ]

        result = GISCitiesApplicationService.run_component(
            'saint_malachie_gisoo',
            mode='standardize')

        self.assertEqual(result.component_name, 'saint_malachie_gisoo')
        self.assertEqual(result.mode, GisComponentRunMode.STANDARDIZE)
        self.assertEqual(result.workflow_output_path, 'workflow_output.shp')
        self.assertIsNone(result.fsa)
        self.assertEqual(
            result.standardized_output_path,
            'standardized.geojson')
        ensure_component_callable_mock.assert_has_calls([
            call(
                component_name='saint_malachie_gisoo',
                module_name='workflow',
                callable_name='run_workflow'),
            call(
                component_name='saint_malachie_gisoo',
                module_name='contract_adapter',
                callable_name='run_contract_adapter'),
        ])
        workflow_runner.assert_called_once_with()
        contract_adapter_runner.assert_called_once_with()

    @patch.object(GISCitiesApplicationService, '_import_component_callable')
    @patch.object(GISCitiesApplicationService, '_ensure_component_callable')
    @patch.object(GISCitiesApplicationService, '_normalize_component_name')
    def test_run_component_passes_normalized_fsa_to_supported_callables(
            self,
            normalize_component_name_mock,
            ensure_component_callable_mock,
            import_component_callable_mock):
        normalize_component_name_mock.return_value = 'mtl_fsa_gisoo'
        calls = []

        def workflow_runner(*, fsa):
            calls.append(('workflow', fsa))
            return f'workflow_{fsa}.shp'

        def contract_adapter_runner(*, fsa):
            calls.append(('contract_adapter', fsa))
            return f'standardized_{fsa}.geojson'

        import_component_callable_mock.side_effect = [
            workflow_runner,
            contract_adapter_runner,
        ]

        result = GISCitiesApplicationService.run_component(
            'mtl_fsa_gisoo',
            mode='standardize',
            fsa=' h3h ')

        self.assertEqual(result.fsa, 'H3H')
        self.assertEqual(result.workflow_output_path, 'workflow_H3H.shp')
        self.assertEqual(
            result.standardized_output_path,
            'standardized_H3H.geojson')
        self.assertEqual(
            calls,
            [('workflow', 'H3H'), ('contract_adapter', 'H3H')])

    @patch.object(GISCitiesApplicationService, '_import_component_callable')
    @patch.object(GISCitiesApplicationService, '_ensure_component_callable')
    @patch.object(GISCitiesApplicationService, '_normalize_component_name')
    def test_run_component_requires_fsa_when_workflow_requires_it(
            self,
            normalize_component_name_mock,
            ensure_component_callable_mock,
            import_component_callable_mock):
        normalize_component_name_mock.return_value = 'mtl_fsa_gisoo'

        def workflow_runner(*, fsa):
            return f'workflow_{fsa}.shp'

        import_component_callable_mock.return_value = workflow_runner

        with self.assertRaises(ValueError):
            GISCitiesApplicationService.run_component(
                'mtl_fsa_gisoo',
                mode='independent')

    @patch.object(GISCitiesApplicationService, '_import_component_callable')
    @patch.object(GISCitiesApplicationService, '_ensure_component_callable')
    @patch.object(GISCitiesApplicationService, '_normalize_component_name')
    def test_run_component_rejects_fsa_for_unsupported_workflow(
            self,
            normalize_component_name_mock,
            ensure_component_callable_mock,
            import_component_callable_mock):
        normalize_component_name_mock.return_value = 'saint_malachie_gisoo'

        def workflow_runner():
            return 'workflow_output.shp'

        import_component_callable_mock.return_value = workflow_runner

        with self.assertRaises(ValueError):
            GISCitiesApplicationService.run_component(
                'saint_malachie_gisoo',
                mode='independent',
                fsa='H3H')

    def test_standardize_requires_component_contract_adapter(self):
        with patch.object(
                GISCitiesApplicationService,
                '_PACKAGE_NAME',
                'src.jug_gis_cities'):
            with self.assertRaises(GisComponentContractError):
                GISCitiesApplicationService._ensure_component_callable(
                    component_name='mtl_gisoo',
                    module_name='contract_adapter',
                    callable_name='run_contract_adapter')

    @patch.object(GISCitiesApplicationService, '_import_component_callable')
    @patch.object(GISCitiesApplicationService, '_ensure_component_callable')
    @patch.object(GISCitiesApplicationService, '_normalize_component_name')
    def test_run_component_wraps_workflow_exceptions(
            self,
            normalize_component_name_mock,
            ensure_component_callable_mock,
            import_component_callable_mock):
        normalize_component_name_mock.return_value = 'saint_malachie_gisoo'
        workflow_runner = Mock(side_effect=RuntimeError('boom'))
        import_component_callable_mock.return_value = workflow_runner

        with self.assertRaises(GisComponentError):
            GISCitiesApplicationService.run_component(
                'saint_malachie_gisoo',
                mode='independent')


if __name__ == '__main__':
    unittest.main()
