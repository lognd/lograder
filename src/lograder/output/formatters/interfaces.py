from abc import ABC, abstractmethod

from ...builder.common.types import (
    AssignmentMetadata,
    BuilderOutput,
    PreprocessorOutput,
    RuntimeSummary,
)
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
    def format(self, runtime_summary: RuntimeSummary) -> str:
        pass


class TestCaseFormatterInterface(ABC):
    @abstractmethod
    def format(self, test_case: TestInterface) -> str:
        pass
