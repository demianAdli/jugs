"""Backward-compatible Montreal facade for the generic FSA batch runner."""
from __future__ import annotations

from typing import Callable, Iterable

from .fsa_batch_runner import (
    FsaBatchItemResult,
    FsaBatchRunner,
    FsaBatchRunResult,
    discover_component_fsas,
    normalize_fsas,
    run_fsa_batch,
    run_one_fsa,
)
from .jug_gis_cities import GisComponentRunMode


MTL_FSA_COMPONENT_NAME = 'mtl_fsa_gisoo'

# Retain the published result type names while making the generic types
# canonical for new callers.
MtlFsaBatchItemResult = FsaBatchItemResult
MtlFsaBatchRunResult = FsaBatchRunResult


def normalize_mtl_fsas(fsas):
    return normalize_fsas(fsas)


def discover_mtl_fsas():
    return discover_component_fsas(MTL_FSA_COMPONENT_NAME)


def run_one_mtl_fsa(
        fsa,
        mode=GisComponentRunMode.STANDARDIZE,
        non_null_required_fields=None,
        configure_worker_logging=False,
        component_runner=None,
        cleanup_outputs=False,
        keep_outputs=None):
    return run_one_fsa(
        component_name=MTL_FSA_COMPONENT_NAME,
        fsa=fsa,
        mode=mode,
        non_null_required_fields=non_null_required_fields,
        configure_worker_logging=configure_worker_logging,
        component_runner=component_runner,
        cleanup_outputs=cleanup_outputs,
        keep_outputs=keep_outputs)


class MtlFsaBatchRunner(FsaBatchRunner):
    """Compatibility wrapper fixed to the Montreal FSA component."""

    def __init__(
            self,
            mode=GisComponentRunMode.STANDARDIZE,
            max_workers=1,
            non_null_required_fields=None,
            fsa_provider: Callable[[], Iterable[str]] | None = None,
            component_runner=None,
            configure_worker_logging=False,
            cleanup_outputs=False,
            keep_outputs=None):
        super().__init__(
            component_name=MTL_FSA_COMPONENT_NAME,
            mode=mode,
            max_workers=max_workers,
            non_null_required_fields=non_null_required_fields,
            fsa_provider=fsa_provider,
            component_runner=component_runner,
            configure_worker_logging=configure_worker_logging,
            cleanup_outputs=cleanup_outputs,
            keep_outputs=keep_outputs)


def run_mtl_fsa_batch(
        fsas=None,
        mode=GisComponentRunMode.STANDARDIZE,
        max_workers=1,
        non_null_required_fields=None,
        fsa_provider: Callable[[], Iterable[str]] | None = None,
        component_runner=None,
        configure_worker_logging=False,
        cleanup_outputs=False,
        keep_outputs=None):
    """Run the Montreal component through the generic FSA batch runner."""
    return run_fsa_batch(
        component_name=MTL_FSA_COMPONENT_NAME,
        fsas=fsas,
        mode=mode,
        max_workers=max_workers,
        non_null_required_fields=non_null_required_fields,
        fsa_provider=fsa_provider,
        component_runner=component_runner,
        configure_worker_logging=configure_worker_logging,
        cleanup_outputs=cleanup_outputs,
        keep_outputs=keep_outputs)


__all__ = [
    'MTL_FSA_COMPONENT_NAME',
    'MtlFsaBatchItemResult',
    'MtlFsaBatchRunResult',
    'MtlFsaBatchRunner',
    'discover_mtl_fsas',
    'normalize_mtl_fsas',
    'run_mtl_fsa_batch',
    'run_one_mtl_fsa',
]
