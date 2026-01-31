import datetime as dt
import json
import logging
from typing import Optional


# Heavily inspired & plagiarized from mCoding; the source in question can be
# found here: https://youtu.be/9L77QExPmI0. Please consider checking him out;
# he is a _fantastic_ programmer.
class JSONFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: Optional[dict[str, str]] = None):
        super().__init__()
        self.fmt_keys = fmt_keys or {}

    def format(self, record: logging.LogRecord) -> str:
        message = self._record_to_dict(record)
        return json.dumps(message, default=str)

    def _record_to_dict(self, record: logging.LogRecord) -> dict:
        default_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            default_fields["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info is not None:
            default_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg if (msg := default_fields.pop(val, None)) else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(default_fields)

        return message
