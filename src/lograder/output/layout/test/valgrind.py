from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.valgrind import (
    ValgrindError,
    ValgrindTestError,
    ValgrindTestFailure,
    ValgrindTestSuccess,
)
from lograder.process.os_helpers import command_to_str


def _args_str(args: list[str]) -> str:
    return f" {command_to_str(args)}" if args else ""


def _format_vg_error_simple(err: ValgrindError) -> str:
    lines = [f"  [{err.kind}] {err.message}"]
    for frame in err.primary_frames:
        lines.append(f"    at {frame}")
    return "\n".join(lines)


def _format_vg_error_ansi(err: ValgrindError) -> str:
    lines = [f"  {F.RED}[{err.kind}]{F.RESET} {err.message}"]
    for frame in err.primary_frames:
        lines.append(f"    {F.YELLOW}at{F.RESET} {frame}")
    return "\n".join(lines)


@register_layout("valgrind-test-success")
class ValgrindTestSuccessLayout(Layout[ValgrindTestSuccess]):
    @classmethod
    def to_simple(cls, data: ValgrindTestSuccess) -> str:
        return (
            f"[CLEAN] `{data.artifact_name}` — {data.test_name}{_args_str(data.args)}"
        )

    @classmethod
    def to_ansi(cls, data: ValgrindTestSuccess) -> str:
        return (
            f"{S.BRIGHT}{F.GREEN}[CLEAN]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` — {data.test_name}{_args_str(data.args)}"
        )


@register_layout("valgrind-test-failure")
class ValgrindTestFailureLayout(Layout[ValgrindTestFailure]):
    @classmethod
    def to_simple(cls, data: ValgrindTestFailure) -> str:
        parts = [
            f"[ERRORS] `{data.artifact_name}` — {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.crashed:
            parts.append("  Fatal signal (crash) detected.\n")
        for err in data.errors:
            parts.append(_format_vg_error_simple(err))
            parts.append("\n")
        if data.stdin_text:
            parts.append(f"STDIN: {repr(data.stdin_text)}\n")
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: ValgrindTestFailure) -> str:
        parts = [
            f"{S.BRIGHT}{F.RED}[ERRORS]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` — {data.test_name}{_args_str(data.args)}\n",
        ]
        if data.crashed:
            parts.append(f"  {F.RED}Fatal signal (crash) detected.{F.RESET}\n")
        for err in data.errors:
            parts.append(_format_vg_error_ansi(err))
            parts.append("\n")
        if data.stdin_text:
            parts.append(f"STDIN: {F.YELLOW}{repr(data.stdin_text)}{F.RESET}\n")
        return "".join(parts)


@register_layout("valgrind-test-error")
class ValgrindTestErrorLayout(Layout[ValgrindTestError]):
    @classmethod
    def to_simple(cls, data: ValgrindTestError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: ValgrindTestError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
        )
