from __future__ import annotations

from abc import ABC, abstractmethod

from ..penalties.interfaces.penalty import PenaltyInterface


class AddonInterface(PenaltyInterface, ABC):
    @abstractmethod
    def run(self) -> None:
        pass
