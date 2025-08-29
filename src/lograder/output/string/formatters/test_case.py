from typing import Union

from colorama import Fore

from .common import FormatterInterface, StreamFormatter


class StatusFormatter:
    pass


class ActualSTDOUTFormatter(
    StreamFormatter, stream_name="actual stdout", stream_color=Fore.MAGENTA
):
    pass


class ExpectedSTDOUTFormatter(
    StreamFormatter, stream_name="expected stdout", stream_color=Fore.GREEN
):
    pass


class STDERRFormatter(StreamFormatter, stream_name="stderr", stream_color=Fore.RED):
    pass


class STDINFormatter(StreamFormatter, stream_name="stdin", stream_color=Fore.CYAN):
    pass


class ReprFormatter(FormatterInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content: Union[FormatterInterface, str] = ""

    def set(self, *, content: Union[FormatterInterface, str] = "", **_) -> None:
        self._content = content

    def __str__(self) -> str:
        return f"{repr(self._content if isinstance(self._content, str) else self._content.to_string())}"
