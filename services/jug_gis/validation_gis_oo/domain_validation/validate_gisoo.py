from pathlib import Path
import pandas as pd
import geopandas as gpd


class ValidateGISOO:
  def __init__(self, census_data_csv, district_data_geojson):
    base_dir = Path(__file__).resolve().parent.parent

    census_data_path = base_dir / 'input_files' / census_data_csv
    the_district_path = base_dir / 'input_files' / district_data_geojson

    self.census_data = pd.read_csv(
      census_data_path,
      encoding="cp1252",
      encoding_errors="replace",
      low_memory=False)

    self.district = gpd.read_file(the_district_path)
    self.district_units_num = len(self.district)
