**Project Developer: Alireza Adli**

alireza.adli4@gmail.com
alireza.adli@mail.concordia.ca

## Table of Contents

[Handle MTL DS Workflow](#workflowpy)
[ScrubLayer](#scrublayer)  
[ScrubMTL](#scrubmtl)
[Setting up an environment to use standalone PyQGIS – How to import qgis.core](#setting-up)

<a name="#scrublayer"/>

## ScrubLayer

This module is the essence of the mtl_gis_oo project. It encompasses required functionalities of PyQGIS as methods. Some other methods also have been added to use the functionalities in a specific way. For example, clip_by_multiply carry outs PyQGIS clipping using multiple overlay layers.

<a name="#workflowpy"/>

## Building Cleanup Workflow

This is the process of cleaning and aggregating Montreal buildings datasets. This workflow is backed up by ScrubLayer. After defining the paths, running the module outputs the updated and integrated dataset (map layer).

<a name="helpers"/>

## Helpers

The module contains several functions that cannot be defines as a method of ScrubLayer class but are useful and sometimes necessary for a method or a part of the workflow (building_cleanup_workflow.py).
Creating folders, finding a type of files and merging layers are examples of the module's functionalities.

<a name="config"/>

## Config

This module contains the QGIS installation path, and two dictionaries for holding input and output layers paths. The module will be modified completely to address paths in a general way instead of locally.

<a name="scrubmtl"/>
## ScrubMTL

This module is not being used or developed right now.

<a name="setting-up"/>

## Setting up an environment to use standalone PyQGIS – How to import qgis.core

To use PyQGIS without having the QGIS application run in the background, one needs to add the python path to the environment variables. Here is how to do it on Windows:

1. Install QGIS

2. Assign a specific name to the QGIS Python executable:
   This is being done in order to access the QGIS Python from the command prompt without mixing with the system’s original Python installation(s).

   a. Go to the QGIS installation directory’s Python folder. e.g. C:\Program Files\QGIS 3.34.1\apps\Python39  
   b. Rename the Python executable (python.exe) to a specific-desired name, e.g. pythonqgis.exe

3. Updating the Path variables

   a. Go to Environmental Variables (from Windows start)  
   b. Click on Path and then click on Edit. Add the following paths:

   > C:\Program Files\QGIS 3.34.1\apps\Python39

   c. Go back to the Environmental variables this time click on New and in New Variable box enter PYTHONPATH and in the Variable Value add the following paths (separate them with a colon). Some paths might be different. For example, apps\qgis can be apps\qgis-ltr.

   > i. C:\Program Files\QGIS 3.34.1\apps\qgis\python  
   > ii. C:\Program Files\QGIS 3.34.1\apps\qgis\python\plugins  
   > iii. C:\Program Files\QGIS 3.34.1\apps\Qt5\plugins  
   > iv. C:\Program Files\QGIS 3.34.1\apps\gdal\share\gdal  
   > v. Or altogether: C:\Program Files\QGIS 3.34.1\apps\qgis\python;C:\Program Files\QGIS 3.34.1\apps\qgis\python\plugins;C:\Program Files\QGIS 3.34.1\apps\Qt5\plugins;C:\Program Files\QGIS 3.34.1\apps\gdal\share\gdal

4. Validate importing qgis.core

   a. Open a command prompt window
   b. Enter pythonqgis  
   c. If the process has been done correctly, you won’t face any error.  
   d. In the Python environment, import the package by:

   > import qgis.core
