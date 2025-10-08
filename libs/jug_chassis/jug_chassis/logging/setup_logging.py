import os, sys, json, time, logging, contextvars
from logging.config import dictConfig
from pathlib import Path

# ---------- Correlation ID (per-request / per-context) ----------
_request_id = contextvars.ContextVar("request_id", default="-")

def set_request_id(value: str) -> None:
    _request_id.set(value)

def get_request_id() -> str:
    return _request_id.get()

# ---------- Context filter to enrich all log records ----------
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        record.service = os.getenv("LOG_SERVICE", "lca-carbon-api")
        record.env = os.getenv("LOG_ENV", "dev")
        return True

# ---------- Lightweight JSON formatter (no external deps) ----------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "service": getattr(record, "service", None),
            "env": getattr(record, "env", None),
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__
            payload["exc_msg"] = str(record.exc_info[1])
            payload["stack"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(path=None):
    if path is None:
        path = Path(__file__).with_name("logging_config.json")

    with open(path) as f:
        cfg = json.load(f)

    # patch environment-specific values
    cfg["root"]["level"] = os.getenv("LOG_LEVEL", "INFO")
    cfg["loggers"]["werkzeug"]["level"] = os.getenv("WERKZEUG_LEVEL", "INFO")

    logging.config.dictConfig(cfg)
    logging.captureWarnings(True)  # route Python warnings into logging
