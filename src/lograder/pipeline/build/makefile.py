from typing import Generator, final

from lograder.common import Ok, Result, Unreachable
from lograder.process.registry.makefile import MakefileArgs, MakefileExecutable
from lograder.pipeline.build.build import Build, BuildOutput, make_build_output
from lograder.pipeline.check.project.simple_project import MakefileManifest
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.parsers.makefile import artifacts_from_makefile


@final
class MakefileBuild(
    Build[
        MakefileManifest,
        dict[str, Artifact],
        BuildOutput,
        BuildOutput,
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
        Result[BuildOutput, Unreachable],
        None,
        Result[dict[str, Artifact], BuildOutput],
    ]:
        makefile = input.root / "Makefile"

        make_args = MakefileArgs(directory=input.root)
        make_output = self.executable(make_args)
        make_info = make_build_output(make_output, input, makefile)

        if make_info.is_err:
            return make_info.swap_ok(dict[str, Artifact])
        yield make_info.swap_err(Unreachable)

        # Parse the Makefile to discover built artifacts
        source_files = input._files  # list[Path], absolute
        expected = artifacts_from_makefile(makefile, source_files)

        artifacts: dict[str, Artifact] = {}
        for name, path in expected.items():
            if path.is_file():
                artifacts[name] = FileArtifact(path=path)

        return Ok(artifacts)
