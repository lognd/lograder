from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.output_compare import (
    OutputCompareError,
    OutputCompareFailure,
    OutputCompareSuccess,
)
from lograder.process.os_helpers import command_to_str


def _args_str(args: list[str]) -> str:
    return f" {command_to_str(args)}" if args else ""


@register_layout("output-compare-success")
class OutputCompareSuccessLayout(Layout[OutputCompareSuccess]):
    @classmethod
    def to_simple(cls, data: OutputCompareSuccess) -> str:
        return f"[PASS] `{data.artifact_name}` — {data.test_name}{_args_str(data.args)}"

    @classmethod
    def to_ansi(cls, data: OutputCompareSuccess) -> str:
        return (
            f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` — {data.test_name}"
            f"{_args_str(data.args)}"
        )


@register_layout("output-compare-failure")
class OutputCompareFailureLayout(Layout[OutputCompareFailure]):
    @classmethod
    def to_simple(cls, data: OutputCompareFailure) -> str:
        parts = [
            f"[FAIL] `{data.artifact_name}` — {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.diff:
            parts.append(f"Output diff (expected → actual):\n{data.diff}\n")
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
    def to_ansi(cls, data: OutputCompareFailure) -> str:
        parts = [
            f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` — {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.diff:
            parts.append(
                f"{F.YELLOW}Output diff (expected → actual):{F.RESET}\n{data.diff}\n"
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


@register_layout("output-compare-error")
class OutputCompareErrorLayout(Layout[OutputCompareError]):
    @classmethod
    def to_simple(cls, data: OutputCompareError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: OutputCompareError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
        )
