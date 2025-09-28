import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

from ...data.build import BuildConfig
from ...data.penalties import PenaltyConfig
from ...random_utils import random_name
from ..formatters.dispatcher import FormatPackage
from .addon import AddonInterface

if TYPE_CHECKING:
    from ...types import Command
    from ...types import ValgrindOutput as ValgrindOutput_t


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


class ValgrindOutput:
    LEAK_REGEX = re.compile(
        r"(\d+)\s+bytes in\s+(\d+)\s+blocks are (definitely lost|indirectly lost|possibly lost|still reachable)"
    )
    WARNING_PATTERNS = {
        "invalid_read": re.compile(r"Invalid read"),
        "invalid_write": re.compile(r"Invalid write"),
        "invalid_free": re.compile(r"Invalid free"),
        "mismatched_free": re.compile(r"Mismatched free"),
        "uninitialized_value": re.compile(r"uninitialised value"),
        "conditional_jump": re.compile(
            r"Conditional jump or move depends on uninitialised value"
        ),
        "syscall_param": re.compile(r"Syscall param"),
        "overlap": re.compile(r"overlap"),
    }

    def __init__(self, stderr: str):
        self._stderr: str = stderr
        self._warnings: ValgrindWarningSummary = ValgrindWarningSummary()
        self._leaks: ValgrindLeakSummary = ValgrindLeakSummary()
        self.parse_stderr()

    @classmethod
    def parse_valgrind_log(
        cls, stderr: str
    ) -> tuple[ValgrindLeakSummary, ValgrindWarningSummary]:
        # Init structures
        leaks: ValgrindLeakSummary = ValgrindLeakSummary()
        warnings: ValgrindWarningSummary = ValgrindWarningSummary()
        warnings.other = 0

        for line in stderr.split("\n"):
            # --- Leak parsing ---
            leak_match = cls.LEAK_REGEX.search(line)
            if leak_match:
                bytes_count = int(leak_match.group(1).replace(",", ""))
                blocks_count = int(leak_match.group(2).replace(",", ""))
                kind = leak_match.group(3).replace(" ", "_")  # normalize to dict key
                loss_entry = getattr(leaks, kind)
                prev_bytes = loss_entry.bytes
                prev_blocks = loss_entry.blocks
                setattr(
                    leaks,
                    kind,
                    LossEntry(
                        bytes=prev_bytes + bytes_count,
                        blocks=prev_blocks + blocks_count,
                    ),
                )
                continue

            # --- Warning parsing ---
            matched = False
            for key, pattern in cls.WARNING_PATTERNS.items():
                if pattern.search(line):
                    setattr(warnings, key, getattr(warnings, key) + 1)
                    matched = True
                    break
            if not matched and "==" in line and "==" in line.strip():
                # heuristic: unknown Valgrind warning line
                if not any(x in line for x in ["lost", "reachable"]):
                    warnings.other += 1

        return leaks, warnings

    def parse_stderr(self):
        self._leaks, self._warnings = self.parse_valgrind_log(self._stderr)

    def get_leaks(self) -> ValgrindLeakSummary:
        return self._leaks

    def get_warnings(self) -> ValgrindWarningSummary:
        return self._warnings


def valgrind(
    cmd: List[str | Path], stdin: Optional[str] = None
) -> tuple[ValgrindLeakSummary, ValgrindWarningSummary]:

    if sys.platform.startswith("win"):
        return ValgrindLeakSummary(), ValgrindWarningSummary()

    valgrind_file = f"valgrind-{random_name()}.log"
    with open(os.devnull, "w") as devnull:
        result = subprocess.run(
            [
                "valgrind",
                "--leak-check=full",
                "--show-leak-kinds=all",
                f"--log-file={valgrind_file}",
            ]
            + cmd,
            input=stdin,
            stdout=devnull,
            stderr=devnull,
            text=True,
            timeout=BuildConfig.DEFAULT_EXECUTABLE_TIMEOUT,
        )

    if result.returncode != 0:
        if Path(valgrind_file).is_file():
            os.remove(valgrind_file)
        return ValgrindLeakSummary(), ValgrindWarningSummary()

    with open(valgrind_file, "r", encoding="utf-8", errors="ignore") as f:
        valgrind_log = f.read()
    valgrind_output = ValgrindOutput(valgrind_log)
    os.remove(valgrind_file)

    return valgrind_output.get_leaks(), valgrind_output.get_warnings()


class ValgrindAddon(AddonInterface):
    def __init__(self):
        super().__init__()
        self._output: Optional[ValgrindLeakSummary] = None
        self._warnings: Optional[ValgrindWarningSummary] = None
        self._stdin: str = ""
        self._args: Command = []

    def set_args(self, args: Command):
        self._args = args

    def get_args(self) -> Command:
        return self._args

    def set_stdin(self, stdin: str):
        self._stdin = stdin

    def get_stdin(self):
        return self._stdin

    def run(self) -> None:
        self._output, self._warnings = valgrind(
            self.get_builder().get_start_command() + self.get_args(), self.get_stdin()
        )

    def get_penalty(self) -> float:
        if self._output is None:
            self.run()
        assert self._output is not None
        return (
            PenaltyConfig.DEFAULT_VALGRIND_LEAK_PENALTY if self._output.is_safe else 1.0
        )

    def get_output(self) -> FormatPackage:
        if self._output is None or self._warnings is None:
            self.run()
        assert self._output is not None
        assert self._warnings is not None

        data: ValgrindOutput_t = {"leaks": self._output, "warnings": self._warnings}

        return FormatPackage(
            label="valgrind",
            data=data,
        )
