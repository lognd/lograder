from typing import List, Optional

from pydantic import BaseModel, Field

from ...output.formatters.interfaces import (
    BuildInfoFormatterInterface,
    BuildOutputFormatterInterface,
    MetadataFormatterInterface,
    PreprocessorInfoFormatterInterface,
    PreprocessorOutputFormatterInterface,
    RuntimeSummaryFormatterInterface,
    TestCaseFormatterInterface,
)
from ...output.raw_json.assignment import AssignmentJSON
from ...output.raw_json.test_case import TestCaseJSON
from ...tests.test import TestInterface
from .types import (
    AssignmentMetadata,
    BuildInfo,
    BuildOutput,
    PreprocessorInfo,
    PreprocessorOutput,
    RuntimeSummary,
)


class AssignmentSummary(BaseModel):
    metadata: AssignmentMetadata
    preprocessor_output: PreprocessorOutput
    preprocessor_info: PreprocessorInfo
    build_output: BuildOutput
    build_info: BuildInfo
    runtime_summary: RuntimeSummary
    test_cases: List[TestInterface]

    metadata_fmt: MetadataFormatterInterface = Field(default_factory=..., exclude=True)
    preprocessor_output_fmt: PreprocessorOutputFormatterInterface = Field(
        default_factory=..., exclude=True
    )
    preprocessor_info_fmt: PreprocessorInfoFormatterInterface = Field(
        default_factory=..., exclude=True
    )
    build_output_fmt: BuildOutputFormatterInterface = Field(
        default_factory=..., exclude=True
    )
    build_info_fmt: BuildInfoFormatterInterface = Field(
        default_factory=..., exclude=True
    )
    runtime_summary_fmt: RuntimeSummaryFormatterInterface = Field(
        default_factory=..., exclude=True
    )
    test_case_fmt: TestCaseFormatterInterface = Field(default_factory=..., exclude=True)

    @classmethod
    def set_formatters(
        cls,
        *,
        metadata: Optional[MetadataFormatterInterface] = None,
        preprocessor_output: Optional[PreprocessorOutputFormatterInterface] = None,
        preprocessor_info: Optional[PreprocessorInfoFormatterInterface] = None,
        build_output: Optional[BuildOutputFormatterInterface] = None,
        build_info: Optional[BuildInfoFormatterInterface] = None,
        runtime_summary: Optional[RuntimeSummaryFormatterInterface] = None,
        test_case: Optional[TestCaseFormatterInterface] = None,
    ):
        if metadata is not None:
            cls.metadata_fmt = metadata
        if preprocessor_output is not None:
            cls.preprocessor_output_fmt = preprocessor_output
        if preprocessor_info is not None:
            cls.preprocessor_info_fmt = preprocessor_info
        if build_output is not None:
            cls.build_output_fmt = build_output
        if build_info is not None:
            cls.build_info_fmt = build_info
        if runtime_summary is not None:
            cls.runtime_summary_fmt = runtime_summary
        if test_case is not None:
            cls.test_case_fmt = test_case

    def get_assignment_text(self):
        return (
            f"{self.metadata_fmt.format(self.metadata)}"
            f"{self.preprocessor_info_fmt.format(self.preprocessor_info)}"
            f"{self.preprocessor_output_fmt.format(self.preprocessor_output)}"
            f"{self.build_info_fmt.format(self.build_info)}"
            f"{self.build_output_fmt.format(self.build_output)}"
            f"{self.runtime_summary_fmt.format(self.runtime_summary)}"
        )

    def get_score_multiplier(self):
        total_score = sum([test_case.get_weight() for test_case in self.test_cases])
        return 100.0 / total_score if total_score else 0.0

    def get_raw(self) -> AssignmentJSON:
        return AssignmentJSON(
            output=self.get_assignment_text(),
            visibility="visible",
            tests=[
                TestCaseJSON(
                    name=test_case.get_name(),
                    output=self.test_case_fmt.format(test_case),
                    score=self.get_score_multiplier()
                    * test_case.get_weight()
                    * test_case.get_successful(),
                    max_score=self.get_score_multiplier() * test_case.get_weight(),
                    execution_time=self.get_execution_time(),
                )
                for test_case in self.test_cases
            ],
            leaderboard=None,  # TODO: Add leaderboard support.
        )
