from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from typing_extensions import Self

from lograder.process.cli_args import (
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


class PytestArgs(CLIArgs):
    paths: list[Path] = CLIMultiOption(default_factory=list)

    keyword: str | None = CLIOption(default=None, emit=["-k", "{}"])
    marker: str | None = CLIOption(default=None, emit=["-m", "{}"])

    max_fail: int | None = CLIOption(default=None, emit=["--maxfail={}"])
    exit_first: bool = CLIPresenceFlag(["-x"], default=False)

    verbose: bool = CLIPresenceFlag(["-v"], default=False)
    quiet: bool = CLIPresenceFlag(["-q"], default=False)

    capture: str | None = CLIOption(default=None, emit=["--capture={}"])
    show_capture: str | None = CLIOption(default=None, emit=["--show-capture={}"])

    disable_warnings: bool = CLIPresenceFlag(["--disable-warnings"], default=False)
    show_locals: bool = CLIPresenceFlag(["--showlocals"], default=False)

    durations: int | None = CLIOption(default=None, emit=["--durations={}"])
    durations_min: float | None = CLIOption(default=None, emit=["--durations-min={}"])

    junit_xml: Path | None = CLIOption(default=None, emit=["--junitxml={}"])
    junit_prefix: str | None = CLIOption(default=None, emit=["--junitprefix={}"])

    traceback: str | None = CLIOption(default=None, emit=["--tb={}"])
    color: str | None = CLIOption(default=None, emit=["--color={}"])

    last_failed: bool = CLIPresenceFlag(["--lf"], default=False)
    failed_first: bool = CLIPresenceFlag(["--ff"], default=False)
    new_first: bool = CLIPresenceFlag(["--nf"], default=False)

    cache_clear: bool = CLIPresenceFlag(["--cache-clear"], default=False)

    stepwise: bool = CLIPresenceFlag(["--sw"], default=False)
    stepwise_skip: bool = CLIPresenceFlag(["--sw-skip"], default=False)

    collect_only: bool = CLIPresenceFlag(["--collect-only"], default=False)

    ignore: list[Path] = CLIMultiOption(
        default_factory=list,
        token_emit=["--ignore={}"],
    )
    ignore_glob: list[str] = CLIMultiOption(
        default_factory=list,
        token_emit=["--ignore-glob={}"],
    )

    deselect: list[str] = CLIMultiOption(
        default_factory=list,
        token_emit=["--deselect={}"],
    )

    root_dir: Path | None = CLIOption(default=None, emit=["--rootdir={}"])
    conf_cut_dir: Path | None = CLIOption(default=None, emit=["--confcutdir={}"])

    import_mode: str | None = CLIOption(default=None, emit=["--import-mode={}"])

    base_temp: Path | None = CLIOption(default=None, emit=["--basetemp={}"])

    python_warnings: list[str] = CLIMultiOption(
        default_factory=list,
        token_emit=["-W{}"],
    )

    env: dict[str, str] = CLIKVOption(
        default_factory=dict,
        token_emit=["--env={key}={value}"],
    )

    add_opts: list[str] = CLIMultiOption(default_factory=list)

    @field_validator(
        "keyword",
        "marker",
        "capture",
        "show_capture",
        "junit_prefix",
        "traceback",
        "color",
        "import_mode",
        mode="before",
    )
    @classmethod
    def validate_nonempty_strings(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank string is not valid in `{cls.__name__}`.")
        return v

    @field_validator("paths", "ignore", mode="before")
    @classmethod
    def validate_nonempty_raw_path_strings(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(
                        f"Blank path is not valid in `{cls.__name__}` at index `{i}`."
                    )
        return v

    @field_validator("paths", mode="after")
    @classmethod
    def validate_path_exists(cls, v: list[Path]) -> list[Path]:
        for p in v:
            if not p.exists():
                raise ValueError(f"The source path, `{p}`, does not exist.")
        return v

    @field_validator(
        "junit_xml", "root_dir", "conf_cut_dir", "base_temp", mode="before"
    )
    @classmethod
    def validate_nonempty_path_strings(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"Blank path is not valid in `{cls.__name__}`.")
        return v

    @field_validator("max_fail", "durations", mode="after")
    @classmethod
    def validate_positive_int_options(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError(f"Value must be > 0 in `{cls.__name__}`, but got `{v}`.")
        return v

    @field_validator("durations_min", mode="after")
    @classmethod
    def validate_nonnegative_float_options(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if v < 0:
            raise ValueError(f"Value must be >= 0 in `{cls.__name__}`, but got `{v}`.")
        return v

    @field_validator(
        "ignore_glob",
        "deselect",
        "python_warnings",
        "add_opts",
        mode="before",
    )
    @classmethod
    def validate_string_sequences(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                if isinstance(item, str) and not item.strip():
                    raise ValueError(
                        f"Blank string is not valid in `{cls.__name__}` at index `{i}`."
                    )
        return v

    @field_validator("env", mode="after")
    @classmethod
    def validate_env_keys_and_values(cls, v: dict[str, str]) -> dict[str, str]:
        for key, value in v.items():
            if not key.strip():
                raise ValueError(
                    f"`env` in `{cls.__name__}` cannot contain blank keys."
                )
            if not value.strip():
                raise ValueError(
                    f"`env` in `{cls.__name__}` cannot contain blank values."
                )
        return v

    @model_validator(mode="after")
    def validate_verbosity(self) -> Self:
        if self.verbose and self.quiet:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `verbose` and `quiet` cannot both be enabled."
            )
        return self

    @model_validator(mode="after")
    def validate_stepwise(self) -> Self:
        if self.stepwise_skip and not self.stepwise:
            raise ValueError(
                f"In `{self.__class__.__name__}`, `stepwise_skip` requires `stepwise=True`."
            )
        return self


@register_typed_executable(["pytest"])
class PytestExecutable(TypedExecutable[PytestArgs]):
    install_executable = InstallScript(
        {
            is_posix: PlatformInstallScript(
                executable=BashExecutable(),
                args=BashScriptArgs(
                    script=Path(__file__).parent
                    / "install_scripts/posix/install_pytest.sh"
                ),
                install_location=Path.cwd() / ".pytest/bin/pytest",
            )
        }
    )
