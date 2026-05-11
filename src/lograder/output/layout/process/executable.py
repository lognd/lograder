# noinspection PyPep8Naming
import os

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.process.executable import ExecutableData, InstallWarning
from lograder.process.os_helpers import command_to_str


@register_layout("install-warning")
class InstallWarningLayout(Layout[InstallWarning]):
    @classmethod
    def to_simple(cls, data: InstallWarning) -> str:
        return f"The command corresponding to `{data.calling_object}`, which is `{data.command[0]}` (full command: `{command_to_str(data.command)}`), cannot be found. Attempting installation as a fallback, but know that this SERIOUSLY hurts performance."

    @classmethod
    def to_ansi(cls, data: InstallWarning) -> str:
        return f"The command corresponding to `{F.BLUE}{data.calling_object}{F.RESET}`, which is `{F.BLUE}{data.command[0]}{F.RESET}` (full command: `{F.BLUE}{command_to_str(data.command)}{F.RESET}`), cannot be found. Attempting installation {F.RED}AS A FALLBACK{F.RESET}, but please notify the course staff that required binaries are being {F.RED}ON THE FLY{F.RESET}, tanking performance."


@register_layout("executable-data")
class ExecutableDataLayout(Layout[ExecutableData]):
    @classmethod
    def to_simple(cls, data: ExecutableData) -> str:
        output = [
            f"Executed the following command `{command_to_str(data.output.command)}` with return code, `{data.output.return_code}`",
        ]

        if data.input.env:
            output.extend(
                (
                    f" with environment variables: ",
                    *(f"`{k}`=`{v}`" for k, v in data.input.env.items()),
                    f". ",
                )
            )
        else:
            output.extend((f" with no environment variables. ",))

        if data.input.stdin_bytes:
            output.append(
                f"STDIN was `{repr(data.input.stdin_bytes.decode('utf-8', errors='ignore'))}`. "
            )
        else:
            output.append(f"STDIN was empty. ")

        if data.input.stdin_bytes:
            output.append(
                f"STDERR was `{repr(data.output.stderr_bytes.decode('utf-8', errors='ignore'))}`. "
            )
        else:
            output.append(f"STDERR was empty. ")

        if data.input.stdin_bytes:
            output.append(
                f"STDOUT was `{repr(data.output.stdout_bytes.decode('utf-8', errors='ignore'))}`. "
            )
        else:
            output.append(f"STDOUT was empty. ")

        return "".join(output)

    @staticmethod
    def stream_wrap(
        color: str, stream_name: str, stream_data: bytes, hidden: bool
    ) -> tuple[str, ...]:
        if hidden:
            return (f"< {color}{stream_name.upper()} HIDDEN{F.RESET} >\n\n",)
        if stream_data:
            return (
                f"< {color}BEGIN {stream_name.upper()}{F.RESET} >\n",
                stream_data.decode("utf-8", errors="ignore"),
                "\n",
                f"< {color}END {stream_name.upper()}{F.RESET} >\n",
                f"< {color}BEGIN RAW {stream_name.upper()}{F.RESET} >\n",
                repr(stream_data.decode("utf-8", errors="ignore")),
                "\n",
                f"< {color}END RAW {stream_name.upper()}{F.RESET} >\n\n",
            )
        return (f"< {color} EMPTY {stream_name.upper()}{F.RESET} >\n\n",)

    @classmethod
    def to_ansi(cls, data: ExecutableData) -> str:
        output = [
            f"Executed the following command `{command_to_str(data.output.command)}` with return code, `{data.output.return_code}`.\n\n",
        ]

        if data.input.env != os.environ:
            if not data.input.hide_input:
                if not data.input.env:
                    output.append(
                        f"< {F.MAGENTA}INTENTIONALLY BLANK ENVIRONMENT VARIABLES{F.RESET} >\n\n"
                    )
                else:
                    output.extend(
                        (
                            f"< {F.MAGENTA}BEGIN ENVIRONMENT VARIABLES{F.RESET} >\n",
                            *(f"`{k}`=`{v}`" for k, v in data.input.env.items()),
                            f"< {F.MAGENTA}END ENVIRONMENT VARIABLES{F.RESET} >\n\n",
                        )
                    )
            else:
                output.append(f"< {F.MAGENTA}ENVIRONMENT VARIABLES HIDDEN{F.RESET} >\n")

        output.extend(
            cls.stream_wrap(
                F.YELLOW, "stdin", data.input.stdin_bytes, data.input.hide_input
            )
        )
        output.extend(
            cls.stream_wrap(
                F.BLUE, "stdout", data.output.stdout_bytes, data.input.hide_output
            )
        )
        output.extend(
            cls.stream_wrap(
                F.RED, "stderr", data.output.stderr_bytes, data.input.hide_output
            )
        )

        return "".join(output)
