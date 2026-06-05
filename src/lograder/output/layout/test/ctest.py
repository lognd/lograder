from __future__ import annotations

from colorama import Fore as F

from lograder.output.layout.format_helpers.test_layout import ERROR as _ERROR
from lograder.output.layout.format_helpers.test_layout import PASS as _PASS
from lograder.output.layout.format_helpers.test_layout import (
    duration_str as _duration_str,
)
from lograder.output.layout.format_helpers.test_layout import (
    junit_failure_ansi as _junit_failure_ansi,
)
from lograder.output.layout.format_helpers.test_layout import (
    junit_failure_simple as _junit_failure_simple,
)
from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.test.ctest import CTestError, CTestFailure, CTestSuccess


@register_layout("ctest-success")
class CTestSuccessLayout(Layout[CTestSuccess]):
    @classmethod
    def to_simple(cls, data: CTestSuccess) -> str:
        return (
            f"[PASS] `{data.artifact_name}` - {data.test_name}"
            f"{_duration_str(data.duration)}"
        )

    @classmethod
    def to_ansi(cls, data: CTestSuccess) -> str:
        return (
            f"{_PASS}"
            f" `{F.CYAN}{data.artifact_name}{F.RESET}` - {data.test_name}"
            f"{F.YELLOW}{_duration_str(data.duration)}{F.RESET}"
        )


@register_layout("ctest-failure")
class CTestFailureLayout(Layout[CTestFailure]):
    @classmethod
    def to_simple(cls, data: CTestFailure) -> str:
        return _junit_failure_simple(
            data.artifact_name,
            data.test_name,
            data.duration,
            data.failure_message,
            data.failure_text,
        )

    @classmethod
    def to_ansi(cls, data: CTestFailure) -> str:
        return _junit_failure_ansi(
            data.artifact_name,
            data.test_name,
            data.duration,
            data.failure_message,
            data.failure_text,
        )


@register_layout("ctest-error")
class CTestErrorLayout(Layout[CTestError]):
    @classmethod
    def to_simple(cls, data: CTestError) -> str:
        return f"[ERROR] `{data.artifact_name}`: {data.message}"

    @classmethod
    def to_ansi(cls, data: CTestError) -> str:
        return f"{_ERROR} `{F.CYAN}{data.artifact_name}{F.RESET}`: {data.message}"
