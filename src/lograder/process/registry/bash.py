from __future__ import annotations

import shlex
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.exception import DeveloperException
from lograder.process.cli_args import CLIArgs, CLIOption, CLIPresenceFlag
from lograder.process.executable import TypedExecutable, register_typed_executable

T = TypeVar("T", bound=CLIArgs)


class _BashCommonArgs(CLIArgs):
    login: bool = CLIPresenceFlag(["--login"], default=False)
    interactive: bool = CLIPresenceFlag(["-i"], default=False)
    no_profile: bool = CLIPresenceFlag(["--noprofile"], default=False)
    no_rc: bool = CLIPresenceFlag(["--norc"], default=False)
    restricted: bool = CLIPresenceFlag(["-r"], default=False)
    posix: bool = CLIPresenceFlag(["--posix"], default=False)

    errexit: bool = CLIPresenceFlag(["-e"], default=False)
    nounset: bool = CLIPresenceFlag(["-u"], default=False)
    xtrace: bool = CLIPresenceFlag(["-x"], default=False)

    @model_validator(mode="after")
    def validate_profile_flags(self) -> Self:
        if self.no_profile and not self.login:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `no_profile=True` only makes sense with `login=True`."
            )
        if self.no_rc and self.interactive:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `no_rc=True` conflicts with `interactive=True`."
            )
        return self


class BashCommandArgs(_BashCommonArgs, Generic[T]):
    command: T = CLIOption(
        emitter=lambda x: ["-c", shlex.join(x.emit())],
        position=-1,
    )

    @field_validator("command", mode="after")
    @classmethod
    def validate_command(cls, v: T) -> T:
        try:
            return cls._validate_nested(v, cls.__name__, "command")
        except DeveloperException as e:
            raise ValueError from e

    @staticmethod
    def _validate_nested(v: T, cls_name: str, field_name: str) -> T:
        emitted = v.emit()
        if not emitted:
            raise ValueError(
                f"`{field_name}` in `{cls_name}` must emit at least one token."
            )
        if "" in emitted:
            raise ValueError(
                f"`{field_name}` in `{cls_name}` cannot emit empty-string tokens."
            )
        if any(not isinstance(tok, str) for tok in emitted):
            raise ValueError(
                f"`{field_name}` in `{cls_name}` must emit only string tokens."
            )
        return v


class BashScriptArgs(_BashCommonArgs):
    script: Path = CLIOption(
        position=-1,
    )

    @field_validator("script", mode="after")
    @classmethod
    def validate_script(cls, v: Path) -> Path:
        if not v.is_file():
            raise ValueError(
                f"`{v}` is not a file (which is required to run it as a script with `{cls.__name__}`)."
            )
        return v


@register_typed_executable(["bash"])
class BashExecutable(TypedExecutable[BashCommandArgs[CLIArgs] | BashScriptArgs]):
    pass
