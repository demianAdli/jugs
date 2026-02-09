import os, sys, json, time, logging, contextvars
from logging.config import dictConfig
from pathlib import Path

# ---------- Correlation ID (per-request / per-context) ----------
_request_id = contextvars.ContextVar('request_id', default="-")

def set_request_id(value: str) -> None:
    _request_id.set(value)

def get_request_id() -> str:
    return _request_id.get()

# ---------- Context filter to enrich all log records ----------
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        record.service = os.getenv('LOG_SERVICE', 'lca-carbon-api')
        record.env = os.getenv('LOG_ENV', 'dev')
        return True

# ---------- Lightweight JSON formatter (no external deps) ----------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(record.created)),
            'level': record.levelname,
            'service': getattr(record, 'service', None),
            'env': getattr(record, 'env', None),
            'logger': record.name,
            'request_id': getattr(record, 'request_id', '-'),
            'msg': record.getMessage(),
        }
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__
            payload["exc_msg"] = str(record.exc_info[1])
            payload["stack"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(path=None):
    if path is None:
        path = Path(__file__).with_name('logging_file_stdout_config.json')
    else:
        path = Path(path)

    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)

    # env overrides
    cfg['root']['level'] = os.getenv('LOG_LEVEL', cfg['root'].get('level', 'INFO'))
    cfg.setdefault('loggers', {}).setdefault('werkzeug', {})["level"] = os.getenv('WERKZEUG_LEVEL', 'INFO')

    # --- normalize & prepare file handler ---
    fh = cfg.get('handlers', {}).get("file")
    if fh and 'filename' in fh:
        base = Path(os.getenv('LOG_DIR_BASE', Path(__file__).resolve().parent))
        file_path = Path(fh['filename'])
        if not file_path.is_absolute():
            file_path = base / file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fh['filename'] = str(file_path)
        fh.setdefault('encoding', 'utf-8')
        fh.setdefault('mode', 'a')

    # --- APPLY the config (always) ---
    try:
        dictConfig(cfg)
    except Exception:
        import traceback, pprint
        print('stderr handler cfg:')
        pprint.pp(cfg.get('handlers', {}).get('stderr'))
        traceback.print_exc()
        raise

    logging.captureWarnings(True)
