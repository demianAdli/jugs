"""
Let's firstly just code the business-value part then we move on to make it
clean by loading file in another module and think through what
to do (maybe we have to move the read json or path kinda module of
the cap to the chassis) chassis can have a component that handles
input/output data
Chassis can have another component that handles dbms needs

IMPORTANT: I have to change the function of the below class to
extract geojson area info then I will make a wf or
a wf class that compare the results with census data. I also
need to load files in another class like read_geojson_content in jug_ee
so the wf can work either it is in the middle of the cleaning wf,
or receiving data through api or receiving just a geojson content/file
"""
from pathlib import Path
import pandas as pd
import geopandas as gpd


class ValidateHouseholds:
    def __init__(self, census_data, district):
        base_dir = Path(__file__).resolve().parent
        # the class needs to read both path and file
        # (or we'll do the loading in the workflow)
        # 'census_data.csv' 'Beauport.geojson'
        census_data_path = base_dir / 'input_files' / census_data
        the_district_path = base_dir / 'input_files' / district

        self.census_data = pd.read_csv(
            census_data_path,
            encoding="cp1252",
            encoding_errors="replace",
            low_memory=False)

        self.district = gpd.read_file(the_district_path)
        self.district_units_num = len(self.district)

        self.district_fsa_codes = self.return_all_fsa_codes()

    def return_all_fsa_codes(self):
        all_fsa = set()
        for unit in range(len(self.district)):
            all_fsa.add(self.district.iloc[unit]['CODE_POSTA'][:3])
        return list(all_fsa)

    def none_num(self):
        total_nones = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit]['CODE_POSTA'] == 'None' \
                    and self.district.iloc[unit]['function'] == 'Logement':
                total_nones += 1
        nones_percentage = total_nones * 100 / len(self.district)
        return total_nones, nones_percentage

    def summarize_fsa_area(self, fsa_code):
        fsa_total_area = 0
        code_unit_nums = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit]['CODE_POSTA'][:3] == fsa_code:
                code_unit_nums += 1
                fsa_total_area += self.district.iloc[unit]['total_area']
        return code_unit_nums, fsa_total_area

    def summarize_area_for_all(self):
        areas_and_units_num = []
        for fsa_code in self.district_fsa_codes:
            areas_and_units_num.append(self.summarize_fsa_area(fsa_code))
        return areas_and_units_num

    def calculate_code_units_frequency_ratio(self):
        code_frequencies = [info[0] for info in self.summarize_area_for_all()]
        district_units_num = sum(code_frequencies)
        return [code_frequency * 100 / district_units_num
                for code_frequency in code_frequencies]

    def calculate_code_area_frequency_ratio(self):
        code_area_frequencies = [info[1] for info in self.summarize_area_for_all()]
        district_total_area = sum(code_area_frequencies)
        return [code_frequency * 100 / district_total_area
                for code_frequency in code_area_frequencies]











