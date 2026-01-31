from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

_PAST_SETUP: Optional[Path] = None


def setup_logger(toml_file: Path = Path(__file__).parent / "config.toml") -> None:
    global _PAST_SETUP
    if _PAST_SETUP != toml_file:
        logging.config.dictConfig(tomllib.load(toml_file.open("rb")))
        _PAST_SETUP = toml_file


setup_logger()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger
