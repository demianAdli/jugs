from __future__ import annotations

import logging
import os

from .context import get_request_id


class ContextFilter(logging.Filter):
    def __init__(
        self,
        service: str | None = None,
        env: str | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._env = env

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.service = self._service or os.getenv('LOG_SERVICE', 'jugs-service')
        record.env = self._env or os.getenv('LOG_ENV', 'dev')
        return True
