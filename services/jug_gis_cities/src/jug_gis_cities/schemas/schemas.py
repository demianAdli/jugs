"""
Sabu project
jug_gis_cities package
schemas module
Defines REST API request and response schemas.
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
alireza.adli4@gmail.com
www.demianadli.com
"""

from marshmallow import Schema, fields, validate

from ..application import GisComponentRunMode


class GISComponentRunRequestSchema(Schema):
    """Schema for triggering a GIS component run."""

    mode = fields.String(
        load_default=GisComponentRunMode.STANDARDIZE.value,
        validate=validate.OneOf(
            [mode.value for mode in GisComponentRunMode]),
    )


class GISComponentRunResultSchema(Schema):
    """Schema for a GIS component run result."""

    component_name = fields.String(required=True)
    mode = fields.String(required=True)
    workflow_output_path = fields.String(required=True)
    standardized_output_path = fields.String(allow_none=True)
