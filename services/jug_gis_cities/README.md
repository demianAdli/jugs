# jug_gis_cities

Geospatial data-cleaning service for Sabu city GIS components.

Logs are written to:

```text
services/jug_gis_cities/logs/jug_gis_cities.log
```

unless `LOG_DIR_BASE` or `LOG_FILE_NAME` is overridden.

## Install For Local Runs

Install the service into the Python environment that can import QGIS:

```powershell
cd C:\Users\a_adli\docker_projects\sabu
pyqgis344 -m pip install -e .\libs\sabu_chassis
pyqgis344 -m pip install -e .\libs\citygisoo
pyqgis344 -m pip install -e .\services\jug_gis_cities
```

## Direct Python Run

Run the Saint-Malachie component in standardized mode:

```powershell
cd C:\Users\a_adli\docker_projects\sabu
pyqgis344 -m jug_gis_cities --component saint_malachie_gisoo --mode standardize
```

Use `--mode independent` to run only the component workflow without the
contract adapter.

```powershell
pyqgis344 -m jug_gis_cities --component saint_malachie_gisoo --mode independent
```

## REST API Run

Start the API:

```powershell
cd C:\Users\a_adli\docker_projects\sabu\services\jug_gis_cities
pyqgis344 -m flask --app app run --host 127.0.0.1 --port 5000
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

## Docker API Run

The Docker image includes PyQGIS and defaults to the REST API.

Build and run with Compose:

```powershell
cd C:\Users\a_adli\docker_projects\sabu
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

Compose mounts:

```text
services/jug_gis_cities/logs -> /app/logs
D:/GIS/saint_malachie_gisoo_data -> /data/saint_malachie_gisoo_data
```

## Docker Direct Run

Build the image:

```powershell
cd C:\Users\a_adli\docker_projects\sabu
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
  -v ${PWD}\services\jug_gis_cities\logs:/app/logs `
  -v D:\GIS\saint_malachie_gisoo_data:/data/saint_malachie_gisoo_data `
  demianadli/jug_gis_cities:0.1.0 `
  python3 -m jug_gis_cities --component saint_malachie_gisoo --mode standardize
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
