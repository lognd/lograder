from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable
from lograder.process.install_script import InstallScript, PlatformInstallScript
from lograder.process.os_helpers import is_posix
from lograder.process.registry.bash import BashExecutable, BashScriptArgs

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

T = TypeVar("T", bound=CLIArgs)


class ValgrindLeakCheck(StrEnum):
    NO = "no"
    SUMMARY = "summary"
    FULL = "full"


class ValgrindArgs(CLIArgs, Generic[T]):
    command: T = CLIOption(
        emitter=lambda x: x.emit(),
        position=-1,
    )

    xml: bool = CLIPresenceFlag(["--xml=yes"], default=False)
    xml_file: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--xml-file={}"],
    )

    leak_check: ValgrindLeakCheck | CLI_ARG_MISSING = CLIOption(
        default=ValgrindLeakCheck.FULL,
        emit=["--leak-check={}"],
    )

    quiet: bool = CLIPresenceFlag(["-q"], default=False)
    child_silent_after_fork: bool = CLIPresenceFlag(
        ["--child-silent-after-fork=yes"],
        default=False,
    )
    track_origins: bool = CLIPresenceFlag(["--track-origins=yes"], default=False)
    error_exitcode: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--error-exitcode={}"],
    )

    @field_validator("xml_file", mode="before")
    @classmethod
    def validate_nonempty_xml_file(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v

    @field_validator("error_exitcode", mode="after")
    @classmethod
    def validate_error_exitcode(cls, v: int | CLI_ARG_MISSING) -> int | CLI_ARG_MISSING:
        if isinstance(v, CLI_ARG_MISSING):
            return v
        if v <= 0:
            raise ValueError(
                f"`error_exitcode` in `{cls.__name__}` must be > 0, but got `{v}`."
            )
        return v

    @field_validator("command", mode="after")
    @classmethod
    def validate_nested_command_emits(cls, v: T) -> T:
        emitted = v.emit()
        if not emitted:
            raise ValueError(
                f"`command` in `{cls.__name__}` must emit at least one token."
            )
        if "" in emitted:
            raise ValueError(
                f"`command` in `{cls.__name__}` cannot emit empty-string tokens."
            )
        return v

    @model_validator(mode="after")
    def validate_xml_configuration(self) -> Self:
        if self.xml_file is not CLI_ARG_MISSING() and not self.xml:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `xml_file` requires `xml=True`."
            )
        return self


@register_typed_executable(["valgrind"])
class ValgrindExecutable(TypedExecutable[ValgrindArgs[CLIArgs]]):
    install_executable = InstallScript(
        {
            is_posix: PlatformInstallScript(
                executable=BashExecutable(),
                args=BashScriptArgs(
                    script=Path(__file__).parent
                    / "install_scripts/posix/install_valgrind.sh"
                ),
                install_location=Path.cwd() / ".valgrind/bin/valgrind",
            )
        }
    )
