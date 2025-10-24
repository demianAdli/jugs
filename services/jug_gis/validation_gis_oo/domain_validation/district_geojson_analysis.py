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

    def summarize_all_codes_dict(
            self,
            postal_code_key: str,
            return_key: str,
            codes: list[str],
            prefix_len: int = 3,
            function_key: str | None = None,
            function_value: object | None = None,
    ):
        """
        Summarize count and sum(return_key) by postal-code prefix for the given `codes`.
        If function_key and function_value are provided, only include rows where
        df[function_key] == function_value.
        """
        the_district = self.load_district


        df2 = (
            the_district.assign(_prefix=the_district[postal_code_key].astype(str).str[:prefix_len])
            .loc[lambda d: d['_prefix'].notna() & d['_prefix'].isin(codes)]
        )

        if function_key is not None:
            df2 = df2.loc[df2[function_key].eq(function_value)]

        grouped = (
            df2.groupby('_prefix', dropna=False)
            .agg(
                count=(postal_code_key, lambda s: s.notna().sum()),
                sum=(return_key, 'sum'),
            )
            .reindex(codes, fill_value=0)
        )

        grouped['sum'] = grouped['sum'].fillna(0.0).astype(float)
        grouped['count'] = grouped['count'].astype(int)

        return {code: (int(row['count']), float(row['sum'])) for code, row in grouped.iterrows()}
