"""
In this module, I refer to the fsa code as code
"""


class DistrictGeoJSONAnalysis:
    def __init__(self, district):

        self.district = district
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