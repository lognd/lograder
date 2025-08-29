from typing import List, Optional, Sequence

from ..common.validation import validate_common_size
from ..registry import TestRegistry
from ..test import ComparisonTest


def make_tests_from_strs(
    *,  # kwargs-only; to avoid confusion with argument sequence.
    names: Sequence[str],
    inputs: Sequence[str],
    expected_outputs: Sequence[str],
    weights: Optional[Sequence[float]] = None,  # Defaults to equal-weight.
) -> List[ComparisonTest]:

    if weights is None:
        weights = [1.0 for _ in names]

    validate_common_size(
        names=names, inputs=inputs, expected_outputs=expected_outputs, weights=weights
    )

    generated_tests = []
    for name, input_, expected_output, weight in zip(
        names, inputs, expected_outputs, weights, strict=True
    ):
        generated_tests.append(
            ComparisonTest(
                name=name,
                input=input_,
                expected_output=expected_output,
                weight=weight,
            )
        )
    TestRegistry.extend(generated_tests)

    return generated_tests
