import shlex
from datetime import timedelta
from os import PathLike
from typing import Optional, Sequence, Union

from colorama import Fore

from ...builder.common.types import (
    AssignmentMetadata,
    BuilderOutput,
    PreprocessorOutput,
)
from ...constants import Constants
from ...tests.test import TestInterface
from ...tests.test.analytics import (
    CallgrindSummary,
    ExecutionTimeSummary,
    ValgrindLeakSummary,
    ValgrindWarningSummary,
)
from .format_templates import ContextRenderer, ProcessStep
from .interfaces import (
    BuildOutputFormatterInterface,
    ExecutionTimeSummaryFormatterInterface,
    MetadataFormatterInterface,
    PreprocessorOutputFormatterInterface,
    RuntimeSummaryFormatterInterface,
    TestCaseFormatterInterface,
    ValgrindLeakSummaryFormatterInterface,
    ValgrindWarningSummaryFormatterInterface,
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
    def __init__(self, command: Sequence[Union[str, bytes, PathLike]]):
        self.command = shlex.join([str(comm) for comm in command])

    def render(self):
        return f"Ran `{Fore.MAGENTA}{self.command}{Fore.RESET}` in CLI."


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
    empty=f"<{Fore.CYAN}NO PREPROCESSOR PRESENT{Fore.RESET}>",
):
    pass


class DefaultBuilderContext(
    ContextRenderer,
    prefix=f"<{Fore.YELLOW}BEGIN BUILDER{Fore.RESET}>\n",
    suffix=f"\n<{Fore.YELLOW}END BUILDER{Fore.RESET}>",
    empty=f"<{Fore.YELLOW}NO BUILDER PRESENT{Fore.RESET}>",
):
    pass


class DefaultSTDOUTContext(
    ContextRenderer,
    prefix=f"<{Fore.BLUE}BEGIN STDOUT{Fore.RESET}>\n",
    suffix=f"\n<{Fore.BLUE}END STDOUT{Fore.RESET}>",
    empty=f"<{Fore.BLUE}EMPTY STDOUT{Fore.RESET}>",
):
    pass


class DefaultExpectedSTDOUTContext(
    ContextRenderer,
    prefix=f"<{Fore.BLUE}BEGIN EXPECTED STDOUT{Fore.RESET}>\n",
    suffix=f"\n<{Fore.BLUE}END EXPECTED STDOUT{Fore.RESET}>",
    empty=f"<{Fore.BLUE}EMPTY EXPECTED STDOUT{Fore.RESET}>",
):
    pass


class DefaultActualSTDOUTContext(
    ContextRenderer,
    prefix=f"<{Fore.BLUE}BEGIN ACTUAL STDOUT{Fore.RESET}>\n",
    suffix=f"\n<{Fore.BLUE}END ACTUAL STDOUT{Fore.RESET}>",
    empty=f"<{Fore.BLUE}EMPTY ACTUAL STDOUT{Fore.RESET}>",
):
    pass


class DefaultSTDERRContext(
    ContextRenderer,
    prefix=f"<{Fore.RED}BEGIN STDERR{Fore.RESET}>\n",
    suffix=f"\n<{Fore.RED}END STDERR{Fore.RESET}>",
    empty=f"<{Fore.RED}EMPTY STDERR{Fore.RESET}>",
):
    pass


class DefaultSTDINContext(
    ContextRenderer,
    prefix=f"<{Fore.LIGHTBLUE_EX}BEGIN STDIN{Fore.RESET}>\n",
    suffix=f"\n<{Fore.LIGHTBLUE_EX}END STDIN{Fore.RESET}>",
    empty=f"<{Fore.LIGHTBLUE_EX}EMPTY STDIN{Fore.RESET}>",
):
    pass


