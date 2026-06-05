from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.gtest import GTestError, GTestFailure, GTestSuccess

_PASS = f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
_FAIL = f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
_ERROR = f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"


def _duration_str(d: float | None) -> str:
    return f" ({d:.3f}s)" if d is not None else ""


def _truncate(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


@register_layout("gtest-success")
class GTestSuccessLayout(Layout[GTestSuccess]):
    @classmethod
    def to_simple(cls, data: GTestSuccess) -> str:
        return (
            f"[PASS] `{data.artifact_name}` - {data.test_name}"
            f"{_duration_str(data.duration)}"
        )

    @classmethod
    def to_ansi(cls, data: GTestSuccess) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{F.YELLOW}{_duration_str(data.duration)}{F.RESET}"
        )


@register_layout("gtest-failure")
class GTestFailureLayout(Layout[GTestFailure]):
    @classmethod
    def to_simple(cls, data: GTestFailure) -> str:
        parts = [
            f"[FAIL] `{data.artifact_name}` - {data.test_name}"
            f"{_duration_str(data.duration)}\n",
        ]
        if data.failure_message:
            parts.append(f"  {data.failure_message}\n")
        if data.failure_text:
            parts.append(f"{_truncate(data.failure_text)}\n")
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: GTestFailure) -> str:
        parts = [
            f"{_FAIL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{F.YELLOW}{_duration_str(data.duration)}{F.RESET}\n",
        ]
        if data.failure_message:
            parts.append(f"  {F.RED}{data.failure_message}{F.RESET}\n")
        if data.failure_text:
            parts.append(f"{_truncate(data.failure_text)}\n")
        return "".join(parts)


@register_layout("gtest-error")
class GTestErrorLayout(Layout[GTestError]):
    @classmethod
    def to_simple(cls, data: GTestError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: GTestError) -> str:
        return (
            f"{_ERROR}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
        )
