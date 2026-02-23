# JUG LCA Buildings Contract Artifacts

This folder contains example payloads for the `jug_lca_buildings` HTTP API.

Files
- `emissions.request.json`: Example JSON body for `POST /emissions`
- `emissions.response.201.json`: Example success response (201)
- `emissions.response.200.csv`: Example CSV download response for `POST /emissions?export=csv`
- `emissions_upload.response.400.invalid_json.json`: Example error when uploaded file is not valid JSON
- `emissions_upload.response.422.validation.json`: Example schema validation error shape (illustrative)

Notes
- For `POST /emissions/upload`, upload a GeoJSON file whose JSON content matches `emissions.request.json`.
- `POST /emissions` and `POST /emissions/upload` support `?export=csv` to return a downloadable CSV report (`200 text/csv`) instead of the JSON response (`201 application/json`).
- The exact `errors` structure in 422 responses can vary with `flask-smorest`/marshmallow versions.
