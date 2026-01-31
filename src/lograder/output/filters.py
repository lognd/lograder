from __future__ import annotations

import logging
from typing import Union

from ..exception import DeveloperException


def _coerce_level(level: Union[int, str]) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        s = level.strip().upper()
        n = logging._nameToLevel.get(s)
        if isinstance(n, int) and n != 0:
            return n
        if s.isdigit():
            return int(s)
    raise DeveloperException(f"Invalid logging level encountered: {level!r}")


class BelowLevelFilter(logging.Filter):
    def __init__(self, *, below: Union[int, str] = "WARNING", name: str = ""):
        super().__init__(name)
        self._below = _coerce_level(below)

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self._below
