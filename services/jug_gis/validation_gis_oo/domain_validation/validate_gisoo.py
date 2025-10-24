from pathlib import Path
import pandas as pd
import geopandas as gpd

from .query_census_data_csv import QueryCensusDataCSV
from .district_geojson_analysis import DistrictGeoJSONAnalysis


class ValidateGISOO:
  def __init__(self, census_data_csv, district_data_geojson,
               postal_code_key, function_key, function_value, area_key):
    base_dir = Path(__file__).resolve().parent.parent

    census_data_path = base_dir / 'input_files' / census_data_csv
    the_district_path = base_dir / 'input_files' / district_data_geojson

    self.load_census_data = pd.read_csv(
      census_data_path,
      encoding="cp1252",
      encoding_errors="replace",
      low_memory=False)

    self.census_data = QueryCensusDataCSV(self.load_census_data)

    self.load_district = gpd.read_file(the_district_path)

    self.postal_code_key = postal_code_key
    self.function_key = function_key
    self.function_value = function_value
    self.area_key = area_key

    self.district = DistrictGeoJSONAnalysis(self.load_district)
    self.district_codes = self.district.return_all_codes(self.postal_code_key)
    self.all_codes_dict = self.district.summarize_all_codes_dict(
      postal_code_key=self.postal_code_key,
      return_key=self.area_key,
      codes=self.district_codes,
      prefix_len=3,
      function_key=self.function_key,
      function_value=self.function_value
    )

  def calculate_codes_unit_frequency_ratio(self):
    district_total_area = sum(
      [index[0] for index in self.all_codes_dict.values()])
    return {code: self.all_codes_dict[code][0] * 100 / district_total_area
            for code in self.all_codes_dict.keys()}

  def calculate_codes_area_frequency_ratio(self):
    district_total_area = sum(
      [index[1] for index in self.all_codes_dict.values()])
    return {code: self.all_codes_dict[code][1] * 100 / district_total_area
            for code in self.all_codes_dict.keys()}

  # def allocate_none_codes(self):
  #   none_nums = self.district.none_codes(
  #     self.postal_code_key, self.function_key, self.function_value)[0]
  #   codes_unit_ratio = self.calculate_codes_unit_frequency_ratio()
  #   allocated_nones = [
  #     round(none_nums * ratio / 100) for ratio in codes_unit_ratio]
  #   code_units = self.calculate_codes_frequency()
  #   zip_codes_and_nones = zip(code_units, allocated_nones)
  #   return [units for units in zip_codes_and_nones]

  def allocate_none_codes_address_base(self):
    """ How can I use the address or other geojson fields
    to allocate the nones to the actual fsa"""
    pass
