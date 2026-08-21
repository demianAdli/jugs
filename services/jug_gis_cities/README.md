# jug_gis_cities

**Project Designer and Developer:** Alireza Adli  
**Website:** [demianadli.com](https://demianadli.com)  
**Contact:** [demianadli.com/profile](https://demianadli.com/profile)

Geospatial data-cleaning service for Sabu that utilizes `citygisoo` to develop automated geospatial data-cleaning workflows for different cities and municipalities.

This directory contains the packaging, Dockerization, and REST API files for the technical part of the service. The automated geospatial workflows can be found in:

```text
src/jug_gis_cities
```

Inside `src/jug_gis_cities`, workflow components follow the naming convention:

```text
[district_name]_gisoo
```

The most updated case is `mtl_fsa_gisoo`. In this name, `fsa` refers to using Forward Sortation Areas (FSAs) to divide a larger district into smaller areas for workflow execution.

## Table of Contents

- [Overview](#overview)
- [Logs](#logs)
- [Install For Local Runs](#install-for-local-runs)
- [Direct Python Run](#direct-python-run)
- [REST API Run](#rest-api-run)
- [Docker API Run](#docker-api-run)
- [Docker Direct Run](#docker-direct-run)
- [Published Package Docker Build](#published-package-docker-build)

## Overview

`jug_gis_cities` is the Sabu geospatial data-cleaning service for city and municipality workflows. It imports and uses `citygisoo`, a PyQGIS-based shared library, to compose reusable automated or semi-automated geospatial data-cleaning workflows.

The service-level technical infrastructure is kept in the current service directory. This includes package configuration, Docker files, REST API execution, and deployment-related files.

The city- or district-specific workflow logic is organized under:

```text
src/jug_gis_cities
```

Each workflow component is named using the convention:

```text
[district_name]_gisoo
```

Examples include:

```text
saint_malachie_gisoo
mtl_fsa_gisoo
```

In `mtl_fsa_gisoo`, the `fsa` part refers to Forward Sortation Areas. This workflow uses FSAs to divide a larger district into smaller areas so that the cleaning workflow can be executed in a more manageable way.

## Logs

Logs are written to:

```text
services/jug_gis_cities/logs/jug_gis_cities.log
```

unless `LOG_DIR_BASE` or `LOG_FILE_NAME` is overridden.

## Install For Local Runs

Install the service into the Python environment that can import QGIS:

```powershell
cd <sabu-root>
python -m pip install -e .\libs\sabu_chassis
python -m pip install -e .\libs\citygisoo
python -m pip install -e .\services\jug_gis_cities
```

## Direct Python Run

Run the Saint-Malachie component in standardized mode:

```powershell
cd <sabu-root>
python -m jug_gis_cities --component saint_malachie_gisoo --mode standardize
```

Use `--mode independent` to run only the component workflow without the
contract adapter.

```powershell
python -m jug_gis_cities --component saint_malachie_gisoo --mode independent
```

Run the Montreal FSA component for one district by passing the three-character
FSA. Lowercase input is accepted and normalized to uppercase.

```powershell
python -m jug_gis_cities --component mtl_fsa_gisoo --mode independent --fsa H3H
```

By default, every workflow output is retained. Opt in to removing intermediate
Montreal FSA datasets after a successful run with `--cleanup-outputs`:

```powershell
python -m jug_gis_cities `
  --component mtl_fsa_gisoo `
  --mode standardize `
  --fsa H3H `
  --cleanup-outputs
```

Cleanup always retains `fsa_boundary`, `nrcan_fixed`, `roll`, `usage_fixed`,
`mtl_H3H_gisoo`, and the standardized output when one is produced. Use the
repeatable `--keep-output` option to retain additional workflow output keys:

```powershell
python -m jug_gis_cities `
  --component mtl_fsa_gisoo `
  --mode standardize `
  --fsa H3H `
  --cleanup-outputs `
  --keep-output usage_clean `
  --keep-output inter_summary
```

Leaving out `--cleanup-outputs` is equivalent to `cleanup_outputs=False` and
preserves all generated datasets.

Cleanup-enabled runs execute the PyQGIS workflow in a disposable spawned
worker. The worker inherits the active Python environment (for example
`pyqgis44`), shuts down after producing the raw and standardized outputs, and
the coordinating process deletes intermediates only after all QGIS/GDAL file
handles have been released. No interpreter path is hardcoded.

Run selected FSAs with three workers:

```powershell
python -m jug_gis_cities `
  --component mtl_fsa_gisoo `
  --mode standardize `
  --fsas H3H H2X `
  --max-workers 3 `
  --cleanup-outputs `
  --keep-output usage_clean `
  --keep-output inter_summary
```

Run every FSA discovered from the component's `workflow_config.py` with the
same settings:

```powershell
python -m jug_gis_cities `
  --component mtl_fsa_gisoo `
  --mode standardize `
  --all-fsas `
  --max-workers 3 `
  --cleanup-outputs `
  --keep-output usage_clean `
  --keep-output inter_summary
```

## REST API Run

Start the API:

```powershell
cd <sabu-root>\services\jug_gis_cities
$env:JUG_GIS_CITIES_JOB_STORE_PATH = ".\data\job_store\jobs.sqlite3"
python -m flask --app app run --host 127.0.0.1 --port 5000
```

Start the persistent batch worker in a second PowerShell session. The API and
worker must use the same `JUG_GIS_CITIES_JOB_STORE_PATH`:

```powershell
$env:JUG_GIS_CITIES_JOB_STORE_PATH = ".\data\job_store\jobs.sqlite3"
python -m jug_gis_cities.batch_worker
```

Run the Saint-Malachie standardized workflow through the API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:5000/components/saint_malachie_gisoo/runs `
  -ContentType "application/json" `
  -Body '{"mode":"standardize"}'
```

Run only the independent workflow through the API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:5000/components/saint_malachie_gisoo/runs `
  -ContentType "application/json" `
  -Body '{"mode":"independent"}'
```

Run the Montreal FSA workflow through the API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:5000/components/mtl_fsa_gisoo/runs `
  -ContentType "application/json" `
  -Body '{"mode":"independent","fsa":"H3H"}'
```

Enable cleanup and retain extra output keys through the API with:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:5000/components/mtl_fsa_gisoo/runs `
  -ContentType "application/json" `
  -Body '{"mode":"standardize","fsa":"H3H","cleanup_outputs":true,"keep_outputs":["usage_clean","inter_summary"]}'
```

Submit all configured FSAs asynchronously with three local worker processes:

```powershell
$batch = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:5000/components/mtl_fsa_gisoo/batch-runs `
  -ContentType "application/json" `
  -Body '{"mode":"standardize","all_fsas":true,"max_workers":3,"cleanup_outputs":true,"keep_outputs":["usage_clean","inter_summary"]}'
```

Poll its persistent status and ordered per-FSA results:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:5000/components/mtl_fsa_gisoo/batch-runs/$($batch.batch_id)"
```

Use `"fsas":["H3H","H2X"]` instead of `"all_fsas":true` to submit a
selected batch. The API returns `202 Accepted`; status is one of `queued`,
`running`, `succeeded`, or `failed`. A failed batch still includes successful
and failed per-FSA results.

The same JSON fields apply to the Docker API. Docker direct execution accepts
the same CLI options as the local direct Python run.

Programmatic FSA batch runs accept a component name, use that component's
standard `workflow_config.py` FSA settings when discovering all districts, and
clean each successful FSA before moving on:

```python
run_fsa_batch(
    component_name="mtl_fsa_gisoo",
    mode="standardize",
    max_workers=3,
    cleanup_outputs=True,
    keep_outputs=["usage_clean", "inter_summary"],
)
```

FSA-capable components expose `run_workflow(fsa)` and define `qgis_path`,
`input_paths["fsa"]`, and `fsa_field_name` in `workflow_config.py`. Passing an
explicit `fsas` iterable skips boundary-layer discovery. The legacy
`run_mtl_fsa_batch()` interface remains available as a deprecated Montreal
compatibility wrapper for this release. CLI, API, worker, Docker, and new code
use the generic runner so the facade can be removed in the following version.

## Docker API Run

The Docker image includes PyQGIS and defaults to the REST API.

Build and run with Compose. This starts both the existing API container and a
batch worker from the same image:

```powershell
cd <sabu-root>
docker compose -f services/jug_gis_cities/docker-compose.yml up -d --build
```

Call the API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8081/components/saint_malachie_gisoo/runs `
  -ContentType "application/json" `
  -Body '{"mode":"standardize"}'
```

Run the Montreal FSA workflow through the Docker API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8081/components/mtl_fsa_gisoo/runs `
  -ContentType "application/json" `
  -Body '{"mode":"independent","fsa":"H3H"}'
```

Submit the whole-island batch through the Docker API:

```powershell
$batch = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8081/components/mtl_fsa_gisoo/batch-runs `
  -ContentType "application/json" `
  -Body '{"mode":"standardize","all_fsas":true,"max_workers":3,"cleanup_outputs":true,"keep_outputs":["usage_clean","inter_summary"]}'
```

The API and worker share the `jug_gis_cities_job_store` volume. Queued and
completed statuses survive container restarts; interrupted running jobs are
returned to the queue. A persistent component/FSA lock prevents asynchronous
batches and single-FSA API runs from writing the same output concurrently.

Compose mounts:

```text
services/jug_gis_cities/logs -> /app/logs
jug_gis_cities_job_store -> /data/job_store
D:/GIS/saint_malachie_gisoo_data -> /data/saint_malachie_gisoo_data
D:/GIS/mtl_gisoo_fsa_data -> /data/mtl_gisoo_fsa_data
```

## Docker Direct Run

Build the image:

```powershell
cd <sabu-root>
docker build `
  -f services/jug_gis_cities/docker/Dockerfile `
  -t demianadli/jug_gis_cities:0.1.0 `
  .
```

Run the component directly in the container:

```powershell
docker run --rm `
  -e LOG_SERVICE=gis_cities-direct `
  -e LOG_DIR_BASE=/app `
  -e LOG_FILE_NAME=logs/jug_gis_cities.log `
  -e JUG_GIS_CITIES_QGIS_PATH=/usr `
  -e JUG_GIS_CITIES_SAINT_MALACHIE_DATA_DIR=/data/saint_malachie_gisoo_data `
  -e JUG_GIS_CITIES_MTL_FSA_DATA_DIR=/data/mtl_gisoo_fsa_data `
  -v ${PWD}\services\jug_gis_cities\logs:/app/logs `
  -v D:\GIS\saint_malachie_gisoo_data:/data/saint_malachie_gisoo_data `
  -v D:\GIS\mtl_gisoo_fsa_data:/data/mtl_gisoo_fsa_data `
  demianadli/jug_gis_cities:0.1.0 `
  python3 -m jug_gis_cities --component saint_malachie_gisoo --mode standardize
```

Run the Montreal FSA component directly in the container:

```powershell
docker run --rm `
  -e LOG_SERVICE=gis_cities-direct `
  -e LOG_DIR_BASE=/app `
  -e LOG_FILE_NAME=logs/jug_gis_cities.log `
  -e JUG_GIS_CITIES_QGIS_PATH=/usr `
  -e JUG_GIS_CITIES_MTL_FSA_DATA_DIR=/data/mtl_gisoo_fsa_data `
  -v ${PWD}\services\jug_gis_cities\logs:/app/logs `
  -v D:\GIS\mtl_gisoo_fsa_data:/data/mtl_gisoo_fsa_data `
  demianadli/jug_gis_cities:0.1.0 `
  python3 -m jug_gis_cities --component mtl_fsa_gisoo --mode independent --fsa H3H
```

The same image also supports direct generic batches by replacing the final
command with:

```powershell
python3 -m jug_gis_cities --component mtl_fsa_gisoo --mode standardize --all-fsas --max-workers 3 --cleanup-outputs --keep-output usage_clean --keep-output inter_summary
```

## Published Package Docker Build

By default, the Dockerfile installs the local checkout. To build from PyPI
instead, set `INSTALL_LOCAL=false` and optionally pin package versions:

```powershell
docker build `
  -f services/jug_gis_cities/docker/Dockerfile `
  --build-arg INSTALL_LOCAL=false `
  --build-arg JUG_GIS_CITIES_VERSION=0.1.0 `
  --build-arg CITYGISOO_VERSION=0.2.1 `
  --build-arg SABU_CHASSIS_VERSION=0.1.1 `
  -t demianadli/jug_gis_cities:0.1.0 `
  .
```
