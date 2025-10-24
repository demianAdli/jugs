"""
In this module, I refer to the fsa code as code
"""


class DistrictGeoJSONAnalysis:
    def __init__(self, load_district):
        self.load_district = load_district
        self.district_units_num = len(self.load_district)

    def return_all_codes(self, postal_code_key):
        all_codes = set()
        for unit in range(len(self.load_district)):
            all_codes.add(self.load_district.iloc[unit][postal_code_key][:3])
        return list(all_codes)

    def none_codes(self, postal_code_key, function_key, function_value):
        total_nones = 0
        for unit in range(self.district_units_num):
            if self.load_district.iloc[unit][postal_code_key] == 'None' \
                    and self.load_district.iloc[unit][function_key] == \
                    function_value:
                total_nones += 1
        nones_percentage = total_nones * 100 / len(self.load_district)
        return total_nones, nones_percentage

    def match_key_value(
            self, match_key, match_value, unit):
        if not self.load_district.iloc[unit][match_key][:3] == \
               match_value:
            return False
        else:
            return True

    def summarize_all_codes_dict(self, postal_code_key, return_key, codes, prefix_len=3):
        grouped = (
            self.load_district
            .assign(_prefix=self.load_district[postal_code_key].astype(str).str[:prefix_len])
            .groupby('_prefix', dropna=False)
            .agg(count=('_prefix', 'size'), sum=(return_key, 'sum'))
            .reindex(codes, fill_value=0)
        )
        return {code: (int(row['count']), float(row['sum'])) for code, row in grouped.iterrows()}
