from __future__ import annotations

from pathlib import Path
from typing import Literal

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

from lograder.pipeline.types.executable.cli_args import CLIArgs, CLIField


class LanguageStandard(StrEnum):
    C89 = "c89"
    C99 = "c99"
    C11 = "c11"
    C17 = "c17"
    C23 = "c23"

    CXX98 = "c++98"
    CXX03 = "c++03"
    CXX11 = "c++11"
    CXX14 = "c++14"
    CXX17 = "c++17"
    CXX20 = "c++20"
    CXX23 = "c++23"
    CXX26 = "c++26"


class OptimizationLevel(StrEnum):
    O0 = "0"
    O1 = "1"
    O2 = "2"
    O3 = "3"
    OS = "s"
    OFAST = "fast"
    OG = "g"
    OZ = "z"  # clang supports this; gcc may not


class DebugLevel(StrEnum):
    G = ""
    G1 = "1"
    G2 = "2"
    G3 = "3"


class WarningLevel(StrEnum):
    ALL = "all"
    EXTRA = "extra"
    PEDANTIC = "pedantic"


class GCCLikeCompilerArgs(CLIArgs):
    """
    Shared for gcc/g++/clang/clang++.

    Supports:
        compile-only, preprocess-only, assemble-only, link,
        include dirs, defines, warnings, optimization, debug,
        library search paths, libraries, and raw passthrough.
    """

    # Inputs / outputs
    inputs: list[Path | str] = CLIField(default_factory=list, positional=True)
    output: Path | str | None = CLIField(default=None, flag="-o")

    # Stages
    compile_only: bool = CLIField(default=False, flag="-c")
    preprocess_only: bool = CLIField(default=False, flag="-E")
    assemble_only: bool = CLIField(default=False, flag="-S")
    emit_llvm: bool = CLIField(default=False, flag="-emit-llvm")  # mostly clang

    # Language / mode
    language: str | None = CLIField(default=None, flag="-x")
    standard: LanguageStandard | str | None = CLIField(
        default=None, flag="-std", compact=True
    )

    # Warnings
    wall: bool = CLIField(default=False, flag="-Wall")
    wextra: bool = CLIField(default=False, flag="-Wextra")
    wpedantic: bool = CLIField(default=False, flag="-Wpedantic")
    werror: bool = CLIField(default=False, flag="-Werror")
    suppress_warnings: bool = CLIField(default=False, flag="-w")

    # Targeted warnings, e.g. {"unused-parameter": False, "shadow": True}
    warnings: dict[str, bool | str | int] = CLIField(
        default_factory=dict,
        exclude=True,
    )

    # Optimization / debug
    optimization: OptimizationLevel | str | None = CLIField(
        default=None, flag="-O", compact=True
    )
    debug: bool = CLIField(default=False, flag="-g")
    debug_level: DebugLevel | str | None = CLIField(default=None, exclude=True)

    # Preprocessor
    defines: dict[str, str | int | float | bool | None] = CLIField(
        default_factory=dict,
        exclude=True,
    )
    undefines: list[str] = CLIField(default_factory=list, flag="-U", repeat=True)
    include_dirs: list[Path | str] = CLIField(
        default_factory=list, flag="-I", repeat=True
    )
    system_include_dirs: list[Path | str] = CLIField(
        default_factory=list, flag="-isystem", repeat=True
    )
    include_headers: list[Path | str] = CLIField(
        default_factory=list, flag="-include", repeat=True
    )

    # Dependency generation
    md: bool = CLIField(default=False, flag="-MD")
    mmd: bool = CLIField(default=False, flag="-MMD")
    mf: Path | str | None = CLIField(default=None, flag="-MF")
    mt: str | None = CLIField(default=None, flag="-MT")
    mp: bool = CLIField(default=False, flag="-MP")

    # Codegen / PIC
    pic: bool = CLIField(default=False, flag="-fPIC")
    pie: bool = CLIField(default=False, flag="-fPIE")
    shared: bool = CLIField(default=False, flag="-shared")
    static: bool = CLIField(default=False, flag="-static")

    # Libraries / link
    library_dirs: list[Path | str] = CLIField(
        default_factory=list, flag="-L", repeat=True
    )
    libraries: list[str] = CLIField(default_factory=list, exclude=True)
    linker_options: list[str] = CLIField(default_factory=list, exclude=True)

    # Machine / arch / target
    machine: str | None = CLIField(default=None, flag="-m", compact=True)  # e.g. 64
    target: str | None = CLIField(default=None, flag="--target")

    # Misc
    pthread: bool = CLIField(default=False, flag="-pthread")
    pipe: bool = CLIField(default=False, flag="-pipe")
    verbose: bool = CLIField(default=False, flag="-v")

    # Escape hatch
    extra: list[str] = CLIField(default_factory=list, positional=True)

    def to_arguments(self) -> list[str]:
        args = []

        # Standard modeled fields first.
        if self.output is not None:
            args.extend(["-o", str(self.output)])

        if self.compile_only:
            args.append("-c")
        if self.preprocess_only:
            args.append("-E")
        if self.assemble_only:
            args.append("-S")
        if self.emit_llvm:
            args.append("-emit-llvm")

        if self.language is not None:
            args.extend(["-x", str(self.language)])
        if self.standard is not None:
            args.append(f"-std={self.standard}")

        if self.wall:
            args.append("-Wall")
        if self.wextra:
            args.append("-Wextra")
        if self.wpedantic:
            args.append("-Wpedantic")
        if self.werror:
            args.append("-Werror")
        if self.suppress_warnings:
            args.append("-w")

        for name, value in self.warnings.items():
            if value is True:
                args.append(f"-W{name}")
            elif value is False:
                args.append(f"-Wno-{name}")
            else:
                args.append(f"-W{name}={value}")

        if self.optimization is not None:
            args.append(f"-O{self.optimization}")

        if self.debug_level is not None:
            args.append(f"-g{self.debug_level}")
        elif self.debug:
            args.append("-g")

        for key, value in self.defines.items():
            if value is None:
                args.append(f"-D{key}")
            elif value is True:
                args.append(f"-D{key}=1")
            elif value is False:
                args.append(f"-D{key}=0")
            else:
                args.append(f"-D{key}={value}")

        for name in self.undefines:
            args.extend(["-U", name])

        for path in self.include_dirs:
            args.extend(["-I", str(path)])

        for path in self.system_include_dirs:
            args.extend(["-isystem", str(path)])

        for header in self.include_headers:
            args.extend(["-include", str(header)])

        if self.md:
            args.append("-MD")
        if self.mmd:
            args.append("-MMD")
        if self.mf is not None:
            args.extend(["-MF", str(self.mf)])
        if self.mt is not None:
            args.extend(["-MT", self.mt])
        if self.mp:
            args.append("-MP")

        if self.pic:
            args.append("-fPIC")
        if self.pie:
            args.append("-fPIE")
        if self.shared:
            args.append("-shared")
        if self.static:
            args.append("-static")

        for path in self.library_dirs:
            args.extend(["-L", str(path)])

        for lib in self.libraries:
            args.append(f"-l{lib}")

        for opt in self.linker_options:
            args.append(f"-Wl,{opt}")

        if self.machine is not None:
            args.append(f"-m{self.machine}")
        if self.target is not None:
            args.extend(["--target", self.target])

        if self.pthread:
            args.append("-pthread")
        if self.pipe:
            args.append("-pipe")
        if self.verbose:
            args.append("-v")

        args.extend(str(x) for x in self.inputs)
        args.extend(str(x) for x in self.extra)
        return args


