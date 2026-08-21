"""Consistency checks for runtime batch payloads and repository contracts."""
import json
import os
import sys
import tempfile
import unittest


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)

from src.jug_gis_cities.application.batch_jobs import SqliteBatchJobStore


_CONTRACT_ROOT = os.path.join(_REPO_ROOT, 'contracts')


def _load_json(*parts):
    path = os.path.join(_CONTRACT_ROOT, *parts)
    with open(path, encoding='utf-8-sig') as source:
        return json.load(source)


class TestFsaBatchContracts(unittest.TestCase):
    def test_runtime_job_has_exact_json_schema_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SqliteBatchJobStore(
                os.path.join(temp_dir, 'jobs.sqlite3'))
            response = store.create_job(
                component_name='mtl_fsa_gisoo',
                mode='standardize',
                requested_fsas=None,
                all_fsas=True,
                max_workers=3,
                cleanup_outputs=True,
                keep_outputs=('usage_clean',)).to_response()

        schema = _load_json(
            'jsonschema',
            'jug_gis_cities',
            'batch_job.schema.json')
        self.assertEqual(set(response), set(schema['properties']))
        self.assertTrue(set(schema['required']).issubset(response))

    def test_batch_examples_match_declared_job_fields(self):
        schema = _load_json(
            'jsonschema',
            'jug_gis_cities',
            'batch_job.schema.json')
        expected_fields = set(schema['properties'])

        for filename in (
                'api_batch_all_fsas.response.202.json',
                'api_batch_status.response.200.json'):
            with self.subTest(filename=filename):
                example = _load_json(
                    'examples',
                    'jug_gis_cities',
                    filename)
                self.assertEqual(set(example), expected_fields)

    def test_single_run_examples_include_cleanup_metadata(self):
        for filename in (
                'api_run_independent.response.201.json',
                'api_run_mtl_fsa_independent.response.201.json',
                'api_run_standardize.response.201.json'):
            with self.subTest(filename=filename):
                example = _load_json(
                    'examples',
                    'jug_gis_cities',
                    filename)
                self.assertIn('cleaned_output_paths', example)

    def test_openapi_declares_batch_operations_and_schemas(self):
        try:
            import yaml
        except ModuleNotFoundError as exc:
            self.skipTest(f'PyYAML is required for OpenAPI parsing: {exc}')

        openapi_path = os.path.join(
            _CONTRACT_ROOT,
            'openapi',
            'jug_gis_cities.yaml')
        with open(openapi_path, encoding='utf-8') as source:
            contract = yaml.safe_load(source)

        self.assertIn(
            '/components/{component_name}/batch-runs',
            contract['paths'])
        self.assertIn(
            '/components/{component_name}/batch-runs/{batch_id}',
            contract['paths'])
        self.assertIn('FsaBatchRunRequest', contract['components']['schemas'])
        self.assertIn('FsaBatchJob', contract['components']['schemas'])


if __name__ == '__main__':
    unittest.main()
