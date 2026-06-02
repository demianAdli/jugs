from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CensusAreaConfig:
    """
    Default average areas (m²) per building type.
    Keys MUST match the normalized characteristic labels (after stripping).
    """
    avg_area_by_characteristic: Dict[str, float]

    total_private_dwellings_label: str = 'Total private dwellings'
    total_households_label: str = 'Total - Private households by household size - 100% data'
    remaining_dwellings_label: str = 'Remaining dwellings'

    @staticmethod
    def defaults() -> 'CensusAreaConfig':
        return CensusAreaConfig(
            avg_area_by_characteristic={
                'Single-detached house': 160.0,
                'Semi-detached house': 160.0,
                'Row house': 120.0,
                'Apartment or flat in a duplex': 95.0,
                'Apartment in a building that has fewer than five storeys': 95.0,
                'Apartment in a building that has five or more storeys': 95.0,
                'Other single-attached house': 95.0,
                'Movable dwelling': 95.0,
                # If the below is not equal to 0.0, the calculation is
                # based on total private dwellings. (synthetic parameter).
                'Remaining dwellings': 0.0,
            }
        )
