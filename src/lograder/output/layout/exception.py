# noinspection PyPep8Naming
from colorama import Fore as F
from colorama import Style as S

from lograder.exception import DeveloperException, StaffException, UncaughtException
from lograder.output.layout.layout import Layout, register_layout


@register_layout("uncaught-exception")
class UncaughtExceptionLayout(Layout[UncaughtException]):
    @classmethod
    def to_ansi(cls, data: UncaughtException) -> str:
        output = []
        if isinstance(data.error, StaffException):
            output.append(
                f"The autograder met an error that was likely caused by a {S.BRIGHT}misconfiguration by your course staff.{S.RESET_ALL}"
            )
        elif isinstance(data.error, DeveloperException):
            output.append(
                f"The autograder met an error that was most likely caused by a {S.BRIGHT}bug in the autograder source code.{S.RESET_ALL} Consult your course staff (so that they may coordinate with the developer). {S.BRIGHT}Please open an issue at `https://github.com/lognd/lograder/issues`{S.RESET_ALL} including this output, describing the bug and what lead up to it. Thanks!"
            )
        else:
            output.append(
                f"The autograder met a fatal error (of type `{data.error_type}`) that {S.BRIGHT}wasn't anticipated in any capacity by the autograder source code or the course staff.{S.RESET_ALL} Consult your course staff (so that they may coordinate with the developer). {S.BRIGHT}Please open an issue at `https://github.com/lognd/lograder/issues` as soon as possible{S.RESET_ALL} including this output, describing the bug and what lead up to it. Thanks!"
            )
        emsg_fmt = data.error_msg.replace("\n", "\n    ")
        output.append(
            f"The following error was reached:{F.RED}\n    {emsg_fmt}{F.RESET}"
        )
        output.append(
            f"Here's the full traceback for the error:\n< {F.RED}BEGIN ERROR TRACEBACK{F.RESET} >{F.RED}"
        )
        output.append(data.error_traceback)
        output.append(f"{F.RESET}\n< {F.RED}END ERROR TRACEBACK{F.RESET} >")
        block_output = "\n".join(output)
        return (
            f"{S.BRIGHT}< {F.CYAN}ERROR WITH AUTOGRADER{F.RESET} >{S.RESET_ALL}\n"
            f"{block_output}"
        )

    @classmethod
    def to_simple(cls, data: UncaughtException) -> str:
        if isinstance(data.error, StaffException):
            cause = "staff misconfiguration"
        elif isinstance(data.error, DeveloperException):
            cause = "autograder bug"
        else:
            cause = f"unanticipated fatal error ({data.error_type})"

        return f"The graph met an error due to a {cause}; `{data.error_msg}`. Full traceback: {repr(data.error_traceback)}"
