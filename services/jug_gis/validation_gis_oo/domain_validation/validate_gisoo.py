from pathlib import Path
import pandas as pd
import geopandas as gpd

from .district_geojson_analysis import DistrictGeoJSONAnalysis


class ValidateGISOO:
  def __init__(self, census_data_csv, district_data_geojson,
               postal_code_key, function_key, function_value, area_key):
    base_dir = Path(__file__).resolve().parent.parent

    census_data_path = base_dir / 'input_files' / census_data_csv
    the_district_path = base_dir / 'input_files' / district_data_geojson

    self.census_data = pd.read_csv(
      census_data_path,
      encoding="cp1252",
      encoding_errors="replace",
      low_memory=False)

    self.load_district = gpd.read_file(the_district_path)

    self.postal_code_key = postal_code_key
    self.function_key = function_key
    self.function_value = function_value
    self.area_key = area_key

    self.district = DistrictGeoJSONAnalysis(self.load_district)
    self.district_codes = self.district.return_all_codes(self.postal_code_key )

  def summarize_area_and_unit_for_all(self):
      areas_and_units_num = []
      for code in self.district_codes:
          areas_and_units_num.append(
              self.district.summarize_code_unit_and_area(
                self.postal_code_key, self.area_key, postal_code_value=code))
      return areas_and_units_num
