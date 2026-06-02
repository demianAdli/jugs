"""Validation-specific exceptions for jug_gis_validation."""
from __future__ import annotations


class GISValidationError(RuntimeError):
    """Base error for GIS validation failures."""


class GISValidationInputError(GISValidationError):
    """Raised when a validation input cannot be resolved or parsed."""


class GISValidationDataContractError(GISValidationError):
    """Raised when input data does not contain the expected fields."""


class GISValidationCalculationError(GISValidationError):
    """Raised when a validation calculation cannot be completed."""
