"""
Let's firstly just code the business-value part then we move on to make it clean
by loading file in another module and think through what to do (maybe we have
to move the read json or path kinda module of the cap to the chassis)
chassis can have a component that handles input/output data
chassis can have another component that handles dbms needs
"""
from pathlib import Path
import pandas as pd
import geopandas as gpd


class ValidateHouseholds:
    def __init__(self, census_data, district):
        base_dir = Path(__file__).resolve().parent
        # the class needs to read both path and file (or we'll do the loading in the workflow)
        # 'census_data.csv' 'Beauport.geojson'
        census_data_path = base_dir / 'input_files' / census_data
        the_district_path = base_dir / 'input_files' / district

        self.census_data = pd.read_csv(census_data_path, encoding="cp1252", encoding_errors="replace", low_memory=False)
        self.district = gpd.read_file(the_district_path)
        self.district_units_num = len(self.district)

        # Je pense que je dois mettre le ci-dessous dans le wf.
        # self.district_fsa_codes = self.return_all_fsa()
        # self.district_fsa_codes_num = 0

    def return_all_fsa_codes(self):
        all_fsa = set()
        for unit in range(len(self.district)):
            all_fsa.add(self.district.iloc[unit]['CODE_POSTA'][:3])
        return list(all_fsa)

    def none_num(self):
        total_nones = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit]['CODE_POSTA'] == 'None' and self.district.iloc[unit]['function'] == 'Logement':
                total_nones += 1
        nones_percentage = total_nones * 100 / len(self.district)
        return total_nones, nones_percentage

    def summarize_fsa_area(self, fsa_code):
        fsa_total_area = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit]['CODE_POSTA'][:3] == fsa_code:
                fsa_total_area += self.district.iloc[unit]['total_area']
        return fsa_total_area

    def calculate_code_frequency_ratio(self):
        # Si je met ca dans le wf, le ci-dessous sera verbeuse
        codes = self.return_all_fsa_codes()
        pass










