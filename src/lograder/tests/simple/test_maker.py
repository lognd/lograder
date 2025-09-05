from typing import List, Optional, Sequence

from ..common.validation import validate_common_size
from ..registry.registry import TestRegistry
from ..test.comparison_test import ExecutableOutputComparisonTest


def make_tests_from_strs(
    *,  # kwargs-only; to avoid confusion with argument sequence.
    names: Sequence[str],
    inputs: Sequence[str],
    expected_outputs: Sequence[str],
    flag_sets: Optional[Sequence[List[str]]] = None,
    weights: Optional[Sequence[float]] = None,  # Defaults to equal-weight.
) -> List[ExecutableOutputComparisonTest]:

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

    generated_tests = []
    for name, input_, expected_output, weight, flags in zip(
        names, inputs, expected_outputs, weights, flag_sets, strict=True
    ):
        generated_tests.append(
            ExecutableOutputComparisonTest(
                name=name,
                input=input_,
                expected_output=expected_output,
                weight=weight,
                flags=flags,
            )
        )
    TestRegistry.extend(generated_tests)

    return generated_tests
