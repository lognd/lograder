from abc import ABC, abstractmethod
from typing import Union

from colorama import Fore, Style


class FormatterInterface(ABC):
    @abstractmethod
    def set(self, **kwargs):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def to_string(self):
        return self.__str__()


class ColoredText(FormatterInterface):
    _prefix: str = ""
    _suffix: str = ""

    def __init__(self, content: Union[FormatterInterface, str] = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content: Union[FormatterInterface, str] = content

    def __init_subclass__(cls, *args, color: str, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._prefix = color
        cls._suffix = Fore.RESET + Style.RESET_ALL

    def set(self, *, content: Union[FormatterInterface, str] = "", **_):
        self._content = content

    def __str__(self):
        return f"{self._prefix}{self._content if isinstance(self._content, str) else self._content.to_string()}{self._suffix}"


class RedText(ColoredText, color=Fore.LIGHTRED_EX):
    pass


class GreenText(ColoredText, color=Fore.LIGHTGREEN_EX):
    pass


class ContextFormatter(FormatterInterface):
    _prefix: str = ""
    _suffix: str = ""

    def __init__(self, content: Union[FormatterInterface, str] = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content: Union[FormatterInterface, str] = content

    def __init_subclass__(cls, *args, prefix: str, suffix: str, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._prefix = prefix
        cls._suffix = suffix

    def set(self, *, content: Union[FormatterInterface, str] = "", **_):
        self._content = content

    def __str__(self):
        return f"{self._prefix}{self._content if isinstance(self._content, str) else self._content.to_string()}{self._suffix}"


class StreamFormatter(ContextFormatter):  # type: ignore[call-arg]
    def __init_subclass__(  # I override the __init_subclass__, but mypy doesn't know that.
        cls, *args, stream_name: str, stream_color: str = Fore.CYAN, **kwargs
    ):
        super().__init_subclass__(
            *args,
            prefix=f"<{Style.BRIGHT}{stream_color}BEGIN {stream_name.upper()}{Fore.RESET}{Style.RESET_ALL}>\n",
            suffix=f"\n<{Style.BRIGHT}{stream_color}END {stream_name.upper()}{Fore.RESET}{Style.RESET_ALL}>",
            **kwargs,
        )
