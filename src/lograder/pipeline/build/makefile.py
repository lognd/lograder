from typing import final, Generator

from lograder.common import Unreachable, Result
from lograder.pipeline.build.build import Build, BuildData, BuildError
from lograder.pipeline.check.project.simple_project import MakefileManifest
from lograder.pipeline.types.artifacts import Artifact


class MakefileBuildError(BuildError): ...


class MakefileBuildData(BuildData): ...


@final
class MakefileBuild(
    Build[
        MakefileManifest,
        list[Artifact],
        MakefileBuildError,
        MakefileBuildData,
        Unreachable,
    ]
):
    def __call__(
        self, input: MakefileManifest
    ) -> Generator[
        Result[list[Artifact], MakefileBuildError],
        None,
        Result[MakefileBuildData, Unreachable],
    ]:
        pass
