from colorama import Fore

from .common import StreamFormatter


class BuildErrorFormatter(
    StreamFormatter, stream_name="build errors", stream_color=Fore.RED
):
    pass


class BuildInfoFormatter(
    StreamFormatter, stream_name="build info", stream_color=Fore.BLUE
):
    pass


class PreprocessorErrorFormatter(
    StreamFormatter, stream_name="preprocessing errors", stream_color=Fore.RED
):
    pass


class PreprocessorInfoFormatter(
    StreamFormatter, stream_name="build info", stream_color=Fore.YELLOW
):
    pass


class AssignmentStatsFormatter:
    pass
