import shutil
from pathlib import Path

from lograder.common import Ok, Unreachable
from lograder.pipeline.build.build import make_build_output
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.check.project.simple_project import CMakeManifest
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.executable import ExecutableOptions
from lograder.process.parsers.cmake import cmake_artifacts_from_file_api
from lograder.process.registry.cmake import CMakeBuildArgs, CMakeConfigureArgs

PROJECTS = Path(__file__).parent / "projects"


class FixedDirCMakeBuild(CMakeBuild):
    """CMakeBuild with an explicit build directory for use in tests.

    The default CMakeBuild uses ``Path("build")`` relative to the process cwd,
    which is captured at import time.  This subclass accepts an explicit
    ``build_dir`` so cmake artifacts land inside ``tmp_path`` per test.
    """

    def __init__(self, build_dir: Path) -> None:
        self._fixed_build_dir = build_dir

    def __call__(self, input: CMakeManifest):  # type: ignore[override]
        cmake_file = input.root / "CMakeLists.txt"
        build_dir = self._fixed_build_dir
        build_dir.mkdir(parents=True, exist_ok=True)

        opts = ExecutableOptions(cwd=build_dir)

        conf_args = CMakeConfigureArgs(source_dir=input.root, build_dir=build_dir)
        conf_output = self.executable(conf_args, options=opts)
        cmake_info = make_build_output(conf_output, input, cmake_file)

        if cmake_info.is_err:
            return cmake_info.swap_ok(dict[str, Artifact])
        yield cmake_info.swap_err(Unreachable)

        build_args = CMakeBuildArgs(build_dir=build_dir)
        build_output = self.executable(build_args, options=opts)
        cmake_info = make_build_output(build_output, input, cmake_file)

        if cmake_info.is_err:
            return cmake_info.swap_ok(dict[str, Artifact])
        yield cmake_info.swap_err(Unreachable)

        artifact_map: dict[str, Artifact] = {}
        for artifact in cmake_artifacts_from_file_api(build_dir):
            existing = artifact_map.get(artifact.name)
            if existing is None or (
                isinstance(artifact, FileArtifact)
                and not isinstance(existing, FileArtifact)
            ):
                artifact_map[artifact.name] = artifact
        return Ok(artifact_map)


def copy_submission(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def copy_staff(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
