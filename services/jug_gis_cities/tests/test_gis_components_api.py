"""
Sabu project
jug_gis_cities package
test_gis_components_api module
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import unittest
import os
import sys
import tempfile
from unittest.mock import patch


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)

try:
    from flask import Flask
    from flask_smorest import Api
except ModuleNotFoundError as exc:
    raise unittest.SkipTest(
        'Flask service dependencies are required for API tests.'
    ) from exc

from src.jug_gis_cities.application import (
    GisComponentContractError,
    GisComponentError,
    GisComponentNotFoundError,
    GisComponentRunMode,
    GisComponentRunResult,
)
from src.jug_gis_cities.resources.gis_components import (
    blp as gis_components_blueprint,
)
from src.jug_gis_cities.application.batch_jobs import get_batch_job_store


def _build_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['API_TITLE'] = 'GIS Cities Workflow API'
    app.config['API_VERSION'] = 'v1'
    app.config['OPENAPI_VERSION'] = '3.0.2'

    api = Api(app)
    api.register_blueprint(gis_components_blueprint)
    return app


class TestGISComponentsApi(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.job_store_env = patch.dict(
            os.environ,
            {'JUG_GIS_CITIES_JOB_STORE_PATH': os.path.join(
                self.temp_dir.name,
                'jobs.sqlite3')})
        self.job_store_env.start()
        self.app = _build_test_app()
        self.client = self.app.test_client()

    def tearDown(self):
        self.job_store_env.stop()
        self.temp_dir.cleanup()

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_json_contract(self, run_component_mock):
        run_component_mock.return_value = GisComponentRunResult(
            component_name='saint_malachie_gisoo',
            mode=GisComponentRunMode.STANDARDIZE,
            workflow_output_path='workflow_output.shp',
            standardized_output_path='standardized.geojson')

        response = self.client.post(
            '/components/saint_malachie_gisoo/runs',
            json={'mode': 'standardize'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json(),
            {
                'component_name': 'saint_malachie_gisoo',
                'mode': 'standardize',
                'fsa': None,
                'workflow_output_path': 'workflow_output.shp',
                'standardized_output_path': 'standardized.geojson',
                'cleaned_output_paths': [],
            })
        run_component_mock.assert_called_once_with(
            component_name='saint_malachie_gisoo',
            mode='standardize',
            fsa=None,
            non_null_required_fields=None,
            cleanup_outputs=False,
            keep_outputs=None)

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_accepts_fsa(self, run_component_mock):
        run_component_mock.return_value = GisComponentRunResult(
            component_name='mtl_fsa_gisoo',
            mode=GisComponentRunMode.INDEPENDENT,
            fsa='H3H',
            workflow_output_path='workflow_output.shp',
            standardized_output_path=None)

        response = self.client.post(
            '/components/mtl_fsa_gisoo/runs',
            json={'mode': 'independent', 'fsa': 'h3h'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json(),
            {
                'component_name': 'mtl_fsa_gisoo',
                'mode': 'independent',
                'fsa': 'H3H',
                'workflow_output_path': 'workflow_output.shp',
                'standardized_output_path': None,
                'cleaned_output_paths': [],
            })
        run_component_mock.assert_called_once_with(
            component_name='mtl_fsa_gisoo',
            mode='independent',
            fsa='h3h',
            non_null_required_fields=None,
            cleanup_outputs=False,
            keep_outputs=None)

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_accepts_drop_null_fields(
            self,
            run_component_mock):
        run_component_mock.return_value = GisComponentRunResult(
            component_name='mtl_fsa_gisoo',
            mode=GisComponentRunMode.STANDARDIZE,
            fsa='H3H',
            workflow_output_path='workflow_output.gpkg',
            standardized_output_path='standardized.geojson')

        response = self.client.post(
            '/components/mtl_fsa_gisoo/runs',
            json={
                'mode': 'standardize',
                'fsa': 'h3h',
                'drop_null_fields': ['citygisoo_id', 'FSA'],
            })

        self.assertEqual(response.status_code, 201)
        run_component_mock.assert_called_once_with(
            component_name='mtl_fsa_gisoo',
            mode='standardize',
            fsa='h3h',
            non_null_required_fields=['citygisoo_id', 'FSA'],
            cleanup_outputs=False,
            keep_outputs=None)

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_accepts_cleanup_options(
            self,
            run_component_mock):
        run_component_mock.return_value = GisComponentRunResult(
            component_name='mtl_fsa_gisoo',
            mode=GisComponentRunMode.INDEPENDENT,
            fsa='H3H',
            workflow_output_path='workflow_output.gpkg',
            cleaned_output_paths=('usage_clean',))

        response = self.client.post(
            '/components/mtl_fsa_gisoo/runs',
            json={
                'mode': 'independent',
                'fsa': 'h3h',
                'cleanup_outputs': True,
                'keep_outputs': ['inter_summary'],
            })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json()['cleaned_output_paths'],
            ['usage_clean'])
        run_component_mock.assert_called_once_with(
            component_name='mtl_fsa_gisoo',
            mode='independent',
            fsa='h3h',
            non_null_required_fields=None,
            cleanup_outputs=True,
            keep_outputs=['inter_summary'])

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_not_found(self, run_component_mock):
        run_component_mock.side_effect = GisComponentNotFoundError(
            'GIS city component not found: missing_component')

        response = self.client.post(
            '/components/missing_component/runs',
            json={'mode': 'standardize'})

        self.assertEqual(response.status_code, 404)
        self.assertIn('missing_component', response.get_data(as_text=True))

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_contract_error(self, run_component_mock):
        run_component_mock.side_effect = GisComponentContractError(
            'GIS city component mtl_gisoo is missing contract_adapter.py.')

        response = self.client.post(
            '/components/mtl_gisoo/runs',
            json={'mode': 'standardize'})

        self.assertEqual(response.status_code, 422)
        self.assertIn('contract_adapter.py',
                      response.get_data(as_text=True))

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_bad_request(self, run_component_mock):
        run_component_mock.side_effect = ValueError(
            'Unsupported GIS component mode: finalize.')

        response = self.client.post(
            '/components/saint_malachie_gisoo/runs',
            json={'mode': 'standardize'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported GIS component mode',
                      response.get_data(as_text=True))

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_post_component_run_execution_error(self, run_component_mock):
        run_component_mock.side_effect = GisComponentError(
            'GIS city component execution failed: saint_malachie_gisoo')

        response = self.client.post(
            '/components/saint_malachie_gisoo/runs',
            json={'mode': 'standardize'})

        self.assertEqual(response.status_code, 500)
        self.assertIn('GIS city component execution failed',
                      response.get_data(as_text=True))

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'FsaBatchRunner.validate_component'
    )
    def test_submit_and_get_all_fsa_batch(self, validate_component_mock):
        response = self.client.post(
            '/components/future_fsa_gisoo/batch-runs',
            json={
                'mode': 'standardize',
                'all_fsas': True,
                'max_workers': 3,
                'cleanup_outputs': True,
                'keep_outputs': ['usage_clean'],
            })

        self.assertEqual(response.status_code, 202)
        submitted = response.get_json()
        self.assertEqual(submitted['status'], 'queued')
        self.assertEqual(submitted['component_name'], 'future_fsa_gisoo')
        self.assertTrue(submitted['all_fsas'])
        self.assertIsNone(submitted['fsas'])
        self.assertEqual(submitted['max_workers'], 3)
        self.assertEqual(submitted['completed_count'], 0)

        status_response = self.client.get(
            '/components/future_fsa_gisoo/batch-runs/'
            f"{submitted['batch_id']}")

        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.get_json(), submitted)
        validate_component_mock.assert_called_once_with()

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'FsaBatchRunner.validate_component'
    )
    def test_submit_selected_fsas_normalizes_and_deduplicates(
            self,
            validate_component_mock):
        response = self.client.post(
            '/components/future_fsa_gisoo/batch-runs',
            json={
                'fsas': ['h3h', 'H2X', 'H3H'],
                'max_workers': 3,
            })

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()['fsas'], ['H3H', 'H2X'])
        validate_component_mock.assert_called_once_with()

    def test_batch_submission_requires_one_fsa_selection(self):
        missing = self.client.post(
            '/components/future_fsa_gisoo/batch-runs',
            json={'max_workers': 3})
        both = self.client.post(
            '/components/future_fsa_gisoo/batch-runs',
            json={'fsas': ['H3H'], 'all_fsas': True})

        self.assertEqual(missing.status_code, 422)
        self.assertEqual(both.status_code, 422)

    def test_get_unknown_batch_returns_not_found(self):
        response = self.client.get(
            '/components/future_fsa_gisoo/batch-runs/missing')

        self.assertEqual(response.status_code, 404)

    @patch(
        'src.jug_gis_cities.resources.gis_components.'
        'GISCitiesApplicationService.run_component'
    )
    def test_single_fsa_run_rejects_conflicting_batch_lock(
            self,
            run_component_mock):
        store = get_batch_job_store()
        self.assertTrue(store.acquire_fsa_locks(
            'existing-batch',
            'mtl_fsa_gisoo',
            ('H3H',)))

        response = self.client.post(
            '/components/mtl_fsa_gisoo/runs',
            json={'mode': 'independent', 'fsa': 'h3h'})

        self.assertEqual(response.status_code, 409)
        run_component_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
