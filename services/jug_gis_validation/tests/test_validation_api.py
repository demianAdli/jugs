import importlib.util
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SERVICE_ROOT = os.path.join(_REPO_ROOT, 'services', 'jug_gis_validation')
_SERVICE_SRC = os.path.join(_SERVICE_ROOT, 'src')
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
for path in (_SERVICE_ROOT, _SERVICE_SRC, _SABU_CHASSIS_SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

_DEPS_SKIP_REASON = None
try:
    import pandas as pd
    import flask
    import flask_smorest
    import geopandas
    import matplotlib.pyplot as plt
except ModuleNotFoundError as exc:
    if exc.name in {
            'pandas',
            'flask',
            'flask_smorest',
            'geopandas',
            'matplotlib',
            'numpy',
    }:
        _DEPS_SKIP_REASON = (
            f'jug_gis_validation API test dependency is not installed: '
            f'{exc.name}'
        )
        pd = None
        plt = None
    else:
        raise


def _load_api_app():
    app_path = os.path.join(_SERVICE_ROOT, 'app.py')
    spec = importlib.util.spec_from_file_location(
        'jug_gis_validation_api_app',
        app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.testing = True
    return module.app


def _geojson_payload():
    return {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {
                    'fsa': 'H2X',
                    'function': '1000',
                    'area': 100,
                    'floor_num': 2,
                    'height': 7,
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [-73.56, 45.51],
                },
            },
        ],
    }


class _FakeValidator:
    @staticmethod
    def plot_area_comparison(
            codes_info,
            areas,
            census_areas,
            *,
            title,
            y_label,
            x_label):
        fig, ax = plt.subplots()
        ax.bar([0], [1])
        ax.set_title(title)
        ax.set_ylabel(y_label)
        return fig, ax


def _fake_result():
    dataframe = pd.DataFrame(
        [
            {
                'FSA': 'H2X',
                'Cleaned Units Num': 1,
                'Census Units Num': 8,
                'Cleaned Total Area': 200.0,
                'Cleaned Total Area (with proxy)': 200.0,
                'Census Total Area (by type)': 320.0,
            },
        ]
    )
    return SimpleNamespace(
        validator=_FakeValidator(),
        codes=('H2X',),
        comparison_dataframe=dataframe,
        uniquification_stats=SimpleNamespace(
            as_dict=lambda: {
                'applied': False,
                'unique_attribute_key': None,
                'input_features': 1,
                'retained_features': 1,
                'removed_features': 0,
                'duplicate_groups': 0,
            }),
    )


@unittest.skipIf(_DEPS_SKIP_REASON is not None, _DEPS_SKIP_REASON)
class TestValidationApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _load_api_app()

    def setUp(self):
        self.client = self.app.test_client()

    @patch(
        'jug_gis_validation.resources.validations.'
        'GISValidationApplicationService.run_validation')
    def test_post_raw_geojson_returns_json_result(self, run_validation_mock):
        run_validation_mock.return_value = _fake_result()

        response = self.client.post('/validations', json=_geojson_payload())

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body['codes'], ['H2X'])
        self.assertEqual(body['rows_count'], 1)
        self.assertFalse(body['uniquification']['applied'])
        run_validation_mock.assert_called_once()
        self.assertEqual(
            run_validation_mock.call_args.kwargs['buildings_set']['type'],
            'FeatureCollection')

    @patch(
        'jug_gis_validation.resources.validations.'
        'GISValidationApplicationService.run_validation')
    def test_post_passes_unique_attribute_key(self, run_validation_mock):
        run_validation_mock.return_value = _fake_result()
        payload = {
            'buildings_set': _geojson_payload(),
            'unique_attribute_key': 'roll_provincial_id',
        }

        response = self.client.post('/validations', json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            run_validation_mock.call_args.kwargs['unique_attribute_key'],
            'roll_provincial_id')

    def test_duplicate_with_invalid_area_returns_contract_error(self):
        buildings = _geojson_payload()
        first = buildings['features'][0]
        first['properties']['roll_provincial_id'] = 'ROLL-A'
        duplicate = {
            'type': 'Feature',
            'properties': dict(first['properties']),
            'geometry': {
                'type': 'Point',
                'coordinates': [-73.57, 45.52],
            },
        }
        duplicate['properties']['area'] = None
        buildings['features'].append(duplicate)

        response = self.client.post(
            '/validations',
            json={
                'buildings_set': buildings,
                'unique_attribute_key': 'roll_provincial_id',
            })

        self.assertEqual(response.status_code, 422)
        self.assertIn('Duplicate', response.get_json()['message'])

    @patch(
        'jug_gis_validation.resources.validations.'
        'GISValidationApplicationService.run_validation')
    def test_post_path_payload_passes_path_to_application(
            self,
            run_validation_mock):
        run_validation_mock.return_value = _fake_result()

        response = self.client.post(
            '/validations',
            json={'buildings_set_path': 'QuebecCity.geojson'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            run_validation_mock.call_args.kwargs['buildings_set'],
            'QuebecCity.geojson')

    @patch(
        'jug_gis_validation.resources.validations.'
        'GISValidationApplicationService.run_validation')
    def test_csv_export_returns_csv_response(self, run_validation_mock):
        run_validation_mock.return_value = _fake_result()

        response = self.client.post(
            '/validations?export=csv',
            json=_geojson_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn('FSA', response.get_data(as_text=True))

    @patch(
        'jug_gis_validation.resources.validations.'
        'GISValidationApplicationService.run_validation')
    def test_plot_export_returns_png_response(self, run_validation_mock):
        run_validation_mock.return_value = _fake_result()

        response = self.client.post(
            '/validations?export=plot',
            json=_geojson_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')
        self.assertTrue(response.get_data().startswith(b'\x89PNG'))


if __name__ == '__main__':
    unittest.main()
