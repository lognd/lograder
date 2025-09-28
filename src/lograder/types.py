from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Literal, TypedDict, Union, cast

if TYPE_CHECKING:
    from .grader.addons.valgrind import ValgrindLeakSummary, ValgrindWarningSummary

# --- BUILD TYPES ---
Command = List[Union[str, Path]]
ProjectType = Literal["cmake", "cxx-source", "makefile", "py-source", "pyproject"]
TestType = Literal["catch2", "pytest"]

# --- GRADESCOPE TYPES ---
TextFormat = Literal["text", "html", "simple_format", "md", "ansi"]
Visibility = Literal["visible", "after_due_date", "after_published", "hidden"]
Status = Literal["passed", "failed"]
AscendingOrder = Literal["asc"]

# --- FORMATTER TYPES ---
FormatLabel = Literal[
    "raw",
    "valgrind",
    "callgrind",
    "time",
    "stdin",
    "expected-stdout",
    "actual-stdout",
    "byte-cmp",
    "stderr",
    "stdout",
    "unit-tests",
    "build-fail",
]


class StreamOutput(TypedDict):
    stream_contents: str


class ByteStreamComparisonOutput(TypedDict):
    stream_actual_bytes: bytes
    stream_expected_bytes: bytes


class ValgrindOutput(TypedDict):
    leaks: ValgrindLeakSummary
    warnings: ValgrindWarningSummary


# --- UNIT-TEST TYPES ---
class UnitTestCase(TypedDict):
    name: str
    success: bool
    output: str


class UnitTestSuite(TypedDict):
    name: str
    cases: List[UnitTestCase | UnitTestSuite]


def is_successful_test(suite: UnitTestSuite | UnitTestCase) -> bool:
    if "success" in suite.keys():
        return cast(UnitTestCase, suite)["success"]
    return all(is_successful_test(case) for case in cast(UnitTestSuite, suite)["cases"])
