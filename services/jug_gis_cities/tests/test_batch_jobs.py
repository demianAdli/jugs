"""Tests for persistent FSA batch jobs and output locks."""
import os
import sys
import tempfile
import unittest


_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_SERVICE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)
_SABU_CHASSIS_SRC = os.path.join(_REPO_ROOT, 'libs', 'sabu_chassis', 'src')
if _SABU_CHASSIS_SRC not in sys.path:
    sys.path.insert(0, _SABU_CHASSIS_SRC)

from src.jug_gis_cities.application.batch_jobs import (
    QUEUED,
    RUNNING,
    SqliteBatchJobStore,
)


class TestSqliteBatchJobStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp_dir.name, 'jobs.sqlite3')
        self.store = SqliteBatchJobStore(self.path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_job(self):
        return self.store.create_job(
            component_name='future_fsa_gisoo',
            mode='standardize',
            requested_fsas=('H3H', 'H2X'),
            all_fsas=False,
            max_workers=3,
            cleanup_outputs=True,
            keep_outputs=('usage_clean',))

    def test_job_persists_across_store_instances(self):
        created = self._create_job()

        loaded = SqliteBatchJobStore(self.path).get_job(created.batch_id)

        self.assertEqual(loaded.status, QUEUED)
        self.assertEqual(loaded.requested_fsas, ('H3H', 'H2X'))
        self.assertEqual(loaded.max_workers, 3)
        self.assertEqual(loaded.keep_outputs, ('usage_clean',))

    def test_claim_progress_and_completion(self):
        created = self._create_job()

        claimed = self.store.claim_next_job('worker-1')
        self.store.set_resolved_fsas(created.batch_id, ('H3H', 'H2X'))
        self.store.record_result(created.batch_id, {
            'fsa': 'H2X',
            'succeeded': True,
            'workflow_output_path': 'H2X.gpkg',
            'standardized_output_path': None,
            'cleaned_output_paths': [],
            'error': None,
            'elapsed_seconds': 0.5,
        })
        self.store.record_result(created.batch_id, {
            'fsa': 'H3H',
            'succeeded': True,
            'workflow_output_path': 'H3H.gpkg',
            'standardized_output_path': None,
            'cleaned_output_paths': [],
            'error': None,
            'elapsed_seconds': 1.0,
        })
        self.store.complete_job(created.batch_id, succeeded=True)
        completed = self.store.get_job(created.batch_id)

        self.assertEqual(claimed.status, RUNNING)
        self.assertEqual(completed.status, 'succeeded')
        self.assertEqual(completed.total_count, 2)
        self.assertEqual(completed.completed_count, 2)
        self.assertEqual(completed.succeeded_count, 2)
        self.assertEqual(
            tuple(result['fsa'] for result in completed.results),
            ('H3H', 'H2X'))

    def test_fsa_locks_reject_conflicting_owner(self):
        self.assertTrue(self.store.acquire_fsa_locks(
            'job-1', 'future_fsa_gisoo', ('H3H', 'H2X')))
        self.assertFalse(self.store.acquire_fsa_locks(
            'job-2', 'future_fsa_gisoo', ('H2X',)))

        self.store.release_fsa_locks('job-1')

        self.assertTrue(self.store.acquire_fsa_locks(
            'job-2', 'future_fsa_gisoo', ('H2X',)))

    def test_recover_running_job_requeues_and_releases_locks(self):
        created = self._create_job()
        self.store.claim_next_job('worker-1')
        self.store.acquire_fsa_locks(
            created.batch_id,
            created.component_name,
            ('H3H',))

        recovered = self.store.recover_running_jobs()

        self.assertEqual(recovered, 1)
        self.assertEqual(self.store.get_job(created.batch_id).status, QUEUED)
        self.assertTrue(self.store.acquire_fsa_locks(
            'job-2', created.component_name, ('H3H',)))


if __name__ == '__main__':
    unittest.main()
