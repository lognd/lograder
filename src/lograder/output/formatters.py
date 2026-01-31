import datetime as dt
import json
import logging
from typing import Optional

from ..exception import DeveloperException
from .layout import SupportedFormat, dispatch_layout
from .logger import LograderLogger
from .packets import unwrap_packet


class PacketFormatter(logging.Formatter):
    def __init__(self, *, mode: SupportedFormat = "simple"):
        super().__init__()
        self.mode = mode
        self._fallback = logging.Formatter("%(levelname)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        packet = getattr(record, LograderLogger.PACKET_ATTR, None)
        if packet is None:
            return self._fallback.format(record)

        data = unwrap_packet(packet)
        layout = dispatch_layout(data)

        format_output = getattr(layout, self.mode)
        if format_output is None:
            raise DeveloperException(
                f"`Layout` subclass (`{layout.__class__.__name__}`) does not support an output of type, `{self.mode}`."
            )
        elif not isinstance(format_output, str):
            raise DeveloperException(
                f"`Layout` subclass (`{layout.__class__.__name__}`) is malformed; output type of `{self.mode}` property is not a `str` rather the type of, `{format_output.__class__.__name__}`."
            )
        return format_output
