from typing import Optional, List
import re
import os
import subprocess
from pydantic import BaseModel, Field
from pathlib import Path
from ...common.types import FilePath
from ...common.utils import random_name

class LossEntry(BaseModel):
    bytes: int = Field(default=0)
    blocks: int = Field(default=0)

    @property
    def is_safe(self) -> bool:
        return not self.bytes and not self.blocks

class MemoryLossSummary(BaseModel):
    definitely_lost: LossEntry = Field(default_factory=LossEntry)
    indirectly_lost: LossEntry = Field(default_factory=LossEntry)
    possibly_lost: LossEntry = Field(default_factory=LossEntry)
    still_reachable: LossEntry = Field(default_factory=LossEntry)

    @property
    def is_safe(self) -> bool:
        return self.directly_lost.is_safe and self.indirectly_lost.is_safe and self.possibly_lost.is_safe

class WarningSummary(BaseModel):
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
        return not self.invalid_read and not self.invalid_write and not self.invalid_free and not self.mismatched_free \
    and not self.uninitialized_value and not self.conditional_jump and not self.syscall_param and not self.overlap and not self.other

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
        "conditional_jump": re.compile(r"Conditional jump or move depends on uninitialised value"),
        "syscall_param": re.compile(r"Syscall param"),
        "overlap": re.compile(r"overlap"),
    }

    def __init__(self, stderr: str):
        self._stderr: str = stderr
        self._warnings: WarningSummary = WarningSummary()
        self._leaks: MemoryLossSummary = MemoryLossSummary()
        self.parse_stderr()

    @classmethod
    def parse_valgrind_log(cls, path: FilePath) -> tuple[MemoryLossSummary, WarningSummary]:
        # Init structures
        leaks: MemoryLossSummary = MemoryLossSummary()
        warnings: WarningSummary = WarningSummary()
        warnings["other"] = 0

        with open(Path(path), "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # --- Leak parsing ---
                leak_match = cls.LEAK_REGEX.search(line)
                if leak_match:
                    bytes_count = int(leak_match.group(1).replace(",", ""))
                    blocks_count = int(leak_match.group(2).replace(",", ""))
                    kind = leak_match.group(3).replace(" ", "_")  # normalize to dict key
                    prev_bytes, prev_blocks = leaks[kind]
                    leaks[kind] = (prev_bytes + bytes_count, prev_blocks + blocks_count)
                    continue

                # --- Warning parsing ---
                matched = False
                for key, pattern in cls.WARNING_PATTERNS.items():
                    if pattern.search(line):
                        warnings[key] += 1
                        matched = True
                        break
                if not matched and "==" in line and "==" in line.strip():
                    # heuristic: unknown Valgrind warning line
                    if not any(x in line for x in ["lost", "reachable"]):
                        warnings["other"] += 1

        return leaks, warnings

    def parse_stderr(self):
        self._leaks, self._warnings = self.parse_valgrind_log(self._stderr)

    def get_leaks(self) -> MemoryLossSummary:
        return self._leaks

    def get_warnings(self) -> WarningSummary:
        return self._warnings

class CallSummary(BaseModel):
    cost: int
    percent: float
    file: str
    function: str
    shared_object: Optional[str]

class CallgrindOutput:
    LINE_REGEX = re.compile(
        r"^\s*(?P<cost>[\d,]+)\s+\((?P<percent>[\d\.]+)%\)\s+"
        r"(?P<file>[^:]+):(?P<function>[^\[]+)"
        r"(?:\s+\[(?P<so>[^\]]+)\])?"
    )

    def __init__(self, stdout: str):
        self._stdout: str = stdout
        self._calls: List[CallSummary] = []
        self.parse_stdout()

    @classmethod
    def parse_callgrind_annotate(cls, path: FilePath) -> List[CallSummary]:
        results: List[CallSummary] = []
        with open(Path(path), "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = cls.LINE_REGEX.match(line)
                if not m:
                    continue
                results.append(CallSummary(
                    cost=int(m.group("cost").replace(",", "")),
                    percent=float(m.group("percent")),
                    file=m.group("file").strip(),
                    function=m.group("function").strip(),
                    shared_object=m.group("so"),
                ))
        return results

    def parse_stdout(self):
        self._calls = self.parse_callgrind_annotate(self._stdout)

    def get_calls(self):
        return self._calls

    def get_instruction_count(self):
        return sum([call.cost for call in self.get_calls()])

class TimeSummary(BaseModel):
    user_cpu_time: float = Field(default=0)
    system_cpu_time: float = Field(default=0)
    total_cpu_time: float = Field(default=0)
    percent_cpu_utilization: float = Field(default=0)
    peak_physical_memory_usage: float = Field(default=0)
    num_disk_reads: int = Field(default=0)
    num_disk_writes: int = Field(default=0)
    num_major_page_faults: int = Field(default=0)
    num_minor_page_faults: int = Field(default=0)
    num_pages_swapped_to_disk: int = Field(default=0)

class TimeOutput:
    def __init__(self, stderr: str):
        self._stderr: str = stderr
        self._time: TimeSummary = TimeSummary()
        self.parse_stderr()

    @staticmethod
    def parse_usr_time(stderr: str) -> TimeSummary:
        stats = {}
        for line in stderr.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                stats[k.strip()] = v.strip().replace("%", "")
        return TimeSummary(**stats)

    def parse_stderr(self):
        self._time = self.parse_usr_time(self._stderr)

    def get_time(self) -> TimeSummary:
        return self._time

def valgrind(cmd: List[str], stdin: Optional[str] = None) -> tuple[MemoryLossSummary, WarningSummary]:
    valgrind_file = f"valgrind-{random_name()}.log"
    with open(os.devnull, "w") as devnull:
        subprocess.run(
            ["valgrind", "--leak-check=full", "--show-leak-kinds=all", "--log-file", valgrind_file] + cmd,
            stdin=stdin,
            stdout=devnull,
            stderr=devnull,
            text=True
        )

    with open(valgrind_file, "r", encoding="utf-8", errors="ignore") as f:
        valgrind_log = f.read()

    valgrind_output = ValgrindOutput(valgrind_log)
    return valgrind_output.get_leaks(), valgrind_output.get_warnings()

def callgrind(cmd: List[str], stdin: Optional[str] = None) -> List[CallSummary]:
    callgrind_file = f"callgrind-{random_name()}.out"
    annotate_file = f"annotate-{random_name()}.log"

    with open(os.devnull, "w") as devnull:
        subprocess.run(
            ["valgrind", "--tool=callgrind", f"--callgrind-out-file={callgrind_file}"] + cmd,
            stdin=stdin,
            stdout=devnull,
            stderr=devnull,
            text=True
        )

    subprocess.run(
        ["callgrind_annotate", "--auto=yes", "--threshold=0", callgrind_file],
        stdout=open(annotate_file, "w", encoding="utf-8"),
        stderr=subprocess.DEVNULL,
        text=True
    )

    with open(annotate_file, "r", encoding="utf-8", errors="ignore") as f:
        annotate_output = f.read()

    return CallgrindOutput(annotate_output).get_calls()

def usr_time(cmd: List[str], stdin: Optional[str] = None) -> TimeSummary:
    time_file = f"time-{random_name()}.log"
    with open(os.devnull, "w") as devnull:
        subprocess.run(
            ["/usr/bin/time",
             "-f", "user_cpu_time=%U\nsystem_cpu_time=%S\ntotal_cpu_time=%e\npercent_cpu_utilization=%P\npeak_physical_memory_usage=%M\nnum_disk_reads=%I\nnum_disk_writes=%O\nnum_major_page_faults=%F\nnum_minor_page_faults=%R\nnum_pages_swapped_to_disk=%W\n",
             "-o", time_file]
            + cmd,
            stdin=stdin,  # program can still read from stdin
            stdout=devnull,  # hide stdout
            stderr=devnull,
            text=True
        )
    with open(time_file) as f:
        time_stats = f.read()

    return TimeOutput(time_stats).get_time()
