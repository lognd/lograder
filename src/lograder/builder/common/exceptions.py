from ...common.types import FilePath
from .._core_exceptions import LograderPreprocessorError


class RequiredFileNotFoundError(LograderPreprocessorError):
    def __init__(self, path: FilePath):
        super().__init__(f"Could not find required file, `{str(path)}`.")
