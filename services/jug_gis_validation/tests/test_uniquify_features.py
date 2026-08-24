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
    import geopandas as gpd

    from jug_gis_validation.domain_validation.uniquify_features import (
        uniquify_features,
    )
    from jug_gis_validation.errors import GISValidationDataContractError
except ModuleNotFoundError as exc:
    if exc.name in {'geopandas', 'pandas'}:
        _DEPS_SKIP_REASON = (
            f'jug_gis_validation test dependency is not installed: {exc.name}'
        )
        gpd = None
        uniquify_features = None
        GISValidationDataContractError = None
    else:
        raise


def _frame(rows):
    return gpd.GeoDataFrame(rows, geometry=[None] * len(rows))


@unittest.skipIf(_DEPS_SKIP_REASON is not None, _DEPS_SKIP_REASON)
class TestUniquifyFeatures(unittest.TestCase):
    def test_keeps_greatest_area_and_preserves_order_and_missing_ids(self):
        buildings = _frame([
            {'marker': 'a-small', 'roll_id': 'A', 'area': 10},
            {'marker': 'missing', 'roll_id': None, 'area': 1},
            {'marker': 'a-large', 'roll_id': 'A', 'area': '20'},
            {'marker': 'b-first', 'roll_id': 'B', 'area': 5},
            {'marker': 'blank', 'roll_id': '   ', 'area': 2},
            {'marker': 'b-tied', 'roll_id': 'B', 'area': 5},
        ])

        result, stats = uniquify_features(
            buildings,
            unique_attribute_key='roll_id',
            area_key='area')

        self.assertEqual(
            result['marker'].tolist(),
            ['missing', 'a-large', 'b-first', 'blank'])
        self.assertEqual(len(buildings), 6)
        self.assertEqual(stats.input_features, 6)
        self.assertEqual(stats.retained_features, 4)
        self.assertEqual(stats.removed_features, 2)
        self.assertEqual(stats.duplicate_groups, 2)

    def test_invalid_area_in_duplicate_group_raises_contract_error(self):
        buildings = _frame([
            {'roll_id': 'A', 'area': 10},
            {'roll_id': 'A', 'area': None},
        ])

        with self.assertRaisesRegex(
                GISValidationDataContractError,
                'Duplicate.*area'):
            uniquify_features(
                buildings,
                unique_attribute_key='roll_id',
                area_key='area')

    def test_invalid_area_on_unique_feature_does_not_change_existing_policy(self):
        buildings = _frame([
            {'roll_id': 'A', 'area': 'unknown'},
            {'roll_id': 'B', 'area': 20},
        ])

        result, stats = uniquify_features(
            buildings,
            unique_attribute_key='roll_id',
            area_key='area')

        self.assertEqual(len(result), 2)
        self.assertEqual(stats.removed_features, 0)

    def test_missing_configured_column_raises_contract_error(self):
        buildings = _frame([{'area': 10}])

        with self.assertRaisesRegex(
                GISValidationDataContractError,
                'roll_id'):
            uniquify_features(
                buildings,
                unique_attribute_key='roll_id',
                area_key='area')

    def test_handles_seventeen_thousand_features(self):
        buildings = _frame([
            {
                'roll_id': f'R{position // 2}',
                'area': position % 2,
            }
            for position in range(17_000)
        ])

        result, stats = uniquify_features(
            buildings,
            unique_attribute_key='roll_id',
            area_key='area')

        self.assertEqual(len(result), 8_500)
        self.assertEqual(stats.removed_features, 8_500)
        self.assertEqual(stats.duplicate_groups, 8_500)
        self.assertTrue((result['area'] == 1).all())


if __name__ == '__main__':
    unittest.main()
