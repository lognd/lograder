from __future__ import annotations

from colorama import Fore as F

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import FAIL as _FAIL
from lograder.output.layout.format_helpers.test_layout import PASS as _PASS
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.complexity import (
    ComplexityError,
    ComplexityFailure,
    ComplexitySuccess,
)


def _summary(data: ComplexitySuccess | ComplexityFailure) -> str:
    pairs = ", ".join(
        f"n={s}: {t:.4f}s" for s, t in zip(data.sizes, data.times_s, strict=True)
    )
    return (
        f"expected {data.expected}, got ~{data.measured_class} "
        f"(alpha={data.measured_exponent:.2f}) | {pairs}"
    )


@register_layout("complexity-success")
class ComplexitySuccessLayout(Layout[ComplexitySuccess]):
    @classmethod
    def to_simple(cls, data: ComplexitySuccess) -> str:
        return f"[PASS] `{data.artifact_name}` - {data.test_name}: {_summary(data)}"

    @classmethod
    def to_ansi(cls, data: ComplexitySuccess) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}\n"
            f"  {F.GREEN}{_summary(data)}{F.RESET}"
        )


@register_layout("complexity-failure")
class ComplexityFailureLayout(Layout[ComplexityFailure]):
    @classmethod
    def to_simple(cls, data: ComplexityFailure) -> str:
        return f"[FAIL] `{data.artifact_name}` - {data.test_name}: {_summary(data)}"

    @classmethod
    def to_ansi(cls, data: ComplexityFailure) -> str:
        return (
            f"{_FAIL}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}\n"
            f"  {F.RED}{_summary(data)}{F.RESET}"
        )


@register_layout("complexity-error")
class ComplexityErrorLayout(Layout[ComplexityError]):
    @classmethod
    def to_simple(cls, data: ComplexityError) -> str:
        return f"[ERROR] complexity `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: ComplexityError) -> str:
        return (
            f"{_ERROR} complexity"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}`:"
            f" {F.RED}{data.message}{F.RESET}"
        )
