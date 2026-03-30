from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.exception import DeveloperException
from lograder.process.cli_args import (
    CLIArgs,
    CLIKVOption,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable
from lograder.process.registry.common import (
    CStandard,
    CXXStandard,
    Standard,
    find_missing,
)

if TYPE_CHECKING:
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum


class ClangCStandard(StrEnum):
    C23 = "c23"
    C17 = "c17"
    C11 = "c11"
    C99 = "c99"
    C90 = "c90"


_missing_c = find_missing(CStandard, ClangCStandard)
if _missing_c:
    raise DeveloperException(
        f"`ClangCStandard` should be a superset of `CStandard`. Missing: `{'`, `'.join(sorted(_missing_c))}`."
    )


class ClangCXXStandard(StrEnum):
    CXX23 = "c++23"
    CXX20 = "c++20"
    CXX17 = "c++17"
    CXX14 = "c++14"
    CXX11 = "c++11"
    CXX03 = "c++03"
    CXX98 = "c++98"


_missing_cxx = find_missing(CXXStandard, ClangCXXStandard)
if _missing_cxx:
    raise DeveloperException(
        f"`ClangCXXStandard` should be a superset of `CXXStandard`. Missing: `{'`, `'.join(sorted(_missing_cxx))}`."
    )


class ClangCompilerArgs(CLIArgs, Generic[Standard]):
    input: list[Path] = CLIMultiOption()
    output: Path | None = CLIOption(default=None, emit=["-o", "{}"])

    standard: Standard | None = CLIOption(default=None, emit=["-std={}"])

    preprocess_only: bool = CLIPresenceFlag(["-E"], default=False)
    assemble_only: bool = CLIPresenceFlag(["-S"], default=False)
    compile_only: bool = CLIPresenceFlag(["-c"], default=False)

    debug_symbols: bool = CLIPresenceFlag(["-g"], default=False)

    optimization: str | None = CLIOption(default=None, emit=["-O{}"])

    include_dirs: list[Path] = CLIMultiOption(default_factory=list, token_emit=["-I{}"])
    library_dirs: list[Path] = CLIMultiOption(default_factory=list, token_emit=["-L{}"])
    libraries: list[str] = CLIMultiOption(default_factory=list, token_emit=["-l{}"])

    defines: dict[str, str | int | bool | None] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: (
            [f"-D{k}"] if v is None else [f"-D{k}={_clang_macro(v)}"]
        ),
    )

    compile_options: list[str] = CLIMultiOption(default_factory=list)
    linker_options: list[str] = CLIMultiOption(
        default_factory=list, token_emit=["-Wl,{}"]
    )

    warnings_all: bool = CLIPresenceFlag(["-Wall"], default=True)
    warnings_extra: bool = CLIPresenceFlag(["-Wextra"], default=True)
    warnings_pedantic: bool = CLIPresenceFlag(["-pedantic"], default=False)
    warnings_error: bool = CLIPresenceFlag(["-Werror"], default=False)

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    @field_validator("input", mode="before")
    @classmethod
    def validate_nonempty_inputs(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank input at index {i}.")
        return v

    @field_validator("input", mode="after")
    @classmethod
    def validate_at_least_one_input(cls, v: list[Path]) -> list[Path]:
        if not v:
            raise ValueError("`input` must contain at least one source file.")
        return v

    @field_validator("output", mode="before")
    @classmethod
    def validate_output(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError("Output cannot be blank.")
        return v

    @field_validator("include_dirs", "library_dirs", mode="before")
    @classmethod
    def validate_dirs(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank path at index {i}.")
        return v

    @field_validator(
        "libraries", "compile_options", "linker_options", "add_opts", mode="before"
    )
    @classmethod
    def validate_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(f"Blank string at index {i}.")
        return v

    @model_validator(mode="after")
    def validate_pipeline(self) -> Self:
        active = sum([self.preprocess_only, self.compile_only, self.assemble_only])
        if active > 1:
            raise ValueError("Pipeline flags are mutually exclusive.")
        return self


def _clang_macro(v: str | int | bool) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


class ClangArgs(ClangCompilerArgs[ClangCStandard]):
    pass


class ClangXXArgs(ClangCompilerArgs[ClangCXXStandard]):
    permissive: bool = CLIPresenceFlag(["-fpermissive"], default=False)


@register_typed_executable(["clang"])
class ClangExecutable(TypedExecutable[ClangArgs]):
    pass


@register_typed_executable(["clang++"])
class ClangXXExecutable(TypedExecutable[ClangXXArgs]):
    pass
