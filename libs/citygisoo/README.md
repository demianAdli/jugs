<p align="center">
  <img src="https://demianadli.com/projects_en/citygisoo/logo.png" alt="citygisoo logo" width="960">
</p>

# citygisoo

Project Developer: Alireza Adli

## Table of Contents

- [What Is citygisoo](#what-is-citygisoo)
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

To use PyQGIS without having the QGIS application run in the background, one needs to add the python path to the environment variables. Here is how to do it on Windows:

1. Install QGIS.

2. Assign a specific name to the QGIS Python executable.
   This is done to access QGIS Python from command prompt without mixing with the system Python installation(s).

   a. Go to the QGIS installation directory's Python folder (for example: `C:\Program Files\QGIS 3.34.1\apps\Python39`).  
   b. Rename the Python executable (`python.exe`) to a specific desired name, for example `pythonqgis.exe`.

3. Update environment variables.

   a. Open Environment Variables from Windows Start.  
   b. Edit `Path` and add:

   > `C:\Program Files\QGIS 3.34.1\apps\Python39`

   c. Create/Edit `PYTHONPATH` and add (separated by semicolons):

   > i. `C:\Program Files\QGIS 3.34.1\apps\qgis\python`  
   > ii. `C:\Program Files\QGIS 3.34.1\apps\qgis\python\plugins`  
   > iii. `C:\Program Files\QGIS 3.34.1\apps\Qt5\plugins`  
   > iv. `C:\Program Files\QGIS 3.34.1\apps\gdal\share\gdal`  
   > v. Or all together: `C:\Program Files\QGIS 3.34.1\apps\qgis\python;C:\Program Files\QGIS 3.34.1\apps\qgis\python\plugins;C:\Program Files\QGIS 3.34.1\apps\Qt5\plugins;C:\Program Files\QGIS 3.34.1\apps\gdal\share\gdal`

4. Validate importing `qgis.core`.

   a. Open a command prompt window.
   b. Run `pythonqgis`.
   c. If setup is correct, there should be no import error.
   d. In Python, run:

   > `import qgis.core`

`citygisoo` must be installed with `pip` in the interpreter configured above.

## Name and Dedication

In Persian, `gisoo` refers to long hair, especially long or braided hair, and the word is most commonly used when speaking about a woman’s hair.

I began developing this project in the aftermath of the Woman, Life, Freedom movement in Iran. The movement emerged following the killing of Mahsa Jina Amini, who died in the custody of the Islamic Republic’s morality police after being arrested for allegedly violating the state’s compulsory hijab rules.

Since the Woman, Life, Freedom movement, the enforcement of hijab restrictions in Iran has changed significantly. Although no formal legal reform has been enacted, the rules are no longer enforced in the same way as before.

While working with geospatial data of Montréal, the shape of the island on the map reminded me of a ponytail—like a gisoo. This association inspired the name of the project. I chose `gisoo` as a small tribute to the courage of the women in Iran who have fought for freedom and human rights.
