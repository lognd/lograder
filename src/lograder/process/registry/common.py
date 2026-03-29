from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIKVOption,
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
        emitter=lambda ss: ([f"-fsanitize={','.join(ss)}"] if ss else []),
        default=(),
    )

    include_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-I{}"])
    library_dirs: list[Path] = CLIMultiOption(default=(), token_emit=["-L{}"])
    libraries: list[str] = CLIMultiOption(default=(), token_emit=["-l{}"])

    defines: dict[str, str | int | bool | None | CLI_ARG_MISSING] = CLIKVOption(
        default={},
        token_emitter=lambda k, v: (
            []
            if isinstance(v, CLI_ARG_MISSING)
            else [f"-D{k}"]
            if v is None
            else [f"-D{k}={_macro_value(v)}"]
        ),
    )

    compile_options: list[str] = CLIMultiOption(default=())
    linker_options: list[str] = CLIMultiOption(
        default=(),
        token_emit=["-Wl,{}"],
    )

    warnings_all: bool = CLIPresenceFlag(["-Wall"], default=True)
    warnings_extra: bool = CLIPresenceFlag(["-Wextra"], default=True)
    warnings_pedantic: bool = CLIPresenceFlag(["-pedantic"], default=False)
    warnings_error: bool = CLIPresenceFlag(["-Werror"], default=False)

    @field_validator("input", mode="before")
    @classmethod
    def validate_nonempty_raw_input_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(
                        f"Parameter `input[{i}]` to `{cls.__name__}` cannot be a blank path."
                    )
        return v

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
        if output.exists() and output.is_dir():
            raise ValueError(
                f"`Path({output.resolve()})` is a directory and thus not valid for `output` parameter of `{cls.__name__}`."
            )
        return output

    @field_validator("include_dirs", "library_dirs", mode="before")
    @classmethod
    def validate_nonempty_directory_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(
                        f"Blank path is not valid in `{cls.__name__}` at index `{i}`."
                    )
        return v

    @field_validator("libraries", "compile_options", "linker_options", mode="before")
    @classmethod
    def validate_nonempty_string_sequences(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(
                        f"Blank string is not valid in `{cls.__name__}` at index `{i}`."
                    )
        return v

    @field_validator("sanitizers", mode="before")
    @classmethod
    def validate_nonempty_sanitizer_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(
                        f"Blank sanitizer entry is not valid in `{cls.__name__}` at index `{i}`."
                    )
        return v

    @field_validator("sanitizers", mode="after")
    @classmethod
    def validate_sanitizers_normalized(cls, sanitizers: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for sanitizer in sanitizers:
            s = sanitizer.strip()
            if "," in s:
                raise ValueError(
                    f"Sanitizer `{sanitizer}` in `{cls.__name__}` must be specified as one logical item, not comma-expanded."
                )
            if s in seen:
                raise ValueError(
                    f"Duplicate sanitizer `{s}` is not valid in `{cls.__name__}`."
                )
            seen.add(s)
            normalized.append(s)

        return normalized

    @field_validator("defines", mode="after")
    @classmethod
    def validate_define_keys(
        cls, defines: dict[str, str | int | bool | None]
    ) -> dict[str, str | int | bool | None]:
        for key in defines:
            if not key.strip():
                raise ValueError(
                    f"`defines` in `{cls.__name__}` cannot contain blank keys."
                )
            if "=" in key:
                raise ValueError(
                    f"`defines` key `{key}` in `{cls.__name__}` cannot contain `=`."
                )
        return defines

    @model_validator(mode="after")
    def validate_pipeline_breaks_mutually_exclusive(self) -> Self:
        active = sum([self.preprocess_only, self.compile_only, self.assemble_only])
        if active > 1:
            raise ValueError(
                f"In `{self.__class__.__name__}`, parameters `preprocess_only` ({self.preprocess_only}), "
                f"`compile_only` ({self.compile_only}), `assemble_only` ({self.assemble_only}) are mutually exclusive; "
                f"only one may be active."
            )
        return self

    @model_validator(mode="after")
    def validate_preprocess_vs_link_inputs(self) -> Self:
        if self.preprocess_only and self.libraries:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `libraries` cannot be specified when `preprocess_only=True`."
            )
        if self.preprocess_only and self.library_dirs:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `library_dirs` cannot be specified when `preprocess_only=True`."
            )
        if self.preprocess_only and self.linker_options:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `linker_options` cannot be specified when `preprocess_only=True`."
            )
        return self


def _macro_value(v: None | str | int | bool) -> str | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)
