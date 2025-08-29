from pathlib import Path
from typing import Sequence

from ...common.types import FilePath
from .exceptions import RequiredFileNotFoundError


def validate_paths(paths: Sequence[FilePath]) -> None:
    for path in paths:
        if not Path(path).exists():
            raise RequiredFileNotFoundError(path)
