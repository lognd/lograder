from __future__ import annotations

from pathlib import Path
from typing import Any

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
from lograder.process.executable import TypedExecutable, register_typed_executable
from lograder.process.install_script import InstallScript, PlatformInstallScript
from lograder.process.os_helpers import is_posix
from lograder.process.registry.bash import BashExecutable, BashScriptArgs


class CMakeConfigureArgs(CLIArgs):
    # Core directories
    source_dir: Path = CLIOption(default=Path("."), emit=["-S", "{}"])
    build_dir: Path = CLIOption(default=Path("build"), emit=["-B", "{}"])

    # High-value configure controls
    generator: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-G", "{}"],
    )
    toolchain_file: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-DCMAKE_TOOLCHAIN_FILE={}"],
    )
    install_prefix: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-DCMAKE_INSTALL_PREFIX={}"],
    )
    build_type: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-DCMAKE_BUILD_TYPE={}"],
    )
    preset: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--preset", "{}"],
    )

    # Cache and extra switches
    cache_entries: dict[str, CLI_ARG_MISSING | None | bool | int | str] = CLIKVOption(
        default_factory=dict,
        token_emitter=lambda k, v: (
            []
            if isinstance(v, CLI_ARG_MISSING)
            else [f"-D{k}"]
            if v is None
            else [f"-D{k}={_cmake_cache_value(v)}"]
        ),
    )
    warnings_as_errors: bool = CLIPresenceFlag(["-Werror=dev"], default=False)
    warn_uninitialized: bool = CLIPresenceFlag(["--warn-uninitialized"], default=False)
    warn_unused_vars: bool = CLIPresenceFlag(["--warn-unused-vars"], default=False)
    fresh: bool = CLIPresenceFlag(["--fresh"], default=False)
    trace: bool = CLIPresenceFlag(["--trace"], default=False)
    trace_expand: bool = CLIPresenceFlag(["--trace-expand"], default=False)
    debug_output: bool = CLIPresenceFlag(["--debug-output"], default=False)
    debug_find: bool = CLIPresenceFlag(["--debug-find"], default=False)

    @field_validator("generator", "preset", "build_type", mode="before")
    @classmethod
    def validate_nonempty_strings(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank string is not valid in `{cls.__name__}`.")
        return v

    @field_validator(
        "source_dir", "build_dir", "toolchain_file", "install_prefix", mode="before"
    )
    @classmethod
    def validate_nonempty_path_strings(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v

    @field_validator("source_dir", mode="after")
    @classmethod
    def validate_source_dir_not_file(cls, v: Path) -> Path:
        if v.exists() and not v.is_dir():
            raise ValueError(
                f"`source_dir` for `{cls.__name__}` must be a directory if it exists, but got file `{v}`."
            )
        return v

    @field_validator("build_dir", mode="after")
    @classmethod
    def validate_build_dir_not_file(cls, v: Path) -> Path:
        if v.exists() and not v.is_dir():
            raise ValueError(
                f"`build_dir` for `{cls.__name__}` must be a directory if it exists, but got file `{v}`."
            )
        return v

    @field_validator("toolchain_file", mode="after")
    @classmethod
    def validate_toolchain_file(
        cls, v: Path | CLI_ARG_MISSING
    ) -> Path | CLI_ARG_MISSING:
        if isinstance(v, CLI_ARG_MISSING):
            return v
        if v.exists() and v.is_dir():
            raise ValueError(
                f"`toolchain_file` for `{cls.__name__}` must be a file, not directory `{v}`."
            )
        return v

    @field_validator("cache_entries", mode="after")
    @classmethod
    def validate_cache_keys(
        cls, v: dict[str, str | int | bool]
    ) -> dict[str, str | int | bool]:
        for key in v:
            if not key.strip():
                raise ValueError(
                    f"`cache_entries` in `{cls.__name__}` cannot contain blank keys."
                )
            if "=" in key:
                raise ValueError(
                    f"`cache_entries` key `{key}` in `{cls.__name__}` cannot contain `=`."
                )
        return v

    @model_validator(mode="after")
    def validate_preset_vs_manual_dirs(self) -> Self:
        # CMake presets usually own source/build configuration.
        # Keep this strict unless you want to allow mixed usage.
        if self.preset is not CLI_ARG_MISSING():
            source_is_default = self.source_dir == Path(".")
            build_is_default = self.build_dir == Path("build")
            if not source_is_default or not build_is_default:
                raise ValueError(
                    f"In `{self.__class__.__name__}`, `preset` should not be combined with explicit "
                    f"`source_dir` or `build_dir` overrides."
                )
        return self

    @model_validator(mode="after")
    def validate_trace_flags(self) -> Self:
        if self.trace_expand and not self.trace:
            # trace-expand is normally only meaningful along with trace
            self.trace = True
        return self


class CMakeBuildArgs(CLIArgs):
    build_dir: Path = CLIOption(default=Path("build"), emit=["--build", "{}"])

    target: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--target", "{}"],
    )
    config: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--config", "{}"],
    )
    parallel: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--parallel", "{}"],
    )

    clean_first: bool = CLIPresenceFlag(["--clean-first"], default=False)
    verbose: bool = CLIPresenceFlag(["--verbose"], default=False)

    # Pass through to underlying native build tool
    native_args: list[str] = CLIMultiOption(
        default_factory=list,
        sequence_emitter=lambda l: (["--", ...] if l else []),
    )

    @field_validator("target", "config", mode="before")
    @classmethod
    def validate_nonempty_strings(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank string is not valid in `{cls.__name__}`.")
        return v

    @field_validator("build_dir", mode="before")
    @classmethod
    def validate_nonempty_build_dir(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            raise ValueError(
                f"Blank path is not valid for `build_dir` in `{cls.__name__}`."
            )
        return v

    @field_validator("build_dir", mode="after")
    @classmethod
    def validate_build_dir_not_file(cls, v: Path) -> Path:
        if v.exists() and not v.is_dir():
            raise ValueError(
                f"`build_dir` for `{cls.__name__}` must be a directory if it exists, but got file `{v}`."
            )
        return v

    @field_validator("parallel", mode="after")
    @classmethod
    def validate_parallel_positive(
        cls, v: int | CLI_ARG_MISSING
    ) -> int | CLI_ARG_MISSING:
        if isinstance(v, CLI_ARG_MISSING):
            return v
        if v <= 0:
            raise ValueError(
                f"`parallel` in `{cls.__name__}` must be > 0, but got `{v}`."
            )
        return v

    @model_validator(mode="after")
    def validate_native_args(self) -> Self:
        if "" in self.native_args:
            raise ValueError(
                f"`native_args` in `{self.__class__.__name__}` cannot contain empty strings."
            )
        return self


class CMakeInstallArgs(CLIArgs):
    build_dir: Path = CLIOption(default=Path("build"), emit=["--install", "{}"])
    config: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--config", "{}"],
    )
    component: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--component", "{}"],
    )
    prefix: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--prefix", "{}"],
    )
    strip: bool = CLIPresenceFlag(["--strip"], default=False)

    @field_validator("config", "component", mode="before")
    @classmethod
    def validate_nonempty_strings(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank string is not valid in `{cls.__name__}`.")
        return v

    @field_validator("build_dir", "prefix", mode="before")
    @classmethod
    def validate_nonempty_paths(cls, v: Any) -> Any:
        if v is CLI_ARG_MISSING():
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v


@register_typed_executable(["cmake"])
class CMakeExecutable(
    TypedExecutable[CMakeConfigureArgs | CMakeBuildArgs | CMakeInstallArgs]
):
    install_executable = InstallScript(
        {
            is_posix: PlatformInstallScript(
                executable=BashExecutable(),
                args=BashScriptArgs(
                    script=Path(__file__).parent
                    / "install_scripts/posix/install_cmake.sh"
                ),
                install_location=Path.cwd() / ".cmake/bin/cmake",
            )
        }
    )


def _cmake_cache_value(v: str | int | bool) -> str:
    if isinstance(v, bool):
        return "ON" if v else "OFF"
    return str(v)
