from pathlib import Path
import pandas as pd
import geopandas as gpd

from .query_census_data_csv import QueryCensusDataCSV
from .district_geojson_analysis import DistrictGeoJSONAnalysis


class ValidateGISOO:
  def __init__(self, census_data_csv, district_data_geojson,
               census_code_field_title, census_units_num_title,
               postal_code_key, function_key, function_value, area_key):
    base_dir = Path(__file__).resolve().parent.parent

    census_data_path = base_dir / 'input_files' / census_data_csv
    the_district_path = base_dir / 'input_files' / district_data_geojson

    self.load_census_data = pd.read_csv(
      census_data_path,
      encoding="cp1252",
      encoding_errors="replace",
      low_memory=False)

    self.census_code_field_title = census_code_field_title
    self.census_units_num_title = census_units_num_title

    self.census_data = QueryCensusDataCSV(self.load_census_data,
                                          self.census_code_field_title,
                                          self.census_units_num_title)

    self.census_units_num_all = self.census_units_num_all()

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

  def census_units_num_all(self):
    units_num = self.census_data.lookup.reindex(self.district_codes)
    return units_num.to_dict()

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

  def census_vs_clean_district_unit(self, code):
    pass

  def census_vs_clean_districts_unit(self):
    pass

  def census_vs_clean_district_area(self, code):
    pass

  def census_vs_clean_districts_area(self):
    pass
