from pathlib import Path
from typing import List

from .._core_exceptions import LograderStudentBuildError


class CxxSourceBuildError(LograderStudentBuildError):
    def __init__(self, sources: List[Path]):
        super().__init__(
            f"Was unable to compile C++ sources; found source files: {', '.join([str(path.resolve()) for path in sources])}."
        )


class CMakeListsNotFoundError(LograderStudentBuildError):
    def __init__(self):
        super().__init__("Could not find a `CMakeLists.txt` anywhere in the project.")


class CMakeTargetNotFoundError(LograderStudentBuildError):
    def __init__(self, targets: List[str], cmake_path: Path):
        super().__init__(
            f"Could not find a valid cmake target anywhere in `{cmake_path.resolve()}`. The targets found were: [{', '.join(targets)}]."
        )


class CMakeExecutableNotFoundError(LograderStudentBuildError):
    def __init__(self, cmake_path: Path):
        super().__init__(
            f"Could not find a valid cmake executable output path anywhere in `{cmake_path.resolve()}`."
        )


class MakefileNotFoundError(LograderStudentBuildError):
    def __init__(self):
        super().__init__("Could not find a `Makefile` anywhere in the project.")


class MakefileRunNotFoundError(LograderStudentBuildError):
    def __init__(self, makefile_path: Path):
        super().__init__(
            f"Could not find an `run` entrypoint in `{makefile_path.resolve()}` (i.e. the command `make run ARGS=<test-args>` is used to run the project)."
        )
