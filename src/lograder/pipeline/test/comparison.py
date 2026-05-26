from typing import Generator, Sequence
from typing_extensions import Self

from lograder.exception import StaffException
from lograder.common import Unreachable, Result, Ok, Err
from lograder.pipeline.types.artifacts import Artifact
from lograder.pipeline.test.test import TestFailure, TestSuccess, Test
from lograder.process.executable import ExecutableInput, ExecutableOptions, ExecutableOutput, resolve_invocation

class OutputComparisonTest(Test[dict[str, Artifact], dict[str, Artifact], Unreachable, TestSuccess, TestFailure]):
    __test__: bool = False

    def __init__(self, artifact_name: str,
                 inputs: Sequence[ExecutableInput] | ExecutableInput = ExecutableInput(),
                 options: Sequence[ExecutableOptions] | ExecutableOptions = ExecutableOptions()) -> None:
        self._artifact_name = artifact_name

        if isinstance(inputs, ExecutableInput):
            _inputs: list[ExecutableInput] = [inputs]
        else:
            _inputs = list(inputs)

        if isinstance(options, ExecutableOptions):
            _options: list[ExecutableOptions] = [options]
        else:
            _options = list(options)

        if len(_inputs) == 1:
            _inputs = _inputs * len(_options)
        if len(_options) == 1:
            _options = _options * len(_inputs)

        if len(_inputs) != len(_options):
            raise StaffException(
                f"`OutputComparisonTest` must receive an equal number of `ExecutableInput`' "
                f"(received `{len(_inputs)}`) and `ExecutableOptions`'s (received `{len(_options)}`)."
            )

        self._invocations = [
            resolve_invocation()
        ]

    @classmethod
    def from_file(cls) -> Self:
        pass

    @classmethod
    def from_iter(cls) -> Self:
        pass

    def __call__(self, input: dict[str, Artifact]) -> Generator[
        Result[TestSuccess, TestFailure],
        None,
        Result[dict[str, Artifact], Unreachable],
    ]:
        yield from ()
        return Ok(input)