class DefaultValgrindLeakSummaryFormatter(ValgrindLeakSummaryFormatterInterface):
    def format(self, leak_summary: Optional[ValgrindLeakSummary]) -> str:
        if leak_summary is None:
            return f"<{Fore.YELLOW}VALGRIND LEAK SUMMARY DISABLED{Fore.RESET}>"
        def_lost_color = "" if leak_summary.definitely_lost.is_safe else Fore.RED
        ind_lost_color = "" if leak_summary.indirectly_lost.is_safe else Fore.RED
        pos_lost_color = "" if leak_summary.possibly_lost.is_safe else Fore.RED
        return (
            f"{Fore.LIGHTGREEN_EX}VALGRIND LEAK SUMMARY{Fore.RESET}:\n"
            f"* {def_lost_color}{leak_summary.definitely_lost.bytes}{Fore.RESET} bytes, {def_lost_color}{leak_summary.definitely_lost.blocks}{Fore.RESET} blocks {def_lost_color}definitely lost{Fore.RESET}.\n"
            f"* {ind_lost_color}{leak_summary.indirectly_lost.bytes}{Fore.RESET} bytes, {ind_lost_color}{leak_summary.indirectly_lost.blocks}{Fore.RESET} blocks {ind_lost_color}indirectly lost{Fore.RESET}.\n"
            f"* {pos_lost_color}{leak_summary.possibly_lost.bytes}{Fore.RESET} bytes, {pos_lost_color}{leak_summary.possibly_lost.blocks}{Fore.RESET} blocks {pos_lost_color}possibly lost{Fore.RESET}.\n"
            f"* {leak_summary.still_reachable.bytes} bytes, {leak_summary.still_reachable.blocks} blocks still reachable."
        )


class DefaultValgrindWarningSummaryFormatter(ValgrindWarningSummaryFormatterInterface):
    def format(self, warning_summary: Optional[ValgrindWarningSummary]) -> str:
        if warning_summary is None:
            return f"<{Fore.YELLOW}VALGRIND WARNING SUMMARY DISABLED{Fore.RESET}>"
        warning = warning_summary.model_dump()
        output = [f"{Fore.LIGHTGREEN_EX}VALGRIND WARNING SUMMARY{Fore.RESET}:"]
        output += [
            f"* {v} `{k.replace('_', ' ').upper()}` warnings encountered."
            for k, v in warning.items()
        ]
        return "\n".join(output)


class DefaultExecutionTimeSummaryFormatter(ExecutionTimeSummaryFormatterInterface):
    def format(
        self,
        callgrind_summary: Optional[Sequence[CallgrindSummary]],
        execution_time_summary: Optional[ExecutionTimeSummary],
    ) -> str:
        if callgrind_summary is None or execution_time_summary is None:
            return f"<{Fore.YELLOW}PERFORMANCE SUMMARY DISABLED{Fore.RESET}>"
        total_time = execution_time_summary.total_cpu_time
        output = [
            f"{Fore.LIGHTGREEN_EX}PERFORMANCE SUMMARY{Fore.RESET}:",
            "Time elapsed on CPU:",
            f"  * in total: {Fore.LIGHTGREEN_EX}{format_timedelta(timedelta(seconds=total_time))}{Fore.RESET}",
            f"  * on user-initiated tasks: {Fore.LIGHTGREEN_EX}{format_timedelta(timedelta(seconds=execution_time_summary.user_cpu_time))}{Fore.RESET}",
            f"  * on system-initiated tasks: {Fore.LIGHTGREEN_EX}{format_timedelta(timedelta(seconds=execution_time_summary.system_cpu_time))}{Fore.RESET}",
            f"{Fore.LIGHTGREEN_EX}{execution_time_summary.percent_cpu_utilization:.2f}%{Fore.RESET} CPU Usage",
            f"{Fore.LIGHTGREEN_EX}{execution_time_summary.peak_physical_memory_usage:.2f} KB{Fore.RESET} Peak Memory Usage",
            f"Read from disk {Fore.LIGHTGREEN_EX}{execution_time_summary.num_disk_reads}{Fore.RESET} times",
            f"Wrote to disk {Fore.LIGHTGREEN_EX}{execution_time_summary.num_disk_writes}{Fore.RESET} times",
            f"{Fore.LIGHTGREEN_EX}{execution_time_summary.num_major_page_faults}{Fore.RESET} pages fetched from disk (major page-faults).",
            f"{Fore.LIGHTGREEN_EX}{execution_time_summary.num_minor_page_faults}{Fore.RESET} pages mapped from RAM (minor page-faults).",
            f"{Fore.LIGHTGREEN_EX}{execution_time_summary.num_pages_swapped_to_disk}{Fore.RESET} pages swapped to disk."
            f"Function call breakdown:",
        ]
        function_text = []

        total_instructions = sum([call.cost for call in callgrind_summary])
        for call_summary in callgrind_summary:
            function_text.append(
                f"  * {Fore.LIGHTGREEN_EX}{call_summary.percent:.2f}%{Fore.RESET} ({Fore.LIGHTGREEN_EX}{call_summary.cost}{Fore.RESET} inst., ~{Fore.LIGHTGREEN_EX}{format_timedelta(timedelta(seconds=total_time * call_summary.cost / total_instructions))}{Fore.RESET}): {Fore.LIGHTMAGENTA_EX}{call_summary.function}{Fore.RESET} from {Fore.MAGENTA}{call_summary.file}{Fore.RESET} {'in ' + Fore.BLUE + call_summary.shared_object + Fore.RESET if call_summary.shared_object is not None else ''}"
            )
        if not function_text:
            function_text = [f"  * <{Fore.RED}EMPTY?{Fore.RESET}>"]

        return "\n".join(output + function_text)


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
        output = [
            f"Detected build types of `{Fore.MAGENTA}{build_output.build_type}{Fore.RESET}`.\n\n"
        ]
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


