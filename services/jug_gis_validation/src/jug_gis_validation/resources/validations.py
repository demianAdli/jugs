"""
Sabu project
jug_gis_validation project
jug_gis_validation package
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
https://demianadli.com/

REST resource for running GISOO validations.
"""
from __future__ import annotations

import io
import json
import logging
import os

from flask import Response, current_app, jsonify, request, send_file
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from ..application import GISValidationApplicationService
from ..errors import (
    GISValidationCalculationError,
    GISValidationDataContractError,
    GISValidationError,
    GISValidationInputError,
)
from ..schemas import (
    GeoJSONUploadSchema,
    GISValidationRequestSchema,
)


logger = logging.getLogger(__name__)
DEV_MODE = os.getenv('LOG_ENV', 'dev') == 'dev'

blp = Blueprint(
    'GIS Validations',
    __name__,
    description='Running GISOO validation workflows.',
)


def _buildings_input_from_request(request_data):
    if request_data.get('buildings_set_path'):
        return request_data['buildings_set_path']
    return request_data.get('buildings_set')


def _load_validation_request_data(raw_payload):
    if raw_payload is None:
        abort(400, message='Request body must be valid JSON.')

    if isinstance(raw_payload, list):
        raw_payload = {'buildings_set': raw_payload}
    elif isinstance(raw_payload, dict):
        if (
                raw_payload.get('type') in {'FeatureCollection', 'Feature'}
                and 'buildings_set' not in raw_payload
                and 'buildings_set_path' not in raw_payload):
            raw_payload = {'buildings_set': raw_payload}
    else:
        abort(
            400,
            message=(
                'Request body must be a GeoJSON object, a feature list, or a '
                'validation request object.'))

    try:
        return GISValidationRequestSchema().load(raw_payload)
    except ValidationError as exc:
        abort(
            422,
            message='Invalid validation request payload',
            errors=exc.messages)


def _run_validation_workflow(
        request_data,
        *,
        request_received_log,
        request_failed_log):
    export_format = (request.args.get('export') or '').strip().lower()
    if export_format == 'json':
        export_format = ''
    if export_format and export_format not in {'csv', 'plot'}:
        abort(
            400,
            message='Unsupported export format. Supported values: csv, plot')

    logger.info(request_received_log)
    try:
        result = GISValidationApplicationService.run_validation(
            buildings_set=_buildings_input_from_request(request_data),
            census_code_field_title=request_data['census_code_field_title'],
            census_units_num_title=request_data['census_units_num_title'],
            postal_code_key=request_data['postal_code_key'],
            function_key=request_data['function_key'],
            function_value=request_data['function_value'],
            area_key=request_data['area_key'],
            floor_num_key=request_data['floor_num_key'],
            height_key=request_data['height_key'],
            census_avg_area_by_type=request_data.get(
                'census_avg_area_by_type'),
            output_mode='none',
            district_name=request_data['district_name'],
            plot_title=request_data.get('plot_title'))
    except HTTPException:
        raise
    except GISValidationInputError as exc:
        logger.warning('gis_validation_bad_input', extra={'error': str(exc)})
        abort(400, message=str(exc))
    except (GISValidationDataContractError,
            GISValidationCalculationError) as exc:
        logger.warning(
            'gis_validation_contract_or_calculation_error',
            extra={'error': str(exc)})
        abort(422, message=str(exc))
    except GISValidationError as exc:
        logger.exception(request_failed_log)
        public_msg = (
            str(exc) if (DEV_MODE or current_app.debug)
            else 'Failed to run GIS validation'
        )
        abort(500, message=public_msg)
    except Exception as exc:
        logger.exception('gis_validation_unhandled_exception')
        public_msg = (
            str(exc) if (DEV_MODE or current_app.debug)
            else 'Failed to run GIS validation'
        )
        abort(500, message=public_msg)

    logger.info(
        'gis_validation_succeeded',
        extra={
            'district_codes': len(result.codes),
            'export': export_format or 'json',
        })

    if export_format == 'csv':
        return _csv_response(result, request_data['district_name'])
    if export_format == 'plot':
        return _plot_response(result, request_data)
    return jsonify(_result_to_response(result)), 201


def _result_to_response(result):
    dataframe = result.comparison_dataframe
    records = json.loads(dataframe.to_json(orient='records'))
    return {
        'codes': list(result.codes),
        'rows_count': len(records),
        'comparison_table': records,
    }


def _csv_response(result, district_name):
    csv_text = result.comparison_dataframe.to_csv(index=False)
    filename = f'validate_{district_name}_gi.csv'
    return Response(
        csv_text,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'})


def _plot_response(result, request_data):
    dataframe = result.comparison_dataframe
    fig, _ = result.validator.plot_area_comparison(
        codes_info=dataframe['FSA'],
        areas=dataframe['Cleaned Total Area (with proxy)'],
        census_areas=dataframe['Census Total Area (by type)'],
        title=(
            request_data.get('plot_title')
            or f"Area comparison - {request_data['district_name']}"
        ),
        y_label='Area (m^2)',
        x_label='Cleaned')

    image = io.BytesIO()
    try:
        fig.savefig(image, format='png', dpi=150)
        image.seek(0)
    finally:
        try:
            import matplotlib.pyplot as plt
            plt.close(fig)
        except Exception:
            pass

    filename = f"{request_data['district_name']}_area_comparison.png"
    return send_file(
        image,
        mimetype='image/png',
        as_attachment=False,
        download_name=filename)


@blp.route('/validations')
class GISValidations(MethodView):
    """Runs GISOO validation from pasted GeoJSON content or a server path."""

    def post(self):
        request_data = _load_validation_request_data(
            request.get_json(silent=True))
        return _run_validation_workflow(
            request_data,
            request_received_log='gis_validation_request_received',
            request_failed_log='gis_validation_request_failed')


@blp.route('/validations/upload')
class GISValidationUpload(MethodView):
    """Runs GISOO validation from an uploaded GeoJSON file."""

    @blp.arguments(GeoJSONUploadSchema, location='files')
    def post(self, files_data):
        geojson_file = files_data['geojson_file']
        if not geojson_file or not getattr(geojson_file, 'filename', ''):
            abort(400, message='geojson_file is required')

        try:
            buildings_set = json.load(geojson_file.stream)
        except json.JSONDecodeError:
            abort(400, message='Invalid JSON content in geojson_file')

        raw_request_data = request.form.to_dict()
        raw_request_data['buildings_set'] = buildings_set
        try:
            request_data = GISValidationRequestSchema().load(raw_request_data)
        except ValidationError as exc:
            abort(
                422,
                message='Invalid validation upload payload',
                errors=exc.messages)

        return _run_validation_workflow(
            request_data,
            request_received_log='gis_validation_upload_request_received',
            request_failed_log='gis_validation_upload_request_failed')
