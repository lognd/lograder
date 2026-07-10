from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.check.source.raw_source_check import RawSourceCheckError
from lograder.pipeline.check.source.source_check import (
    SourceCheckData,
    SourceCheckError,
    SourceViolation,
)


def _bar(count: int, max_count: int) -> str:
    if max_count == 0:
        return f"{count}/0 (forbidden)"
    return f"{count}/{max_count}"


@register_layout("source-check-data")
class SourceCheckDataLayout(Layout[SourceCheckData]):
    @classmethod
    def to_ansi(cls, data: SourceCheckData) -> str:
        rows = "\n".join(
            f"  {F.GREEN}[ok]{F.RESET} {r.label}: {_bar(r.count, r.max_count)}"
            for r in data.results
        )
        return (
            f"{S.BRIGHT}< {F.CYAN}{data.check_name.upper()}{F.RESET} >"
            f"{S.RESET_ALL} [{F.CYAN}{data.file}{F.RESET}]\n"
            f"{F.GREEN}All constraints satisfied.{F.RESET}\n"
            f"{rows}"
        )

    @classmethod
    def to_simple(cls, data: SourceCheckData) -> str:
        summary = ", ".join(
            f"{r.label}: {_bar(r.count, r.max_count)}" for r in data.results
        )
        return f"[PASS] {data.check_name} - {data.file} - {summary}"


@register_layout("source-violation")
class SourceViolationLayout(Layout[SourceViolation]):
    @classmethod
    def to_ansi(cls, data: SourceViolation) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[VIOLATION]{F.RESET}{S.RESET_ALL}"
            f" {data.check_name} - {F.CYAN}{data.file}{F.RESET}\n"
            f"  {data.label}: used {F.RED}{data.count}{F.RESET}"
            f" time(s), max allowed is {F.GREEN}{data.max_count}{F.RESET}."
        )

    @classmethod
    def to_simple(cls, data: SourceViolation) -> str:
        return (
            f"[VIOLATION] {data.check_name} - {data.file} - "
            f"{data.label}: {data.count} used, max {data.max_count}."
        )


@register_layout("source-check-error")
class SourceCheckErrorLayout(Layout[SourceCheckError]):
    @classmethod
    def to_ansi(cls, data: SourceCheckError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" {data.check_name} - {F.CYAN}{data.file}{F.RESET}\n"
            f"  {data.message}"
        )

    @classmethod
    def to_simple(cls, data: SourceCheckError) -> str:
        return f"[ERROR] {data.check_name} - {data.file}: {data.message}"


@register_layout("raw-source-check-error")
class RawSourceCheckErrorLayout(Layout[RawSourceCheckError]):
    @classmethod
    def to_ansi(cls, data: RawSourceCheckError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" {data.check_name} - {F.CYAN}{data.file}{F.RESET}\n"
            f"  {data.message}"
        )

    @classmethod
    def to_simple(cls, data: RawSourceCheckError) -> str:
        return f"[ERROR] {data.check_name} - {data.file}: {data.message}"
