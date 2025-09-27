from typing import TYPE_CHECKING, List, Optional, Sequence

from .output_tests import CLIOutputTest
from .validation import validate_common_size

if TYPE_CHECKING:
    from ...builders.interfaces.builder import BuilderInterface


def make_tests_from_strs(
    *,  # kwargs-only; to avoid confusion with argument sequence.
    builder: BuilderInterface,
    names: Sequence[str],
    inputs: Sequence[str],
    expected_outputs: Sequence[str],
    flag_sets: Optional[Sequence[Sequence[str]]] = None,
    weights: Optional[Sequence[float]] = None,  # Defaults to equal-weight.
) -> List[CLIOutputTest]:

    if weights is None:
        weights = [1.0 for _ in names]

    if flag_sets is None:
        flag_sets = [[] for _ in names]

    validate_common_size(
        names=names,
        inputs=inputs,
        expected_outputs=expected_outputs,
        weights=weights,
        flags=flag_sets,
    )

    generated_tests: List[CLIOutputTest] = []
    for name, input_, expected_output, weight, flags in zip(
        names, inputs, expected_outputs, weights, flag_sets, strict=True
    ):
        generated_tests.append(
            CLIOutputTest.make(
                name=name,
                builder=builder,
                stdin=input_,
                weight=weight,
                expected_stdout=expected_output,
                args=list(flags),
                working_dir=builder.get_working_directory(),
                wrap_args=builder.wrap_args(),
            )
        )
    return generated_tests
