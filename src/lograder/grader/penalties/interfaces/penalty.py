from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...formatters.dispatcher import FormatPackage

class PenaltyInterface(ABC):
    @abstractmethod
    def get_penalty(self) -> float:
        pass

    @abstractmethod
    def get_output(self) -> FormatPackage:
        pass

