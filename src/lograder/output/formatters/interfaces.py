from abc import ABC, abstractmethod
from typing import List, Optional

from ...builder.common.types import (
    AssignmentMetadata,
    BuilderOutput,
    PreprocessorOutput,
)
from ...tests.test import TestInterface
from ...tests.test.analytics import (
    CallgrindSummary,
    ExecutionTimeSummary,
    ValgrindLeakSummary,
    ValgrindWarningSummary,
)


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
    def format(self, test_cases: List[TestInterface]) -> str:
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


class TestCaseFormatterInterface(ABC):
    @abstractmethod
    def format(self, test_case: TestInterface) -> str:
        pass
