from .._core_exceptions import LograderPreprocessorError
from ...common.types import FilePath

class RequiredFileNotFoundError(LograderPreprocessorError):
    def __init__(self, path: FilePath):
        super().__init__(f"Could not find required file, `{str(path)}`.")