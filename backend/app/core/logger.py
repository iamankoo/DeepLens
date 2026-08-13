import logging

from app.core.config import settings

_RESERVED_RECORD_ATTRS = set(logging.makeLogRecord({}).__dict__)


class ContextFormatter(logging.Formatter):
    """Appends any `extra={...}` fields passed to a log call as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        context = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_RECORD_ATTRS
        }
        if not context:
            return base
        rendered = " ".join(f"{key}={value!r}" for key, value in context.items())
        return f"{base} | {rendered}"


def _configure() -> logging.Logger:
    log = logging.getLogger("DeepLens")
    log.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            ContextFormatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
        log.addHandler(handler)
        log.propagate = False

    return log


logger = _configure()
