from typing import Mapping, Any
from abc import ABC, abstractmethod

class FormatterInterface(ABC):

    @classmethod
    @abstractmethod
    def to_string(cls, data: Mapping[str, Any]) -> str:
        pass