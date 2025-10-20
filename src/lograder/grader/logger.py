from typing import Optional

class Logger:
    """
    Central place to store all the logging capabilities for `lograder`.
    """
    @classmethod
    def log_function_error(cls, gen_obj: object, exc: Exception, traceback: Optional[str] = None):
        print(f"[{gen_obj.__class__.__name__}] `{exc.__class__.__name__}` occurred: {exc}")
        if traceback is not None:
            print(traceback)

    @classmethod
    def log_subprocess_error(cls, gen_obj: object, return_code: int, stdout: str, stderr: str):
        print(f"[{gen_obj.__class__.__name__}] Subprocess exited with nonzero exit code ({return_code}), producing the following STDOUT and STDERR: \n{stdout}\n{stderr}.")

    @classmethod
    def log_subprocess_timeout(cls, gen_obj: object, timeout: float, stdout: str, stderr: str):
        print(f"[{gen_obj.__class__.__name__}] Subprocess timed out after {timeout}s, producing the following partial STDOUT and STDERR: \n{stdout}\n{stderr}.")
