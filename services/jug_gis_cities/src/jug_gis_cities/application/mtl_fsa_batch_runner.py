"""
Batch orchestration for the Montreal FSA GISOO component.

This module intentionally sits above ``mtl_fsa_gisoo.workflow``. The workflow
continues to process exactly one FSA, while this module decides which FSAs to
run and whether they run sequentially or in separate processes.
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Iterable

from sabu_chassis.logging import get_logger

from ..mtl_fsa_gisoo import workflow_config as mtl_fsa_paths
from .jug_gis_cities import GisComponentRunMode, GISCitiesApplicationService


logger = get_logger(__name__)

MTL_FSA_COMPONENT_NAME = 'mtl_fsa_gisoo'


@dataclass(frozen=True)
class MtlFsaBatchItemResult:
    """Outcome for one FSA in a Montreal FSA batch run."""

    fsa: str
    succeeded: bool
    workflow_output_path: str | None = None
    standardized_output_path: str | None = None
    error: str | None = None
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class MtlFsaBatchRunResult:
    """Outcome summary for a Montreal FSA batch run."""

    component_name: str
    mode: str
    max_workers: int
    results: tuple[MtlFsaBatchItemResult, ...]

    @property
    def fsas(self):
        return tuple(result.fsa for result in self.results)

    @property
    def succeeded_count(self):
        return sum(1 for result in self.results if result.succeeded)

    @property
    def failed_count(self):
        return sum(1 for result in self.results if not result.succeeded)

    @property
    def succeeded(self):
        return self.failed_count == 0


def _mode_value(mode):
    if isinstance(mode, GisComponentRunMode):
        return mode.value
    if not isinstance(mode, str):
        raise TypeError('mode must be a string or GisComponentRunMode.')
    normalized_mode = mode.strip().lower()
    if not normalized_mode:
        raise ValueError('mode is required.')
    return normalized_mode


def normalize_mtl_fsas(fsas):
    """Normalize FSA values while preserving caller order and removing dupes."""
    if fsas is None:
        raise ValueError('fsas is required.')

    normalized_fsas = []
    seen = set()
    for fsa in fsas:
        normalized_fsa = mtl_fsa_paths.normalize_fsa(fsa)
        if normalized_fsa in seen:
            continue
        normalized_fsas.append(normalized_fsa)
        seen.add(normalized_fsa)

    if not normalized_fsas:
        raise ValueError('At least one FSA is required.')
    return tuple(normalized_fsas)


def discover_mtl_fsas():
    """Read the configured FSA boundary layer and return unique FSA values."""
    from citygisoo.scrub_layer_class import ScrubLayer

    fsa_layer = ScrubLayer(
        mtl_fsa_paths.qgis_path,
        mtl_fsa_paths.input_paths['fsa'],
        'fsa_boundaries')

    discovered_fsas = set()
    for feature in fsa_layer.layer.getFeatures():
        value = feature[mtl_fsa_paths.fsa_field_name]
        if value is None:
            continue
        value = str(value).strip()
        if not value:
            continue
        discovered_fsas.add(mtl_fsa_paths.normalize_fsa(value))

    if not discovered_fsas:
        raise ValueError(
            'No FSA values were found in the configured Montreal FSA layer.')
    return tuple(sorted(discovered_fsas))


def _configure_mtl_fsa_worker_logging(fsa):
    from ..logging_setup import configure_service_logging

    os.environ['LOG_SERVICE'] = f'gis_cities-mtl-fsa-{fsa.lower()}'
    os.environ['LOG_FILE_NAME'] = os.path.join(
        'logs',
        'mtl_fsa',
        f'{fsa}.log')
    configure_service_logging(os.environ['LOG_SERVICE'])


def run_one_mtl_fsa(
        fsa,
        mode=GisComponentRunMode.STANDARDIZE,
        configure_worker_logging=False,
        component_runner=None):
    """Run the Montreal FSA component for one FSA and return a result item."""
    normalized_fsa = mtl_fsa_paths.normalize_fsa(fsa)
    normalized_mode = _mode_value(mode)
    run_t0 = perf_counter()

    if configure_worker_logging:
        _configure_mtl_fsa_worker_logging(normalized_fsa)

    runner = component_runner or GISCitiesApplicationService.run_component
    try:
        result = runner(
            component_name=MTL_FSA_COMPONENT_NAME,
            mode=normalized_mode,
            fsa=normalized_fsa)
    except Exception as exc:
        logger.exception(
            'Montreal FSA batch item failed. FSA=%s Mode=%s',
            normalized_fsa,
            normalized_mode)
        return MtlFsaBatchItemResult(
            fsa=normalized_fsa,
            succeeded=False,
            error=f'{type(exc).__name__}: {exc}',
            elapsed_seconds=perf_counter() - run_t0)

    return MtlFsaBatchItemResult(
        fsa=normalized_fsa,
        succeeded=True,
        workflow_output_path=getattr(result, 'workflow_output_path', None),
        standardized_output_path=getattr(
            result,
            'standardized_output_path',
            None),
        elapsed_seconds=perf_counter() - run_t0)


def _run_mtl_fsa_batch_sequential(
        fsas,
        mode,
        configure_worker_logging,
        component_runner):
    return tuple(
        run_one_mtl_fsa(
            fsa=fsa,
            mode=mode,
            configure_worker_logging=configure_worker_logging,
            component_runner=component_runner)
        for fsa in fsas)


def _run_mtl_fsa_batch_parallel(fsas, mode, max_workers):
    results_by_fsa = {}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                run_one_mtl_fsa,
                fsa,
                mode,
                True): fsa
            for fsa in fsas
        }

        for future in as_completed(futures):
            fsa = futures[future]
            try:
                results_by_fsa[fsa] = future.result()
            except Exception as exc:
                logger.exception(
                    'Montreal FSA worker process failed. FSA=%s Mode=%s',
                    fsa,
                    mode)
                results_by_fsa[fsa] = MtlFsaBatchItemResult(
                    fsa=fsa,
                    succeeded=False,
                    error=f'{type(exc).__name__}: {exc}')

    return tuple(results_by_fsa[fsa] for fsa in fsas)


@dataclass(frozen=True)
class MtlFsaBatchRunner:
    """Configured runner for Montreal FSA batch jobs."""

    mode: str | GisComponentRunMode = GisComponentRunMode.STANDARDIZE
    max_workers: int = 1
    fsa_provider: Callable[[], Iterable[str]] | None = None
    component_runner: Callable | None = None
    configure_worker_logging: bool = False

    def __post_init__(self):
        normalized_mode = _mode_value(self.mode)
        if not isinstance(self.max_workers, int):
            raise TypeError('max_workers must be an integer.')
        if self.max_workers < 1:
            raise ValueError('max_workers must be at least 1.')
        if self.max_workers > 1 and self.component_runner is not None:
            raise ValueError(
                'component_runner injection is only supported for '
                'sequential runs.')
        object.__setattr__(self, 'mode', normalized_mode)

    def discover_fsas(self):
        provider = self.fsa_provider or discover_mtl_fsas
        return normalize_mtl_fsas(provider())

    def resolve_fsas(self, fsas=None):
        if fsas is None:
            return self.discover_fsas()
        return normalize_mtl_fsas(fsas)

    def run_one(self, fsa):
        return run_one_mtl_fsa(
            fsa=fsa,
            mode=self.mode,
            configure_worker_logging=self.configure_worker_logging,
            component_runner=self.component_runner)

    def run_fsas(self, fsas):
        return self.run(fsas=fsas)

    def run_all(self):
        return self.run()

    def run(self, fsas=None):
        selected_fsas = self.resolve_fsas(fsas)
        logger.info(
            'Starting Montreal FSA batch. Count=%s Mode=%s MaxWorkers=%s',
            len(selected_fsas),
            self.mode,
            self.max_workers)

        batch_t0 = perf_counter()
        if self.max_workers == 1:
            results = _run_mtl_fsa_batch_sequential(
                selected_fsas,
                self.mode,
                self.configure_worker_logging,
                self.component_runner)
        else:
            results = _run_mtl_fsa_batch_parallel(
                selected_fsas,
                self.mode,
                self.max_workers)

        batch_result = MtlFsaBatchRunResult(
            component_name=MTL_FSA_COMPONENT_NAME,
            mode=self.mode,
            max_workers=self.max_workers,
            results=results)
        logger.info(
            'Completed Montreal FSA batch. Count=%s Succeeded=%s Failed=%s '
            'Mode=%s MaxWorkers=%s Elapsed=%.3fs',
            len(selected_fsas),
            batch_result.succeeded_count,
            batch_result.failed_count,
            self.mode,
            self.max_workers,
            perf_counter() - batch_t0)
        return batch_result


def run_mtl_fsa_batch(
        fsas=None,
        mode=GisComponentRunMode.STANDARDIZE,
        max_workers=1,
        fsa_provider: Callable[[], Iterable[str]] | None = None,
        component_runner=None,
        configure_worker_logging=False):
    """Run the Montreal FSA GISOO component for many FSAs.

    ``max_workers=1`` runs sequentially in the current process. Values greater
    than one run each FSA in a separate process and automatically enable
    per-FSA log files for worker processes.
    """
    runner = MtlFsaBatchRunner(
        mode=mode,
        max_workers=max_workers,
        fsa_provider=fsa_provider,
        component_runner=component_runner,
        configure_worker_logging=configure_worker_logging)
    return runner.run(fsas=fsas)
