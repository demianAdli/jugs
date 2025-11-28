"""
In this module, I refer to the FSA code as code.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Iterable


class DistrictGeoJSONAnalysis:
    """
    Thin analysis wrapper over a district GeoDataFrame.

    Immutable-by-convention: internal data should not be mutated after
    instantiation. If the underlying district data changes, create a new
    instance.
    """

    def __init__(self, load_district):
        # Internal GeoDataFrame (do not mutate from outside)
        self._load_district = load_district
        self._district_units_num = len(self._load_district)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def load_district(self):
        """Underlying GeoDataFrame (exposed read-only by convention)."""
        return self._load_district

    @property
    def district_units_num(self) -> int:
        """Number of features in the district."""
        return self._district_units_num

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _postal_prefix_series(
        self,
        postal_code_key: str,
        prefix_len: int = 3,
    ) -> pd.Series:
        """
        Extract FSA (codes) from the postal codes.

        Missing codes remain NaN.
        """
        codes_series = self._load_district[postal_code_key]
        mask = codes_series.notna()

        prefix = pd.Series(index=self._load_district.index, dtype=object)
        prefix.loc[mask] = (
            codes_series.loc[mask]
            .astype(str)
            .str.replace(r'\s+', '', regex=True)
            .str[:prefix_len]
        )
        return prefix

    @staticmethod
    def _group_effective_by_prefix(
        prefix: pd.Series,
        effective_value: pd.Series,
        codes: list[str] | None,
    ) -> dict[str, tuple[int, float]]:
        """
        Group an effective_value Series by prefix and return
        {code: (count, sum)} dict, reindexed to `codes` if provided.
        """
        df = pd.DataFrame(
            {
                '_prefix': prefix,
                'effective_value': effective_value,
            }
        )

        grouped = (
            df.dropna(subset=['_prefix'])
            .groupby('_prefix', dropna=False)
            .agg(
                count=('_prefix', 'size'),
                sum=('effective_value', 'sum'),
            )
        )

        if codes is not None:
            grouped = grouped.reindex(pd.Index(codes), fill_value=0)

        grouped['sum'] = grouped['sum'].fillna(0.0).astype(float)
        grouped['count'] = grouped['count'].astype(int)

        return {
            code: (int(values['count']), round(float(values['sum']), 2))
            for code, values in grouped.to_dict('index').items()
        }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def return_all_codes(
        self,
        postal_code_key: str,
        prefix_len: int = 3,
        sort: bool = False,
    ) -> list[str]:
        """
        Return unique FSA (codes) prefixes for the given postal_code_key.
        """
        prefix = self._postal_prefix_series(postal_code_key, prefix_len)
        uniq = pd.unique(prefix.dropna())
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
        function_value: object | None = None,
    ) -> dict[str, tuple[int, float]]:
        """
        Aggregate per-prefix counts and total area (area*floors).

        Parameters
        ----------
        postal_code_key : str
            Column name with postal codes.
        return_key : str
            Column name with base area (e.g. total_area).
        floor_num_key : str
            Column name with number of floors (e. g. NBR_ETAGE).
        codes : list[str] | None
            Optional list of FSA codes to reindex to.
        prefix_len : int
            Number of characters to use as prefix.
        function_key : str | None
            Optional column to filter by.
        function_value : object | None
            Value in function_key to keep.

        Returns
        -------
        dict[str, (int, float)]
            {code: (count, total_effective_area)}
        """
        the_district = self._load_district

        prefix = self._postal_prefix_series(postal_code_key, prefix_len)

        # Optional filter by function key/value
        if function_key is not None:
            sel = the_district[function_key].eq(function_value)
            the_district = the_district.loc[sel]
            prefix = prefix.loc[sel]

        # Floor-aware effective area
        effective_value = (
            pd.to_numeric(the_district[return_key], errors='coerce')
            * pd.to_numeric(the_district[floor_num_key], errors='coerce')
        )

        return self._group_effective_by_prefix(prefix, effective_value, codes)

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
            Value by which heights are divided (e.g. height).

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
            raise ValueError('divisor must be non-zero')

        heights = pd.to_numeric(
            self._load_district[height_field],
            errors='coerce',
        )

        total = len(heights)

        # NaNs -> 'nones'
        mask_nones = heights.isna()
        num_nones = int(mask_nones.sum())
        pct_nones = (num_nones / total * 100.0) if total > 0 else 0.0

        # Zeros -> problematic as well
        mask_zeros = heights.eq(0)
        num_zeros = int(mask_zeros.sum())
        pct_zeros = (num_zeros / total * 100.0) if total > 0 else 0.0

        # Estimate floors
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

    def summarize_all_codes_with_multipliers(
        self,
        postal_code_key: str,
        return_key: str,
        multipliers: Iterable[float],
        codes: list[str] | None,
        prefix_len: int = 3,
        function_key: str | None = None,
        function_value: object | None = None,
    ) -> dict[str, tuple[int, float]]:
        """
        Aggregate per-prefix counts and area * custom multipliers.

        This is used when floor numbers are provided externally
        (e.g. from height_to_floor_proxy).

        Parameters
        ----------
        postal_code_key : str
            Column name with postal codes.
        return_key : str
            Column name with base area (e.g. footprint area).
        multipliers : list[float] | tuple[float, ...]
            One multiplier per feature (must match len(load_district)).
        codes : list[str] | None
            Optional list of FSA codes to reindex to.
        prefix_len : int
            Number of characters to use as prefix.
        function_key : str | None
            Optional column to filter by.
        function_value : object | None
            Value in function_key to keep.

        Returns
        -------
        dict[str, (int, float)]
            {code: (count, total_effective_area)}
        """
        the_district = self._load_district

        multipliers = list(multipliers)
        if len(multipliers) != len(the_district):
            raise ValueError(
                f'Length of multipliers ({len(multipliers)}) does not match '
                f'number of features ({len(the_district)})'
            )

        prefix = self._postal_prefix_series(postal_code_key, prefix_len)

        multiplier_series = pd.Series(multipliers, index=the_district.index)
        multiplier_series = pd.to_numeric(multiplier_series, errors='coerce')

        # Optional filter
        if function_key is not None:
            sel = the_district[function_key].eq(function_value)
            the_district = the_district.loc[sel]
            prefix = prefix.loc[sel]
            multiplier_series = multiplier_series.loc[sel]

        effective_value = (
            pd.to_numeric(the_district[return_key], errors='coerce')
            * multiplier_series
        )

        return self._group_effective_by_prefix(prefix, effective_value, codes)
