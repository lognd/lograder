from abc import ABC, abstractmethod
from typing import Any

from .step import Step


class Block(Step, ABC):
    @abstractmethod
    def __call__(self) -> None: ...
