import os
import logging

from flask import request, jsonify, current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from werkzeug.exceptions import HTTPException

from jug_ee.schemas.schemas import LCAInputDataSchema
from jug_ee.lca_carbon_workflow import LCACarbonWorkflow

logger = logging.getLogger(__name__)
DEV_MODE = os.getenv("LOG_ENV", "dev") == "dev"

blp = Blueprint(
    'Emissions',
    __name__,
    description='Exporting embodied and end-of-life emissions data for buildings'
)

@blp.route("/emissions")
class Emissions(MethodView):
    @blp.arguments(LCAInputDataSchema)
    def post(self, request_city):
        logger.info("emissions_request_received")
        try:
            emissions_data = LCACarbonWorkflow(
                request_city,
                'nrcan_archetypes.json',
                'nrcan_constructions_cap_3.json'
            ).export_emissions()
            logger.info("emissions_request_succeeded", extra={"buildings": len(emissions_data)})
            return jsonify(emissions_data), 201

        except HTTPException:
            # If something upstream already called abort(...), preserve that response.
            raise

        except Exception as e:
            logger.exception("emissions_request_failed", extra={"feature_count": feature_count})
            public_msg = str(e) if (DEV_MODE or current_app.debug) else "Failed to compute emissions"
            abort(500, message=public_msg)
