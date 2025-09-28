from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from ..penalties.interfaces.penalty import PenaltyInterface

if TYPE_CHECKING:
    from ..builders.interfaces.builder import BuilderInterface
    from ...types import Command


class AddonInterface(PenaltyInterface, ABC):
    def __init__(self):
        super().__init__()
        self._builder: Optional[BuilderInterface] = None

    def get_builder(self) -> BuilderInterface:
        assert self._builder is not None
        return self._builder

    def set_builder(self, builder: BuilderInterface) -> None:
        self._builder = builder

    @abstractmethod
    def run(self) -> None:
        pass

class ExecAddonInterface(AddonInterface, ABC):
    def __init__(self):
        super().__init__()
        self._stdin: str = ""
        self._args: Command = []

    def set_args(self, args: Command):
        self._args = args

    def get_args(self) -> Command:
        return self._args

    def set_input(self, stdin: str):
        self._stdin = stdin

    def get_input(self):
        return self._stdin
