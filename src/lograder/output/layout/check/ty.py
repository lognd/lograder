from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.check.ty_check import TyCheckData, TyCheckError, TyViolation


@register_layout("ty-check-data")
class TyCheckDataLayout(Layout[TyCheckData]):
    @classmethod
    def to_simple(cls, data: TyCheckData) -> str:
        files = ", ".join(data.files)
        return f"[PASS] ty - {files} - no type errors"

    @classmethod
    def to_ansi(cls, data: TyCheckData) -> str:
        files = ", ".join(f"{F.CYAN}{f}{F.RESET}" for f in data.files)
        return (
            f"{S.BRIGHT}< {F.CYAN}TY{F.RESET} >{S.RESET_ALL} {files}\n"
            f"{F.GREEN}No type errors found.{F.RESET}"
        )


@register_layout("ty-violation")
class TyViolationLayout(Layout[TyViolation]):
    @classmethod
    def to_simple(cls, data: TyViolation) -> str:
        loc = f"{data.file}:{data.line}:{data.column}"
        rule = f" [{data.rule}]" if data.rule else ""
        return f"[TYPE ERROR] {loc}: {data.message}{rule}"

    @classmethod
    def to_ansi(cls, data: TyViolation) -> str:
        loc = f"{F.CYAN}{data.file}{F.RESET}:{data.line}:{data.column}"
        rule = f" {S.DIM}[{data.rule}]{S.RESET_ALL}" if data.rule else ""
        return (
            f"{S.BRIGHT}{F.RED}[TYPE ERROR]{F.RESET}{S.RESET_ALL}"
            f" {loc}: {F.RED}{data.message}{F.RESET}{rule}"
        )


@register_layout("ty-check-error")
class TyCheckErrorLayout(Layout[TyCheckError]):
    @classmethod
    def to_simple(cls, data: TyCheckError) -> str:
        return f"[ERROR] ty: {data.message}"

    @classmethod
    def to_ansi(cls, data: TyCheckError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" ty: {F.RED}{data.message}{F.RESET}"
        )
