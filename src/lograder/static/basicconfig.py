from pathlib import Path
from typing import List

class LograderBasicConfig:
    DEFAULT_SUBMISSION_PATH: Path = Path("/autograder/submission")
    DEFAULT_RESULT_PATH: Path = Path('/autograder/results/results.json')
    DEFAULT_CXX_STANDARD: str = "c++20"
    DEFAULT_CXX_COMPILATION_FLAGS: List[str] = ["-Wall", "-Wextra", "-Werror"]
    DEFAULT_EXECUTABLE_TIMEOUT: float = 300.0  # In seconds.

    DEFAULT_TOPIC_BREAK: str = "\n\n"

    @classmethod
    def set(cls, key: str, value: str):
        if hasattr(cls, key):
            setattr(cls, key, value)
