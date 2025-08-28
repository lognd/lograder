from subprocess import CompletedProcess
import shlex
from colorama import Fore
from ._core_exceptions import LograderTestError

__all__ = [
    "LograderTestError",
    "LograderCompilationError",
    "LograderRuntimeError",
    "LograderTimeoutError",
    "LograderAmbiguousTargetError",
    "LograderNoTargetsError",
]

class LograderCompilationError(LograderTestError):
    def __init__(self, proc: CompletedProcess):
        super().__init__(
            "Autograder was unable to compile C++ project.\n"
            "Compilation command was the following: \n"
            f"    `{shlex.join(proc.args)}`\n"
            f"Compilation failed with exit code `{proc.returncode}`\n\n"
            "The following standard output was captured: \n"
            "<BEGIN STDOUT>\n"
            f"{proc.stdout}\n"
            "<END STDOUT>\n\n"
            "The following standard error was captured: \n"
            "<BEGIN STDERR>\n"
            f"{Fore.RED}{proc.stderr}{Fore.RESET}\n"
            "<END STDERR>"
        )

class LograderAmbiguousTargetError(LograderTestError):
    def __init__(self, targets: list[str]):
        super().__init__(
            "Autograder was able to find `CMakeLists.txt` and was able to run `cmake`, but too many\n"
            "targets were found. Only one non-default target was expected, but received:\n"
            f'''    "{'", "'.join(targets)}"\n'''
            "Please remove/comment out all targets except one, so the autograder can run."
        )

class LograderNoTargetsError(LograderTestError):
    def __init__(self):
        super().__init__(
            "Autograder was able to find `CMakeLists.txt` and was able to run `cmake`, but couldn't find\n"
            "a valid target to build. No non-default target was specified.\n"
            "Please add a target with a different name than all the default ones, so the autograder can run."
        )

class LograderRuntimeError(LograderTestError):
    def __init__(self, proc: CompletedProcess):
        super().__init__(
            "Autograder produced a valid executable but met an exception while running executable.\n"
            f"Process failed with exit code `{proc.returncode}`\n\n"
            "The following standard output was captured: \n"
            "<BEGIN STDOUT>\n"
            f"{proc.stdout}\n"
            "<END STDOUT>\n\n"
            "The following standard error was captured: \n"
            "<BEGIN STDERR>\n"
            f"{Fore.RED}{proc.stderr}{Fore.RESET}\n"
            "<END STDERR>"
        )

class LograderTimeoutError(LograderTestError):
    def __init__(self):
        super().__init__(
            "Autograder produced a valid executable but execution timed out.\n"
            f"This is likely due to an infinite loop or an unexpected input (i.e. an extra std::cin read)."
        )
