from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.symbol import SymbolError, SymbolFailure, SymbolSuccess

_PASS = f"{S.BRIGHT}{F.GREEN}[PASS]{F.RESET}{S.RESET_ALL}"
_FAIL = f"{S.BRIGHT}{F.RED}[FAIL]{F.RESET}{S.RESET_ALL}"
_ERROR = f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"


@register_layout("symbol-success")
class SymbolSuccessLayout(Layout[SymbolSuccess]):
    @classmethod
    def to_simple(cls, data: SymbolSuccess) -> str:
        found = ", ".join(data.found) if data.found else "(none required)"
        return f"[PASS] `{data.artifact_name}` - {data.test_name} - symbols: {found}"

    @classmethod
    def to_ansi(cls, data: SymbolSuccess) -> str:
        found = (
            ", ".join(f"`{s}`" for s in data.found) if data.found else "(none required)"
        )
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}\n"
            f"  Symbols present: {found}"
        )


@register_layout("symbol-failure")
class SymbolFailureLayout(Layout[SymbolFailure]):
    @classmethod
    def to_simple(cls, data: SymbolFailure) -> str:
        parts = [f"[FAIL] `{data.artifact_name}` - {data.test_name}"]
        if data.missing:
            parts.append(f"  Missing required: {', '.join(data.missing)}")
        if data.present:
            parts.append(f"  Forbidden present: {', '.join(data.present)}")
        return "\n".join(parts)

    @classmethod
    def to_ansi(cls, data: SymbolFailure) -> str:
        parts = [
            f"{_FAIL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
        ]
        if data.missing:
            missing = ", ".join(f"`{s}`" for s in data.missing)
            parts.append(f"  {F.RED}Missing required symbols:{F.RESET} {missing}")
        if data.present:
            present = ", ".join(f"`{s}`" for s in data.present)
            parts.append(f"  {F.RED}Forbidden symbols present:{F.RESET} {present}")
        return "\n".join(parts)


@register_layout("symbol-error")
class SymbolErrorLayout(Layout[SymbolError]):
    @classmethod
    def to_simple(cls, data: SymbolError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: SymbolError) -> str:
        return (
            f"{_ERROR}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
        )
