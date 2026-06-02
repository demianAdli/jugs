"""Logging defaults for jug_gis_validation entrypoints."""
from __future__ import annotations

import os
from pathlib import Path

from sabu_chassis.logging import configure_logging


DEFAULT_LOG_FILE_NAME = "logs/jug_gis_validation.log"


def _service_root() -> Path:
    return Path(__file__).resolve().parents[2]


def configure_service_logging(service_name: str) -> None:
    """Configure sabu-chassis logging with jug_gis_validation file defaults."""
    os.environ.setdefault("LOG_SERVICE", service_name)
    os.environ.setdefault("LOG_DIR_BASE", str(_service_root()))
    os.environ.setdefault("LOG_FILE_NAME", DEFAULT_LOG_FILE_NAME)
    configure_logging()
