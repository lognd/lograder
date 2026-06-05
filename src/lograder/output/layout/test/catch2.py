from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.catch2 import Catch2Error, Catch2Failure, Catch2Success

_PASS = f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
_FAIL = f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
_ERROR = f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"


def _duration_str(d: float | None) -> str:
    return f" ({d:.3f}s)" if d is not None else ""


def _truncate(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


@register_layout("catch2-success")
class Catch2SuccessLayout(Layout[Catch2Success]):
    @classmethod
    def to_simple(cls, data: Catch2Success) -> str:
        return (
            f"[PASS] `{data.artifact_name}` - {data.test_name}"
            f"{_duration_str(data.duration)}"
        )

    @classmethod
    def to_ansi(cls, data: Catch2Success) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{F.YELLOW}{_duration_str(data.duration)}{F.RESET}"
        )


@register_layout("catch2-failure")
class Catch2FailureLayout(Layout[Catch2Failure]):
    @classmethod
    def to_simple(cls, data: Catch2Failure) -> str:
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
    def to_ansi(cls, data: Catch2Failure) -> str:
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


@register_layout("catch2-error")
class Catch2ErrorLayout(Layout[Catch2Error]):
    @classmethod
    def to_simple(cls, data: Catch2Error) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: Catch2Error) -> str:
        return f"{_ERROR} `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
