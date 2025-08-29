from abc import ABC, abstractmethod
from typing import Union


class FormatterInterface(ABC):
    @abstractmethod
    def set(self, **kwargs):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def to_string(self):
        return self.__str__()


class ContextFormatter(FormatterInterface):
    _prefix: str = ""
    _suffix: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content: Union[FormatterInterface, str] = ""

    def __init_subclass__(cls, *args, prefix: str, suffix: str, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._prefix = prefix
        cls._suffix = suffix

    def set(self, *, content: Union[FormatterInterface, str] = "", **_):
        self._content = content

    def __str__(self):
        return f"{self._prefix}{self._content if isinstance(self._content, str) else self._content.to_string()}{self._suffix}"
