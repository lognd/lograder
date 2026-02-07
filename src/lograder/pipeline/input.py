from abc import ABC, abstractmethod

from .package import Package
from .step import Step


class Input(Step, ABC):
    @abstractmethod
    def __call__(self) -> Package: ...
