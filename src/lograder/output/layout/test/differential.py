from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.differential import (
    DifferentialError,
    DifferentialFailure,
    DifferentialSuccess,
)
from lograder.process.os_helpers import command_to_str

_PASS = f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
_FAIL = f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
_ERROR = f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"


def _args_str(args: list[str]) -> str:
    return f" {command_to_str(args)}" if args else ""


def _truncate(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


@register_layout("differential-success")
class DifferentialSuccessLayout(Layout[DifferentialSuccess]):
    @classmethod
    def to_simple(cls, data: DifferentialSuccess) -> str:
        return f"[PASS] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}"

    @classmethod
    def to_ansi(cls, data: DifferentialSuccess) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}"
        )


@register_layout("differential-failure")
class DifferentialFailureLayout(Layout[DifferentialFailure]):
    @classmethod
    def to_simple(cls, data: DifferentialFailure) -> str:
        parts = [
            f"[FAIL] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}\n"
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
            f"{_FAIL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}\n"
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
