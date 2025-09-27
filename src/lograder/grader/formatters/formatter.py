from abc import ABC, abstractmethod
from typing import Any, Mapping


class FormatterInterface(ABC):

    @classmethod
    @abstractmethod
    def to_string(cls, data: Mapping[str, Any]) -> str:
        pass
