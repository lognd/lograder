from typing import final, Generator

from lograder.common import Unreachable, Result
from lograder.pipeline.build.build import Build, BuildData, BuildError
from lograder.pipeline.check.project.simple_project import CMakeManifest
from lograder.pipeline.types.artifacts import Artifact


class CMakeBuildError(BuildError): ...


class CMakeBuildData(BuildData): ...


@final
class CMakeBuild(
    Build[CMakeManifest, list[Artifact], CMakeBuildError, CMakeBuildData, Unreachable]
):
    def __call__(
        self, input: CMakeManifest
    ) -> Generator[
        Result[list[Artifact], CMakeBuildError],
        None,
        Result[CMakeBuildData, Unreachable],
    ]:
        pass
