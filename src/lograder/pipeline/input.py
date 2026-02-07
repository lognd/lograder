from abc import ABC, abstractmethod

from .package import Package
from .step import Step


class Input(ABC, Step):
    @abstractmethod
    def __call__(self) -> Package: ...
