from __future__ import annotations

from colorama import Fore as F

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import FAIL as _FAIL
from lograder.output.layout.format_helpers.test_layout import PASS as _PASS
from lograder.output.layout.format_helpers.test_layout import args_str as _args_str
from lograder.output.layout.format_helpers.test_layout import (
    exit_code_stdin_ansi as _exit_code_stdin_ansi,
)
from lograder.output.layout.format_helpers.test_layout import (
    exit_code_stdin_simple as _exit_code_stdin_simple,
)
from lograder.output.layout.format_helpers.test_layout import truncate as _truncate
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.output_compare import (
    OutputCompareError,
    OutputCompareFailure,
    OutputCompareSuccess,
)


@register_layout("output-compare-success")
class OutputCompareSuccessLayout(Layout[OutputCompareSuccess]):
    @classmethod
    def to_simple(cls, data: OutputCompareSuccess) -> str:
        return f"[PASS] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}"

    @classmethod
    def to_ansi(cls, data: OutputCompareSuccess) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}"
        )


@register_layout("output-compare-failure")
class OutputCompareFailureLayout(Layout[OutputCompareFailure]):
    @classmethod
    def to_simple(cls, data: OutputCompareFailure) -> str:
        parts = [
            f"[FAIL] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.diff:
            parts.append(f"Output diff (expected -> actual):\n{_truncate(data.diff)}\n")
        _exit_code_stdin_simple(
            parts, data.expected_exit_code, data.actual_exit_code, data.stdin_text
        )
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: OutputCompareFailure) -> str:
        parts = [
            f"{_FAIL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}\n",
        ]
        if data.diff:
            parts.append(
                f"{F.YELLOW}Output diff (expected -> actual):{F.RESET}\n"
                f"{_truncate(data.diff)}\n"
            )
        _exit_code_stdin_ansi(
            parts, data.expected_exit_code, data.actual_exit_code, data.stdin_text
        )
        return "".join(parts)


@register_layout("output-compare-error")
class OutputCompareErrorLayout(Layout[OutputCompareError]):
    @classmethod
    def to_simple(cls, data: OutputCompareError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: OutputCompareError) -> str:
        return f"{_ERROR} `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
