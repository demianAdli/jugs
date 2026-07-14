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
        self.app = _build_test_app()
        self.client = self.app.test_client()

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


if __name__ == '__main__':
    unittest.main()
