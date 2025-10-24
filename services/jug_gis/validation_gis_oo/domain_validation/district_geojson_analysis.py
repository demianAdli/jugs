"""
In this module, I refer to the fsa code as code
"""
import numpy as np
import pandas as pd


class DistrictGeoJSONAnalysis:
    def __init__(self, load_district):
        self.load_district = load_district
        self.district_units_num = len(self.load_district)

    def return_all_codes(self, postal_code_key: str, prefix_len: int = 3, sort: bool = False):

        codes_series = self.load_district[postal_code_key]
        mask = codes_series.notna()

        prefixes = pd.Series(index=codes_series.index, dtype=object)
        prefixes.loc[mask] = (
            codes_series.loc[mask].astype(str).str.replace(
                r'\s+', '', regex=True).str[:prefix_len])

        uniq = pd.unique(prefixes.dropna())
        if sort:
            uniq = np.sort(uniq)
        return uniq.tolist()

    def summarize_all_codes_dict(
            self,
            postal_code_key: str,
            return_key: str,
            codes: list[str] | None,
            prefix_len: int = 3,
            function_key: str | None = None,
            function_value: object | None = None,):

        the_district = self.load_district
        codes_series = the_district[postal_code_key]
        mask = codes_series.notna()

        prefix = pd.Series(index=the_district.index, dtype=object)
        prefix.loc[mask] = (
            codes_series.loc[mask].astype(str).str.replace(
                r'\s+', '', regex=True).str[:prefix_len])

        if function_key is not None:
            sel = the_district[function_key].eq(function_value)
            the_district = the_district.loc[sel]
            prefix = prefix.loc[sel]

        grouped = (
            pd.DataFrame(
                {'_prefix': prefix, return_key: the_district[return_key]})
            .dropna(subset=['_prefix'])
            .groupby('_prefix', dropna=False)
            .agg(count=('_prefix', 'size'), sum=(return_key, 'sum'))
        )

        if codes is not None:
            grouped = grouped.reindex(pd.Index(codes), fill_value=0)

        grouped['sum'] = grouped['sum'].fillna(0.0).astype(float)
        grouped['count'] = grouped['count'].astype(int)

        return {
            codes: (int(values['count']), float(values['sum']))
            for codes, values in grouped.to_dict("index").items()}
