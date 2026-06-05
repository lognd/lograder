from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.check.source.source_check import (
    OperatorCheckData,
    OperatorCheckError,
    OperatorViolation,
)


def _bar(count: int, max_count: int) -> str:
    if max_count == 0:
        return f"{count}/0 (forbidden)"
    return f"{count}/{max_count}"


@register_layout("operator-check-data")
class OperatorCheckDataLayout(Layout[OperatorCheckData]):
    @classmethod
    def to_ansi(cls, data: OperatorCheckData) -> str:
        rows = "\n".join(
            f"  {F.GREEN}✓{F.RESET} {r.label}: {_bar(r.count, r.max_count)}"
            for r in data.results
        )
        return (
            f"{S.BRIGHT}< {F.CYAN}{data.check_name.upper()}{F.RESET} >"
            f"{S.RESET_ALL} [{F.CYAN}{data.file}{F.RESET}]\n"
            f"{F.GREEN}All operator constraints satisfied.{F.RESET}\n"
            f"{rows}"
        )

    @classmethod
    def to_simple(cls, data: OperatorCheckData) -> str:
        summary = ", ".join(
            f"{r.label}: {_bar(r.count, r.max_count)}" for r in data.results
        )
        return f"[PASS] {data.check_name} — {data.file} — {summary}"


@register_layout("operator-violation")
class OperatorViolationLayout(Layout[OperatorViolation]):
    @classmethod
    def to_ansi(cls, data: OperatorViolation) -> str:
        toks = ", ".join(f"`{t}`" for t in data.tokens)
        return (
            f"{S.BRIGHT}{F.RED}[VIOLATION]{F.RESET}{S.RESET_ALL}"
            f" {data.check_name} — {F.CYAN}{data.file}{F.RESET}\n"
            f"  {data.label} ({toks}): used {F.RED}{data.count}{F.RESET}"
            f" time(s), max allowed is {F.GREEN}{data.max_count}{F.RESET}."
        )

    @classmethod
    def to_simple(cls, data: OperatorViolation) -> str:
        toks = ", ".join(data.tokens)
        return (
            f"[VIOLATION] {data.check_name} — {data.file} — "
            f"{data.label} ({toks}): {data.count} used, max {data.max_count}."
        )


@register_layout("operator-check-error")
class OperatorCheckErrorLayout(Layout[OperatorCheckError]):
    @classmethod
    def to_ansi(cls, data: OperatorCheckError) -> str:
        return (
            f"{S.BRIGHT}{F.RED}[ERROR]{F.RESET}{S.RESET_ALL}"
            f" {data.check_name} — {F.CYAN}{data.file}{F.RESET}\n"
            f"  {data.message}"
        )

    @classmethod
    def to_simple(cls, data: OperatorCheckError) -> str:
        return f"[ERROR] {data.check_name} — {data.file}: {data.message}"
