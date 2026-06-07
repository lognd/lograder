import logging
from typing import TYPE_CHECKING

from lograder.exception import DeveloperException
from lograder.output.logger import LograderLogger
from lograder.output.packets import unwrap_packet

if TYPE_CHECKING:
    from lograder.output.layout import (
        SupportedFormat,
    )

dispatch_layout = (
    None  # populated lazily on first format() call to avoid circular import
)


def _load_dispatch_layout():
    global dispatch_layout
    if dispatch_layout is None:
        from lograder.output.layout import dispatch_layout as _dl

        dispatch_layout = _dl
    return dispatch_layout


class PacketFormatter(logging.Formatter):
    def __init__(self, *, mode: "SupportedFormat" = "simple"):
        super().__init__()
        self.mode = mode
        self._fallback = logging.Formatter("%(levelname)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        _load_dispatch_layout()
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
