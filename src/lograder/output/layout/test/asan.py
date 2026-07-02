from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import (
    header_line_ansi as _header_line_ansi,
)
from lograder.output.layout.format_helpers.test_layout import (
    header_line_simple as _header_line_simple,
)
from lograder.output.layout.format_helpers.test_layout import truncate as _truncate
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.asan import ASanError, ASanFailure, ASanSuccess

_CLEAN = f"{S.BRIGHT}{F.GREEN}[CLEAN]{F.RESET}{S.RESET_ALL}"
_ASAN_ERR = f"{S.BRIGHT}{F.RED}[ASAN ERROR]{F.RESET}{S.RESET_ALL}"


@register_layout("asan-success")
class ASanSuccessLayout(Layout[ASanSuccess]):
    @classmethod
    def to_simple(cls, data: ASanSuccess) -> str:
        return _header_line_simple(
            "[CLEAN]", data.artifact_name, data.test_name, data.args
        )

    @classmethod
    def to_ansi(cls, data: ASanSuccess) -> str:
        return _header_line_ansi(_CLEAN, data.artifact_name, data.test_name, data.args)


@register_layout("asan-failure")
class ASanFailureLayout(Layout[ASanFailure]):
    @classmethod
    def to_simple(cls, data: ASanFailure) -> str:
        parts = [
            _header_line_simple(
                "[ASAN ERROR]", data.artifact_name, data.test_name, data.args
            )
        ]
        if data.asan_report.strip():
            parts.append(_truncate(data.asan_report, 1200))
        return "\n".join(parts)

    @classmethod
    def to_ansi(cls, data: ASanFailure) -> str:
        parts = [
            _header_line_ansi(_ASAN_ERR, data.artifact_name, data.test_name, data.args)
        ]
        if data.asan_report.strip():
            parts.append(
                f"{S.DIM}ASan report:{S.RESET_ALL}\n"
                f"{F.RED}{_truncate(data.asan_report, 1200)}{F.RESET}"
            )
        return "\n".join(parts)


@register_layout("asan-error")
class ASanErrorLayout(Layout[ASanError]):
    @classmethod
    def to_simple(cls, data: ASanError) -> str:
        return f"[ERROR] asan `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: ASanError) -> str:
        return (
            f"{_ERROR} asan"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}`:"
            f" {F.RED}{data.message}{F.RESET}"
        )
