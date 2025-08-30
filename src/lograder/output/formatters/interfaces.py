from abc import ABC, abstractmethod

from ...builder.common.types import (
    AssignmentMetadata,
    BuildInfo,
    BuildOutput,
    PreprocessorInfo,
    PreprocessorOutput,
    RuntimeSummary,
)
from ...tests.test import TestInterface


class MetadataFormatterInterface(ABC):
    @abstractmethod
    def format(self, assignment_metadata: AssignmentMetadata):
        pass


class PreprocessorOutputFormatterInterface(ABC):
    @abstractmethod
    def format(self, preprocessor_output: PreprocessorOutput):
        pass


class PreprocessorInfoFormatterInterface(ABC):
    @abstractmethod
    def format(self, preprocessor_info: PreprocessorInfo):
        pass


class BuildOutputFormatterInterface(ABC):
    @abstractmethod
    def format(self, build_output: BuildOutput):
        pass


class BuildInfoFormatterInterface(ABC):
    @abstractmethod
    def format(self, build_info: BuildInfo):
        pass


class RuntimeSummaryFormatterInterface(ABC):
    @abstractmethod
    def format(self, runtime_summary: RuntimeSummary):
        pass


class TestCaseFormatterInterface(ABC):
    @abstractmethod
    def format(self, test_case: TestInterface):
        pass
