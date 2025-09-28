import difflib
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Dict, Generic, List, Mapping, Tuple, TypeVar, cast

from colorama import Back, Fore

from ...types import (
    AssignmentMetadataOutput,
    ByteStreamComparisonOutput,
    CommandOutput,
    StreamOutput,
    UnitTestCase,
    UnitTestSuite,
    ValgrindOutput,
    is_successful_test,
)
from .dispatcher import register_format

T = TypeVar("T", bound=Mapping[str, Any])


class FormatterInterface(ABC, Generic[T]):

    @classmethod
    @abstractmethod
    def to_string(cls, data: T) -> str:
        pass


class StreamOutputInterface(FormatterInterface[StreamOutput]):
    _prefix: str = ""
    _suffix: str = ""
    _empty: str = ""

    def __init_subclass__(cls, *, prefix: str, suffix: str, empty: str):
        cls._prefix = prefix
        cls._suffix = suffix
        cls._empty = empty

    @classmethod
    def to_string(cls, data: StreamOutput) -> str:
        return (
            f"{cls.get_prefix()}{data['stream_contents']}{cls.get_suffix()}"
            if data["stream_contents"]
            else cls.get_empty()
        )

    @classmethod
    def get_prefix(cls):
        return cls._prefix

    @classmethod
    def get_suffix(cls):
        return cls._suffix

    @classmethod
    def get_empty(cls):
        return cls._empty


@register_format("raw")
class RawFormatter(FormatterInterface[StreamOutput]):
    @classmethod
    def to_string(cls, data: StreamOutput) -> str:
        return data["stream_contents"]


@register_format("stdin")
class STDInFormatter(
    StreamOutputInterface,
    prefix=f"<{Fore.MAGENTA}BEGIN STDIN{Fore.RESET}>\n",
    suffix=f"\n<{Fore.MAGENTA}END STDIN{Fore.RESET}>",
    empty=f"<{Fore.MAGENTA}EMPTY STDIN{Fore.RESET}>",
): ...


@register_format("stdout")
class STDOutFormatter(
    StreamOutputInterface,
    prefix=f"<{Fore.BLUE}BEGIN STDOUT{Fore.RESET}>\n",
    suffix=f"\n<{Fore.BLUE}END STDOUT{Fore.RESET}>",
    empty=f"<{Fore.BLUE}EMPTY STDOUT{Fore.RESET}>",
): ...


@register_format("stderr")
class STDErrFormatter(
    StreamOutputInterface,
    prefix=f"<{Fore.RED}BEGIN STDERR{Fore.RESET}>\n",
    suffix=f"\n<{Fore.RED}END STDERR{Fore.RESET}>",
    empty=f"<{Fore.RED}EMPTY STDERR{Fore.RESET}>",
): ...


@register_format("expected-stdout")
class ExpectedSTDOutFormatter(
    StreamOutputInterface,
    prefix=f"<{Fore.BLUE}BEGIN EXPECTED STDOUT{Fore.RESET}>\n",
    suffix=f"\n<{Fore.BLUE}END EXPECTED STDOUT{Fore.RESET}>",
    empty=f"<{Fore.BLUE}EMPTY EXPECTED STDOUT{Fore.RESET}>",
): ...


@register_format("actual-stdout")
class ActualSTDOutFormatter(
    StreamOutputInterface,
    prefix=f"<{Fore.LIGHTMAGENTA_EX}BEGIN ACTUAL STDOUT{Fore.RESET}>\n",
    suffix=f"\n<{Fore.LIGHTMAGENTA_EX}END ACTUAL STDOUT{Fore.RESET}>",
    empty=f"<{Fore.LIGHTMAGENTA_EX}EMPTY ACTUAL STDOUT{Fore.RESET}>",
): ...


