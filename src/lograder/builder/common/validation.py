from typing import Sequence
from pathlib import Path

from .exceptions import RequiredFileNotFoundError
from ...common.types import FilePath

def validate_paths(paths: Sequence[FilePath]) -> None:
    for path in paths:
        if not Path(path).exists():
            raise RequiredFileNotFoundError(path)
