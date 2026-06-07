from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.check.mypy_check import (
    MypyCheckData,
    MypyCheckError,
    MypyViolation,
)


@register_layout("mypy-check-data")
class MypyCheckDataLayout(Layout[MypyCheckData]):
    @classmethod
    def to_simple(cls, data: MypyCheckData) -> str:
        files = ", ".join(data.files)
        return f"[PASS] Mypy - {files} - no type errors"

    @classmethod
    def to_ansi(cls, data: MypyCheckData) -> str:
        files = ", ".join(f"{F.CYAN}{f}{F.RESET}" for f in data.files)
        return (
            f"{S.BRIGHT}< {F.CYAN}MYPY{F.RESET} >{S.RESET_ALL} {files}\n"
            f"{F.GREEN}No type errors found.{F.RESET}"
        )


@register_layout("mypy-violation")
class MypyViolationLayout(Layout[MypyViolation]):
    @classmethod
    def to_simple(cls, data: MypyViolation) -> str:
        loc = f"{data.file}:{data.line}:{data.column}"
        code = f" [{data.error_code}]" if data.error_code else ""
        return f"[TYPE ERROR] {loc}: {data.message}{code}"

    @classmethod
    def to_ansi(cls, data: MypyViolation) -> str:
        loc = f"{F.CYAN}{data.file}{F.RESET}:{data.line}:{data.column}"
        code = f" {S.DIM}[{data.error_code}]{S.RESET_ALL}" if data.error_code else ""
        return (
            f"{S.BRIGHT}{F.RED}[TYPE ERROR]{F.RESET}{S.RESET_ALL}"
            f" {loc}: {F.RED}{data.message}{F.RESET}{code}"
        )


@register_layout("mypy-check-error")
class MypyCheckErrorLayout(Layout[MypyCheckError]):
    @classmethod
    def to_simple(cls, data: MypyCheckError) -> str:
        return f"[ERROR] Mypy: {data.message}"

    @classmethod
    def to_ansi(cls, data: MypyCheckError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" Mypy: {F.RED}{data.message}{F.RESET}"
        )
