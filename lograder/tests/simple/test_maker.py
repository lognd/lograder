from typing import Sequence, Optional

def make_tests_from_files(
        *,  # kwargs-only; to avoid confusion with argument sequence.
        names: Sequence[str],
        inputs: Sequence[str],
        expected_outputs: Sequence[str],
        weights: Optional[Sequence[float]] = None # Defaults to equal-weight.
):
    # TODO: Write implementation of `make_tests_from_files` function.
    ...