from typing import Sequence, Optional, List

from ..test import ComparisonTest
from ..common.validation import validate_common_size

def make_tests_from_files(
        *,  # kwargs-only; to avoid confusion with argument sequence.
        names: Sequence[str],
        inputs: Sequence[str],
        expected_outputs: Sequence[str],
        weights: Optional[Sequence[float]] = None # Defaults to equal-weight.
) -> List[ComparisonTest]:

    validate_common_size(
        names = names,
        inputs = inputs,
        expected_outputs = expected_outputs,
        weights = weights
    )

    if weights is None:
        weights = [1.0 for _ in names]

    generated_tests = []
    for name, input_, expected_output, weight in zip(names, inputs, expected_outputs, weights, strict=True):
        generated_tests.append(ComparisonTest(
            name = name,
            input = input_,
            expected_output = expected_output,
            weight = weight,
        ))

    return generated_tests