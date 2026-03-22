from __future__ import annotations

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
from pathlib import Path
from typing import Literal

from lograder.pipeline.types.executable.cli_args import CLIArgs, CLIField


class CMakeBuildType(StrEnum):
    DEBUG = "Debug"
    RELEASE = "Release"
    REL_WITH_DEB_INFO = "RelWithDebInfo"
    MIN_SIZE_REL = "MinSizeRel"


class CMakeGenerator(StrEnum):
    NINJA = "Ninja"
    UNIX_MAKEFILES = "Unix Makefiles"
    NMAKE_MAKEFILES = "NMake Makefiles"
    MINGW_MAKEFILES = "MinGW Makefiles"
    VISUAL_STUDIO_17_2022 = "Visual Studio 17 2022"


class CMakeConfigureArgs(CLIArgs):
    """
    Models:
        cmake -S <source> -B <build> [options...]
    """

    source_dir: Path = CLIField(default=Path("."), flag="-S")
    build_dir: Path = CLIField(default=Path("build"), flag="-B")

    generator: CMakeGenerator | str | None = CLIField(default=None, flag="-G")
    toolchain_file: Path | None = CLIField(
        default=None, flag="-DCMAKE_TOOLCHAIN_FILE", compact=True
    )
    build_type: CMakeBuildType | str | None = CLIField(
        default=None, flag="-DCMAKE_BUILD_TYPE", compact=True
    )
    install_prefix: Path | None = CLIField(
        default=None, flag="-DCMAKE_INSTALL_PREFIX", compact=True
    )

    export_compile_commands: bool | None = CLIField(
        default=None,
        flag="-DCMAKE_EXPORT_COMPILE_COMMANDS",
        bool_style="explicit",
        true_value="ON",
        false_value="OFF",
        compact=True,
    )

    warnings_as_errors: bool | None = CLIField(
        default=None,
        flag="-DCMAKE_COMPILE_WARNING_AS_ERROR",
        bool_style="explicit",
        true_value="ON",
        false_value="OFF",
        compact=True,
    )

    shared_libs: bool | None = CLIField(
        default=None,
        flag="-DBUILD_SHARED_LIBS",
        bool_style="explicit",
        true_value="ON",
        false_value="OFF",
        compact=True,
    )

    defines: dict[str, str | int | float | bool] = CLIField(
        default_factory=dict,
        flag="-D",
        mapping="key_value",
        kv_sep="=",
        repeat=True,
        compact=True,
    )

    unset_cache: list[str] = CLIField(default_factory=list, flag="-U", repeat=True)
    preset: str | None = CLIField(default=None, flag="--preset")
    fresh: bool = CLIField(default=False, flag="--fresh")
    trace: bool = CLIField(default=False, flag="--trace")
    trace_expand: bool = CLIField(default=False, flag="--trace-expand")
    debug_find: bool = CLIField(default=False, flag="--debug-find")
    log_level: (
        Literal["ERROR", "WARNING", "NOTICE", "STATUS", "VERBOSE", "DEBUG", "TRACE"]
        | None
    ) = CLIField(
        default=None,
        flag="--log-level",
    )

    # Raw passthrough for edge cases you do not want to model yet.
    extra: list[str] = CLIField(default_factory=list, positional=True)


class CMakeBuildArgs(CLIArgs):
    """
    Models:
        cmake --build <build-dir> [options...]
    """

    build_dir: Path = CLIField(default=Path("build"), positional=True)

    target: list[str] = CLIField(default_factory=list, flag="--target", repeat=True)
    config: str | None = CLIField(default=None, flag="--config")
    parallel: int | None = CLIField(default=None, flag="--parallel")
    clean_first: bool = CLIField(default=False, flag="--clean-first")
    verbose: bool = CLIField(default=False, flag="--verbose")

    # Arguments after `--` passed through to native build tool.
    native_args: list[str] = CLIField(
        default_factory=list, positional=True, exclude=True
    )

    def to_arguments(self) -> list[str]:
        args = ["--build", *super().to_arguments()]
        if self.native_args:
            args.extend(["--", *self.native_args])
        return args


