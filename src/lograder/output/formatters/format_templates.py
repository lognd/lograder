from abc import ABC, abstractmethod
from typing import Union


class RendererInterface(ABC):
    @abstractmethod
    def render(self) -> str:
        pass


class ProcessStep(RendererInterface, ABC):
    pass


class ContextRenderer(RendererInterface):
    _prefix: str = ""
    _suffix: str = ""
    _empty: str = ""

    def __init_subclass__(cls, *, prefix: str, suffix: str, empty: str):
        cls._prefix = prefix
        cls._suffix = suffix

    def __init__(self, content: Union[RendererInterface, str]):
        self._content: Union[RendererInterface, str] = content

    def get_content(self) -> str:
        return (
            self._content if isinstance(self._content, str) else self._content.render()
        )

    @classmethod
    def get_prefix(cls):
        return cls._prefix

    @classmethod
    def get_suffix(cls):
        return cls._suffix

    @classmethod
    def get_empty(cls):
        return cls._empty

    def render(self) -> str:
        content = self.get_content()
        return (
            f"{self.get_prefix()}{content}{self.get_suffix()}"
            if content
            else self.get_empty()
        )
