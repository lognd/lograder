from typing import final, Generator

from lograder.common import Unreachable, Result
from lograder.process.registry.cmake import (
    CMakeConfigureArgs,
    CMakeBuildArgs,
    CMakeInstallArgs,
    CMakeExecutable,
)
from lograder.pipeline.build.build import Build, BuildData, BuildError
from lograder.pipeline.check.project.simple_project import CMakeManifest
from lograder.pipeline.types.artifacts import Artifact


class CMakeBuildError(BuildError): ...


class CMakeBuildData(BuildData): ...


@final
class CMakeBuild(
    Build[CMakeManifest, list[Artifact], CMakeBuildError, CMakeBuildData, Unreachable]
):
    _executable: CMakeExecutable = CMakeExecutable()

    @property
    def executable(self) -> CMakeExecutable:
        return self._executable

    def __call__(
        self, input: CMakeManifest
    ) -> Generator[
        Result[CMakeBuildData, Unreachable],
        None,
        Result[list[Artifact], CMakeBuildError],
    ]:
        conf_args = CMakeConfigureArgs(source_dir=input.root)
        conf_output = self.executable(conf_args)
        # TODO: Error handling for configuration output.
        build_args = CMakeBuildArgs()
        build_output = self.executable(build_args)
        # TODO: Error handling for build output.
