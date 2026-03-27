from pathlib import Path
from typing import TYPE_CHECKING, Generic, Iterable, TypeVar

from lograder.process.cli_args import (
    CLIArgs,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from _strenum_compat import StrEnum
else:
    try:
        # noinspection PyUnresolvedReferences
        from enum import StrEnum
    except ImportError:
        # noinspection PyUnresolvedReferences
        from strenum import StrEnum


# You cannot inherit from enums, so this is a simple runtime check.
def find_missing(sub: type[StrEnum], sup: type[StrEnum]) -> set[str]:
    return {m.value for m in sub} - {m.value for m in sup}


class CStandard(StrEnum):
    C23 = "c23"
    C17 = "c17"
    C11 = "c11"
    C99 = "c99"
    C90 = "c90"


class CXXStandard(StrEnum):
    CXX23 = "c++23"
    CXX20 = "c++20"
    CXX17 = "c++17"
    CXX14 = "c++14"
    CXX11 = "c++11"
    CXX03 = "c++03"
    CXX98 = "c++98"


Standard = TypeVar("Standard", bound=StrEnum)


class CompilerArgs(CLIArgs, Generic[Standard]):
    input: list[Path] = CLIMultiOption()
    output: Path = CLIOption(emit=["-o", "{}"])
    standard: Standard = CLIOption(emit=["-std={}"])

    preprocess_only: bool = CLIPresenceFlag(["-E"], default=False)
    assemble_only: bool = CLIPresenceFlag(["-S"], default=False)
    compile_only: bool = CLIPresenceFlag(["-c"], default=False)

    debug_symbols: bool = CLIPresenceFlag(["-g"], default=False)
    sanitizers: list[str] = CLIOption(
        emitter=lambda ss: (f"-fsanitize={','.join(ss)}" if ss else ""), default=()
    )
    include_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-I{}"])
    library_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-L{}"])
    libraries: list[str] = CLIMultiOption(default=(), token_emit=["-l{}"])

    warnings_all: bool = CLIPresenceFlag(["-Wall"], default=True)
    warnings_extra: bool = CLIPresenceFlag(["-Wextra"], default=True)
    warnings_pedantic: bool = CLIPresenceFlag(["-pedantic"], default=False)
    warnings_error: bool = CLIPresenceFlag(["-Werror"], default=False)
