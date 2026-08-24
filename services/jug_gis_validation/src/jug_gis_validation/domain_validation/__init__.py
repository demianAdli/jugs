"""Domain validation components."""

from .validate_gisoo import (
    AreaCalculationMode,
    HeightProxyAreaResolutionStats,
    ValidateGISOO,
)
from .uniquify_features import (
    FeatureUniquificationStats,
    uniquify_features,
)

__all__ = [
    "FeatureUniquificationStats",
    "AreaCalculationMode",
    "HeightProxyAreaResolutionStats",
    "ValidateGISOO",
    "uniquify_features",
]
