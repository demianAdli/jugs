"""
Sabu project
jug_gis_validation project
jug_gis_validation package
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
https://demianadli.com/

Application-layer orchestration for GISOO validation.

This module follows the interactive validation notebook workflow and exposes
it through a stable direct-Python service boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping

import pandas as pd
from sabu_chassis.logging import get_logger

from jug_gis_validation.domain_validation.validate_gisoo import (
    AreaCalculationMode,
    DEFAULT_CENSUS_DATA_CSV,
    HeightProxyAreaResolutionStats,
    ValidateGISOO,
)
from jug_gis_validation.domain_validation.uniquify_features import (
    FeatureUniquificationStats,
)
from jug_gis_validation.errors import (
    GISValidationError,
    GISValidationInputError,
)


logger = get_logger(__name__)

DEFAULT_CENSUS_CODE_FIELD_TITLE = 'ALT_GEO_CODE'
DEFAULT_CENSUS_UNITS_NUM_TITLE = 'C1_COUNT_TOTAL'
DEFAULT_POSTAL_CODE_KEY = 'fsa'
DEFAULT_FUNCTION_KEY = 'function'
DEFAULT_FUNCTION_VALUE = '1000'
DEFAULT_AREA_KEY = 'area'
DEFAULT_FLOOR_NUM_KEY = 'floor_num'
DEFAULT_HEIGHT_KEY = 'height'
DEFAULT_DISTRICT_NAME = 'validation'
DEFAULT_OUTPUT_DIR = 'output_files'

NOTEBOOK_CENSUS_AVG_AREA_BY_TYPE = {
    'Single-detached house': 160.0,
    'Semi-detached house': 160.0,
    'Row house': 120.0,
    'Apartment or flat in a duplex': 95.0,
    'Apartment in a building that has fewer than five storeys': 95.0,
    'Apartment in a building that has five or more storeys': 95.0,
    'Other single-attached house': 95.0,
    'Movable dwelling': 95.0,
    'Remaining dwellings': 0.0,
}


class GISValidationOutputMode(str, Enum):
    """Supported comparison-table output modes."""

    NONE = 'none'
    CONSOLE = 'console'
    CSV = 'csv'
    CONSOLE_AND_CSV = 'console-and-csv'


class GISValidationPlotMetric(str, Enum):
    """Metrics supported by the comparison plot."""

    AREA = 'area'
    UNITS = 'units'


@dataclass(frozen=True)
class GISValidationRunResult:
    """Result envelope for a GISOO validation run."""

    validator: ValidateGISOO
    codes: tuple[str, ...]
    comparison_table: dict[str, Any]
    comparison_dataframe: pd.DataFrame
    uniquification_stats: FeatureUniquificationStats
    area_calculation_mode: AreaCalculationMode
    height_proxy_included: bool
    height_proxy_area_key: str | None
    height_proxy_area_resolution_stats: (
        HeightProxyAreaResolutionStats | None)
    uniquified_output_path: Path | None = None
    csv_path: Path | None = None
    plot_path: Path | None = None


class GISValidationApplicationService:
    """Run a complete GISOO validation workflow."""

    @classmethod
    def run_validation(
            cls,
            buildings_set,
            *,
            census_data_csv=DEFAULT_CENSUS_DATA_CSV,
            census_code_field_title=DEFAULT_CENSUS_CODE_FIELD_TITLE,
            census_units_num_title=DEFAULT_CENSUS_UNITS_NUM_TITLE,
            postal_code_key=DEFAULT_POSTAL_CODE_KEY,
            function_key=DEFAULT_FUNCTION_KEY,
            function_value=DEFAULT_FUNCTION_VALUE,
            area_key=DEFAULT_AREA_KEY,
            floor_num_key=DEFAULT_FLOOR_NUM_KEY,
            height_key=DEFAULT_HEIGHT_KEY,
            unique_attribute_key=None,
            uniquification_area_key=None,
            cleaned_units_num_key=None,
            area_calculation_mode=AreaCalculationMode.AREA_TIMES_FLOOR,
            include_height_proxy=False,
            height_proxy_area_key=None,
            height_proxy_area_fallback_key=None,
            height_proxy_area_fallback_value=None,
            uniquified_output_path=None,
            census_avg_area_by_type: Mapping[str, float] | None = None,
            output_mode=GISValidationOutputMode.CONSOLE,
            district_name=DEFAULT_DISTRICT_NAME,
            output_dir=DEFAULT_OUTPUT_DIR,
            csv_path=None,
            include_plot=False,
            plot_path=None,
            plot_title=None,
            plot_metric=GISValidationPlotMetric.AREA,
            console_writer: Callable[[str], None] = print,
    ) -> GISValidationRunResult:
        """Run validation and optionally write console, CSV, and plot outputs."""
        normalized_output_mode = cls._normalize_output_mode(output_mode)
        normalized_plot_metric = cls._normalize_plot_metric(plot_metric)
        normalized_area_calculation_mode = AreaCalculationMode.normalize(
            area_calculation_mode)
        if (
                normalized_area_calculation_mode is AreaCalculationMode.NONE
                and include_height_proxy):
            raise ValueError(
                'include_height_proxy cannot be enabled when '
                'area_calculation_mode is none.')
        if (
                height_proxy_area_fallback_key is not None
                and height_proxy_area_fallback_value is not None):
            raise ValueError(
                'height_proxy_area_fallback_key and '
                'height_proxy_area_fallback_value are mutually exclusive.')
        normalized_height_proxy_area_fallback_value = None
        if height_proxy_area_fallback_value is not None:
            try:
                normalized_height_proxy_area_fallback_value = float(
                    height_proxy_area_fallback_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    'height_proxy_area_fallback_value must be numeric.') from exc
            if (
                    not math.isfinite(
                        normalized_height_proxy_area_fallback_value)
                    or normalized_height_proxy_area_fallback_value <= 0):
                raise ValueError(
                    'height_proxy_area_fallback_value must be finite and '
                    'greater than zero.')
        normalized_census_avg_area = cls._normalize_census_avg_area(
            census_avg_area_by_type)

        run_t0 = perf_counter()
        logger.info(
            'Starting GISOO validation. OutputMode=%s IncludePlot=%s',
            normalized_output_mode.value,
            include_plot or plot_path is not None)

        try:
            if (
                    uniquified_output_path is not None
                    and unique_attribute_key is None):
                raise GISValidationInputError(
                    'uniquified_output_path requires unique_attribute_key.')

            validator = ValidateGISOO(
                buildings_set,
                census_code_field_title,
                census_units_num_title,
                postal_code_key,
                function_key,
                function_value,
                area_key,
                floor_num_key,
                census_data_csv=census_data_csv,
                census_avg_area_by_type=normalized_census_avg_area,
                height_key=height_key,
                unique_attribute_key=unique_attribute_key,
                uniquification_area_key=uniquification_area_key,
                cleaned_units_num_key=cleaned_units_num_key,
                area_calculation_mode=normalized_area_calculation_mode,
                include_height_proxy=include_height_proxy,
                height_proxy_area_key=height_proxy_area_key,
                height_proxy_area_fallback_key=(
                    height_proxy_area_fallback_key),
                height_proxy_area_fallback_value=(
                    normalized_height_proxy_area_fallback_value))

            codes = validator.district_codes
            comparison_table = validator.comparison_table(codes)
            comparison_dataframe = pd.DataFrame(comparison_table)

            resolved_uniquified_output_path = None
            if uniquified_output_path is not None:
                resolved_uniquified_output_path = (
                    cls._write_uniquified_output(
                        validator.validation_features,
                        uniquified_output_path,
                        source=buildings_set))

            if normalized_output_mode in (
                    GISValidationOutputMode.CONSOLE,
                    GISValidationOutputMode.CONSOLE_AND_CSV):
                console_writer(comparison_dataframe.to_string(index=False))

            resolved_csv_path = None
            if (
                    normalized_output_mode in (
                        GISValidationOutputMode.CSV,
                        GISValidationOutputMode.CONSOLE_AND_CSV)
                    or csv_path is not None):
                resolved_csv_path = cls._resolve_csv_path(
                    csv_path=csv_path,
                    output_dir=output_dir,
                    district_name=district_name)
                resolved_csv_path.parent.mkdir(parents=True, exist_ok=True)
                comparison_dataframe.to_csv(resolved_csv_path, index=False)
                logger.info('GISOO comparison CSV written: %s',
                            resolved_csv_path)

            resolved_plot_path = None
            if include_plot or plot_path is not None:
                if (
                        normalized_plot_metric is GISValidationPlotMetric.AREA
                        and normalized_area_calculation_mode
                        is AreaCalculationMode.NONE):
                    raise GISValidationInputError(
                        'Area plots are unavailable when '
                        'area_calculation_mode is none. Use the units plot '
                        'metric or enable an area calculation mode.')
                resolved_plot_path = cls._resolve_plot_path(
                    plot_path=plot_path,
                    output_dir=output_dir,
                    district_name=district_name)
                resolved_plot_path.parent.mkdir(parents=True, exist_ok=True)
                if normalized_plot_metric is GISValidationPlotMetric.UNITS:
                    cleaned_column = 'Cleaned Units Num'
                    census_column = 'Census Units Num'
                    default_title = f'Unit comparison - {district_name}'
                    y_label = 'Number of units'
                else:
                    cleaned_column = 'Cleaned Total Area'
                    census_column = 'Census Total Area (by type)'
                    default_title = f'Area comparison - {district_name}'
                    y_label = 'Area (m^2)'

                fig, _ = validator.plot_area_comparison(
                    codes_info=comparison_dataframe['FSA'],
                    areas=comparison_dataframe[cleaned_column],
                    census_areas=comparison_dataframe[census_column],
                    title=plot_title or default_title,
                    y_label=y_label,
                    x_label='Cleaned')
                fig.savefig(resolved_plot_path, dpi=150)
                logger.info('GISOO comparison plot written: %s',
                            resolved_plot_path)

        except GISValidationError:
            logger.exception('GISOO validation failed.')
            raise
        except Exception as exc:
            logger.exception('Unexpected GISOO validation failure.')
            raise GISValidationError(
                'Unexpected GISOO validation failure.') from exc

        result = GISValidationRunResult(
            validator=validator,
            codes=codes,
            comparison_table=comparison_table,
            comparison_dataframe=comparison_dataframe,
            uniquification_stats=validator.uniquification_stats,
            area_calculation_mode=validator.area_calculation_mode,
            height_proxy_included=validator.include_height_proxy,
            height_proxy_area_key=(
                validator.height_proxy_area_key
                if validator.include_height_proxy
                else None),
            height_proxy_area_resolution_stats=(
                validator.height_proxy_area_resolution_stats),
            uniquified_output_path=resolved_uniquified_output_path,
            csv_path=resolved_csv_path,
            plot_path=resolved_plot_path)

        logger.info(
            'Completed GISOO validation. DistrictCodes=%s CsvPath=%s '
            'PlotPath=%s UniquifiedOutputPath=%s Elapsed=%.3fs',
            len(result.codes),
            result.csv_path,
            result.plot_path,
            result.uniquified_output_path,
            perf_counter() - run_t0)
        return result

    @staticmethod
    def _normalize_output_mode(output_mode) -> GISValidationOutputMode:
        if isinstance(output_mode, GISValidationOutputMode):
            return output_mode
        if isinstance(output_mode, str):
            normalized_output_mode = output_mode.strip().lower()
            try:
                return GISValidationOutputMode(normalized_output_mode)
            except ValueError as exc:
                valid_modes = ', '.join(
                    item.value for item in GISValidationOutputMode)
                raise ValueError(
                    f'Unsupported GIS validation output mode: {output_mode}. '
                    f'Supported modes: {valid_modes}.') from exc
        raise TypeError(
            'output_mode must be a string or GISValidationOutputMode.')

    @staticmethod
    def _normalize_plot_metric(plot_metric) -> GISValidationPlotMetric:
        if isinstance(plot_metric, GISValidationPlotMetric):
            return plot_metric
        if isinstance(plot_metric, str):
            normalized_plot_metric = plot_metric.strip().lower()
            try:
                return GISValidationPlotMetric(normalized_plot_metric)
            except ValueError as exc:
                valid_metrics = ', '.join(
                    item.value for item in GISValidationPlotMetric)
                raise ValueError(
                    f'Unsupported GIS validation plot metric: {plot_metric}. '
                    f'Supported metrics: {valid_metrics}.') from exc
        raise TypeError(
            'plot_metric must be a string or GISValidationPlotMetric.')

    @staticmethod
    def _normalize_census_avg_area(
            census_avg_area_by_type: Mapping[str, float] | None):
        if not census_avg_area_by_type:
            return None
        return dict(census_avg_area_by_type)

    @staticmethod
    def _resolve_csv_path(csv_path, output_dir, district_name) -> Path:
        if csv_path is not None:
            return Path(csv_path)
        return Path(output_dir) / f'validate_{district_name}_gisoo.csv'

    @staticmethod
    def _resolve_plot_path(plot_path, output_dir, district_name) -> Path:
        if plot_path is not None:
            return Path(plot_path)
        return Path(output_dir) / f'{district_name}_area_comparison.png'

    @staticmethod
    def _write_uniquified_output(
            validation_features,
            output_path,
            *,
            source=None) -> Path:
        resolved_path = Path(output_path)
        if resolved_path.suffix.lower() not in {'.geojson', '.json'}:
            raise GISValidationInputError(
                'uniquified_output_path must end with .geojson or .json.')
        if isinstance(source, (str, Path)):
            source_text = str(source).strip()
            if (
                    not source_text.startswith(('{', '['))
                    and Path(source).resolve() == resolved_path.resolve()):
                raise GISValidationInputError(
                    'uniquified_output_path must not overwrite the input '
                    'buildings_set path.')
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            validation_features.to_file(
                resolved_path,
                driver='GeoJSON',
                index=False)
        except Exception as exc:
            raise GISValidationError(
                f'Unable to write uniquified GeoJSON: {resolved_path}') from exc
        logger.info('Uniquified validation GeoJSON written: %s', resolved_path)
        return resolved_path
