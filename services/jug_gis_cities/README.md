# jug_gis_cities

Geospatial data-cleaning service for Sabu city GIS components.

## Direct Python run

Install the service into the Python environment that can import QGIS:

```powershell
pyqgis344 -m pip install -e .
```

Run the Saint-Malachie component:

```powershell
pyqgis344 -m jug_gis_cities --component saint_malachie_gisoo --mode standardize
```

Use `--mode independent` to run only the component workflow without the
contract adapter.
