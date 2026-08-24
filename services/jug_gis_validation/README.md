# GISOO Validation

**Project Developer:**  
**Alireza Adli**  
alireza.adli4@gmail.com  
alireza.adli@mail.concordia.ca  
[www.demianadli.com](https://demianadli.com/)

---

## Overview

**GISOO Validation** service is responsible for comparing cleaned geospatial datasets with census data to ensure consistency, completeness, and accuracy at the district level.

This validation module is part of the larger **Sabu framework**, supporting disaggregated carbon-emissions evaluation beginning from the building sector. It integrates naturally with CityGISOO’s automated cleaning workflows and provides a lightweight, extensible interface to perform data verification across postal-code prefixes (FSA).

According to the design description, the validator:

- Supports very large datasets and produces comparisons efficiently.
- Allows categorization by any user-defined factor.
- Outputs results in multiple formats (Python dictionary, DataFrame, CSV, plots).
- Is designed to work with **any city dataset** following cleaning and preparation through CityGISOO.

Repository path:  
https://github.com/demianAdli/sabu/tree/main/services/jug_gis_validation

---

## Table of Contents

- [Main Classes](#main-classes)
- [Features](#features)
- [Recommended Usage](#recommended-usage)
- [Outputs](#outputs)
- [Architecture](#architecture)
- [Contact](#contact)

---

## Main Classes

### ValidateGISOO

Coordinates the entire validation workflow:

- Loads district GeoJSON data
- Loads census CSV files
- Applies prefix-based (FSA) comparisons
- Adjusts values using floor counts when needed
- Filters by building function (optional)
- Produces aggregated comparison tables and reports

The class follows an _immutable-by-convention_ snapshot pattern to maintain reproducibility.

### DistrictGeoJSONAnalysis

Provides auxiliary district-level preprocessing:

- Postal-code prefix extraction
- Summaries by FSA
- Detection of missing or zero values
- Preparation of structures used by `ValidateGISOO`

---

## Features

- Prefix-based validation (first 3 characters of postal code)
- Flexible choice of validation fields (units, area, custom)
- Optional feature-based or attribute-based cleaned-unit counting
- Explicit `none`, `area-only`, or `area-times-floor` calculation modes
- Optional height-derived floor proxy diagnostic
- Optional filtering by building function
- Missing and zero-value detection
- Optional validation-only feature uniquification by an attribute, retaining
  the feature with the greatest configured area
- Extremely fast validation even for large datasets
- Designed to be highly extensible within the CityGISOO ecosystem

Uniquification is disabled by default. For Montreal standardized data, set
`unique_attribute_key` to `roll_provincial_id`. By default, duplicate ranking
uses `area_key`; set `uniquification_area_key` when ranking should use a
different field. For example, validation can calculate with `roll_area` while
duplicate selection uses `citygisoo_area`. This filters only the validator's
in-memory snapshot; it does not rewrite or delete cleaned GeoJSON features.

The default area calculation mode is `area-times-floor`, which preserves the
existing `area_key * floor_num_key` behavior. Use `area-only` when `area_key`
already represents total building area; in that mode `floor_num_key` is not
required. Use `none` to omit area comparison entirely; building area, floor,
and height fields are then not required unless an area field is separately
needed to rank duplicates during uniquification. `none` cannot be combined
with the height proxy. Height-proxy output is disabled by default and can be requested with
`include_height_proxy` or the CLI flag `--include-height-proxy`. Its base area
defaults to `area_key`; use `height_proxy_area_key` or
`--height-proxy-area-key` to select a different field. Unusable proxy-area
values can fall back to either `height_proxy_area_fallback_key` or
`height_proxy_area_fallback_value`. The choices are mutually exclusive; when
neither is supplied, the constant fallback defaults to `80.0`. Results report
the number and percentage of evaluated features that used the fallback.

By default, `Cleaned Units Num` remains the number of retained features. Set
`cleaned_units_num_key` (or CLI option `--cleaned-units-num-key`) to sum a
feature property such as `unit_num` instead. A NULL value contributes one unit;
other values must be finite, non-negative integers. Unit aggregation happens
after optional uniquification and uses the same building-function filter as the
existing validation workflow.

Python and CLI callers can persist the exact post-uniquification validation
snapshot with `uniquified_output_path` or `--uniquified-output-path`. The REST
API returns the same snapshot with `?export=geojson`. GeoJSON export requires
`unique_attribute_key`; the source dataset is never modified.

---

# Recommended Usage

## Use the Interactive Workflow (Jupyter Notebook)

The recommended way to use this module is through the interactive notebook:

**`interactive_validation_wf.ipynb`**

GitHub provides reliable `.ipynb` rendering, so **please use the following link**:

👉 **https://github.com/demianAdli/sabu/blob/main/services/jug_gis_validation/notebooks/interactive_validation_wf.ipynb**

Gitea currently has issues rendering Jupyter notebooks, so GitHub is the preferred viewer.

---

## Outputs

The validation workflow can generate:

- **Python dictionaries**
- **Pandas DataFrames**
- **CSV summary files**
- **Plots** for visual comparison

These outputs allow different levels of integration—from automated pipelines to manual inspection.

---

## Architecture

The validation service fits into the broader **Sabu framework**, following a modular and extensible microservice-based design:

- Uses a generic, city-agnostic workflow structure
- Can be orchestrated with GISOO-based services to validate their results
- Can be executed as a standalone service or embedded in a more automated sequence
- Supports the architectural goals of Sabu: modularity, reusability, and scalability

---

## Contact

**Alireza Adli**  
alireza.adli4@gmail.com  
alireza.adli@mail.concordia.ca
www.demianadli.com
