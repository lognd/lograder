from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import PASS as _PASS
from lograder.output.layout.format_helpers.test_layout import args_str as _args_str
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.performance import (
    PerformanceTestError,
    PerformanceTestFailure,
    PerformanceTestSuccess,
)

_SLOW = f"{S.BRIGHT}{F.RED}[SLOW]{F.RESET}{S.RESET_ALL}"


def _fmt_time(seconds: float) -> str:
    return f"{seconds:.3f}s"


@register_layout("performance-test-success")
class PerformanceTestSuccessLayout(Layout[PerformanceTestSuccess]):
    @classmethod
    def to_simple(cls, data: PerformanceTestSuccess) -> str:
        return (
            f"[PASS] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}"
            f" ({_fmt_time(data.elapsed)} / {_fmt_time(data.time_limit)})"
        )

    @classmethod
    def to_ansi(cls, data: PerformanceTestSuccess) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}"
            f" ({F.GREEN}{_fmt_time(data.elapsed)}{F.RESET} / {_fmt_time(data.time_limit)})"
        )


@register_layout("performance-test-failure")
class PerformanceTestFailureLayout(Layout[PerformanceTestFailure]):
    @classmethod
    def to_simple(cls, data: PerformanceTestFailure) -> str:
        return (
            f"[SLOW] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}"
            f" ({_fmt_time(data.elapsed)} exceeded limit of {_fmt_time(data.time_limit)})"
        )

    @classmethod
    def to_ansi(cls, data: PerformanceTestFailure) -> str:
        return (
            f"{_SLOW}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}"
            f" ({F.RED}{_fmt_time(data.elapsed)}{F.RESET}"
            f" exceeded limit of {_fmt_time(data.time_limit)})"
        )


@register_layout("performance-test-error")
class PerformanceTestErrorLayout(Layout[PerformanceTestError]):
    @classmethod
    def to_simple(cls, data: PerformanceTestError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: PerformanceTestError) -> str:
        return f"{_ERROR} `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
