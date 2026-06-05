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
from lograder.pipeline.test.file_output import (
    FileOutputError,
    FileOutputFailure,
    FileOutputSuccess,
)


@register_layout("file-output-success")
class FileOutputSuccessLayout(Layout[FileOutputSuccess]):
    @classmethod
    def to_simple(cls, data: FileOutputSuccess) -> str:
        return (
            f"[PASS] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}"
            f" (wrote {data.output_file})"
        )

    @classmethod
    def to_ansi(cls, data: FileOutputSuccess) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}"
            f" (wrote {F.CYAN}{data.output_file}{F.RESET})"
        )


@register_layout("file-output-failure")
class FileOutputFailureLayout(Layout[FileOutputFailure]):
    @classmethod
    def to_simple(cls, data: FileOutputFailure) -> str:
        parts = [
            f"[FAIL] `{data.artifact_name}` - {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.actual_content is None:
            parts.append(f"  File `{data.output_file}` was not created.\n")
        elif data.diff:
            parts.append(
                f"File diff (expected -> actual) for `{data.output_file}`:\n"
                f"{_truncate(data.diff)}\n"
            )
        _exit_code_stdin_simple(
            parts, data.expected_exit_code, data.actual_exit_code, data.stdin_text
        )
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: FileOutputFailure) -> str:
        parts = [
            f"{_FAIL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{_args_str(data.args)}\n",
        ]
        if data.actual_content is None:
            parts.append(
                f"  File `{F.CYAN}{data.output_file}{F.RESET}` was not created.\n"
            )
        elif data.diff:
            parts.append(
                f"{F.YELLOW}File diff (expected -> actual)"
                f" for `{data.output_file}`:{F.RESET}\n"
                f"{_truncate(data.diff)}\n"
            )
        _exit_code_stdin_ansi(
            parts, data.expected_exit_code, data.actual_exit_code, data.stdin_text
        )
        return "".join(parts)


@register_layout("file-output-error")
class FileOutputErrorLayout(Layout[FileOutputError]):
    @classmethod
    def to_simple(cls, data: FileOutputError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: FileOutputError) -> str:
        return f"{_ERROR} `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
