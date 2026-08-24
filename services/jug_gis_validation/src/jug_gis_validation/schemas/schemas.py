"""
Sabu project
jug_gis_validation project
jug_gis_validation package
Project Designer and Developer: Alireza Adli
alireza.adli@mail.concordia.ca
https://demianadli.com/

Marshmallow schemas for GISOO validation API requests and responses.

"""
from __future__ import annotations

from marshmallow import EXCLUDE, Schema, fields, validates_schema, ValidationError

from ..application.jug_gis_validation import (
    DEFAULT_AREA_KEY,
    DEFAULT_CENSUS_CODE_FIELD_TITLE,
    DEFAULT_CENSUS_UNITS_NUM_TITLE,
    DEFAULT_FLOOR_NUM_KEY,
    DEFAULT_FUNCTION_KEY,
    DEFAULT_FUNCTION_VALUE,
    DEFAULT_HEIGHT_KEY,
    DEFAULT_POSTAL_CODE_KEY,
)


class GISValidationRequestSchema(Schema):
    """Request body for validating a buildings_set."""

    class Meta:
        unknown = EXCLUDE

    buildings_set = fields.Raw(load_default=None)
    buildings_set_path = fields.String(load_default=None)

    census_code_field_title = fields.String(
        load_default=DEFAULT_CENSUS_CODE_FIELD_TITLE)
    census_units_num_title = fields.String(
        load_default=DEFAULT_CENSUS_UNITS_NUM_TITLE)
    postal_code_key = fields.String(load_default=DEFAULT_POSTAL_CODE_KEY)
    function_key = fields.String(load_default=DEFAULT_FUNCTION_KEY)
    function_value = fields.Raw(load_default=DEFAULT_FUNCTION_VALUE)
    area_key = fields.String(load_default=DEFAULT_AREA_KEY)
    floor_num_key = fields.String(load_default=DEFAULT_FLOOR_NUM_KEY)
    height_key = fields.String(load_default=DEFAULT_HEIGHT_KEY)
    unique_attribute_key = fields.String(load_default=None, allow_none=True)
    census_avg_area_by_type = fields.Dict(
        keys=fields.String(),
        values=fields.Float(),
        load_default=None)
    district_name = fields.String(load_default='validation')
    plot_title = fields.String(load_default=None)

    @validates_schema
    def validate_buildings_input(self, data, **kwargs):
        has_content = data.get('buildings_set') is not None
        has_path = bool(data.get('buildings_set_path'))
        if not has_content and not has_path:
            raise ValidationError(
                'Either buildings_set or buildings_set_path is required.')
        if has_content and has_path:
            raise ValidationError(
                'Provide only one of buildings_set or buildings_set_path.')


class GeoJSONUploadSchema(Schema):
    """Multipart upload schema for a buildings_set GeoJSON file."""

    geojson_file = fields.Field(
        required=True,
        metadata={"type": "string", "format": "binary"})


class GISValidationResultSchema(Schema):
    """JSON response for a validation run."""

    codes = fields.List(fields.String(), required=True)
    rows_count = fields.Integer(required=True)
    comparison_table = fields.List(fields.Dict(), required=True)
    uniquification = fields.Dict(required=True)
