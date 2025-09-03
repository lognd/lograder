from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Sequence

from ...dispatch.common.types import (
    AssignmentMetadata,
    BuilderOutput,
    PreprocessorOutput,
)
from ...tests.test.analytics import (
    CallgrindSummary,
    ExecutionTimeSummary,
    ValgrindLeakSummary,
    ValgrindWarningSummary,
)

if TYPE_CHECKING:
    from ...tests.test.interface import ExecutableTestInterface


class MetadataFormatterInterface(ABC):
    @abstractmethod
    def format(self, assignment_metadata: AssignmentMetadata) -> str:
        pass


class PreprocessorOutputFormatterInterface(ABC):
    @abstractmethod
    def format(self, preprocessor_output: PreprocessorOutput) -> str:
        pass


class BuildOutputFormatterInterface(ABC):
    @abstractmethod
    def format(self, build_output: BuilderOutput) -> str:
        pass


class RuntimeSummaryFormatterInterface(ABC):
    @abstractmethod
    def format(self, test_cases: Sequence[ExecutableTestInterface]) -> str:
        pass


class ValgrindLeakSummaryFormatterInterface(ABC):
    @abstractmethod
    def format(self, leak_summary: Optional[ValgrindLeakSummary]) -> str:
        pass


class ValgrindWarningSummaryFormatterInterface(ABC):
    @abstractmethod
    def format(self, warning_summary: Optional[ValgrindWarningSummary]) -> str:
        pass


class ExecutionTimeSummaryFormatterInterface(ABC):
    @abstractmethod
    def format(
        self,
        callgrind_summary: Optional[List[CallgrindSummary]],
        execution_time_summary: Optional[ExecutionTimeSummary],
    ) -> str:
        pass


class ExecutableTestFormatterInterface(ABC):
    @abstractmethod
    def format(self, test_case: ExecutableTestInterface) -> str:
        pass
