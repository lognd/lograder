import random
import string
from pathlib import Path

from .data.paths import PathConfig


def random_name(length: int = 20) -> str:
    return "".join(
        random.choices(
            string.ascii_lowercase + string.ascii_uppercase + string.digits, k=length
        )
    )


def random_working_directory() -> Path:
    directory = PathConfig.DEFAULT_ROOT_PATH / random_name()
    directory.mkdir(parents=True, exist_ok=False)
    return directory
