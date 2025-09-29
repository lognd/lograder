from datetime import datetime
from typing import Any, List, Mapping

from ..data.paths import PathConfig
from ..types import AssignmentMetadataOutput, FormatLabel
from .formatters.dispatcher import FormatDispatcher, FormatPackage
from .json.raw_gradescope import AssignmentJSON, TestCaseJSON
from .metadata import AssignmentMetadata
from .tests.interfaces.test import TestInterface


class SubmissionHandler:

    _outputs: List[FormatPackage] = []

    @classmethod
    def add_output(cls, label: FormatLabel, data: Mapping[str, Any]):
        cls._outputs.append(FormatPackage(label=label, data=data))

    @classmethod
    def make_submission(
        cls,
        assignment_name: str,
        assignment_authors: List[str],
        assignment_description: str,
        assignment_due_date: datetime,
    ) -> AssignmentJSON:
        tests = cls.run_tests()

        metadata: AssignmentMetadata = AssignmentMetadata(
            assignment_name=assignment_name,
            assignment_authors=assignment_authors,
            assignment_description=assignment_description,
            assignment_due_date=assignment_due_date,
        )
        packed_metadata: AssignmentMetadataOutput = {"metadata": metadata}
        if not cls._outputs or cls._outputs[0].label != "assignment-metadata":
            cls._outputs.insert(
                0, FormatPackage(label="assignment-metadata", data=packed_metadata)
            )
        build_output: list[str] = [
            FormatDispatcher.format(output) for output in cls._outputs
        ]

        assignment = AssignmentJSON(
            output="\n".join(build_output), tests=tests
        )

        with open(PathConfig.DEFAULT_RESULT_PATH, "w", encoding="utf-8") as f:
            f.write(assignment.model_dump_json(indent=2))

        return assignment

    @classmethod
    def clear(cls):
        cls._outputs.clear()
        TestInterface.clear()

    @classmethod
    def run_tests(cls) -> List[TestCaseJSON]:
        return [t.run() for t in TestInterface.get_tests()]
