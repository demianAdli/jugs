**Project Developer: Alireza Adli**

alireza.adli4@gmail.com

alireza.adli@mail.concordia.ca

## mtl_gis_oo

This project automates the process of integrating and cleaning datasets related to Montreal buildings.
It is the continuation of [hydroquebec_archetype_gispy](https://ngci.encs.concordia.ca/gitea/a_adli/hydroquebec_archetype_gispy). The project involves the following datasets:

1. [NRCAN Building Footprints](https://open.canada.ca/data/en/dataset/7a5cda52-c7df-427f-9ced-26f19a8a64d6)
2. [Shared platform of geospatial data and aerial photographs (GeoIndex)](https://geoapp.bibl.ulaval.ca/)
3. [Montreal Property Assesment Units](https://donnees.montreal.ca/dataset/unites-evaluation-fonciere)
4. [Administrative boundaries of the agglomeration of Montréal (boroughs and related cities)](https://donnees.montreal.ca/dataset/limites-administratives-agglomeration)

The original workflow was developed in ArcGIS by Kartikay Sharma (kartikay.sharma@concordia.ca). This workflow (link) involves steps such as fixing and clipping geometries, removing features from unnecessary parts of the map, splitting sections based on single building footprints, spatially joining datasets, and cleaning the data through processes such as removing duplicates, among others.

GISPy integrates these processes and automates them so that users can update the dataset by running the workflow module (building_cleanup_workflow.py) after acquiring and defining the paths to the mentioned datasets.

GISPy has been written using QGIS Python standalone libraries (PyQGIS). This set of libraries leverages the functionality of QGIS without needing to run the full QGIS desktop application. To use the environment, QGIS needs to be installed, and the environment must be set up ([Setting up an environment to use standalone PyQGIS – How to import qgis.core](#setting-up)).

## Handle MTL DS Workflow

This is the process of cleaning and aggregating Montreal buildings datasets. This workflow is backed up by ScrubLayer. After defining the paths, running the module outputs the updated and integrated dataset (map layer).

<a name="helpers"/>

## Basic Functions

The module contains several functions that cannot be defines as a method of ScrubLayer class but are useful and sometimes necessary for a method or a part of the workflow (handle_mtl_ds_workflow.py).
Creating folders, finding a type of files and merging layers are examples of the module's functionalities.

<a name="config"/>

## IO Paths & Layers

This module contains the QGIS installation path, and two dictionaries for holding input and output layers paths. The module will be modified completely to address paths in a general way instead of locally.

<a name="scrubmtl"/>
## ScrubMTL

This module is not being used or developed right now.
