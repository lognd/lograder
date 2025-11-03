import random
import string
import sys
from pathlib import Path

from .data.paths import PathConfig


def random_name(length: int = 20) -> str:
    return "".join(
        random.choices(
            string.ascii_lowercase + string.ascii_uppercase + string.digits, k=length
        )
    )


def random_working_directory(path_config: PathConfig = PathConfig()) -> Path:
    directory = path_config.root / random_name()
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def random_executable() -> str:
    return random_name() + ".exe" if sys.platform.startswith("win") else random_name()
