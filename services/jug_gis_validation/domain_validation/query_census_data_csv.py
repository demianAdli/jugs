from __future__ import annotations

from typing import Mapping, Optional, Dict

import numpy as np
import pandas as pd

from .census_area_config import CensusAreaConfig


class QueryCensusDataCSV:
  """
  Builds fast lookup Series/dicts keyed by fsa_code
  from a census CSV that contains multiple rows per code
  (one per CHARACTERISTIC_NAME / CHARACTERISTIC_ID).

  Exposes:
    - units_num(code): int/float
    - total_area(code): float (m²)
    - units_num_all_dict / total_area_all_dict
    - remaining_dwellings_all_dict
  """

  def __init__(
          self,
          census_data: pd.DataFrame,
          census_code_field_title: str,
          cencus_code_units_num_field_title: str,
          *,
          characteristic_name_field: str = 'CHARACTERISTIC_NAME',
          characteristic_id_field: str = 'CHARACTERISTIC_ID',
          use_characteristic_id: bool = False,
          normalize_whitespace: bool = True,
          area_by_characteristic: Optional[Mapping[str, float]] = None,
          config: Optional[CensusAreaConfig] = None,
  ):
    self.code_field = census_code_field_title
    self.count_field = cencus_code_units_num_field_title
    self.characteristic_name_field = characteristic_name_field
    self.characteristic_id_field = characteristic_id_field
    self.use_characteristic_id = use_characteristic_id
    self.normalize_whitespace = normalize_whitespace

    base_cfg = config or CensusAreaConfig.defaults()
    if area_by_characteristic is not None:
      merged = dict(base_cfg.avg_area_by_characteristic)
      merged.update(area_by_characteristic)
      base_cfg = CensusAreaConfig(
        avg_area_by_characteristic=merged,
        total_private_dwellings_label=base_cfg.total_private_dwellings_label,
        total_households_label=base_cfg.total_households_label,
        remaining_dwellings_label=base_cfg.remaining_dwellings_label,
      )
    self.cfg = base_cfg

    df = census_data.copy()

    if not use_characteristic_id:
      if normalize_whitespace:
        s = df[self.characteristic_name_field].astype(str)
        s = s.str.replace(r"\s+", " ", regex=True).str.strip()
        df[self.characteristic_name_field] = s
      char_key = self.characteristic_name_field
    else:
      df[self.characteristic_id_field] = pd.to_numeric(
        df[self.characteristic_id_field], errors="coerce"
      )
      char_key = self.characteristic_id_field

    wide = (
      df.pivot_table(
        index=self.code_field,
        columns=char_key,
        values=self.count_field,
        aggfunc="sum",
        dropna=False,
      ).sort_index()
    )

    # Helper to safely fetch a column (missing -> zeros)
    def col_or_zeros(column_key) -> pd.Series:
      if column_key in wide.columns:
        return wide[column_key].fillna(0)
      return pd.Series(0, index=wide.index, dtype='float64')

    if use_characteristic_id:
      raise ValueError(
        'use_characteristic_id=True requires you to map totals by ID. '
        'Keep it False unless you add an ID mapping.'
      )

    total_private = col_or_zeros(self.cfg.total_private_dwellings_label)
    total_households = col_or_zeros(self.cfg.total_households_label)
