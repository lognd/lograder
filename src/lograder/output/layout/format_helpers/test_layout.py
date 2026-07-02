from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.process.os_helpers import command_to_str

PASS = f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
FAIL = f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
ERROR = f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"


def args_str(args: list[str]) -> str:
    return f" {command_to_str(args)}" if args else ""


def header_line_simple(
    badge: str, artifact_name: str, test_name: str, args: list[str]
) -> str:
    return f"{badge} `{artifact_name}` - {test_name}{args_str(args)}"


def header_line_ansi(
    badge: str, artifact_name: str, test_name: str, args: list[str]
) -> str:
    return f"{badge} `{F.CYAN}{artifact_name}{F.RESET}` - {test_name}{args_str(args)}"


def truncate(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


def duration_str(d: float | None) -> str:
    return f" ({d:.3f}s)" if d is not None else ""


def junit_failure_simple(
    artifact_name: str,
    test_name: str,
    duration: float | None,
    failure_message: str,
    failure_text: str,
    limit: int = 800,
) -> str:
    parts = [f"[FAIL] `{artifact_name}` - {test_name}{duration_str(duration)}\n"]
    if failure_message:
        parts.append(f"  {failure_message}\n")
    if failure_text:
        parts.append(f"{truncate(failure_text, limit)}\n")
    return "".join(parts)


def junit_failure_ansi(
    artifact_name: str,
    test_name: str,
    duration: float | None,
    failure_message: str,
    failure_text: str,
    limit: int = 800,
) -> str:
    parts = [
        f"{FAIL} `{F.CYAN}{artifact_name}{F.RESET}` - {test_name}"
        f"{F.YELLOW}{duration_str(duration)}{F.RESET}\n"
    ]
    if failure_message:
        parts.append(f"  {F.RED}{failure_message}{F.RESET}\n")
    if failure_text:
        parts.append(f"{truncate(failure_text, limit)}\n")
    return "".join(parts)


def exit_code_stdin_simple(
    parts: list[str],
    expected_exit_code: int | None,
    actual_exit_code: int,
    stdin_text: str | None,
) -> None:
    if expected_exit_code is not None and actual_exit_code != expected_exit_code:
        parts.append(
            f"Exit code: expected {expected_exit_code}, got {actual_exit_code}.\n"
        )
    if stdin_text:
        parts.append(f"stdin: {repr(stdin_text)}\n")


def exit_code_stdin_ansi(
    parts: list[str],
    expected_exit_code: int | None,
    actual_exit_code: int,
    stdin_text: str | None,
) -> None:
    if expected_exit_code is not None and actual_exit_code != expected_exit_code:
        parts.append(
            f"Exit code: expected {F.GREEN}{expected_exit_code}{F.RESET},"
            f" got {F.RED}{actual_exit_code}{F.RESET}.\n"
        )
    if stdin_text:
        parts.append(f"stdin: {F.YELLOW}{repr(stdin_text)}{F.RESET}\n")
