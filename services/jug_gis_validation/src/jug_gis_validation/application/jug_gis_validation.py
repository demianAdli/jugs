"""Application-layer orchestration for GISOO validation."""
from __future__ import annotations

from time import perf_counter

from sabu_chassis.logging import get_logger

from jug_gis_validation.domain_validation.validate_gisoo import ValidateGISOO
from jug_gis_validation.errors import GISValidationError


logger = get_logger(__name__)


class GISValidationApplicationService:
    """Create validation workflows through a stable application boundary."""

    @staticmethod
    def create_validator(*args, **kwargs) -> ValidateGISOO:
        run_t0 = perf_counter()
        logger.info('Starting GISOO validator creation.')
        try:
            validator = ValidateGISOO(*args, **kwargs)
        except GISValidationError:
            logger.exception('GISOO validator creation failed.')
            raise
        except Exception as exc:
            logger.exception('Unexpected GISOO validator creation failure.')
            raise GISValidationError(
                'Unexpected GISOO validator creation failure.'
            ) from exc

        logger.info(
            'Completed GISOO validator creation. DistrictCodes=%s Elapsed=%.3fs',
            len(validator.district_codes),
            perf_counter() - run_t0)
        return validator