@register_format("byte-cmp")
class ByteCmpFormatter(FormatterInterface[ByteStreamComparisonOutput]):
    @staticmethod
    def bytes_to_safe_ascii(data: bytes) -> str:
        return "".join(
            (
                chr(b)
                if 32 <= b <= 126
                else (
                    r"\n"
                    if b == ord("\n")
                    else (
                        r"\t"
                        if b == ord("\t")
                        else r"\r" if b == ord("\r") else f"\\x{b:02x}"
                    )
                )
            )
            for b in data
        )

    @staticmethod
    def abbreviate(a: bytes, max_len: int = 1024) -> str:
        if len(a) <= max_len:
            return ByteCmpFormatter.bytes_to_safe_ascii(a)
        return (
            f"{ByteCmpFormatter.bytes_to_safe_ascii(a[:max_len//2])}"
            " (...) "
            f"{ByteCmpFormatter.bytes_to_safe_ascii(a[-max_len//2:])}"
        )

    @staticmethod
    def static_comparison(expected: bytes, actual: bytes, max_len: int = 32) -> str:
        differences: List[Tuple[int, int, int]] = []
        for i, (b_a, b_b) in enumerate(zip(expected, actual)):
            if len(differences) > max_len:
                break
            if b_a != b_b:
                differences.append((b_a, b_b, i))

        if len(differences) == 0:
            return (
                f"  {Fore.CYAN}*{Fore.RESET} ({Fore.GREEN}No differences!{Fore.RESET})"
            )
        elif len(differences) <= max_len:
            return "\n".join(
                f"  {Fore.CYAN}*{Fore.RESET} Expected: ({Back.GREEN}{b_a:02x}{Back.RESET}); Actual: ({Back.RED}{b_b:02x}{Back.RESET}); @ Location: 0x{b_l:08x}/{b_l}"
                for b_a, b_b, b_l in differences
            )
        return "\n".join(
            [
                f"  {Fore.CYAN}*{Fore.RESET} Expected: ({Back.GREEN}{b_a:02x}{Back.RESET}); Actual: ({Back.RED}{b_b:02x}{Back.RESET}); @ Location: 0x{b_l:08x}/{b_l}"
                for b_a, b_b, b_l in differences[:max_len]
            ]
            + [f"  {Fore.CYAN}*{Fore.RESET} ..."]
        )

    @staticmethod
    def string_comparison(expected: bytes, actual: bytes, max_len: int = 32768) -> str:
        if len(expected) > max_len or len(actual) > max_len:
            return f"  {Fore.CYAN}*{Fore.RESET} ({Fore.RED}Too long to compare!{Fore.RESET})"
        str_a = ByteCmpFormatter.bytes_to_safe_ascii(expected)
        str_b = ByteCmpFormatter.bytes_to_safe_ascii(actual)
        diff = difflib.ndiff(str_a, str_b)

        out_a: List[str] = []
        out_b: List[str] = []

        for d in diff:
            if d.startswith("- "):
                out_a.append(f"{Back.GREEN}{d[2:]}{Back.RESET}")
            elif d.startswith("+ "):
                out_b.append(f"{Back.RED}{d[2:]}{Back.RESET}")
            elif d.startswith("? "):
                continue
            else:
                out_a.append(d[2:])
                out_b.append(d[2:])

        return (
            f"  {Fore.CYAN}*{Fore.RESET} Expected (Missing Highlighted): "
            + "".join(out_a)
            + f"\n  {Fore.CYAN}*{Fore.RESET} Actual (Insertions Highlighted): "
            + "".join(out_b)
        )

    @classmethod
    def to_string(cls, data: ByteStreamComparisonOutput):
        expected: bytes = data["stream_expected_bytes"]
        actual: bytes = data["stream_actual_bytes"]

        len_expected_output = f"EXPECTED OUTPUT LENGTH: {len(expected)}"
        len_actual_output = f"ACTUAL OUTPUT LENGTH: {len(actual)}"

        raw_expected_output: str = (
            "RAW EXPECTED OUTPUT: " + ByteCmpFormatter.abbreviate(expected)
        )
        raw_actual_output: str = "RAW ACTUAL OUTPUT: " + ByteCmpFormatter.abbreviate(
            actual
        )

        chr_output_comparison: str = (
            "BYTE COMPARISON: \n" + ByteCmpFormatter.static_comparison(expected, actual)
        )
        str_output_comparison: str = (
            "STRING COMPARISON: \n"
            + ByteCmpFormatter.string_comparison(expected, actual)
        )

        return (
            f"<{Fore.LIGHTYELLOW_EX}BEGIN BYTE COMPARISON{Fore.RESET}>\n"
            f"{len_expected_output}\n"
            f"{len_actual_output}\n\n"
            f"{raw_expected_output}\n"
            f"{raw_actual_output}\n\n"
            f"{chr_output_comparison}\n\n"
            f"{str_output_comparison}\n"
            f"<{Fore.LIGHTYELLOW_EX}END BYTE COMPARISON{Fore.RESET}>"
        )


@register_format("unit-tests")
class UnitTestFormatter(FormatterInterface[UnitTestSuite | UnitTestCase]):
    @classmethod
    def to_string(cls, data: UnitTestSuite | UnitTestCase):
        strings: List[str] = []
        color: str
        if "success" in data.keys():
            data = cast(UnitTestCase, data)
            success = is_successful_test(data)
            color = Fore.GREEN if success else Fore.RED
            if not success:
                strings.append(
                    f"<{color}BEGIN FAILED TEST CASE '{data['name']}'{Fore.RESET}>"
                )
                strings.append(
                    "\n".join(f"  {line}" for line in data["output"].split("\n"))
                )
                strings.append(
                    f"<{color}END FAILED TEST CASE '{data['name']}'{Fore.RESET}>\n"
                )
            else:
                strings.append(
                    f"<{color}PASSED TEST CASE '{data['name']}'{Fore.RESET}>"
                )
        else:
            data = cast(UnitTestSuite, data)
            color = Fore.GREEN if is_successful_test(data) else Fore.RED
            desc = "PASSED" if is_successful_test(data) else "FAILED"
            rec_string: str = "\n".join(cls.to_string(_case) for _case in data["cases"])

            strings.append(
                f"<{color}BEGIN {desc} TEST SUITE '{data['name']}'{Fore.RESET}>"
            )
            strings.append("\n".join(f"  {line}" for line in rec_string.split("\n")))
            strings.append(
                f"<{color}END {desc} TEST SUITE '{data['name']}'{Fore.RESET}>\n"
            )

        return "\n".join(strings)


