from __future__ import annotations

import atexit
import logging
import logging.config
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from lograder.exception import StaffException
from lograder.output.handlers import HTMLHandler
from lograder.output.packets import wrap_packet

try:
    import tomllib
except ImportError:
    # This block was added for tomli backwards compatibility.
    # Note that the mypy-suppression is done intentionally because it is wrong.
    import tomli as tomllib  # type: ignore[no-redef]

_PAST_SETUP: Optional[Path] = None


class LograderLogger(logging.Logger):
    PACKET_ATTR = "packet"

    def __init__(self, name: str, level: int | str = logging.NOTSET) -> None:
        super().__init__(name, level)
        atexit.register(self.emit_html)

    def packet(self, data: BaseModel, *, level: int = logging.INFO) -> None:
        self.log(
            level, data.__class__.__name__, extra={self.PACKET_ATTR: wrap_packet(data)}
        )  # extra automatically unwraps dict into kwargs.

    def emit_html(self) -> None:
        for h in self.handlers:
            if isinstance(h, HTMLHandler):
                h.render_page_to_file()


def setup_logger(toml_file: Path = Path(__file__).parent / "config.toml") -> None:
    global _PAST_SETUP
    if _PAST_SETUP != toml_file:
        logging.setLoggerClass(LograderLogger)
        logging.config.dictConfig(tomllib.load(toml_file.open("rb")))
        _PAST_SETUP = toml_file


def get_logger(name: str) -> LograderLogger:
    global _PAST_SETUP
    if _PAST_SETUP is None:
        setup_logger()
    logger = logging.getLogger(name)
    if not isinstance(logger, LograderLogger):
        raise StaffException(
            f"Before any logger can be gotten, `lograder.output.logger.setup_logger()` must be called because it sets the default logger class to `LograderLogger`."
        )
    return logger
