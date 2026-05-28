# JUG GIS Cities Contract Artifacts

This folder contains example payloads and runtime configuration artifacts for
`jug_gis_cities`.

The currently implemented HTTP API triggers an installed component by name:

```text
POST /components/{component_name}/runs
```

The request body currently accepts only `mode`:

- `standardize`: run the component workflow and then the contract adapter.
- `independent`: run only the component workflow.

Dataset manifests in this folder describe flexible input references for direct,
Docker, and future API-oriented execution. The current HTTP endpoint does not
accept those manifests yet.

Files
- `api_run_standardize.request.json`: Example API body for standardized mode.
- `api_run_standardize.response.201.json`: Example standardized-mode API response.
- `api_run_independent.request.json`: Example API body for independent mode.
- `api_run_independent.response.201.json`: Example independent-mode API response.
- `direct_application_config.standardize.json`: Example direct/application configuration.
- `docker_mounted_path_config.json`: Example Docker mounted-path configuration.
- `workflow_input_manifest.saint_malachie.example.json`: Role-based source dataset manifest.
- `standardized_output.example.geojson`: Example strict standardized GeoJSON output.
- `error.response.400.invalid_component_name.json`: Example invalid component-name error.
- `error.response.404.component_not_found.json`: Example component-not-found error.
- `error.response.422.invalid_mode.json`: Example validation error for unsupported mode.
- `error.response.422.component_contract.json`: Example component contract error.

Notes
- Input datasets are referenced by path or URI, not embedded.
- Example paths are generic container-style or public-style paths, not local
  workstation paths.
- `saint_malachie_gisoo` is used as the example component because it is the
  current implementation paradigm.
