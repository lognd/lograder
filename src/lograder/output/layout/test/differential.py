from __future__ import annotations

from colorama import Fore as F

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import FAIL as _FAIL
from lograder.output.layout.format_helpers.test_layout import PASS as _PASS
from lograder.output.layout.format_helpers.test_layout import (
    header_line_ansi as _header_line_ansi,
)
from lograder.output.layout.format_helpers.test_layout import (
    header_line_simple as _header_line_simple,
)
from lograder.output.layout.format_helpers.test_layout import truncate as _truncate
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.differential import (
    DifferentialError,
    DifferentialFailure,
    DifferentialSuccess,
)


@register_layout("differential-success")
class DifferentialSuccessLayout(Layout[DifferentialSuccess]):
    @classmethod
    def to_simple(cls, data: DifferentialSuccess) -> str:
        return _header_line_simple(
            "[PASS]", data.artifact_name, data.test_name, data.args
        )

    @classmethod
    def to_ansi(cls, data: DifferentialSuccess) -> str:
        return _header_line_ansi(_PASS, data.artifact_name, data.test_name, data.args)


@register_layout("differential-failure")
class DifferentialFailureLayout(Layout[DifferentialFailure]):
    @classmethod
    def to_simple(cls, data: DifferentialFailure) -> str:
        parts = [
            _header_line_simple("[FAIL]", data.artifact_name, data.test_name, data.args)
            + "\n"
        ]
        if data.diff:
            parts.append(
                f"Output diff (reference -> student):\n{_truncate(data.diff)}\n"
            )
        if data.student_exit_code != data.reference_exit_code:
            parts.append(
                f"Exit code: reference={data.reference_exit_code},"
                f" student={data.student_exit_code}.\n"
            )
        if data.stdin_text:
            parts.append(f"stdin: {repr(data.stdin_text)}\n")
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: DifferentialFailure) -> str:
        parts = [
            _header_line_ansi(_FAIL, data.artifact_name, data.test_name, data.args)
            + "\n"
        ]
        if data.diff:
            parts.append(
                f"{F.YELLOW}Output diff (reference -> student):{F.RESET}\n"
                f"{_truncate(data.diff)}\n"
            )
        if data.student_exit_code != data.reference_exit_code:
            parts.append(
                f"Exit code: reference={F.GREEN}{data.reference_exit_code}{F.RESET},"
                f" student={F.RED}{data.student_exit_code}{F.RESET}.\n"
            )
        if data.stdin_text:
            parts.append(f"stdin: {F.YELLOW}{repr(data.stdin_text)}{F.RESET}\n")
        return "".join(parts)


@register_layout("differential-error")
class DifferentialErrorLayout(Layout[DifferentialError]):
    @classmethod
    def to_simple(cls, data: DifferentialError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: DifferentialError) -> str:
        return f"{_ERROR} `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
