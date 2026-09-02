<p align="center">
  <img src="https://demianadli.com/projects_en/citygisoo/logo.png" alt="citygisoo logo" width="960">
</p>

# citygisoo

Project Developer: Alireza Adli

## Table of Contents

- [What Is citygisoo](#what-is-citygisoo)
- [What's New in Version 0.3](#whats-new-in-version-03)
- [Approach and Scope](#approach-and-scope)
- [citygisoo in Sabu](#citygisoo-in-sabu)
- [Testing and Publication Context](#testing-and-publication-context)
- [Logging](#logging)
- [Gathering standardized district GeoJSON files](#gathering-standardized-district-geojson-files)
- [ScrubLayer](#scrublayer)
- [FieldSchemaManager](#fieldschemamanager)
- [BuildingContractAdapter](#buildingcontractadapter)
- [Setting up an environment to use standalone PyQGIS - How to import qgis.core](#setting-up-an-environment-to-use-standalone-pyqgis---how-to-import-qgiscore)
- [Name and Dedication](#name-and-dedication)

## What Is citygisoo

`citygisoo` is a Python package that leverages PyQGIS functions for cleaning building-related geospatial data, with the goal of supporting automated data-cleaning pipelines.

The name `citygisoo` stands for **Object-Oriented Geographic Information System for Cities**.

The package follows an object-oriented design. Its central component is the `ScrubLayer` class, which consolidates key cleaning and transformation operations commonly used in city-scale workflows.

## What's New in Version 0.3

Version 0.3 broadens `citygisoo` beyond direct PyQGIS layer-cleaning
operations. PyQGIS remains its geospatial processing engine, while the package
now also coordinates higher-level, repeatable dataset-preparation workflows.

The expanded functionality supports standardizing building datasets into
consistent GeoJSON and GeoPackage outputs for downstream systems such as
urban-scale carbon accounting and building-archetype assignment. It also helps
organize results produced across subdistrict and district pipelines and adds
more options for filtering, enriching, aggregating, joining, and overlaying
geospatial records.

For detailed component descriptions and API guidance, see the
[citygisoo documentation](https://sabu.demianadli.com/libraries/citygisoo/).

## Approach and Scope

`citygisoo` builds on existing PyQGIS functionality and, where necessary, extends or combines these capabilities to support additional operations required for automated geospatial data cleaning.

The design principles and methodology behind this approach will be discussed in more detail in upcoming papers and reports.

## citygisoo in Sabu

`citygisoo` is a shared library within the Sabu project.

Sabu is a sector-based carbon-emission evaluation framework built on a microservices architecture.

Each module runs as an independent service (a “jug”). Current services focus on building life-cycle assessment and city-scale geospatial cleaning and validation workflows. In addition to these services, Sabu includes shared Python libraries such as `sabu-chassis`, which provide reusable internal functionality.

## Testing and Publication Context

`citygisoo` was initially tested using geospatial data from Montréal Island.

It is now being published so that it can be applied to other cities simply by installing the package via `pip`.

## Logging

`citygisoo` uses the `sabu-chassis` logging system to provide consistent operational messages across its workflows. Layer loading, exports, schema changes, cleaning operations, and adapter runs report progress and failures through package loggers instead of ad hoc console output.

This makes `citygisoo` easier to use inside larger Sabu workflows while still keeping the package useful in standalone PyQGIS scripts.

## Gathering standardized district GeoJSON files

`gather_district_geojson_files()` collects standardized GeoJSON results from
the subdistrict directories belonging to a district. It discovers each
subdistrict name from the immediate child directories of the input path and
expects this structure:

```text
<input_path>/
  <subdistrict_name>/
    <district_name>_<subdistrict_name>_gisoo_standardized/
      <district_name>_<subdistrict_name>_gisoo_standardized.geojson
```

Provide the district name separately so the same function can be used for
different districts:

```python
from citygisoo.basic_functions import gather_district_geojson_files

gather_district_geojson_files(
    input_path=r"C:\path\to\processing_results",
    district_name="mtl",
    output_path=r"C:\path\to\gathered_geojson",
)
```

The function validates every expected source file before copying anything. If
a subdistrict result is missing, it raises `FileNotFoundError` with the missing
path or paths. The output directory is created when necessary, and an existing
file with the same standardized name is updated on subsequent runs. If the
output directory is an immediate child of the input directory, it is excluded
from subdistrict discovery.

## ScrubLayer

`ScrubLayer` is the core class of the package. It wraps and orchestrates essential PyQGIS operations used in geospatial cleaning workflows and provides higher-level methods for automating multi-step tasks.

## FieldSchemaManager

`FieldSchemaManager` manages attribute-field schema operations for PyQGIS map layers. It can work with an existing `ScrubLayer` instance or load a layer directly from a file path.

The class is designed for preparing layer attributes without changing feature geometries. It supports common schema-cleaning tasks such as listing fields, checking required fields, renaming fields, dropping fields, keeping only selected fields, reordering fields, exporting layers to GeoJSON, detecting null-like required values, removing incomplete features, adding ID fields, and promoting GeoJSON IDs to the feature level.

`FieldSchemaManager` is useful when a workflow needs the same field-preparation logic across different supported layer formats, including Shapefile and GeoJSON.

## BuildingContractAdapter

`BuildingContractAdapter` prepares building map layers for a standardized GeoJSON building contract used by downstream workflows such as UBEM archetype assignment.

The adapter uses `FieldSchemaManager` to orchestrate the field-preparation workflow. It validates required source fields, exports the input layer to GeoJSON, renames source fields into the expected contract schema, keeps only required contract fields, removes features with missing required values, adds generated integer IDs, and promotes those IDs to GeoJSON feature-level IDs.

This class is intended for repeatable city-specific building-data preparation, where the input layer may use local field names but the downstream service expects a stable contract schema.

## Setting up an environment to use standalone PyQGIS - How to import qgis.core

On Windows, run standalone PyQGIS code with the Python interpreter bundled with
QGIS. Use a custom batch-file command so that this interpreter remains distinct
from other Python installations.

> [!IMPORTANT]
> Do not rename `python.exe` inside a QGIS or OSGeo4W installation. QGIS tools may
> expect that executable name. Also, do not combine paths from different QGIS
> installations or versions in one environment.

The examples below use an OSGeo4W installation at `C:\OSGeo4W`, QGIS LTR, and
Python 3.12. Check the directories in your installation and adjust
`OSGEO4W_ROOT`, `QGIS_RELEASE`, and `QGIS_PYTHON` as needed. For example, a
standalone QGIS installation might use `C:\Program Files\QGIS 3.44.0` as its
root and `qgis` instead of `qgis-ltr` as its release directory.

1. Install QGIS with the standalone installer or OSGeo4W.

2. Create a directory for custom commands. For example:

   ```text
   C:\Users\<your-user>\qgis_scripts
   ```

3. In that directory, create `pythonqgis.bat` with the following content:

   ```bat
   @echo off
   setlocal
   set "OSGEO4W_ROOT=C:\OSGeo4W"
   set "QGIS_RELEASE=qgis-ltr"
   set "QGIS_PYTHON=Python312"
   set "PATH=%OSGEO4W_ROOT%\bin;%OSGEO4W_ROOT%\apps\%QGIS_RELEASE%\bin;%OSGEO4W_ROOT%\apps\%QGIS_PYTHON%;%PATH%"
   set "PYTHONPATH=%OSGEO4W_ROOT%\apps\%QGIS_RELEASE%\python;%OSGEO4W_ROOT%\apps\%QGIS_RELEASE%\python\plugins"
   "%OSGEO4W_ROOT%\apps\%QGIS_PYTHON%\python.exe" %*
   endlocal
   ```

   The launcher sets the QGIS environment only for the process it starts. This
   avoids changing `PATH` and `PYTHONPATH` globally. The Qt plugin and GDAL data
   directories are resources, not Python module directories, so they should not
   be added to `PYTHONPATH`.

4. Add the custom-command directory—not QGIS's `python.exe` directory—to your
   Windows user `Path`:

   ```text
   C:\Users\<your-user>\qgis_scripts
   ```

   Open a new Command Prompt after saving the change so that it receives the
   updated `Path`.

5. Validate the launcher and the `qgis.core` import:

   ```bat
   where pythonqgis
   pythonqgis --version
   pythonqgis -c "import qgis.core; print(qgis.core.Qgis.QGIS_VERSION)"
   ```

6. Install `citygisoo` with the same interpreter:

   ```bat
   pythonqgis -m pip install citygisoo
   ```

Use `pythonqgis your_script.py` to run a standalone script. Importing
`qgis.core` confirms that Python can find the bindings; a script that uses QGIS
providers and layers should also initialize and shut down `QgsApplication`, as
shown in the [official PyQGIS standalone-script documentation](https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/intro.html#using-pyqgis-in-standalone-scripts).
Do not name the script `qgis.py`, because that would shadow the installed `qgis`
package.

```python
from qgis.core import QgsApplication

QgsApplication.setPrefixPath(r"C:\OSGeo4W\apps\qgis-ltr", True)
qgs = QgsApplication([], False)
qgs.initQgis()

try:
    # Import citygisoo and run the PyQGIS workflow here.
    pass
finally:
    qgs.exitQgis()
```

## Name and Dedication

In Persian, `gisoo` refers to long hair, especially long or braided hair, and the word is most commonly used when speaking about a woman’s hair.

I began developing this project in the aftermath of the Woman, Life, Freedom movement in Iran. The movement emerged following the killing of Mahsa Jina Amini, who died in the custody of the Islamic Republic’s morality police after being arrested for allegedly violating the state’s compulsory hijab rules.

Since the Woman, Life, Freedom movement, the enforcement of hijab restrictions in Iran has changed significantly. Although no formal legal reform has been enacted, the rules are no longer enforced in the same way as before.

While working with geospatial data of Montréal, the shape of the island on the map reminded me of a ponytail—like a gisoo. This association inspired the name of the project. I chose `gisoo` as a small tribute to the courage of the women in Iran who have fought for freedom and human rights.
