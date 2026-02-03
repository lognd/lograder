from abc import ABC, abstractmethod
from .step import Step

class Block(ABC, Step):
    @abstractmethod
    def __call__(self) -> None:
        ...