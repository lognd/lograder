import shlex
from subprocess import CompletedProcess

from ...common.types import FilePath
from ...output.string.formatters.test_case import STDERRFormatter, STDOUTFormatter
from .._core_exceptions import LograderPreprocessorError, LograderCompilationError, LograderRuntimeError


class RequiredFileNotFoundError(LograderPreprocessorError):
    def __init__(self, path: FilePath):
        super().__init__(f"Could not find required file, `{str(path)}`.")


class GxxCompilationError(LograderCompilationError):
    def __init__(self, proc: CompletedProcess):
        super().__init__(
            "Autograder was unable to compile C++ project.\n"
            "Compilation command was the following: \n"
            f"    `{shlex.join(proc.args)}`\n"
            f"Compilation failed with exit code `{proc.returncode}`\n\n"
            "The following standard output was captured: \n"
            f"{STDOUTFormatter(proc.stdout).to_string()} \n"
            "The following standard error was captured: \n"
            f"{STDERRFormatter(proc.stderr).to_string()}"
        )

class CxxExecutableRuntimeError(LograderRuntimeError):
    def __init__(self, proc: CompletedProcess):
        super().__init__(
            "Autograder produced a valid executable but met an exception while running executable.\n"
            f"Process failed with exit code `{proc.returncode}`\n\n"
            "The following standard output was captured: \n"
            f"{STDOUTFormatter(proc.stdout).to_string()} \n"
            "The following standard error was captured: \n"
            f"{STDERRFormatter(proc.stderr).to_string()}"
        )

class CxxExecutableTimeoutError(LograderRuntimeError):
    def __init__(self):
        super().__init__(
            "Autograder produced a valid executable but execution timed out.\n"
            f"This is likely due to an infinite loop or an unexpected input (i.e. an extra std::cin read)."
        )
