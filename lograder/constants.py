import string
from pathlib import Path
import random

def random_name(length: int = 50) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

DEFAULT_SUBMISSION_PATH = Path('/autograder/submission')

DEFAULT_CXX_STANDARD = 'c++20'
DEFAULT_CXX_COMPILATION_FLAGS = ['-Wall', '-Wextra', '-Werror']

DEFAULT_EXECUTABLE_NAME = random_name()
DEFAULT_BUILD_DIRECTORY = 'build-'+random_name()
DEFAULT_BIN_DIRECTORY = 'bin-'+random_name()
DEFAULT_EXECUTION_TIMEOUT = 300