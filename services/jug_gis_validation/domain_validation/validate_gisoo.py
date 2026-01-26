"""
JUGS project
jug_gis project
jug_gis package
validate_gisoo module
ValidateGISOO class supports an interactove workflow
to validate cleaned geospatial data.
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca

Update considerations:
- Python>=3.8 need to be added to the requirements.
"""

from pathlib import Path
from functools import cached_property

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from .query_census_data_csv import QueryCensusDataCSV
from .district_geojson_analysis import DistrictGeoJSONAnalysis


class ValidateGISOO:
  def __init__(self, census_data_csv, district_data_geojson,
               census_code_field_title, census_units_num_title,
               postal_code_key, function_key, function_value,
               area_key, floor_num_key,
               census_avg_area_by_type=None):
    base_dir = Path(__file__).resolve().parent.parent

    the_district_path = base_dir / 'input_files' / district_data_geojson
    census_data_path = base_dir / 'input_files' / census_data_csv

    # Configuration
    self.postal_code_key = postal_code_key
    self.function_key = function_key
    self.function_value = function_value
    self.area_key = area_key
    self.floor_num_key = floor_num_key
    self.census_code_field_title = census_code_field_title
    self.census_units_num_title = census_units_num_title

    # Clean District Data
    self._load_district = gpd.read_file(the_district_path)
    self._district = DistrictGeoJSONAnalysis(self._load_district)

    district_codes = self._district.return_all_codes(self.postal_code_key)
    self._district_codes = list(district_codes)
    if "Non" in self._district_codes:
      self._district_codes.remove("Non")

    # Validation Data
    self._load_census_data = pd.read_csv(
      census_data_path,
      encoding="cp1252",
      encoding_errors="replace",
      low_memory=False)

    self._census_data = QueryCensusDataCSV(
      self._load_census_data,
      self.census_code_field_title,
      self.census_units_num_title,
      area_by_characteristic=census_avg_area_by_type,
      normalize_whitespace=True,
    )

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
    info = self._district.summarize_all_codes_dict(
      postal_code_key=self.postal_code_key,
      return_key=self.area_key,
      floor_num_key=self.floor_num_key,
      codes=self._district_codes,
      prefix_len=3,
      function_key=self.function_key,
      function_value=self.function_value,
    )

    nones_info = (0, 0)
    if "Non" in info:
      nones_info = info.pop("Non")

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
    multipliers = self._district.height_to_floor_proxy('height', 3.5)[0]
    info = self._district.summarize_all_codes_with_multipliers(
      postal_code_key=self.postal_code_key,
      return_key=self.area_key,
      multipliers=multipliers,
      codes=self._district_codes,
      prefix_len=3,
      function_key=self.function_key,
      function_value=self.function_value,
    )

    nones_info = (0, 0)
    if 'Non' in info:
      nones_info = info.pop('Non')

    return info, nones_info

  @cached_property
  def census_total_area_all_dict(self):
    areas = self._census_data.total_area.reindex(self._district_codes)
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
    district_total_area = sum(
      [index[0] for index in self.district_codes_info.values()])
    return {code: self.district_codes_info[code][0] * 100 / district_total_area
            for code in self.district_codes_info.keys()}

  def calculate_codes_area_frequency_percentage(self):
    district_total_area = sum(
      [index[1] for index in self.district_codes_info.values()])
    return {code: self.district_codes_info[code][1] * 100 / district_total_area
            for code in self.district_codes_info.keys()}

  def clean_district_vs_census_unit(self, code):
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
    return self.district_codes_info[code][0],\
        self.census_units_num_all_dict[code]

  def clean_districts_and_census_unit(self, codes=None):
    if codes is None:
      codes = self.district_codes

    both_units = dict()
    for code in codes:
      both_units[code] = self.clean_district_and_census_unit(code)
    return both_units

  def clean_district_vs_census_area(self, code, avg_area):
    clean_district_area = self.district_codes_info[code][1]
    census_units_to_area = self.census_units_num_all_dict[code] * avg_area
    difference = clean_district_area - census_units_to_area
    difference_ratio = abs(difference) * 100 / census_units_to_area
    return round(difference, 2), difference_ratio

  def clean_districts_vs_census_area(self, avg_area, codes=None):
    if codes is None:
      codes = self.district_codes

    all_differences_area = dict()
    for code in codes:
      all_differences_area[code] = \
        self.clean_district_vs_census_area(code, avg_area)
    return all_differences_area

  def clean_district_and_census_area(self, code, avg_area):
    return self.district_codes_info[code][1],\
           self.census_units_num_all_dict[code] * avg_area

  def clean_districts_and_census_area(self, avg_area, codes=None):
    if codes is None:
      codes = self.district_codes

    both_areas = dict()
    for code in codes:
      both_areas[code] = \
        self.clean_district_and_census_area(code, avg_area)
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

  def comparison_table(self, codes, avg_area=90) -> dict:
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

  def comparison_csv(self, codes, avg_area, distric_name):
    comparison_df = pd.DataFrame(self.comparison_table(codes, avg_area))
    comparison_df.to_csv(f'{distric_name}_validation.csv', index=False)
