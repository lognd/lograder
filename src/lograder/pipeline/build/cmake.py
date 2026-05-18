from typing import final, Generator

from lograder.common import Unreachable, Result, Ok, Err
from lograder.process.registry.cmake import (
    CMakeConfigureArgs,
    CMakeBuildArgs,
    CMakeInstallArgs,
    CMakeExecutable,
)
from lograder.pipeline.build.build import Build, BuildOutput, make_build_output
from lograder.pipeline.check.project.simple_project import CMakeManifest
from lograder.pipeline.types.artifacts import Artifact


@final
class CMakeBuild(
    Build[CMakeManifest, list[Artifact], BuildOutput, BuildOutput, Unreachable]
):
    _executable: CMakeExecutable = CMakeExecutable()

    @property
    def executable(self) -> CMakeExecutable:
        return self._executable

    def __call__(
        self, input: CMakeManifest
    ) -> Generator[
        Result[BuildOutput, Unreachable],
        None,
        Result[list[Artifact], BuildOutput],
    ]:
        cmake_file = (
            input.root / "CMakeLists.txt"
        )  # Guaranteed to exist from CMakeManifest
        conf_args = CMakeConfigureArgs(source_dir=input.root)

        conf_output = self.executable(conf_args)
        cmake_info = make_build_output(conf_output, input, cmake_file)

        if cmake_info.is_err:
            return cmake_info.swap_ok(list[Artifact])
        yield cmake_info.swap_err(Unreachable)

        build_args = CMakeBuildArgs()
        build_output = self.executable(build_args)
        cmake_info = make_build_output(build_output, input, cmake_file)

        if cmake_info.is_err:
            return cmake_info.swap_ok(list[Artifact])
        yield cmake_info.swap_err(Unreachable)

        # TODO: create CMake parsing.
        return Ok([])
