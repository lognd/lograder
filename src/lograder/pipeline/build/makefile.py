from typing import final, Generator

from lograder.common import Unreachable, Result
from lograder.process.registry.makefile import MakefileArgs, MakefileExecutable
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
    _executable: MakefileExecutable = MakefileExecutable()

    @property
    def executable(self) -> MakefileExecutable:
        return self._executable

    def __call__(
        self, input: MakefileManifest
    ) -> Generator[
        Result[MakefileBuildData, Unreachable],
        None,
        Result[list[Artifact], MakefileBuildError],
    ]:
        make_args = MakefileArgs(directory=input.root)
        make_output = self.executable(make_args)
        # TODO: Error handling for make output.