class MakeArgs(CLIArgs):
    """
    Models:
        make [targets...] [options...]
    """

    file: Path | None = CLIField(default=None, flag="-f")
    directory: Path | None = CLIField(default=None, flag="-C")
    jobs: int | None = CLIField(default=None, flag="-j", compact=True)
    keep_going: bool = CLIField(default=False, flag="-k")
    silent: bool = CLIField(default=False, flag="-s")
    always_make: bool = CLIField(default=False, flag="-B")
    dry_run: bool = CLIField(default=False, flag="-n")
    touch: bool = CLIField(default=False, flag="-t")
    print_directory: bool = CLIField(default=False, flag="-w")
    no_print_directory: bool = CLIField(default=False, flag="--no-print-directory")

    variables: dict[str, str | int | float | bool] = CLIField(
        default_factory=dict,
        positional=True,
    )

    targets: list[str] = CLIField(default_factory=list, positional=True)

    def to_arguments(self) -> list[str]:
        args = super().to_arguments()

        # Convert positional dict entries from {'CC': 'clang'} to ['CC=clang'].
        rendered_vars: list[str] = []
        for k, v in self.variables.items():
            rendered_vars.append(f"{k}={self._render_scalar(v)}")

        # Rebuild with variables before targets for conventional make usage.
        out: list[str] = []

        for name, field in self.__class__.model_fields.items():
            if name in {"variables", "targets"}:
                continue

            value = getattr(self, name)
            if value is None:
                continue

            cli_meta = (field.json_schema_extra or {}).get("cli", {})
            if cli_meta.get("exclude", False):
                continue

            if cli_meta.get("positional", False):
                out.extend(self._flatten_value(value, cli_meta))
                continue

            flag = self._field_flag(name, field, cli_meta)
            out.extend(self._emit_option(name, flag, value, cli_meta))

        out.extend(rendered_vars)
        out.extend(self.targets)
        return out


class PyProjectBuildArgs(CLIArgs):
    """
    Models:
        python -m build [options...]
    Requires package `build`.
    """

    source_dir: Path = CLIField(default=Path("."), positional=True)
    outdir: Path | None = CLIField(default=None, flag="--outdir")
    sdist: bool = CLIField(default=False, flag="--sdist")
    wheel: bool = CLIField(default=False, flag="--wheel")
    no_isolation: bool = CLIField(default=False, flag="--no-isolation")
    skip_dependency_check: bool = CLIField(
        default=False, flag="--skip-dependency-check"
    )
    config_settings: dict[str, str | int | float | bool] = CLIField(
        default_factory=dict,
        flag="-C",
        mapping="key_value",
        kv_sep="=",
        repeat=True,
        compact=False,
    )
    installer: str | None = CLIField(default=None, flag="--installer")
    extra: list[str] = CLIField(default_factory=list, positional=True)


class PyProjectInstallArgs(CLIArgs):
    """
    Models:
        python -m pip install [options...] <path-or-wheel>
    """

    requirement: str | Path = CLIField(default=Path("."), positional=True)

    editable: bool = CLIField(default=False, flag="-e")
    upgrade: bool = CLIField(default=False, flag="-U")
    no_deps: bool = CLIField(default=False, flag="--no-deps")
    force_reinstall: bool = CLIField(default=False, flag="--force-reinstall")
    no_build_isolation: bool = CLIField(default=False, flag="--no-build-isolation")
    index_url: str | None = CLIField(default=None, flag="--index-url")
    extra_index_url: list[str] = CLIField(
        default_factory=list, flag="--extra-index-url", repeat=True
    )
    find_links: list[str | Path] = CLIField(
        default_factory=list, flag="--find-links", repeat=True
    )
    config_settings: dict[str, str | int | float | bool] = CLIField(
        default_factory=dict,
        flag="--config-settings",
        mapping="key_value",
        kv_sep="=",
        repeat=True,
    )
    extra: list[str] = CLIField(default_factory=list, positional=True)
