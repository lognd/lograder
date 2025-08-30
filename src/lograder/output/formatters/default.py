import shlex
from datetime import timedelta
from os import PathLike
from typing import List

from colorama import Fore

from ...builder.common.types import (
    AssignmentMetadata,
    BuilderOutput,
    PreprocessorOutput,
)
from .format_templates import ContextRenderer, ProcessStep
from .interfaces import (
    BuildOutputFormatterInterface,
    MetadataFormatterInterface,
    PreprocessorOutputFormatterInterface,
)


def format_timedelta(td: timedelta) -> str:
    if td < timedelta(0):
        return "0s"
    total_seconds = int(td.total_seconds())
    milliseconds = int(td.microseconds / 1000)

    weeks, remainder = divmod(total_seconds, 7 * 24 * 3600)
    days, remainder = divmod(remainder, 24 * 3600)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if weeks:
        parts.append(f"{weeks}w")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    if milliseconds:
        parts.append(f"{milliseconds}ms")

    return " ".join(parts) if parts else "0s"


class CLIStep(ProcessStep):
    def __init__(self, command: List[str | bytes | PathLike]):
        self.command = shlex.join(command)

    def render(self):
        return f"Ran `{self.command}` in CLI."


class DefaultMetadataFormatter(MetadataFormatterInterface):
    def format(self, assignment_metadata: AssignmentMetadata):
        return (
            f"`{Fore.MAGENTA}{assignment_metadata.assignment_name}{Fore.RESET}` made by {Fore.MAGENTA}{f'{Fore.RESET}, {Fore.MAGENTA}'.join(assignment_metadata.assignment_authors)}{Fore.RESET}.\n"
            f"Received submission at {Fore.MAGENTA}{assignment_metadata.assignment_submit_date.strftime("%Y-%m-%d %H:%M:%S.%f")}{Fore.RESET}.\n"
            f"Assignment is due at {Fore.MAGENTA}{assignment_metadata.assignment_due_date.strftime("%Y-%m-%d %H:%M:%S.%f")}{Fore.RESET}.\n"
            f"Time left for further submissions {Fore.MAGENTA}{format_timedelta(assignment_metadata.assignment_due_date - assignment_metadata.assignment_submit_date)}{Fore.RESET}.\n\n"
            f"Assignment graded with `{Fore.GREEN}{assignment_metadata.library_name}{Fore.RESET}` (version {Fore.GREEN}{assignment_metadata.library_version}{Fore.RESET}), made by {Fore.GREEN}{f'{Fore.RESET}, {Fore.GREEN}'.join(assignment_metadata.library_authors)}.{Fore.RESET}\n\n"
        )


class DefaultPreprocessorContext(
    ContextRenderer,
    prefix=f"<{Fore.CYAN}BEGIN PREPROCESSOR{Fore.RESET}>\n",
    suffix=f"\n<{Fore.CYAN}END PREPROCESSOR{Fore.RESET}>",
    empty=f"<{Fore.CYAN}NO PREPROCESSOR PRESENT{Fore.CYAN}>",
):
    pass


class DefaultBuilderContext(
    ContextRenderer,
    prefix=f"<{Fore.YELLOW}BEGIN BUILDER{Fore.RESET}>\n",
    suffix=f"\n<{Fore.YELLOW}END BUILDER{Fore.RESET}>",
    empty=f"<{Fore.YELLOW}NO BUILDER PRESENT{Fore.CYAN}>",
):
    pass


class DefaultSTDOUTContext(
    ContextRenderer,
    prefix=f"<{Fore.BLUE}BEGIN STDOUT{Fore.RESET}>\n",
    suffix=f"\n<{Fore.BLUE}END STDOUT{Fore.RESET}>",
    empty=f"<{Fore.BLUE}EMPTY STDOUT{Fore.CYAN}>",
):
    pass


class DefaultSTDERRContext(
    ContextRenderer,
    prefix=f"<{Fore.RED}BEGIN STDERR{Fore.RESET}>\n",
    suffix=f"\n<{Fore.RED}END STDERR{Fore.RESET}>",
    empty=f"<{Fore.RED}EMPTY STDERR{Fore.CYAN}>",
):
    pass


class DefaultPreprocessorOutputFormatter(PreprocessorOutputFormatterInterface):
    def format(self, preprocessor_output: PreprocessorOutput) -> str:
        output = [
            (
                f"{CLIStep(command).render()}\n"
                f"{DefaultSTDOUTContext(cout).render()}\n"
                f"{DefaultSTDERRContext(cerr).render()}\n"
            )
            for command, cout, cerr in zip(
                preprocessor_output.commands,
                preprocessor_output.stdout,
                preprocessor_output.stderr,
            )
        ]
        return DefaultPreprocessorContext("\n\n".join(output)).render()


class DefaultBuildOutputFormatter(BuildOutputFormatterInterface):
    def format(self, build_output: BuilderOutput) -> str:
        output = [f"Detected build types of `{build_output.build_type}`.\n\n"]
        output += [
            (
                f"{CLIStep(command).render()}\n"
                f"{DefaultSTDOUTContext(cout).render()}\n"
                f"{DefaultSTDERRContext(cerr).render()}\n"
            )
            for command, cout, cerr in zip(
                build_output.commands, build_output.stdout, build_output.stderr
            )
        ]
        return DefaultBuilderContext("\n\n".join(output)).render()
