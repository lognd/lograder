from __future__ import annotations

from colorama import Fore as F

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import PASS as _PASS
from lograder.output.layout.format_helpers.test_layout import (
    duration_str as _duration_str,
)
from lograder.output.layout.format_helpers.test_layout import (
    junit_failure_ansi as _junit_failure_ansi,
)
from lograder.output.layout.format_helpers.test_layout import (
    junit_failure_simple as _junit_failure_simple,
)
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.catch2 import Catch2Error, Catch2Failure, Catch2Success


@register_layout("catch2-success")
class Catch2SuccessLayout(Layout[Catch2Success]):
    @classmethod
    def to_simple(cls, data: Catch2Success) -> str:
        return (
            f"[PASS] `{data.artifact_name}` - {data.test_name}"
            f"{_duration_str(data.duration)}"
        )

    @classmethod
    def to_ansi(cls, data: Catch2Success) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{F.YELLOW}{_duration_str(data.duration)}{F.RESET}"
        )


@register_layout("catch2-failure")
class Catch2FailureLayout(Layout[Catch2Failure]):
    @classmethod
    def to_simple(cls, data: Catch2Failure) -> str:
        return _junit_failure_simple(
            data.artifact_name,
            data.test_name,
            data.duration,
            data.failure_message,
            data.failure_text,
        )

    @classmethod
    def to_ansi(cls, data: Catch2Failure) -> str:
        return _junit_failure_ansi(
            data.artifact_name,
            data.test_name,
            data.duration,
            data.failure_message,
            data.failure_text,
        )


@register_layout("catch2-error")
class Catch2ErrorLayout(Layout[Catch2Error]):
    @classmethod
    def to_simple(cls, data: Catch2Error) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: Catch2Error) -> str:
        return f"{_ERROR} `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
