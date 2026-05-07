import contextvars
import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.config import settings


request_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)


_SENSITIVE_KEYS = {
    "password",
    "secret",
    "secret_key",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "x-api-key",
    "cookie",
}


def _mask_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _mask_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_mask_value(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith("bearer ") or "secret" in lowered or "token" in lowered:
            return "***REDACTED***"
    return value


def _sanitize_extra(extra: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in extra.items():
        if key in {"msg", "args", "created", "msecs", "relativeCreated", "levelno", "levelname", "name", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "thread", "threadName", "processName", "process", "message"}:
            continue
        if any(secret_key in key.lower() for secret_key in _SENSITIVE_KEYS):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = _mask_value(value)
    return sanitized


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _mask_value(record.getMessage()),
        }

        request_id = getattr(record, "request_id", None) or request_id_context.get()
        if request_id:
            base["request_id"] = request_id

        extra = _sanitize_extra(record.__dict__)
        if extra:
            base.update(extra)

        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


def set_request_id(request_id: str | None) -> None:
    request_id_context.set(request_id)


def clear_request_id() -> None:
    request_id_context.set(None)


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_dir = Path(__file__).resolve().parents[2] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.filters.clear()
    root_logger.addFilter(RequestContextFilter())

    formatter = JsonFormatter()

    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    console.addFilter(RequestContextFilter())
    root_logger.addHandler(console)

    file_handler = RotatingFileHandler(
        filename=str(log_dir / "backend.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(file_handler)

    logging.captureWarnings(True)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
