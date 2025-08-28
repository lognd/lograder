from typing import Sequence, Optional
from pathlib import Path

from ..common import FilePath

def make_tests_from_files(
        *,  # kwargs-only; to avoid confusion with argument sequence.
        names: Sequence[str],
        inputs: Sequence[FilePath],
        expected_outputs: Sequence[FilePath],
        weights: Optional[Sequence[float]] = None # Defaults to equal-weight.
) -> None:
    # TODO: Make `make_tests_from_file` implementation
    ...
