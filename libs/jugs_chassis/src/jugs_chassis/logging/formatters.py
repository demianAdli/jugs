from __future__ import annotations

import json
import logging
import time
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(record.created)),
            'level': record.levelname,
            'service': getattr(record, 'service', None),
            'env': getattr(record, 'env', None),
            'logger': record.name,
            'request_id': getattr(record, 'request_id', '-'),
            'msg': record.getMessage(),
        }

        if record.exc_info:
            payload['exc_type'] = record.exc_info[0].__name__
            payload['exc_msg'] = str(record.exc_info[1])
            payload['stack'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)
