import os, sys, json, time, logging, contextvars
from logging.config import dictConfig

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

def configure_logging() -> None:
    """
    Call once at process start (e.g., top of a service's app.py).
    Sets the ROOT logger so every module logger inherits it.
    """
    # Root level defaults to DEBUG in dev so you "cover all log types"
    log_level  = os.getenv("LOG_LEVEL", "DEBUG").upper()
    log_format = os.getenv("LOG_FORMAT", "json")  # "json" or "plain"

    fmt_name = "json_fmt" if log_format == "json" else "plain_fmt"
    formatters = {
        "json_fmt": {"()": JsonFormatter},
        "plain_fmt": {"format": "%(asctime)s %(levelname)s %(service)s %(env)s "
                                "%(name)s [req:%(request_id)s] - %(message)s"}
    }

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False, 
        "filters": {"ctx": {"()": ContextFilter}},
        "formatters": formatters,
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": fmt_name,
                "filters": ["ctx"],
            }
        },
        "root": {"level": log_level, "handlers": ["stdout"]},
        "loggers": {
            # Quiet noisy libs if needed
            "werkzeug": {"level": os.getenv("WERKZEUG_LEVEL", "INFO")},
            "urllib3": {"level": "WARNING"},
            "marshmallow": {"level": "WARNING"},
        },
    })

    logging.captureWarnings(True)  # route Python warnings into logging
