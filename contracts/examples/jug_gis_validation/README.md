# JUG GIS Validation Contract Artifacts

This folder contains example payloads for the `jug_gis_validation` HTTP API.

Files
- `validations.request.geojson`: Raw GeoJSON body for `POST /validations`
- `validations.request.wrapper.json`: Wrapped JSON body for `POST /validations`
- `validations_path.request.json`: Path-based JSON body for `POST /validations`
- `validations.response.201.json`: Example JSON success response
- `validations.response.200.csv`: Example CSV download response for `POST /validations?export=csv`
- `validations.response.400.invalid_json.json`: Example invalid JSON error response
- `validations.response.422.validation.json`: Example validation/data-contract error response

Notes
- `POST /validations` accepts either a raw GeoJSON FeatureCollection or a wrapper object containing `buildings_set` or `buildings_set_path`.
- `POST /validations/upload` accepts a multipart `geojson_file` whose content matches `validations.request.geojson`.
- `POST /validations` and `POST /validations/upload` support `?export=csv` and `?export=plot`.
- Path-based inputs must use paths visible to the running service. In Docker Compose, host input data can be mounted under `/data/gis`.
- The exact `errors` structure in 422 responses can vary with `flask-smorest`/marshmallow versions.
