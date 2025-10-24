"""
In this module, I refer to the fsa code as code
"""


class DistrictGeoJSONAnalysis:
    def __init__(self, district):
        self.district = district
        self.district_units_num = len(self.district)

    def return_all_codes(self, postal_code_key):
        all_codes = set()
        for unit in range(len(self.district)):
            all_codes.add(self.district.iloc[unit][postal_code_key][:3])
        return list(all_codes)

    def none_codes(self, postal_code_key, function_key, function_value):
        total_nones = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit][postal_code_key] == 'None' \
                    and self.district.iloc[unit][function_key] == \
                    function_value:
                total_nones += 1
        nones_percentage = total_nones * 100 / len(self.district)
        return total_nones, nones_percentage

    def match_key_value(
            self, match_key, match_value, unit):
        if not self.district.iloc[unit][match_key][:3] == \
                match_value:
            return False
        else:
            return True

    def summarize_code_unit_and_area_new(
            self, postal_code_key, return_key, match_value):
        code_total_area = 0
        code_unit_nums = 0
        for unit in range(self.district_units_num):
            if self.match_key_value(postal_code_key, match_value, unit):
                code_unit_nums += 1
                code_total_area += float(self.district.iloc[unit][return_key])
        return code_unit_nums, code_total_area

    def summarize_code_unit_and_area(
            self, match_key, return_key, match_value):
        code_total_area = 0
        code_unit_nums = 0
        for unit in range(self.district_units_num):
            if self.district.iloc[unit][match_key][:3] == \
                    match_value:
                code_unit_nums += 1
                code_total_area += float(self.district.iloc[unit][return_key])
        return code_unit_nums, code_total_area

    def summarize_all_codes(self, postal_code_key, return_key, codes, prefix_len=3):
        df = self.district.copy()
        df["_prefix"] = df[postal_code_key].astype(str).str[:prefix_len]
        df[return_key] = df[return_key].astype(float)

        grouped = df.groupby("_prefix", dropna=False)[return_key].agg(["count", "sum"])

        out = []
        for code in codes:
            if code in grouped.index:
                cnt = int(grouped.loc[code, "count"])
                total = float(grouped.loc[code, "sum"])
            else:
                cnt, total = 0, 0.0
            out.append((cnt, total))
        return out
