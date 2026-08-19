"""
Sabu project
jug_gis_validation project
jug_gis_validation package
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
https://demianadli.com/
"""

from __future__ import annotations

from typing import Mapping, Optional, Dict

import numpy as np
import pandas as pd
from sabu_chassis.logging import get_logger

from jug_gis_validation.errors import GISValidationDataContractError
from .census_area_config import CensusAreaConfig


logger = get_logger(__name__)


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
          census_code_units_num_field_title: str,
          *,
          characteristic_name_field: str = 'CHARACTERISTIC_NAME',
          area_by_characteristic: Optional[Mapping[str, float]] = None,
          config: Optional[CensusAreaConfig] = None,
  ):
    self.code_field = census_code_field_title
    self.count_field = census_code_units_num_field_title
    self.characteristic_name_field = characteristic_name_field
    self._ensure_columns(
      census_data,
      [
        self.code_field,
        self.count_field,
        self.characteristic_name_field,
      ])

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

    s = df[self.characteristic_name_field].astype(str)
    s = s.str.replace(r'\s+', ' ', regex=True).str.strip()
    df[self.characteristic_name_field] = s
    char_key = self.characteristic_name_field

    wide = (
      df.pivot_table(
        index=self.code_field,
        columns=char_key,
        values=self.count_field,
        aggfunc='sum',
        dropna=False,
      ).sort_index()
    )
    missing_characteristics = sorted(
      label for label in base_cfg.avg_area_by_characteristic
      if label != base_cfg.remaining_dwellings_label
      and label not in wide.columns
    )
    if missing_characteristics:
      logger.warning(
        'Census data is missing %s configured characteristic label(s). '
        'Sample=%s',
        len(missing_characteristics),
        missing_characteristics[:10])

    # Helper to safely fetch a column (missing -> zeros)
    def col_or_zeros(column_key) -> pd.Series:
      if column_key in wide.columns:
        return wide[column_key].fillna(0)
      return pd.Series(0, index=wide.index, dtype='float64')

    total_private = col_or_zeros(self.cfg.total_private_dwellings_label)
    total_households = col_or_zeros(self.cfg.total_households_label)

    remaining = (total_private - total_households).clip(lower=0)

    remaining_avg = float(
      self.cfg.avg_area_by_characteristic.get(
        self.cfg.remaining_dwellings_label, 0.0))

    #    units = total_households unless remaining_avg != 0,
    #    then units = total_private_dwellings
    units_num = np.where(
      remaining_avg != 0,
      total_private.to_numpy(),
      total_households.to_numpy())
    units_num = pd.Series(units_num, index=wide.index).astype(float)

    area = pd.Series(0.0, index=wide.index)

    for typ, avg in self.cfg.avg_area_by_characteristic.items():
      if typ == self.cfg.remaining_dwellings_label:
        continue
      area = area.add(col_or_zeros(typ) * float(avg), fill_value=0)

    area = area + remaining * remaining_avg

    self._wide = wide
    self.remaining_dwellings = remaining
    self.units_num = units_num
    self.total_area = area

  @staticmethod
  def _ensure_columns(census_data: pd.DataFrame, required_columns) -> None:
    missing_columns = [
      column for column in required_columns
      if column and column not in census_data.columns
    ]
    if missing_columns:
      raise GISValidationDataContractError(
        'census_data_csv is missing required column(s): '
        f'{", ".join(missing_columns)}')

  def census_code_units_num(self, census_code):
    return self.units_num.get(census_code)

  def census_code_total_area(self, census_code):
    return self.total_area.get(census_code)

  @property
  def units_num_all_dict(self) -> Dict[str, float]:
    return self.units_num.to_dict()

  @property
  def total_area_all_dict(self) -> Dict[str, float]:
    return self.total_area.to_dict()

  @property
  def remaining_dwellings_all_dict(self) -> Dict[str, float]:
    return self.remaining_dwellings.to_dict()
