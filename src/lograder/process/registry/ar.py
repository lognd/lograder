from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLIArgs,
    CLIMultiOption,
    CLIOption,
)
from lograder.process.executable import TypedExecutable, register_typed_executable

if TYPE_CHECKING:
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum


class ArOperation(StrEnum):
    REPLACE = "r"
    DELETE = "d"
    EXTRACT = "x"
    TABLE = "t"
    MOVE = "m"
    PRINT = "p"
    QUICK_APPEND = "q"


class ArArgs(CLIArgs):
    operation: ArOperation

    create: bool = False
    index: bool = False
    verbose: bool = False
    update_only: bool = False

    insert_after: bool = False
    insert_before: bool = False

    raw_modifiers: str = ""

    flags: str = CLIOption(
        default="",
        emit=["{}"],
        position=0,
    )

    archive: Path = CLIOption(
        emit=["{}"],
        position=1,
    )

    position_member: Path | None = CLIOption(
        default=None,
        emit=["{}"],
        position=2,
    )

    files: list[Path] = CLIMultiOption(
        default_factory=list,
        token_emit=["{}"],
    )

    @field_validator("archive", mode="before")
    @classmethod
    def validate_nonempty_archive(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v

    @field_validator("position_member", mode="before")
    @classmethod
    def validate_nonempty_position_member(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v

    @field_validator("raw_modifiers", mode="before")
    @classmethod
    def validate_raw_modifiers(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank string is not valid in `{cls.__name__}`.")
        return v

    @field_validator("files", mode="before")
    @classmethod
    def validate_nonempty_raw_file_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(
                        f"Blank path is not valid in `{cls.__name__}` at index `{i}`."
                    )
        return v

    @model_validator(mode="after")
    def validate_insert_flags(self) -> Self:
        if self.insert_after and self.insert_before:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `insert_after` and `insert_before` are mutually exclusive."
            )
        if (self.insert_after or self.insert_before) and self.position_member is None:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `position_member` must be provided when `insert_after=True` or `insert_before=True`."
            )
        if (
            not (self.insert_after or self.insert_before)
            and self.position_member is not None
        ):
            raise ValueError(
                f"In `{self.__class__.__name__}`, `position_member` cannot be specified unless `insert_after=True` or `insert_before=True`."
            )
        return self

    @model_validator(mode="after")
    def synthesize_flags(self) -> Self:
        flags = [self.operation.value]

        if self.create:
            flags.append("c")
        if self.index:
            flags.append("s")
        if self.verbose:
            flags.append("v")
        if self.update_only:
            flags.append("u")
        if self.insert_after:
            flags.append("a")
        if self.insert_before:
            flags.append("b")
        if self.raw_modifiers:
            flags.append(self.raw_modifiers)

        self.flags = "".join(flags)
        return self


@register_typed_executable(["ar"])
class ArExecutable(TypedExecutable[ArArgs]):
    pass
