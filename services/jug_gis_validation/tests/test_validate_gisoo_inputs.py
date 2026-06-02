import os
import sys
import unittest


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SERVICE_SRC = os.path.join(
    _REPO_ROOT, 'services', 'jug_gis_validation', 'src')
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
for path in (_SERVICE_SRC, _SABU_CHASSIS_SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

_DEPS_SKIP_REASON = None
try:
    import pandas as pd
    from jug_gis_validation.domain_validation.validate_gisoo import ValidateGISOO
    from jug_gis_validation.errors import (
        GISValidationCalculationError,
        GISValidationDataContractError,
    )
except ModuleNotFoundError as exc:
    if exc.name in {'pandas', 'geopandas', 'matplotlib', 'numpy'}:
        _DEPS_SKIP_REASON = (
            f'jug_gis_validation test dependency is not installed: {exc.name}'
        )
        pd = None
        ValidateGISOO = None
        GISValidationCalculationError = None
        GISValidationDataContractError = None
    else:
        raise


def _buildings_feature_collection(postal_code='H2X 1A1'):
    return {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {
                    'postal': postal_code,
                    'function': 'residential',
                    'area': 100,
                    'floors': 2,
                    'height': 7,
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [-73.56, 45.51],
                },
            },
        ],
    }


def _census_dataframe(code='H2X', single_detached_count=2):
    return pd.DataFrame(
        [
            {
                'CODE': code,
                'CHARACTERISTIC_NAME': 'Total private dwellings',
                'COUNT': 10,
            },
            {
                'CODE': code,
                'CHARACTERISTIC_NAME': (
                    'Total - Private households by household size - 100% data'
                ),
                'COUNT': 8,
            },
            {
                'CODE': code,
                'CHARACTERISTIC_NAME': 'Single-detached house',
                'COUNT': single_detached_count,
            },
        ]
    )


@unittest.skipIf(_DEPS_SKIP_REASON is not None, _DEPS_SKIP_REASON)
class TestValidateGISOOInputs(unittest.TestCase):
    def test_geojson_dict_and_custom_census_dataframe(self):
        validator = ValidateGISOO(
            _buildings_feature_collection(),
            'CODE',
            'COUNT',
            'postal',
            'function',
            'residential',
            'area',
            'floors',
            census_data_csv=_census_dataframe(),
        )

        self.assertEqual(validator.district_codes, ('H2X',))
        self.assertEqual(
            validator.clean_district_and_census_unit('H2X'),
            (1, 8.0))

    def test_default_packaged_census_is_used_when_not_provided(self):
        validator = ValidateGISOO(
            _buildings_feature_collection(),
            'ALT_GEO_CODE',
            'C1_COUNT_TOTAL',
            'postal',
            'function',
            'residential',
            'area',
            'floors',
        )

        self.assertEqual(validator._census_source, 'packaged:filtered_census.csv')

    def test_missing_buildings_column_raises_contract_error(self):
        buildings = _buildings_feature_collection()
        del buildings['features'][0]['properties']['floors']

        with self.assertRaises(GISValidationDataContractError):
            ValidateGISOO(
                buildings,
                'CODE',
                'COUNT',
                'postal',
                'function',
                'residential',
                'area',
                'floors',
                census_data_csv=_census_dataframe(),
            )

    def test_zero_census_area_raises_clear_calculation_error(self):
        validator = ValidateGISOO(
            _buildings_feature_collection(),
            'CODE',
            'COUNT',
            'postal',
            'function',
            'residential',
            'area',
            'floors',
            census_data_csv=_census_dataframe(single_detached_count=0),
        )

        with self.assertRaises(GISValidationCalculationError):
            validator.clean_district_vs_census_area('H2X')


if __name__ == '__main__':
    unittest.main()
