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
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping

import pandas as pd
from sabu_chassis.logging import get_logger

from jug_gis_validation.domain_validation.validate_gisoo import (
    DEFAULT_CENSUS_DATA_CSV,
    ValidateGISOO,
)
from jug_gis_validation.errors import GISValidationError


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


@dataclass(frozen=True)
class GISValidationRunResult:
    """Result envelope for a GISOO validation run."""

    validator: ValidateGISOO
    codes: tuple[str, ...]
    comparison_table: dict[str, Any]
    comparison_dataframe: pd.DataFrame
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
            census_avg_area_by_type: Mapping[str, float] | None = None,
            output_mode=GISValidationOutputMode.CONSOLE,
            district_name=DEFAULT_DISTRICT_NAME,
            output_dir=DEFAULT_OUTPUT_DIR,
            csv_path=None,
            include_plot=False,
            plot_path=None,
            plot_title=None,
            console_writer: Callable[[str], None] = print,
    ) -> GISValidationRunResult:
        """Run validation and optionally write console, CSV, and plot outputs."""
        normalized_output_mode = cls._normalize_output_mode(output_mode)
        normalized_census_avg_area = cls._normalize_census_avg_area(
            census_avg_area_by_type)

        run_t0 = perf_counter()
        logger.info(
            'Starting GISOO validation. OutputMode=%s IncludePlot=%s',
            normalized_output_mode.value,
            include_plot or plot_path is not None)

        try:
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
                height_key=height_key)

            codes = validator.district_codes
            comparison_table = validator.comparison_table(codes)
            comparison_dataframe = pd.DataFrame(comparison_table)

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
                resolved_plot_path = cls._resolve_plot_path(
                    plot_path=plot_path,
                    output_dir=output_dir,
                    district_name=district_name)
                resolved_plot_path.parent.mkdir(parents=True, exist_ok=True)
                fig, _ = validator.plot_area_comparison(
                    codes_info=comparison_dataframe['FSA'],
                    areas=(
                        comparison_dataframe[
                            'Cleaned Total Area (with proxy)']),
                    census_areas=(
                        comparison_dataframe['Census Total Area (by type)']),
                    title=plot_title or f'Area comparison - {district_name}',
                    y_label='Area (m^2)',
                    x_label='Processed')
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
            csv_path=resolved_csv_path,
            plot_path=resolved_plot_path)

        logger.info(
            'Completed GISOO validation. DistrictCodes=%s CsvPath=%s '
            'PlotPath=%s Elapsed=%.3fs',
            len(result.codes),
            result.csv_path,
            result.plot_path,
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
