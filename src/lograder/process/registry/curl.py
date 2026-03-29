from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIKVOption,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class CURLArgs(CLIArgs):
    url: str = CLIOption(emit=["{}"], position=-1)

    output: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-o", "{}"],
    )

    response_headers_only: bool = CLIPresenceFlag(["-I"], default=False)
    follow_redirects: bool = CLIPresenceFlag(["-L"], default=False)
    fail: bool = CLIPresenceFlag(["-f"], default=False)
    silent: bool = CLIPresenceFlag(["-s"], default=False)
    show_error: bool = CLIPresenceFlag(["-S"], default=False)

    method: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-X", "{}"],
    )

    data: dict[str, Any] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: ["--data", f"{k}={v}"],
    )

    headers: dict[str, Any] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: ["-H", f"{k}: {v}"],
    )

    @field_validator("url", "method", mode="before")
    @classmethod
    def validate_nonempty_strings(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank string is not valid in `{cls.__name__}`.")
        return v

    @field_validator("output", mode="before")
    @classmethod
    def validate_nonempty_output_path(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v

    @field_validator("headers", mode="after")
    @classmethod
    def validate_headers(cls, v: dict[str, Any]) -> dict[str, Any]:
        for key, value in v.items():
            if not key.strip():
                raise ValueError(
                    f"`headers` in `{cls.__name__}` cannot contain blank keys."
                )
            if "\n" in key or "\r" in key:
                raise ValueError(
                    f"`headers` key `{key}` in `{cls.__name__}` cannot contain newlines."
                )
            value_str = str(value)
            if not value_str.strip():
                raise ValueError(
                    f"`headers` in `{cls.__name__}` cannot contain blank values."
                )
            if "\n" in value_str or "\r" in value_str:
                raise ValueError(
                    f"`headers` value for key `{key}` in `{cls.__name__}` cannot contain newlines."
                )
        return v

    @field_validator("data", mode="after")
    @classmethod
    def validate_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        for key in v:
            if not str(key).strip():
                raise ValueError(
                    f"`data` in `{cls.__name__}` cannot contain blank keys."
                )
        return v

    @model_validator(mode="after")
    def validate_show_error_usage(self) -> Self:
        # `-S` is only useful when `-s` is enabled.
        if self.show_error and not self.silent:
            self.silent = True
        return self


@register_typed_executable(["curl"])
class CURLExecutable(TypedExecutable[CURLArgs]): ...
