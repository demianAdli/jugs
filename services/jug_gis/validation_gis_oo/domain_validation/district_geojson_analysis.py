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

I think it makes more sense to have number of units as the base
for distributing Nones, rather than total_area. Because, it makes more
sense if we say, an area that has more units should take more of
Nones (more units) rather than an area which has more total _area.

At the end, assign the methods which depends on a lot of methods
in the wf class


In this module, I refer to the fsa code as code
"""
from pathlib import Path
import pandas as pd
import geopandas as gpd


class DistrictGeoJSONAnalysis:
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

        self.district_codes = self.return_all_codes()

    def return_all_codes(self):
        all_codes = set()
        for unit in range(len(self.district)):
            all_codes.add(self.district.iloc[unit]['CODE_POSTA'][:3])
        return list(all_codes)

    def none_codes(self):
        total_nones = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit]['CODE_POSTA'] == 'None' \
                    and self.district.iloc[unit]['function'] == 'Logement':
                total_nones += 1
        nones_percentage = total_nones * 100 / len(self.district)
        return total_nones, nones_percentage

    def summarize_code_unit_and_area(self, code):
        code_total_area = 0
        code_unit_nums = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit]['CODE_POSTA'][:3] == code:
                code_unit_nums += 1
                code_total_area += self.district.iloc[unit]['total_area']
        return code_unit_nums, code_total_area

    def summarize_area_and_unit_for_all(self):
        areas_and_units_num = []
        for code in self.district_codes:
            areas_and_units_num.append(self.summarize_code_unit_and_area(code))
        return areas_and_units_num

    def calculate_codes_frequency(self):
        return [info[0] for info in self.summarize_area_and_unit_for_all()]

    def calculate_codes_unit_frequency_ratio(self):
        code_frequencies = self.calculate_codes_frequency()
        district_units_num = sum(code_frequencies)
        return [code_frequency * 100 / district_units_num
                for code_frequency in code_frequencies]

    def calculate_codes_area_frequency_ratio(self):
        code_area_frequencies = \
            [info[1] for info in self.summarize_area_and_unit_for_all()]
        district_total_area = sum(code_area_frequencies)
        return [area_frequency * 100 / district_total_area
                for area_frequency in code_area_frequencies]

    def allocate_none_code_units(self):
        none_nums = self.none_codes()[0]
        codes_unit_ratio = self.calculate_codes_unit_frequency_ratio()
        allocated_nones = [round(none_nums * ratio / 100) for ratio in codes_unit_ratio]
        code_units = self.calculate_codes_frequency()
        zip_codes_and_nones = zip(code_units, allocated_nones)
        return [units for units in zip_codes_and_nones]
# How can I use the address or other geojson fields to allocate the nones to the actual fsa