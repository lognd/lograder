from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.file_output import (
    FileOutputError,
    FileOutputFailure,
    FileOutputSuccess,
)
from lograder.process.os_helpers import command_to_str


def _args_str(args: list[str]) -> str:
    return f" {command_to_str(args)}" if args else ""


@register_layout("file-output-success")
class FileOutputSuccessLayout(Layout[FileOutputSuccess]):
    @classmethod
    def to_simple(cls, data: FileOutputSuccess) -> str:
        return (
            f"[PASS] `{data.artifact_name}` — {data.test_name}{_args_str(data.args)}"
            f" (wrote {data.output_file})"
        )

    @classmethod
    def to_ansi(cls, data: FileOutputSuccess) -> str:
        return (
            f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` — {data.test_name}{_args_str(data.args)}"
            f" (wrote {F.CYAN}{data.output_file}{F.RESET})"
        )


@register_layout("file-output-failure")
class FileOutputFailureLayout(Layout[FileOutputFailure]):
    @classmethod
    def to_simple(cls, data: FileOutputFailure) -> str:
        parts = [
            f"[FAIL] `{data.artifact_name}` — {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.actual_content is None:
            parts.append(f"  File `{data.output_file}` was not created.\n")
        elif data.diff:
            parts.append(
                f"File diff (expected → actual) for `{data.output_file}`:\n{data.diff}\n"
            )
        if (
            data.expected_exit_code is not None
            and data.actual_exit_code != data.expected_exit_code
        ):
            parts.append(
                f"Exit code: expected {data.expected_exit_code}, got {data.actual_exit_code}.\n"
            )
        if data.stdin_text:
            parts.append(f"STDIN: {repr(data.stdin_text)}\n")
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: FileOutputFailure) -> str:
        parts = [
            f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` — {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.actual_content is None:
            parts.append(
                f"  File `{F.CYAN}{data.output_file}{F.RESET}` was not created.\n"
            )
        elif data.diff:
            parts.append(
                f"{F.YELLOW}File diff (expected → actual) for `{data.output_file}`:{F.RESET}\n{data.diff}\n"
            )
        if (
            data.expected_exit_code is not None
            and data.actual_exit_code != data.expected_exit_code
        ):
            parts.append(
                f"Exit code: expected {F.GREEN}{data.expected_exit_code}{F.RESET},"
                f" got {F.RED}{data.actual_exit_code}{F.RESET}.\n"
            )
        if data.stdin_text:
            parts.append(f"STDIN: {F.YELLOW}{repr(data.stdin_text)}{F.RESET}\n")
        return "".join(parts)


@register_layout("file-output-error")
class FileOutputErrorLayout(Layout[FileOutputError]):
    @classmethod
    def to_simple(cls, data: FileOutputError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: FileOutputError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
        )
