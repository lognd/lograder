from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import field_validator, model_validator
from typing_extensions import Self

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
        emitter=lambda ss: ([f"-fsanitize={','.join(ss)}"] if ss else []), default=()
    )
    include_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-I{}"])
    library_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-L{}"])
    libraries: list[str] = CLIMultiOption(default=(), token_emit=["-l{}"])

    warnings_all: bool = CLIPresenceFlag(["-Wall"], default=True)
    warnings_extra: bool = CLIPresenceFlag(["-Wextra"], default=True)
    warnings_pedantic: bool = CLIPresenceFlag(["-pedantic"], default=False)
    warnings_error: bool = CLIPresenceFlag(["-Werror"], default=False)

    @field_validator("input", mode="after")
    @classmethod
    def validate_at_least_one_input(cls, input: list[Path]) -> list[Path]:
        if not input:
            raise ValueError(
                f"Parameter `input` to `{cls.__name__}` should contain at least one `Path`, but was empty."
            )
        return input

    @field_validator("output", mode="before")
    @classmethod
    def validate_nonempty_output_path(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            raise ValueError(
                f"Empty string is not valid for `output` in `{cls.__name__}`."
            )
        return v

    @field_validator("output", mode="after")
    @classmethod
    def validate_output_not_a_directory(cls, output: Path) -> Path:
        if output.is_dir():
            raise ValueError(
                f"`Path({output.resolve()})` is a directory and thus not valid for `output` parameter of `{cls.__name__}`."
            )
        return output

    @model_validator(mode="after")
    def validate_pipeline_breaks_mutually_exclusive(self) -> Self:
        if sum([self.preprocess_only, self.compile_only, self.assemble_only]) > 1:
            raise ValueError(
                f"In `{self.__class__.__name__}`, parameters `preprocess_only` ({self.preprocess_only}), `compile_only` ({self.compile_only}), `assemble_only` ({self.assemble_only}) are mutually exclusive; only one may be active."
            )
        return self