class MSVCWarningLevel(StrEnum):
    W0 = "0"
    W1 = "1"
    W2 = "2"
    W3 = "3"
    W4 = "4"
    WX = "X"


class RuntimeLibrary(StrEnum):
    MD = "MD"
    MDd = "MDd"
    MT = "MT"
    MTd = "MTd"
    LD = "LD"
    LDd = "LDd"


class MSVCCompilerArgs(CLIArgs):
    """
    Models cl.exe.

    Notes:
    - cl uses /flag style.
    - linking can be done via cl, with linker args after /link.
    """

    inputs: list[Path | str] = CLIField(default_factory=list, positional=True)

    # Output / stages
    compile_only: bool = CLIField(default=False, flag="/c")
    preprocess_only: bool = CLIField(default=False, flag="/EP")
    output_obj: Path | str | None = CLIField(default=None, exclude=True)
    output_exe: Path | str | None = CLIField(default=None, exclude=True)

    # Language / conformance
    std: str | None = CLIField(default=None, exclude=True)  # e.g. c++20, c17
    permissive_minus: bool = CLIField(default=False, flag="/permissive-")
    experimental_modules: bool = CLIField(default=False, flag="/experimental:module")

    # Warnings / debug / optimization
    warning_level: MSVCWarningLevel | str | None = CLIField(default=None, exclude=True)
    wx: bool = CLIField(default=False, flag="/WX")
    debug: bool = CLIField(default=False, flag="/Zi")
    optimize: Literal["Od", "O1", "O2", "Ox"] | None = CLIField(
        default=None, exclude=True
    )

    # Runtime / EH / RTTI
    runtime_library: RuntimeLibrary | str | None = CLIField(default=None, exclude=True)
    exceptions: bool = CLIField(default=False, flag="/EHsc")
    rtti: bool | None = CLIField(
        default=None, exclude=True
    )  # True => /GR, False => /GR-

    # Preprocessor / includes
    defines: dict[str, str | int | float | bool | None] = CLIField(
        default_factory=dict, exclude=True
    )
    undefines: list[str] = CLIField(default_factory=list, exclude=True)
    include_dirs: list[Path | str] = CLIField(default_factory=list, exclude=True)

    # Link
    link: bool = CLIField(default=True, exclude=True)
    library_dirs: list[Path | str] = CLIField(default_factory=list, exclude=True)
    libraries: list[str | Path] = CLIField(default_factory=list, exclude=True)
    linker_options: list[str] = CLIField(default_factory=list, exclude=True)

    # Misc
    nologo: bool = CLIField(default=True, flag="/nologo")
    utf8: bool = CLIField(default=False, flag="/utf-8")
    bigobj: bool = CLIField(default=False, flag="/bigobj")

    extra: list[str] = CLIField(default_factory=list, positional=True)

    def to_arguments(self) -> list[str]:
        args = []

        if self.nologo:
            args.append("/nologo")
        if self.compile_only:
            args.append("/c")
        if self.preprocess_only:
            args.append("/EP")

        if self.output_obj is not None:
            args.append(f"/Fo{self.output_obj}")
        if self.output_exe is not None:
            args.append(f"/Fe{self.output_exe}")

        if self.std is not None:
            args.append(f"/std:{self.std}")
        if self.permissive_minus:
            args.append("/permissive-")
        if self.experimental_modules:
            args.append("/experimental:module")

        if self.warning_level is not None:
            args.append(f"/W{self.warning_level}")
        if self.wx:
            args.append("/WX")
        if self.debug:
            args.append("/Zi")
        if self.optimize is not None:
            args.append(f"/{self.optimize}")

        if self.runtime_library is not None:
            args.append(f"/{self.runtime_library}")
        if self.exceptions:
            args.append("/EHsc")
        if self.rtti is True:
            args.append("/GR")
        elif self.rtti is False:
            args.append("/GR-")

        for key, value in self.defines.items():
            if value is None:
                args.append(f"/D{key}")
            elif value is True:
                args.append(f"/D{key}=1")
            elif value is False:
                args.append(f"/D{key}=0")
            else:
                args.append(f"/D{key}={value}")

        for name in self.undefines:
            args.append(f"/U{name}")

        for path in self.include_dirs:
            args.append(f"/I{path}")

        if self.utf8:
            args.append("/utf-8")
        if self.bigobj:
            args.append("/bigobj")

        args.extend(str(x) for x in self.inputs)
        args.extend(str(x) for x in self.extra)

        if self.link:
            link_args = []

            for path in self.library_dirs:
                link_args.append(f"/LIBPATH:{path}")

            for lib in self.libraries:
                link_args.append(str(lib))

            link_args.extend(self.linker_options)

            if link_args:
                args.append("/link")
                args.extend(link_args)

        return args
