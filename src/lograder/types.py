from __future__ import annotations

from pathlib import Path
from typing import List, Literal, TypedDict

# --- GENERAL TYPES ---
Command = List[Path | str]

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
    stream_a_bytes: bytes
    stream_b_bytes: bytes


# --- UNIT-TEST TYPES ---
class UnitTestCase(TypedDict):
    name: str
    success: bool
    output: str


class UnitTestSuite(TypedDict):
    name: str
    cases: List[UnitTestCase | UnitTestSuite]
