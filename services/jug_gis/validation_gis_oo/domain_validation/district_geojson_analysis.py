"""
In this module, I refer to the fsa code as code.
"""
import numpy as np
import pandas as pd


class DistrictGeoJSONAnalysis:
    def __init__(self, load_district):
        self.load_district = load_district
        self.district_units_num = len(self.load_district)

    def return_all_codes(self,
                         postal_code_key: str,
                         prefix_len: int = 3,
                         sort: bool = False):

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
            floor_num_key: str,
            codes: list[str] | None,
            prefix_len: int = 3,
            function_key: str | None = None,
            function_value: object | None = None):

        the_district = self.load_district
        codes_series = the_district[postal_code_key]
        mask = codes_series.notna()

        prefix = pd.Series(index=the_district.index, dtype=object)
        prefix.loc[mask] = (
            codes_series.loc[mask].astype(str)
                .str.replace(r'\s+', '', regex=True)
                .str[:prefix_len]
        )

        if function_key is not None:
            sel = the_district[function_key].eq(function_value)
            the_district = the_district.loc[sel]
            prefix = prefix.loc[sel]

        # NEW: multiply floor area (return_key) by number of floors (floor_num_key)
        effective_value = (
                pd.to_numeric(the_district[return_key], errors="coerce") *
                pd.to_numeric(the_district[floor_num_key], errors="coerce")
        )

        grouped = (
            pd.DataFrame(
                {
                    "_prefix": prefix,
                    "effective_value": effective_value,
                }
            )
            .dropna(subset=["_prefix"])
            .groupby("_prefix", dropna=False)
            .agg(
                count=("_prefix", "size"),
                sum=("effective_value", "sum"),
            )
        )

        if codes is not None:
            grouped = grouped.reindex(pd.Index(codes), fill_value=0)

        grouped["sum"] = grouped["sum"].fillna(0.0).astype(float)
        grouped["count"] = grouped["count"].astype(int)

        return {
            code: (int(values["count"]), round(float(values["sum"]), 2))
            for code, values in grouped.to_dict("index").items()
        }

    def height_to_floor_proxy(
            self,
            height_field: str,
            divisor: float,
    ) -> tuple[list[int], int, float, int, float]:
        """
        Use a height field to estimate floor numbers.

        Parameters
        ----------
        height_field : str
            Name of the column containing building heights.
        divisor : float
            Value by which heights are divided (e.g. average floor height).

        Returns
        -------
        tuple[list[int], int, float, int, float]
            - List of integer floor-count proxies for each feature
              (same length as load_district).
            - Number of entries where height was missing or non-numeric (NaN).
            - Percentage of such entries in [0, 100].
            - Number of entries where height equals exactly zero.
            - Percentage of such entries in [0, 100].
        """
        if divisor == 0:
            raise ValueError("divisor must be non-zero")

        # Safely convert to numeric; non-numeric becomes NaN
        heights = pd.to_numeric(self.load_district[height_field], errors="coerce")

        total = len(heights)

        # NaNs -> "nones"
        mask_nones = heights.isna()
        num_nones = int(mask_nones.sum())
        pct_nones = (num_nones / total * 100.0) if total > 0 else 0.0

        # Zeros -> problematic as well
        mask_zeros = heights.eq(0)
        num_zeros = int(mask_zeros.sum())
        pct_zeros = (num_zeros / total * 100.0) if total > 0 else 0.0

        # Divide and round to nearest integer
        floors = (heights / float(divisor)).round()

        # Replace NaN with 0, cast to ints
        floors = floors.fillna(0).astype(int)

        return (
            floors.tolist(),
            num_nones,
            round(pct_nones, 2),
            num_zeros,
            round(pct_zeros, 2),
        )
