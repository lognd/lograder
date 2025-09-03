from ...common.types import ProjectType, PreprocessorOutput
from ..interface import ExecutableBuildResults, BuildResults, PreprocessorInterface, BuilderInterface, BuilderOutput, \
    PreprocessorResults


class TrivialPreprocessor(PreprocessorInterface):
    def validate(self):
        return True

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            output=PreprocessorOutput(
                commands = [],
                stdout = [],
                stderr = []
            )
        )

class TrivialBuilder(BuilderInterface):
    def __init__(self, project_type: ProjectType):
        super().__init__()
        self._project_type = project_type

    def build(self) -> BuildResults:
        return BuildResults(
            output=BuilderOutput(
                commands = [],
                stdout = [],
                stderr = [],
                project_type = self._project_type,
            )
        )