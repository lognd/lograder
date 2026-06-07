from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import FAIL as _FAIL
from lograder.output.layout.format_helpers.test_layout import PASS as _PASS
from lograder.output.layout.format_helpers.test_layout import truncate as _truncate
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.compile_check import (
    CompileCheckError,
    CompileCheckFailure,
    CompileCheckSuccess,
)


@register_layout("compile-check-success")
class CompileCheckSuccessLayout(Layout[CompileCheckSuccess]):
    @classmethod
    def to_simple(cls, data: CompileCheckSuccess) -> str:
        return f"[PASS] compile-check - {data.test_name}: {data.compile_message}"

    @classmethod
    def to_ansi(cls, data: CompileCheckSuccess) -> str:
        return (
            f"{_PASS} compile-check - {data.test_name}: "
            f"{F.GREEN}{data.compile_message}{F.RESET}"
        )


@register_layout("compile-check-failure")
class CompileCheckFailureLayout(Layout[CompileCheckFailure]):
    @classmethod
    def to_simple(cls, data: CompileCheckFailure) -> str:
        parts = [f"[FAIL] compile-check - {data.test_name}: {data.compile_message}"]
        if data.stderr.strip():
            parts.append(_truncate(data.stderr.rstrip()))
        return "\n".join(parts)

    @classmethod
    def to_ansi(cls, data: CompileCheckFailure) -> str:
        parts = [
            f"{_FAIL} compile-check - {data.test_name}: "
            f"{F.RED}{data.compile_message}{F.RESET}"
        ]
        if data.stderr.strip():
            parts.append(
                f"{S.DIM}compiler output:{S.RESET_ALL}\n{_truncate(data.stderr.rstrip())}"
            )
        return "\n".join(parts)


@register_layout("compile-check-error")
class CompileCheckErrorLayout(Layout[CompileCheckError]):
    @classmethod
    def to_simple(cls, data: CompileCheckError) -> str:
        return f"[ERROR] compile-check: {data.message}"

    @classmethod
    def to_ansi(cls, data: CompileCheckError) -> str:
        return f"{_ERROR} compile-check: {F.RED}{data.message}{F.RESET}"
