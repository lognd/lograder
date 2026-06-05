from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.pytest import PytestError, PytestFailure, PytestSuccess

_PASS = f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
_FAIL = f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
_ERROR = f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"


def _duration_str(d: float | None) -> str:
    return f" ({d:.3f}s)" if d is not None else ""


def _truncate(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


@register_layout("pytest-success")
class PytestSuccessLayout(Layout[PytestSuccess]):
    @classmethod
    def to_simple(cls, data: PytestSuccess) -> str:
        return f"[PASS] {data.test_name}{_duration_str(data.duration)}"

    @classmethod
    def to_ansi(cls, data: PytestSuccess) -> str:
        return (
            f"{_PASS} {data.test_name}{F.YELLOW}{_duration_str(data.duration)}{F.RESET}"
        )


@register_layout("pytest-failure")
class PytestFailureLayout(Layout[PytestFailure]):
    @classmethod
    def to_simple(cls, data: PytestFailure) -> str:
        parts = [f"[FAIL] {data.test_name}{_duration_str(data.duration)}\n"]
        if data.failure_message:
            parts.append(f"  {data.failure_message}\n")
        if data.failure_text:
            parts.append(f"{_truncate(data.failure_text)}\n")
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: PytestFailure) -> str:
        parts = [
            f"{_FAIL}"
            f" {data.test_name}"
            f"{F.YELLOW}{_duration_str(data.duration)}{F.RESET}\n",
        ]
        if data.failure_message:
            parts.append(f"  {F.RED}{data.failure_message}{F.RESET}\n")
        if data.failure_text:
            parts.append(f"{_truncate(data.failure_text)}\n")
        return "".join(parts)


@register_layout("pytest-error")
class PytestErrorLayout(Layout[PytestError]):
    @classmethod
    def to_simple(cls, data: PytestError) -> str:
        return f"[ERROR] pytest: {data.message}"

    @classmethod
    def to_ansi(cls, data: PytestError) -> str:
        return f"{_ERROR} {F.CYAN}pytest{F.RESET}: {data.message}"
