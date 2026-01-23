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