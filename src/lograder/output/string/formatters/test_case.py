from typing import Union

from colorama import Fore, Style

from .common import ContextFormatter, FormatterInterface, RedText


class StatusFormatter:
    pass


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


class ActualSTDOUTFormatter(StreamFormatter, stream_name="actual-stdout", stream_color=Fore.MAGENTA):
    pass


class ExpectedSTDOUTFormatter(StreamFormatter, stream_name="expected-stdout", stream_color=Fore.GREEN):
    pass


class STDERRFormatter(StreamFormatter, stream_name="stderr", stream_color=Fore.RED):
    pass


class STDINFormatter(StreamFormatter, stream_name="stdin", stream_color=Fore.CYAN):
    pass


class ReprFormatter(FormatterInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content: Union[FormatterInterface, str] = ""

    def set(self, *, content: Union[FormatterInterface, str] = "", **_):
        self._content = content

    def __str__(self):
        return f"{repr(self._content if isinstance(self._content, str) else self._content.to_string())}"
