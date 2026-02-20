import json
import os
import logging

from flask import jsonify, current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from ..schemas.schemas import LCAInputDataSchema, GeoJSONUploadSchema
from ..lca_carbon_workflow import LCACarbonWorkflow

logger = logging.getLogger(__name__)
DEV_MODE = os.getenv('LOG_ENV', 'dev') == 'dev'

blp = Blueprint(
    'Emissions',
    __name__,
    description='Exporting embodied and end-of-life emissions data for buildings'
)


def _run_emissions_workflow(request_city, request_received_log, request_failed_log):
    logger.info(request_received_log)
    try:
        emissions_data = LCACarbonWorkflow(
            request_city,
            'nrcan_archetypes.json',
            'nrcan_constructions_cap_3.json'
        ).export_emissions()
        logger.info("emissions_request_succeeded", extra={'buildings': len(emissions_data)})
        return jsonify(emissions_data), 201

    except HTTPException:
        # If something upstream already called abort(...), preserve that response.
        raise

    except Exception as e:
        logger.exception(request_failed_log)
        public_msg = str(e) if (DEV_MODE or current_app.debug) else "Failed to compute emissions"
        abort(500, message=public_msg)


@blp.route('/emissions')
class Emissions(MethodView):
    @blp.arguments(LCAInputDataSchema)
    def post(self, request_city):
        return _run_emissions_workflow(
            request_city,
            request_received_log='emissions_request_received',
            request_failed_log='emissions_request_failed',
        )


@blp.route('/emissions/upload')
class EmissionsUpload(MethodView):
    @blp.arguments(GeoJSONUploadSchema, location='files')
    def post(self, files_data):
        geojson_file = files_data['geojson_file']

        if not geojson_file or not getattr(geojson_file, "filename", ""):
            abort(400, message="geojson_file is required")

        try:
            request_city = json.load(geojson_file.stream)
        except json.JSONDecodeError:
            abort(400, message="Invalid JSON content in geojson_file")

        try:
            validated_request_city = LCAInputDataSchema().load(request_city)
        except ValidationError as err:
            abort(422, message="Invalid GeoJSON payload", errors=err.messages)

        return _run_emissions_workflow(
            validated_request_city,
            request_received_log='emissions_upload_request_received',
            request_failed_log='emissions_upload_request_failed',
        )
