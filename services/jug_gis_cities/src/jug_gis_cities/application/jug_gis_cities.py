"""
Sabu project
jug_gis_cities package
Application-layer orchestration for city GIS cleaning components.
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
from __future__ import annotations

import ast
import inspect
import importlib
import importlib.util
import re
from dataclasses import dataclass
from enum import Enum
from time import perf_counter

from sabu_chassis.logging import get_logger


logger = get_logger(__name__)

_COMPONENT_NAME_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_FSA_PATTERN = re.compile(r'^[A-Z][0-9][A-Z]$')


class GisComponentRunMode(str, Enum):
    """Supported direct execution modes for a GIS city component."""

    INDEPENDENT = 'independent'
    STANDARDIZE = 'standardize'


@dataclass(frozen=True)
class GisComponentRunResult:
    """Result envelope for a GIS city component run."""

    component_name: str
    mode: GisComponentRunMode
    workflow_output_path: str
    standardized_output_path: str | None = None
    fsa: str | None = None


class GisComponentError(RuntimeError):
    """Base error for GIS component application orchestration failures."""


class GisComponentNotFoundError(GisComponentError):
    """Raised when a requested component package cannot be found."""


class GisComponentContractError(GisComponentError):
    """Raised when a component does not implement the expected interface."""


class GISCitiesApplicationService:
    """Run a jug_gis_cities component through a stable application contract."""

    _PACKAGE_NAME = 'jug_gis_cities'

    @classmethod
    def run_component(
            cls,
            component_name,
            mode=GisComponentRunMode.STANDARDIZE,
            fsa=None,
            non_null_required_fields=None):
        """Run a component workflow in independent or standardized mode.

        independent:
            Run only the component's workflow.run_workflow().

        standardize:
            Run workflow.run_workflow(), then
            contract_adapter.run_contract_adapter().
        """
        normalized_component_name = cls._normalize_component_name(
            component_name)
        normalized_mode = cls._normalize_mode(mode)
        normalized_fsa = cls._normalize_fsa(fsa)
        normalized_non_null_required_fields = (
            cls._normalize_non_null_required_fields(non_null_required_fields))

        run_t0 = perf_counter()
        logger.info(
            'Starting GIS city component. Component=%s Mode=%s FSA=%s',
            normalized_component_name,
            normalized_mode.value,
            normalized_fsa)

        try:
            cls._ensure_component_callable(
                component_name=normalized_component_name,
                module_name='workflow',
                callable_name='run_workflow')
            if normalized_mode == GisComponentRunMode.STANDARDIZE:
                cls._ensure_component_callable(
                    component_name=normalized_component_name,
                    module_name='contract_adapter',
                    callable_name='run_contract_adapter')

            workflow_runner = cls._import_component_callable(
                component_name=normalized_component_name,
                module_name='workflow',
                callable_name='run_workflow')
            workflow_output_path = cls._run_component_callable(
                runner=workflow_runner,
                component_name=normalized_component_name,
                callable_label='workflow.run_workflow',
                fsa=normalized_fsa)

            standardized_output_path = None
            if normalized_mode == GisComponentRunMode.STANDARDIZE:
                contract_adapter_runner = cls._import_component_callable(
                    component_name=normalized_component_name,
                    module_name='contract_adapter',
                    callable_name='run_contract_adapter')
                standardized_output_path = cls._run_component_callable(
                    runner=contract_adapter_runner,
                    component_name=normalized_component_name,
                    callable_label='contract_adapter.run_contract_adapter',
                    fsa=normalized_fsa,
                    optional_kwargs={
                        'non_null_required_fields':
                            normalized_non_null_required_fields,
                    })

        except GisComponentError:
            logger.exception(
                'GIS city component failed before execution completed. '
                'Component=%s Mode=%s FSA=%s',
                normalized_component_name,
                normalized_mode.value,
                normalized_fsa)
            raise
        except (TypeError, ValueError):
            logger.exception(
                'GIS city component run parameters rejected. Component=%s '
                'Mode=%s FSA=%s',
                normalized_component_name,
                normalized_mode.value,
                normalized_fsa)
            raise
        except Exception as exc:
            logger.exception(
                'GIS city component execution failed. Component=%s Mode=%s '
                'FSA=%s',
                normalized_component_name,
                normalized_mode.value,
                normalized_fsa)
            raise GisComponentError(
                'GIS city component execution failed: '
                f'{normalized_component_name} ({normalized_mode.value})'
            ) from exc

        result = GisComponentRunResult(
            component_name=normalized_component_name,
            mode=normalized_mode,
            workflow_output_path=workflow_output_path,
            fsa=normalized_fsa,
            standardized_output_path=standardized_output_path)

        logger.info(
            'Completed GIS city component. Component=%s Mode=%s '
            'FSA=%s WorkflowOutput=%s StandardizedOutput=%s Elapsed=%.3fs',
            result.component_name,
            result.mode.value,
            result.fsa,
            result.workflow_output_path,
            result.standardized_output_path,
            perf_counter() - run_t0)
        return result

    @classmethod
    def _normalize_component_name(cls, component_name):
        if not isinstance(component_name, str):
            raise TypeError('component_name must be a string.')

        normalized_component_name = component_name.strip()
        if not normalized_component_name:
            raise ValueError('component_name is required.')
        if not _COMPONENT_NAME_PATTERN.match(normalized_component_name):
            raise ValueError(
                'component_name must be a valid Python package name.')

        component_package = (
            f'{cls._PACKAGE_NAME}.{normalized_component_name}')
        if importlib.util.find_spec(component_package) is None:
            raise GisComponentNotFoundError(
                f'GIS city component not found: {normalized_component_name}')

        return normalized_component_name

    @staticmethod
    def _normalize_mode(mode):
        if isinstance(mode, GisComponentRunMode):
            return mode
        if isinstance(mode, str):
            normalized_mode = mode.strip().lower()
            try:
                return GisComponentRunMode(normalized_mode)
            except ValueError as exc:
                valid_modes = ', '.join(item.value for item in
                                        GisComponentRunMode)
                raise ValueError(
                    f'Unsupported GIS component mode: {mode}. '
                    f'Supported modes: {valid_modes}.') from exc
        raise TypeError('mode must be a string or GisComponentRunMode.')

    @staticmethod
    def _normalize_fsa(fsa):
        if fsa is None:
            return None
        if not isinstance(fsa, str):
            raise TypeError('fsa must be a string when provided.')

        normalized_fsa = fsa.strip().upper()
        if not normalized_fsa:
            return None
        if not _FSA_PATTERN.match(normalized_fsa):
            raise ValueError(
                'fsa must be a three-character Canadian FSA, for example H3H.'
            )
        return normalized_fsa

    @staticmethod
    def _normalize_non_null_required_fields(non_null_required_fields):
        if non_null_required_fields is None:
            return None
        if isinstance(non_null_required_fields, (str, bytes)):
            raise TypeError(
                'non_null_required_fields must be a list, tuple, set, '
                'or None.')

        try:
            raw_fields = list(non_null_required_fields)
        except TypeError as exc:
            raise TypeError(
                'non_null_required_fields must be a list, tuple, set, '
                'or None.') from exc

        if any(not isinstance(field_name, str) for field_name in raw_fields):
            raise TypeError(
                'non_null_required_fields must contain only strings.')

        normalized_fields = [
            field_name.strip()
            for field_name in raw_fields
        ]

        normalized_fields = [
            field_name for field_name in normalized_fields if field_name
        ]
        return normalized_fields or None

    @classmethod
    def _run_component_callable(
            cls,
            runner,
            component_name,
            callable_label,
            fsa,
            optional_kwargs=None):
        supports_fsa = cls._callable_accepts_parameter(runner, 'fsa')
        requires_fsa = cls._callable_requires_parameter(runner, 'fsa')
        optional_kwargs = optional_kwargs or {}
        supported_optional_kwargs = {
            name: value
            for name, value in optional_kwargs.items()
            if value is not None
            and cls._callable_accepts_parameter(runner, name)
        }

        if fsa is None:
            if requires_fsa:
                raise ValueError(
                    f'fsa is required for GIS city component: '
                    f'{component_name}.')
            return runner(**supported_optional_kwargs)

        if not supports_fsa:
            raise ValueError(
                f'fsa is not supported by GIS city component: '
                f'{component_name}.')
        logger.info(
            'Running GIS city component callable with FSA. Component=%s '
            'Callable=%s FSA=%s',
            component_name,
            callable_label,
            fsa)
        return runner(fsa=fsa, **supported_optional_kwargs)

    @staticmethod
    def _callable_accepts_parameter(runner, parameter_name):
        try:
            callable_signature = inspect.signature(runner)
        except (TypeError, ValueError):
            return False

        for parameter in callable_signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                return True
            if parameter.name == parameter_name:
                return True
        return False

    @staticmethod
    def _callable_requires_parameter(runner, parameter_name):
        try:
            callable_signature = inspect.signature(runner)
        except (TypeError, ValueError):
            return False

        parameter = callable_signature.parameters.get(parameter_name)
        if parameter is None:
            return False
        return (
            parameter.default is inspect.Parameter.empty
            and parameter.kind in {
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            }
        )

    @classmethod
    def _ensure_component_callable(
            cls,
            component_name,
            module_name,
            callable_name):
        module_path = f'{cls._PACKAGE_NAME}.{component_name}.{module_name}'
        module_spec = importlib.util.find_spec(module_path)
        if module_spec is None:
            raise GisComponentContractError(
                f'GIS city component {component_name} is missing '
                f'{module_name}.py.')

        cls._ensure_module_declares_callable(
            component_name=component_name,
            module_name=module_name,
            module_path=module_path,
            module_spec=module_spec,
            callable_name=callable_name)

    @classmethod
    def _import_component_callable(
            cls,
            component_name,
            module_name,
            callable_name):
        module_path = f'{cls._PACKAGE_NAME}.{component_name}.{module_name}'
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            if exc.name == module_path:
                raise GisComponentContractError(
                    f'GIS city component {component_name} is missing '
                    f'{module_name}.py.') from exc
            raise

        runner = getattr(module, callable_name, None)
        if runner is None or not callable(runner):
            raise GisComponentContractError(
                f'GIS city component {component_name}.{module_name} must '
                f'define callable {callable_name}().')
        return runner

    @staticmethod
    def _ensure_module_declares_callable(
            component_name,
            module_name,
            module_path,
            module_spec,
            callable_name):
        module_origin = getattr(module_spec, 'origin', None)
        if not module_origin or not module_origin.endswith('.py'):
            logger.debug(
                'Skipping static callable inspection for module %s. '
                'Origin=%s',
                module_path,
                module_origin)
            return

        try:
            with open(module_origin, encoding='utf-8') as module_file:
                module_tree = ast.parse(
                    module_file.read(),
                    filename=module_origin)
        except OSError as exc:
            raise GisComponentContractError(
                f'Unable to inspect GIS city component module: {module_path}'
            ) from exc

        for node in module_tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == callable_name:
                    return

        raise GisComponentContractError(
            f'GIS city component {component_name}.{module_name} must define '
            f'callable {callable_name}().')
