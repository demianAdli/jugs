FROM ubuntu:22.0

# Tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg software-properties-common \
 && rm -rf /var/lib/apt/lists/*

# QGIS signing key (new location) and repo as a .sources file
RUN mkdir -p /etc/apt/keyrings \
 && wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg \
 && printf "Types: deb\nURIs: https://qgis.org/ubuntu-ltr\nSuites: jammy\nArchitectures: amd64\nComponents: main\nSigned-By: /etc/apt/keyrings/qgis-archive-keyring.gpg\n" \
    > /etc/apt/sources.list.d/qgis.sources

# Install only what's needed to import PyQGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-qgis gdal-bin \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV QGIS_PREFIX_PATH=/usr \
    PYTHONPATH=/usr/share/qgis/python:/usr/share/qgis/python/plugins \
    QT_QPA_PLATFORM=offscreen \
    GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj \
    QGIS_DISABLE_MESSAGE_HOOKS=1

# Build-time smoke test (fail the build if import/init fails)
RUN python3 -c "import qgis.core as qc; from qgis.core import QgsApplication; \
QgsApplication.setPrefixPath('/usr', True); a=QgsApplication([], False); a.initQgis(); \
print('QGIS OK:', qc.Qgis.QGIS_VERSION); a.exitQgis()"

# No CMD — you’ll pass commands at docker run time
