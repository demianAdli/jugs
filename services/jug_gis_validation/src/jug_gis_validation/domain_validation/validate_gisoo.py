"""
Sabu project
jug_gis_validation project
jug_gis_validation package
validate_gisoo module
ValidateGISOO class supports an interactove workflow
to validate cleaned geospatial data.
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
https://demianadli.com/
Update considerations:
- Python>=3.8 need to be added to the requirements.
"""

from __future__ import annotations

import json
from functools import cached_property
from importlib.resources import as_file, files
from os import PathLike
from pathlib import Path
from typing import Any

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from sabu_chassis.logging import get_logger

from jug_gis_validation.errors import (
  GISValidationCalculationError,
  GISValidationDataContractError,
  GISValidationInputError,
)
from .query_census_data_csv import QueryCensusDataCSV
from .district_geojson_analysis import DistrictGeoJSONAnalysis


logger = get_logger(__name__)
DEFAULT_CENSUS_RESOURCE = 'filtered_census.csv'
DEFAULT_CENSUS_DATA_CSV = f'data/{DEFAULT_CENSUS_RESOURCE}'


class ValidateGISOO:
  def __init__(self, buildings_set,
               census_code_field_title, census_units_num_title,
               postal_code_key, function_key, function_value,
               area_key, floor_num_key,
               census_data_csv=DEFAULT_CENSUS_DATA_CSV,
               census_avg_area_by_type=None,
               height_key='height'):
    # Configuration
    self.postal_code_key = postal_code_key
    self.function_key = function_key
    self.function_value = function_value
    self.area_key = area_key
    self.floor_num_key = floor_num_key
    self.height_key = height_key
    self.census_code_field_title = census_code_field_title
    self.census_units_num_title = census_units_num_title

    # Clean District Data
    self._load_district, self._buildings_source = self._load_buildings_set(
      buildings_set)
    self._ensure_columns(
      self._load_district,
      self._required_district_columns(),
      'buildings_set')
    self._district = DistrictGeoJSONAnalysis(self._load_district)

    district_codes = self._district.return_all_codes(self.postal_code_key)
    self._district_codes = list(district_codes)
    if "Non" in self._district_codes:
      self._district_codes.remove("Non")

    # Validation Data
    self._load_census_data, self._census_source = self._load_census_data_csv(
      census_data_csv)

    self._census_data = QueryCensusDataCSV(
      self._load_census_data,
      self.census_code_field_title,
      self.census_units_num_title,
      area_by_characteristic=census_avg_area_by_type
    )

    missing_census_codes = sorted(
      set(self._district_codes) - set(self._census_data.units_num.index))
    if missing_census_codes:
      logger.warning(
        'Census data is missing %s district code(s). Sample=%s',
        len(missing_census_codes),
        missing_census_codes[:10])

    if not self._district_codes:
      logger.warning('No district codes were found in buildings_set.')

    logger.info(
      'Initialized GISOO validator. BuildingsSource=%s CensusSource=%s '
      'Features=%s DistrictCodes=%s',
      self._buildings_source,
      self._census_source,
      len(self._load_district),
      len(self._district_codes))

  @staticmethod
  def _load_buildings_set(buildings_set) -> tuple[gpd.GeoDataFrame, str]:
    if isinstance(buildings_set, gpd.GeoDataFrame):
      return buildings_set.copy(), 'geodataframe'

    if isinstance(buildings_set, dict):
      return ValidateGISOO._geojson_to_geodataframe(
        buildings_set), 'geojson-dict'

    if isinstance(buildings_set, list):
      return ValidateGISOO._geojson_to_geodataframe(
        buildings_set), 'feature-list'

    if hasattr(buildings_set, 'read'):
      try:
        raw_content = buildings_set.read()
      except Exception as exc:
        raise GISValidationInputError(
          'Unable to read buildings_set file-like object.') from exc
      return (
        ValidateGISOO._geojson_text_to_geodataframe(raw_content),
        'file-like')

    if isinstance(buildings_set, (str, PathLike)):
      if isinstance(buildings_set, str):
        candidate_text = buildings_set.strip()
        if candidate_text.startswith(('{', '[')):
          return (
            ValidateGISOO._geojson_text_to_geodataframe(candidate_text),
            'geojson-string')

      path = Path(buildings_set).expanduser()
      if not path.exists():
        raise GISValidationInputError(
          f'buildings_set path does not exist: {path}')

      try:
        return gpd.read_file(path), f'path:{path}'
      except Exception as exc:
        raise GISValidationInputError(
          f'Unable to read buildings_set GeoJSON file: {path}') from exc

    raise GISValidationInputError(
      'buildings_set must be a GeoDataFrame, GeoJSON dict/string, feature '
      'list, file-like object, or path to a GeoJSON file.')

  @staticmethod
  def _geojson_text_to_geodataframe(raw_content) -> gpd.GeoDataFrame:
    if isinstance(raw_content, bytes):
      raw_content = raw_content.decode('utf-8')

    if not isinstance(raw_content, str):
      raise GISValidationInputError(
        'GeoJSON file-like content must be text or bytes.')

    try:
      geojson_obj = json.loads(raw_content)
    except json.JSONDecodeError as exc:
      raise GISValidationInputError(
        'buildings_set content is not valid GeoJSON JSON text.') from exc

    return ValidateGISOO._geojson_to_geodataframe(geojson_obj)

  @staticmethod
  def _geojson_to_geodataframe(geojson_obj: Any) -> gpd.GeoDataFrame:
    if isinstance(geojson_obj, dict):
      geojson_type = geojson_obj.get('type')
      if geojson_type == 'FeatureCollection':
        features = geojson_obj.get('features')
      elif geojson_type == 'Feature':
        features = [geojson_obj]
      else:
        raise GISValidationInputError(
          'GeoJSON object must be a FeatureCollection or Feature.')
    elif isinstance(geojson_obj, list):
      features = geojson_obj
    else:
      raise GISValidationInputError(
        'GeoJSON content must be a FeatureCollection, Feature, or feature list.')

    if not isinstance(features, list):
      raise GISValidationInputError('GeoJSON features must be a list.')

    try:
      return gpd.GeoDataFrame.from_features(features)
    except Exception as exc:
      raise GISValidationInputError(
        'Unable to convert buildings_set GeoJSON features to a GeoDataFrame.'
      ) from exc

  @staticmethod
  def _load_census_data_csv(census_data_csv) -> tuple[pd.DataFrame, str]:
    if isinstance(census_data_csv, pd.DataFrame):
      return census_data_csv.copy(), 'dataframe'

    read_kwargs = {
      'encoding': 'cp1252',
      'encoding_errors': 'replace',
      'low_memory': False,
    }

    if (
      census_data_csv is None
      or (
        isinstance(census_data_csv, str)
        and census_data_csv in (DEFAULT_CENSUS_DATA_CSV,
                                DEFAULT_CENSUS_RESOURCE)
      )
    ):
      resource = files('jug_gis_validation.data').joinpath(
        DEFAULT_CENSUS_RESOURCE)
      try:
        with as_file(resource) as census_path:
          return pd.read_csv(census_path, **read_kwargs), (
            f'packaged:{DEFAULT_CENSUS_RESOURCE}')
      except FileNotFoundError as exc:
        raise GISValidationInputError(
          f'Packaged census data is missing: {DEFAULT_CENSUS_RESOURCE}'
        ) from exc
      except Exception as exc:
        raise GISValidationInputError(
          f'Unable to read packaged census data: {DEFAULT_CENSUS_RESOURCE}'
        ) from exc

    if hasattr(census_data_csv, 'read'):
      try:
        return pd.read_csv(census_data_csv, **read_kwargs), 'file-like'
      except Exception as exc:
        raise GISValidationInputError(
          'Unable to read census_data_csv file-like object.') from exc

    path = Path(census_data_csv).expanduser()
    if not path.exists():
      raise GISValidationInputError(
        f'census_data_csv path does not exist: {path}')

    try:
      return pd.read_csv(path, **read_kwargs), f'path:{path}'
    except Exception as exc:
      raise GISValidationInputError(
        f'Unable to read census_data_csv file: {path}') from exc

  def _required_district_columns(self):
    required_columns = [
      self.postal_code_key,
      self.area_key,
      self.floor_num_key,
    ]
    if self.function_key is not None:
      required_columns.append(self.function_key)
    return required_columns

  @staticmethod
  def _ensure_columns(dataframe, required_columns, dataset_name):
    missing_columns = [
      column for column in required_columns
      if column and column not in dataframe.columns
    ]
    if missing_columns:
      raise GISValidationDataContractError(
        f'{dataset_name} is missing required column(s): '
        f'{", ".join(missing_columns)}')

  def _ensure_code(self, code, dataset):
    if code not in dataset:
      raise GISValidationDataContractError(
        f'District code is not available in validation results: {code}')

  @property
  def district_codes(self):
    """FSA codes present in the district (no 'Non')."""
    # immutable -> no changes in the workflow
    return tuple(self._district_codes)

  @cached_property
  def _codes_info(self):
    """
    Internal cached (info, nones_info) for height-from-floor_num workflow.

    info: dict[FSA] -> (units_num, total_area)
    nones_info: tuple(units_num_with_None_or_zero, area_with_None_or_zero)
    """
    logger.debug('Computing district code summaries with floor number.')
    try:
      info = self._district.summarize_all_codes_dict(
        postal_code_key=self.postal_code_key,
        return_key=self.area_key,
        floor_num_key=self.floor_num_key,
        codes=self._district_codes,
        prefix_len=3,
        function_key=self.function_key,
        function_value=self.function_value,
      )
    except GISValidationDataContractError:
      raise
    except Exception as exc:
      raise GISValidationCalculationError(
        'Unable to summarize district codes with floor number.') from exc

    nones_info = (0, 0)
    if "Non" in info:
      nones_info = info.pop("Non")
      logger.warning(
        'District summary contains features with missing/nonstandard code. '
        'Units=%s Area=%s',
        nones_info[0],
        nones_info[1])

    return info, nones_info

  @property
  def district_codes_info(self):
    """dict[FSA] -> (units_num, total_area) using floor_num."""
    return self._codes_info[0]

  @property
  def district_nones(self):
    """(units_with_none_or_zero, area_with_none_or_zero)
    For floor_num workflow.
    """
    return self._codes_info[1]

  @cached_property
  def _codes_info_proxy(self):
    """
    Internal cached (info, nones_info) for height-to-floor proxy workflow.
    """
    logger.debug('Computing district code summaries with height proxy.')
    self._ensure_columns(self._load_district, [self.height_key],
                         'buildings_set')
    try:
      proxy_info = self._district.height_to_floor_proxy(self.height_key, 3.5)
      multipliers, num_nones, pct_nones, num_zeros, pct_zeros = proxy_info
      if num_nones or num_zeros:
        logger.warning(
          'Height proxy contains missing or zero values. '
          'Missing=%s MissingPct=%.2f Zero=%s ZeroPct=%.2f',
          num_nones,
          pct_nones,
          num_zeros,
          pct_zeros)
      info = self._district.summarize_all_codes_with_multipliers(
        postal_code_key=self.postal_code_key,
        return_key=self.area_key,
        multipliers=multipliers,
        codes=self._district_codes,
        prefix_len=3,
        function_key=self.function_key,
        function_value=self.function_value,
      )
    except GISValidationDataContractError:
      raise
    except Exception as exc:
      raise GISValidationCalculationError(
        'Unable to summarize district codes with height proxy.') from exc

    nones_info = (0, 0)
    if 'Non' in info:
      nones_info = info.pop('Non')
      logger.warning(
        'Height proxy summary contains features with missing/nonstandard code. '
        'Units=%s Area=%s',
        nones_info[0],
        nones_info[1])

    return info, nones_info

  @cached_property
  def census_total_area_all_dict(self):
    areas = self._census_data.total_area.reindex(self._district_codes)
    missing = sorted(areas[areas.isna()].index.tolist())
    if missing:
      logger.warning(
        'Census total area is missing for %s district code(s). Sample=%s',
        len(missing),
        missing[:10])
    return areas.to_dict()

  @property
  def district_codes_info_proxy(self):
    """dict[FSA] -> (units_num, total_area) using height-to-floor proxy."""
    return self._codes_info_proxy[0]

  @property
  def district_nones_proxy(self):
    """(units_with_none_or_zero, area_with_none_or_zero) for proxy workflow."""
    return self._codes_info_proxy[1]

  @cached_property
  def census_units_num_all_dict(self):
    """
    dict[FSA] -> census units count, reindexed to district_codes.
    Uses the units rule:
      - if remaining_dwellings != 0 => Total private dwellings
      - else => Total - Private households by household size - 100% data
    """
    units_num = self._census_data.units_num.reindex(self._district_codes).fillna(0)
    return units_num.to_dict()

  def calculate_codes_unit_frequency_percentage(self):
    district_total_units = sum(
      [index[0] for index in self.district_codes_info.values()])
    if district_total_units == 0:
      raise GISValidationCalculationError(
        'Cannot calculate unit frequency percentages because total district '
        'units is zero.')
    return {code: self.district_codes_info[code][0] * 100 / district_total_units
            for code in self.district_codes_info.keys()}

  def calculate_codes_area_frequency_percentage(self):
    district_total_area = sum(
      [index[1] for index in self.district_codes_info.values()])
    if district_total_area == 0:
      raise GISValidationCalculationError(
        'Cannot calculate area frequency percentages because total district '
        'area is zero.')
    return {code: self.district_codes_info[code][1] * 100 / district_total_area
            for code in self.district_codes_info.keys()}

  def clean_district_vs_census_unit(self, code):
    self._ensure_code(code, self.district_codes_info)
    self._ensure_code(code, self.census_units_num_all_dict)
    clean_district_unit = self.district_codes_info[code][0]
    difference = clean_district_unit - self.census_units_num_all_dict[code]
    if clean_district_unit == 0:
      difference_ratio = 0
    else:
      difference_ratio = abs(difference) * 100 / clean_district_unit
    return difference, difference_ratio

  def clean_districts_vs_census_unit(self, codes=None):
    if codes is None:
      codes = self.district_codes

    all_differences_unit = dict()
    for code in codes:
      all_differences_unit[code] = self.clean_district_vs_census_unit(code)
    return all_differences_unit

  def clean_district_and_census_unit(self, code):
    self._ensure_code(code, self.district_codes_info)
    self._ensure_code(code, self.census_units_num_all_dict)
    return self.district_codes_info[code][0],\
        self.census_units_num_all_dict[code]

  def clean_districts_and_census_unit(self, codes=None):
    if codes is None:
      codes = self.district_codes

    both_units = dict()
    for code in codes:
      both_units[code] = self.clean_district_and_census_unit(code)
    return both_units

  def clean_district_vs_census_area(self, code):
    self._ensure_code(code, self.district_codes_info)
    self._ensure_code(code, self.census_total_area_all_dict)
    clean_district_area = self.district_codes_info[code][1]
    census_units_to_area = self.census_total_area_all_dict[code]
    if pd.isna(census_units_to_area) or census_units_to_area == 0:
      raise GISValidationCalculationError(
        f'Cannot calculate area ratio for {code} because census total area '
        'is missing or zero.')
    difference = clean_district_area - census_units_to_area
    difference_ratio = abs(difference) * 100 / census_units_to_area
    return round(difference, 2), difference_ratio

  def clean_districts_vs_census_area(self, codes=None):
    if codes is None:
      codes = self.district_codes

    all_differences_area = dict()
    for code in codes:
      all_differences_area[code] = \
        self.clean_district_vs_census_area(code)
    return all_differences_area

  def clean_district_and_census_area(self, code):
    self._ensure_code(code, self.district_codes_info)
    self._ensure_code(code, self.census_total_area_all_dict)
    return self.district_codes_info[code][1],\
           self.census_total_area_all_dict[code]

  def clean_districts_and_census_area(self, codes=None):
    if codes is None:
      codes = self.district_codes

    both_areas = dict()
    for code in codes:
      both_areas[code] = \
        self.clean_district_and_census_area(code)
    return both_areas

  @staticmethod
  def plot_area_comparison(
          codes_info,
          areas,
          census_areas,
          *,
          title='Area comparison',
          y_label='Area (m²)',
          x_label=''
  ):
    if not (len(codes_info) == len(areas) == len(census_areas)):
      raise ValueError('codes, areas, and census_areas must have the same length')

    n = len(codes_info)
    x = np.arange(n)
    width = 0.39

    fig, ax = plt.subplots(figsize=(max(5.0, n * 1.2), 4.5))
    rects1 = ax.bar(x - width / 2, areas, width, label=x_label)
    rects2 = ax.bar(x + width / 2, census_areas, width, label='Census')

    ax.set_xlabel('Code')
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xticks(x, codes_info)
    ax.legend()

    # Format y-axis with thousands separators
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{int(v):,}'))
    fig.tight_layout()
    return fig, ax

  def comparison_table(self, codes) -> dict:
    return {'FSA': codes,
            'Cleaned Units Num':
              [self.district_codes_info[code][0] for code in codes],
            'Census Units Num':
              [self.census_units_num_all_dict[code] for code in codes],
            'Cleaned vs. Census Units':
              [value[0] for value in
               self.clean_districts_vs_census_unit(codes).values()],
            'Cleaned Total Area':
              [self.district_codes_info_proxy[code][1] for code in codes],
            'Cleaned Total Area (with proxy)':
              [self.district_codes_info[code][1] for code in codes],
            'Census Total Area (by type)':
              [self.census_total_area_all_dict[code] for code in codes],
            }

  def comparison_csv(self, codes, distric_name):
    comparison_df = pd.DataFrame(self.comparison_table(codes))
    comparison_df.to_csv(f'validate_{distric_name}_gi.csv', index=False)
