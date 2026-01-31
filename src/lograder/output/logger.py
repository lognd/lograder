from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from .packets import wrap_packet

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

_PAST_SETUP: Optional[Path] = None


class LograderLogger(logging.Logger):
    PACKET_ATTR = "packet"

    def packet(self, data: BaseModel, *, level: int = logging.INFO) -> None:
        self.log(
            level, data.__class__.__name__, extra={self.PACKET_ATTR: wrap_packet(data)}
        )  # extra automatically unwraps dict into kwargs.


def setup_logger(toml_file: Path = Path(__file__).parent / "config.toml") -> None:
    global _PAST_SETUP
    if _PAST_SETUP != toml_file:
        logging.config.dictConfig(tomllib.load(toml_file.open("rb")))
        _PAST_SETUP = toml_file


setup_logger()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger
