from abc import ABC, abstractmethod
from typing import List

from ...builder.common.types import (
    AssignmentMetadata,
    BuilderOutput,
    PreprocessorOutput
)
from ...tests.test.analytics import ValgrindLeakSummary, ValgrindWarningSummary, CallgrindSummary, ExecutionTimeSummary
from ...tests.test import TestInterface


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
    def format(self, leak_summary: ValgrindLeakSummary) -> str:
        pass

class ValgrindWarningSummaryFormatterInterface(ABC):
    @abstractmethod
    def format(self, warning_summary: ValgrindWarningSummary) -> str:
        pass

class ExecutionTimeSummaryFormatterInterface(ABC):
    @abstractmethod
    def format(self,
               callgrind_summary: List[CallgrindSummary],
               execution_time_summary: ExecutionTimeSummary) -> str:
        pass

class TestCaseFormatterInterface(ABC):
    @abstractmethod
    def format(self, test_case: TestInterface) -> str:
        pass