class DefaultRuntimeSummaryFormatter(RuntimeSummaryFormatterInterface):
    def format(self, test_cases: Sequence[TestInterface]) -> str:
        total_cpu_time = sum(
            (et.total_cpu_time if (et := tc.get_execution_time()) is not None else 0.0)
            for tc in test_cases
        )
        user_cpu_time = sum(
            (et.user_cpu_time if (et := tc.get_execution_time()) is not None else 0.0)
            for tc in test_cases
        )
        system_cpu_time = sum(
            (et.system_cpu_time if (et := tc.get_execution_time()) is not None else 0.0)
            for tc in test_cases
        )
        call_lists: list[list[CallgrindSummary]] = [
            calls
            for test_case in test_cases
            if (calls := test_case.get_calls()) is not None
        ]
        total_instructions: list[int] = [
            sum(call.cost for call in calls) for calls in call_lists
        ]
        num_tests = len(test_cases)
        num_successful_tests = sum(
            [test_case.get_successful() for test_case in test_cases]
        )
        if num_successful_tests < 0.5 * num_tests:
            color = Fore.RED
        elif num_successful_tests < 0.75 * num_tests:
            color = Fore.LIGHTRED_EX
        elif num_successful_tests < 0.95 * num_tests:
            color = Fore.YELLOW
        elif num_successful_tests < num_tests:
            color = Fore.GREEN
        else:
            color = Fore.CYAN
        return (
            f"{color}{num_successful_tests}{Fore.RESET}/{num_tests} Tests Passed.\n"
            f"Total Time elapsed on CPU:\n"
            f"  * in total: {Fore.LIGHTGREEN_EX}{format_timedelta(timedelta(seconds=total_cpu_time))}{Fore.RESET}\n"
            f"  * on user-initiated tasks: {Fore.LIGHTGREEN_EX}{format_timedelta(timedelta(seconds=user_cpu_time))}{Fore.RESET}\n"
            f"  * on system-initiated tasks: {Fore.LIGHTGREEN_EX}{format_timedelta(timedelta(seconds=system_cpu_time))}{Fore.RESET}\n"
            f"Total number of instructions run: {total_instructions}."
        )


class DefaultTestCaseFormatter(TestCaseFormatterInterface):
    def format(self, test_case: TestInterface) -> str:
        if not test_case.get_successful():
            title_text = (
                f"{Fore.RED}Test `{test_case.get_name()}` failed!{Fore.RESET}\n"
            )
        elif test_case.get_penalty() < 1.0:
            title_text = f"{Fore.YELLOW}Test `{test_case.get_name()}` partially passed, but was penalized!{Fore.RESET}\n"
        elif test_case.get_penalty() == 1.0:
            title_text = (
                f"{Fore.GREEN}Test `{test_case.get_name()}` passed!{Fore.RESET}\n"
            )
        else:
            title_text = f"{Fore.CYAN}Test `{test_case.get_name()}` passed with flying colors (bonus points)!{Fore.RESET}!\n"
        output = [
            title_text,
            Constants.DEFAULT_TOPIC_BREAK,
            DefaultSTDINContext(test_case.get_input()).render(),
            Constants.DEFAULT_TOPIC_BREAK,
            DefaultExpectedSTDOUTContext(test_case.get_expected_output()).render(),
            DefaultActualSTDOUTContext(test_case.get_actual_output()).render(),
            Constants.DEFAULT_TOPIC_BREAK,
            DefaultSTDERRContext(test_case.get_error()).render(),
            Constants.DEFAULT_TOPIC_BREAK,
            DefaultValgrindLeakSummaryFormatter().format(test_case.get_leaks()),
            DefaultValgrindWarningSummaryFormatter().format(test_case.get_warnings()),
            Constants.DEFAULT_TOPIC_BREAK,
            DefaultExecutionTimeSummaryFormatter().format(
                test_case.get_calls(), test_case.get_execution_time()
            ),
        ]
        return "\n".join(output)
