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
    fsa = fields.String(
        allow_none=True,
        validate=validate.Regexp(
            r'^[A-Za-z][0-9][A-Za-z]$',
            error=(
                'fsa must be a three-character Canadian FSA, '
                'for example H3H.')),
    )
    drop_null_fields = fields.List(
        fields.String(validate=validate.Length(min=1)),
        allow_none=True,
        load_default=None,
    )
    cleanup_outputs = fields.Boolean(load_default=False)
    keep_outputs = fields.List(
        fields.String(validate=validate.Length(min=1)),
        allow_none=True,
        load_default=None,
    )


class GISComponentRunResultSchema(Schema):
    """Schema for a GIS component run result."""

    component_name = fields.String(required=True)
    mode = fields.String(required=True)
    fsa = fields.String(allow_none=True)
    workflow_output_path = fields.String(required=True)
    standardized_output_path = fields.String(allow_none=True)
    cleaned_output_paths = fields.List(fields.String(), required=True)
