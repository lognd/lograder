from ...common.types import PreprocessorOutput, ProjectType
from ..interface import (
    BuilderInterface,
    BuilderOutput,
    BuildResults,
    PreprocessorInterface,
    PreprocessorResults,
)


class TrivialPreprocessor(PreprocessorInterface):
    def validate(self):
        return True

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            output=PreprocessorOutput(commands=[], stdout=[], stderr=[])
        )


class TrivialBuilder(BuilderInterface):
    def __init__(self, project_type: ProjectType):
        super().__init__()
        self._project_type = project_type

    def build(self) -> BuildResults:
        return BuildResults(
            output=BuilderOutput(
                commands=[],
                stdout=[],
                stderr=[],
                project_type=self._project_type,
            )
        )
