# noinspection PyPep8Naming
from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.process.executable import InstallWarning
from lograder.process.os_helpers import command_to_str


@register_layout("install-warning")
class InstallWarningLayout(Layout[InstallWarning]):
    @classmethod
    def to_simple(cls, data: InstallWarning) -> str:
        return f"The command corresponding to `{data.calling_object}`, which is `{data.command[0]}` (full command: `{command_to_str(data.command)}`), cannot be found. Attempting installation as a fallback, but know that this SERIOUSLY hurts performance."

    @classmethod
    def to_ansi(cls, data: InstallWarning) -> str:
        return f"The command corresponding to `{F.BLUE}{data.calling_object}{F.RESET}`, which is `{F.BLUE}{data.command[0]}{F.RESET}` (full command: `{F.BLUE}{command_to_str(data.command)}{F.RESET}`), cannot be found. Attempting installation {F.RED}AS A FALLBACK{F.RESET}, but please notify the course staff that required binaries are being {F.RED}ON THE FLY{F.RESET}, tanking performance."