@register_format("build-fail")
class BuildFailureFormatter(FormatterInterface[Dict]):
    @classmethod
    def to_string(cls, data: Dict):
        return f"{Fore.RED}<NO EXECUTABLE GENERATED>{Fore.RESET}"


@register_format("valgrind")
class ValgrindFormatter(FormatterInterface[ValgrindOutput]):
    @classmethod
    def to_string(cls, data: ValgrindOutput):
        leak_summary = data["leaks"]
        warning_summary = data["warnings"]

        def_lost_color = (
            Fore.LIGHTGREEN_EX if leak_summary.definitely_lost.is_safe else Fore.RED
        )
        ind_lost_color = (
            Fore.LIGHTGREEN_EX if leak_summary.indirectly_lost.is_safe else Fore.RED
        )
        pos_lost_color = (
            Fore.LIGHTGREEN_EX if leak_summary.possibly_lost.is_safe else Fore.RED
        )
        leak_text = (
            f"{Fore.LIGHTGREEN_EX}VALGRIND LEAK SUMMARY{Fore.RESET}:\n"  # I know these pluses aren't necessary, but I'm doing it for back-compatibility because linters yell at me for line-continuation.
            + f"  {Fore.LIGHTBLUE_EX}*{Fore.RESET} {def_lost_color}{leak_summary.definitely_lost.bytes}{Fore.RESET} bytes, {def_lost_color}{leak_summary.definitely_lost.blocks}{Fore.RESET} blocks {def_lost_color}definitely lost{Fore.RESET}.\n"
            + f"  {Fore.LIGHTBLUE_EX}*{Fore.RESET} {ind_lost_color}{leak_summary.indirectly_lost.bytes}{Fore.RESET} bytes, {ind_lost_color}{leak_summary.indirectly_lost.blocks}{Fore.RESET} blocks {ind_lost_color}indirectly lost{Fore.RESET}.\n"
            + f"  {Fore.LIGHTBLUE_EX}*{Fore.RESET} {pos_lost_color}{leak_summary.possibly_lost.bytes}{Fore.RESET} bytes, {pos_lost_color}{leak_summary.possibly_lost.blocks}{Fore.RESET} blocks {pos_lost_color}possibly lost{Fore.RESET}.\n"
            + f"  {Fore.LIGHTBLUE_EX}*{Fore.RESET} {Fore.LIGHTGREEN_EX}{leak_summary.still_reachable.bytes}{Fore.RESET} bytes, {Fore.LIGHTGREEN_EX}{leak_summary.still_reachable.blocks}{Fore.RESET} blocks {Fore.LIGHTGREEN_EX}still reachable{Fore.RESET}."
        )

        warning = warning_summary.model_dump()
        output = [f"{Fore.LIGHTGREEN_EX}VALGRIND WARNING SUMMARY{Fore.RESET}:"]
        output += [
            f"  {Fore.LIGHTBLUE_EX}*{Fore.RESET} {Fore.LIGHTGREEN_EX if v == 0 else Fore.RED}{v}{Fore.RESET} `{Fore.LIGHTRED_EX}{k.replace('_', ' ').upper()}{Fore.RESET}` warnings encountered."
            for k, v in warning.items()
        ]

        warning_text = "\n".join(output)

        return f"{leak_text}\n\n{warning_text}"


@register_format("command")
class CommandFormatter(FormatterInterface[CommandOutput]):
    @classmethod
    def to_string(cls, data: CommandOutput):
        return f"Ran `{Fore.MAGENTA}{data['command']}{Fore.RESET}` in CLI with exit code, \"{data['exit_code']}\"."


@register_format("assignment-metadata")
class MetadataFormatter(FormatterInterface[AssignmentMetadataOutput]):
    @staticmethod
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

    @classmethod
    def to_string(cls, data: AssignmentMetadataOutput) -> str:
        return (
            f"`{Fore.MAGENTA}{data['metadata'].assignment_name}{Fore.RESET}` made by {Fore.MAGENTA}{f'{Fore.RESET}, {Fore.MAGENTA}'.join(data['metadata'].assignment_authors)}{Fore.RESET}.\n"
            + f'Submission date: {Fore.MAGENTA}{data["metadata"].assignment_submit_date.strftime("%Y-%m-%d %H:%M:%S.%f")}{Fore.RESET}.\n'
            + f'Due date: {Fore.MAGENTA}{data["metadata"].assignment_due_date.strftime("%Y-%m-%d %H:%M:%S.%f")}{Fore.RESET}.\n'
            + f"Time left: {Fore.MAGENTA}{cls.format_timedelta(data['metadata'].assignment_due_date - data['metadata'].assignment_submit_date)}{Fore.RESET}.\n\n"
            + f"Assignment graded with `{Fore.GREEN}{data['metadata'].library_name}{Fore.RESET}` (version {Fore.GREEN}{data['metadata'].library_version}{Fore.RESET}), made by {Fore.GREEN}{f'{Fore.RESET}, {Fore.GREEN}'.join(data['metadata'].library_authors)}.{Fore.RESET}\n\n"
        )
