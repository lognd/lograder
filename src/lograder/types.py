from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Literal, TypedDict, Union, cast

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .grader.metadata import AssignmentMetadata

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
    "assignment-metadata",
    "command",
    "raw",
    "valgrind",
    "stdin",
    "expected-stdout",
    "actual-stdout",
    "byte-cmp",
    "stderr",
    "stdout",
    "unit-tests",
    "build-fail",
    "tree-diff",
]


class StreamOutput(TypedDict):
    stream_contents: str


class ByteStreamComparisonOutput(TypedDict):
    stream_actual_bytes: bytes
    stream_expected_bytes: bytes


class LossEntry(BaseModel):
    bytes: int = Field(default=0)
    blocks: int = Field(default=0)

    @property
    def is_safe(self) -> bool:
        return not self.bytes and not self.blocks


class ValgrindLeakSummary(BaseModel):
    definitely_lost: LossEntry = Field(default_factory=LossEntry)
    indirectly_lost: LossEntry = Field(default_factory=LossEntry)
    possibly_lost: LossEntry = Field(default_factory=LossEntry)
    still_reachable: LossEntry = Field(default_factory=LossEntry)

    @property
    def is_safe(self) -> bool:
        return (
            self.definitely_lost.is_safe
            and self.indirectly_lost.is_safe
            and self.possibly_lost.is_safe
        )


class ValgrindWarningSummary(BaseModel):
    invalid_read: int = Field(default=0)
    invalid_write: int = Field(default=0)
    invalid_free: int = Field(default=0)
    mismatched_free: int = Field(default=0)
    uninitialized_value: int = Field(default=0)
    conditional_jump: int = Field(default=0)
    syscall_param: int = Field(default=0)
    overlap: int = Field(default=0)
    other: int = Field(default=0)  # fallback bucket

    @property
    def is_safe(self) -> bool:
        return (
            not self.invalid_read
            and not self.invalid_write
            and not self.invalid_free
            and not self.mismatched_free
            and not self.uninitialized_value
            and not self.conditional_jump
            and not self.syscall_param
            and not self.overlap
            and not self.other
        )


class ValgrindOutput(TypedDict):
    leaks: ValgrindLeakSummary
    warnings: ValgrindWarningSummary


class CommandOutput(TypedDict):
    command: Command
    exit_code: int


class AssignmentMetadataOutput(TypedDict):
    metadata: AssignmentMetadata


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
