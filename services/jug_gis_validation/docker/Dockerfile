FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install geospatial runtime/build dependencies used by geopandas and friends.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    proj-data \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy local sources so development builds can install the current checkout.
COPY libs/sabu_chassis /tmp/build/sabu_chassis
COPY services/jug_gis_validation /tmp/build/jug_gis_validation

# Install from the local checkout for development, or from PyPI for published
# image builds. Leave version args empty to install the latest available PyPI
# releases, or pass build args to pin exact versions.
ARG INSTALL_LOCAL=true
ARG JUG_GIS_VALIDATION_VERSION=latest
ARG SABU_CHASSIS_VERSION=latest
RUN set -eux; \
    python -m pip install --upgrade pip; \
    if [ "${INSTALL_LOCAL}" = "true" ]; then \
        python -m pip install --upgrade \
            /tmp/build/sabu_chassis \
            /tmp/build/jug_gis_validation \
            gunicorn; \
    else \
        jug_gis_validation_spec="jug_gis_validation"; \
        sabu_chassis_spec="sabu-chassis"; \
        if [ "${JUG_GIS_VALIDATION_VERSION}" != "latest" ]; then \
            jug_gis_validation_spec="jug_gis_validation==${JUG_GIS_VALIDATION_VERSION}"; \
        fi; \
        if [ "${SABU_CHASSIS_VERSION}" != "latest" ]; then \
            sabu_chassis_spec="sabu-chassis==${SABU_CHASSIS_VERSION}"; \
        fi; \
        python -m pip install --upgrade \
            "${jug_gis_validation_spec}" \
            "${sabu_chassis_spec}" \
            gunicorn; \
    fi; \
    rm -rf /tmp/build

COPY services/jug_gis_validation/app.py /app/app.py

# Build-time smoke test: fail the image build if key runtime imports fail.
RUN python -c "import geopandas; import jug_gis_validation; print('jug_gis_validation Docker imports OK')"

# Keep logs in a predictable mount-friendly location.
ENV LOG_DIR_BASE=/app
ENV LOG_FILE_NAME=logs/jug_gis_validation.log
ENV LOG_SERVICE=gis_validation-api

# Path-based buildings_set API inputs should be mounted under /data.
RUN mkdir -p /app/logs /data

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
