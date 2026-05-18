from typing import final, Generator
from pathlib import Path


from lograder.common import Unreachable, Result, Ok, Err
from lograder.process.registry.makefile import MakefileArgs, MakefileExecutable
from lograder.pipeline.build.build import Build, BuildOutput, make_build_output
from lograder.pipeline.check.project.simple_project import MakefileManifest
from lograder.pipeline.types.artifacts import Artifact


@final
class MakefileBuild(
    Build[
        MakefileManifest,
        list[Artifact],
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
        Result[list[Artifact], BuildOutput],
    ]:
        makefile = Path(
            input.root / "Makefile"
        )  # This must exist because of MakefileManifest check.

        make_args = MakefileArgs(directory=input.root)
        make_output = self.executable(make_args)
        make_info = make_build_output(make_output, input, makefile)

        if make_info.is_err:
            return make_info.swap_ok(list[Artifact])
        yield make_info.swap_err(Unreachable)

        # TODO: create Makefile parsing.
        return Ok([])
