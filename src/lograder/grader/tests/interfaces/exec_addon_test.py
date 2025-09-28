from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .test import TestInterface

if TYPE_CHECKING:
    from ....types import Command


class ExecAddonTestInterface(TestInterface, ABC):
    @abstractmethod
    def get_args(self) -> Command: ...

    @abstractmethod
    def get_input(self) -> str: ...
