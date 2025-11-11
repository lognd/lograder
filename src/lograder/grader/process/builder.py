"""builder.py

Implements specialized process builders for compiling and building C++ projects.

This module defines three file-based build systems:
    - `CxxSourceBuilder`: Direct compilation using g++ or another compiler.
    - `CMakeBuilder`: Multi-step CMake build pipeline (configure, build, install).
    - `MakefileBuilder`: Traditional Makefile build process with variable overrides.

Each builder inherits from `FileProcess`, integrates with a configuration
object (`CxxConfig`, `CMakeConfig`, `MakeConfig`), and produces a list of
`OrderedCommand` objects describing the full build pipeline.
"""

from pathlib import Path
from typing import List, final

from ...data.cxx import CMakeConfig, CxxConfig, MakeConfig
from .process import FileProcess, OrderedCommand


@final
class CxxSourceBuilder(FileProcess):
    """
    Direct C++ compilation using g++ or another compiler specified in CxxConfig.

    This builder executes a single-step compilation process, invoking the
    compiler directly over all discovered C++ source files under the project
    root directory. It automatically includes all base flags, optimization
    options, defines, include directories, and linker arguments provided by
    the `CxxConfig`.

    Attributes:
        config (CxxConfig): The configuration describing compiler flags,
            include paths, and other C++ build options.
    """

    id: str = "cxx-project"

    def __init__(self, root: Path, config: CxxConfig):
        """
        Initialize the C++ source builder.

        Args:
            root: Root directory containing the C++ source files.
            config: Configuration defining compiler, flags, and output options.
        """
        super().__init__(root)
        self.config = config

    @property
    def commands(self) -> List[OrderedCommand]:
        """
        Construct the compilation command.

        Returns:
            A list containing a single `OrderedCommand` describing the
            full g++ (or configured compiler) invocation, including
            standard flags, defines, and output target path.
        """
        cfg = self.config
        cmd = [
            cfg.compiler,
            *cfg.base_flags,
            "${cxx_files}",
            "-o",
            "${executable}",
            *cfg.link_args,
        ]
        return [OrderedCommand(order=0, command=cmd)]


@final
class CMakeBuilder(FileProcess):
    """
    Standard CMake build pipeline.

    This builder automates multi-phase CMake workflows, including configuration,
    building, cleaning, and optional installation. It uses a temporary build
    directory to isolate artifacts and integrates all settings defined in the
    `CMakeConfig`.

    Steps:
        0. (optional) Clean previous build artifacts.
        1. Configure project and generate build files.
        2. Build the project in parallel.
        3. (optional) Install compiled artifacts.

    Attributes:
        config (CMakeConfig): Configuration defining generator, compiler, and
            custom CMake flags.
    """

    id: str = "cmake-project"

    def __init__(self, root: Path, config: CMakeConfig):
        """
        Initialize the CMake builder.

        Args:
            root: Root project directory containing CMakeLists.txt.
            config: Configuration describing CMake behavior, build type,
                generator, and installation preferences.
        """
        super().__init__(root)
        self.config = config

    @property
    def commands(self) -> List[OrderedCommand]:
        """
        Generate an ordered list of CMake build commands.

        Returns:
            A sequence of `OrderedCommand` objects representing:
                0. Clean (if requested)
                1. Configuration (cmake -S ... -B ...)
                2. Build (cmake --build ...)
                3. Install (if enabled)
        """
        cfg = self.config
        cmds: List[OrderedCommand] = []

        # (0) Clean build directory if requested
        if cfg.clean_first:
            cmds.append(
                OrderedCommand(
                    order=0,
                    command=[
                        cfg.cmake_executable,
                        "--build",
                        "${temp_folder}",
                        "--target",
                        "clean",
                    ],
                )
            )

        # (1) Configure
        cmds.append(
            OrderedCommand(
                order=1,
                command=[
                    cfg.cmake_executable,
                    "-S",
                    "${root}",
                    "-B",
                    "${temp_folder}",
                    "-G",
                    cfg.generator,
                    *cfg.to_cmake_args(),
                ],
            )
        )

        # (2) Build
        build_cmd = [
            cfg.cmake_executable,
            "--build",
            "${temp_folder}",
            "--parallel",
            str(cfg.parallel),
        ]
        if cfg.build_target:
            build_cmd += ["--target", cfg.build_target]
        cmds.append(OrderedCommand(order=2, command=build_cmd))

        # (3) Install (optional)
        if cfg.install:
            cmds.append(
                OrderedCommand(
                    order=3,
                    command=[cfg.cmake_executable, "--install", "${temp_folder}"],
                )
            )

        return cmds


@final
class MakefileBuilder(FileProcess):
    """
    Makefile build process using MakeConfig.

    This builder runs the traditional `make` command with full support for:
        - Pre-build cleaning (`make clean`)
        - Parallel job control (`-jN`)
        - Custom target selection (e.g., `install`, `all`)
        - Variable substitution (`CC=g++`, `CXXFLAGS=-O2`, etc.)
        - Dry-run and keep-going modes for error-tolerant builds

    Attributes:
        config (MakeConfig): The configuration defining make behavior,
            variables, and build options.
    """

    id = "make-project"

    def __init__(self, root: Path, config: MakeConfig):
        """
        Initialize the Makefile builder.

        Args:
            root: Project directory containing a Makefile.
            config: Configuration specifying make parameters,
                targets, and environment overrides.
        """
        super().__init__(root)
        self.config = config

    @property
    def commands(self) -> List[OrderedCommand]:
        """
        Generate a sequence of Makefile build commands.

        Returns:
            A list of `OrderedCommand` objects representing:
                0. `make clean` (if requested)
                1. Main make invocation with user-defined arguments.
        """
        cfg = self.config
        cmds: List[OrderedCommand] = []

        # (0) Clean before build if requested
        if cfg.clean_before:
            cmds.append(
                OrderedCommand(
                    order=0,
                    command=["make", "-C", "${root}", "clean"],
                )
            )

        # (1) Build phase
        make_cmd = ["make", *cfg.to_make_args()]
        cmds.append(OrderedCommand(order=1, command=make_cmd))

        return cmds
