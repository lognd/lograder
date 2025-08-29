import random
import string
from pathlib import Path
from typing import List


def random_name(length: int = 50) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


DEFAULT_SUBMISSION_PATH: Path = Path("/autograder/submission")

DEFAULT_CXX_STANDARD: str = "c++20"
DEFAULT_CXX_COMPILATION_FLAGS: List[str] = ["-Wall", "-Wextra", "-Werror"]

DEFAULT_BUILD_DIRECTORY: str = "build-" + random_name()
DEFAULT_BIN_DIRECTORY: str = "bin-" + random_name()

DEFAULT_EXECUTABLE_NAME: str = random_name()
DEFAULT_EXECUTION_TIMEOUT: float = 300
DEFAULT_EXECUTION_FLAGS: List[str] = []
