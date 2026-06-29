"""
Sabu project
jug_gis_cities package
gis_components resource module
REST resource for running city GIS cleaning components.
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""
import logging
import os

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from werkzeug.exceptions import HTTPException

from ..application import (
    GisComponentContractError,
    GisComponentError,
    GisComponentNotFoundError,
    GISCitiesApplicationService,
)
from ..schemas import (
    GISComponentRunRequestSchema,
    GISComponentRunResultSchema,
)


logger = logging.getLogger(__name__)
DEV_MODE = os.getenv('LOG_ENV', 'dev') == 'dev'

blp = Blueprint(
    'GIS Components',
    __name__,
    description='Running city GIS cleaning components.',
)


def _result_to_response(result):
    return {
        'component_name': result.component_name,
        'mode': result.mode.value,
        'fsa': result.fsa,
        'workflow_output_path': result.workflow_output_path,
        'standardized_output_path': result.standardized_output_path,
    }


def _run_gis_component(component_name, request_data):
    mode = request_data.get('mode')
    fsa = request_data.get('fsa')
    logger.info(
        'gis_component_run_received',
        extra={
            'component_name': component_name,
            'mode': mode,
            'fsa': fsa,
        },
    )

    try:
        result = GISCitiesApplicationService.run_component(
            component_name=component_name,
            mode=mode,
            fsa=fsa,
        )
    except HTTPException:
        raise
    except GisComponentNotFoundError as exc:
        logger.warning(
            'gis_component_run_not_found',
            extra={
                'component_name': component_name,
                'mode': mode,
                'fsa': fsa,
                'error': str(exc),
            },
        )
        abort(404, message=str(exc))
    except GisComponentContractError as exc:
        logger.warning(
            'gis_component_run_contract_invalid',
            extra={
                'component_name': component_name,
                'mode': mode,
                'fsa': fsa,
                'error': str(exc),
            },
        )
        abort(422, message=str(exc))
    except (TypeError, ValueError) as exc:
        logger.warning(
            'gis_component_run_bad_request',
            extra={
                'component_name': component_name,
                'mode': mode,
                'fsa': fsa,
                'error': str(exc),
            },
        )
        abort(400, message=str(exc))
    except GisComponentError as exc:
        logger.exception(
            'gis_component_run_failed',
            extra={
                'component_name': component_name,
                'mode': mode,
                'fsa': fsa,
            },
        )
        public_msg = (
            str(exc) if (DEV_MODE or current_app.debug)
            else 'Failed to run GIS component'
        )
        abort(500, message=public_msg)
    except Exception as exc:
        logger.exception(
            'gis_component_run_unhandled_exception',
            extra={
                'component_name': component_name,
                'mode': mode,
                'fsa': fsa,
            },
        )
        public_msg = (
            str(exc) if (DEV_MODE or current_app.debug)
            else 'Failed to run GIS component'
        )
        abort(500, message=public_msg)

    response_data = _result_to_response(result)
    logger.info(
        'gis_component_run_succeeded',
        extra={
            'component_name': result.component_name,
            'mode': result.mode.value,
            'fsa': result.fsa,
            'workflow_output_path': result.workflow_output_path,
            'standardized_output_path': result.standardized_output_path,
        },
    )
    return response_data


@blp.route('/components/<string:component_name>/runs')
class GISComponentRuns(MethodView):
    """Runs a configured GIS component."""

    @blp.arguments(GISComponentRunRequestSchema)
    @blp.response(201, GISComponentRunResultSchema)
    def post(self, request_data, component_name):
        return _run_gis_component(component_name, request_data)
