from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CxxConfig(BaseModel):
    """Base configuration for all C++ builds."""

    compiler: str = Field(default="g++", description="C++ compiler executable.")
    standard: str = Field(
        default="c++20", description="C++ standard (e.g. c++17, c++20)."
    )

    warnings: List[str] = Field(
        default_factory=lambda: [
            "-Wall",
            "-Wextra",
            "-Wshadow",
            "-Wconversion",
            "-Wsign-conversion",
            "-Wnull-dereference",
            "-Werror=return-type",
        ],
        description="Common warning and safety flags.",
    )

    optimization: str = Field(default="-O2", description="Optimization level.")
    defines: List[str] = Field(
        default_factory=list, description="Preprocessor defines."
    )
    include_dirs: List[Path] = Field(
        default_factory=list, description="Include directories."
    )
    link_flags: List[str] = Field(
        default_factory=list, description="Additional linker flags."
    )
    extra_flags: List[str] = Field(
        default_factory=list, description="Additional compiler flags."
    )

    output_dir: Optional[Path] = Field(
        default=None, description="Output directory for binaries."
    )
    jobs: int = Field(default=4, ge=1, description="Parallel build jobs.")

    @property
    def base_flags(self) -> List[str]:
        """Compose all standard + user flags into a single flat list."""
        return [
            f"-std={self.standard}",
            self.optimization,
            *self.warnings,
            *[f"-D{d}" for d in self.defines],
            *[f"-I{str(p)}" for p in self.include_dirs],
            *self.extra_flags,
        ]

    @property
    def link_args(self) -> List[str]:
        return self.link_flags


class CMakeConfig(CxxConfig):
    """CMake-specific build configuration."""

    generator: str = Field(default="Unix Makefiles", description="CMake generator.")
    build_type: str = Field(default="Release", description="CMake build type.")
    parallel: int = Field(default=4, ge=1, description="Parallel jobs for build step.")
    cmake_executable: str = Field(
        default="cmake", description="Path to cmake executable."
    )
    build_target: Optional[str] = Field(
        default=None, description="Specific target to build."
    )
    install: bool = Field(
        default=False, description="Run 'cmake --install' after build."
    )
    clean_first: bool = Field(default=False, description="Run clean before building.")
    extra_cmake_flags: List[str] = Field(
        default_factory=list, description="Additional cmake -D flags."
    )

    def to_cmake_args(self) -> List[str]:
        args = [
            f"-DCMAKE_CXX_STANDARD={self.standard[-2:]}",  # extracts e.g. 20 from "c++20"
            f"-DCMAKE_BUILD_TYPE={self.build_type}",
            f"-DCMAKE_CXX_COMPILER={self.compiler}",
            *[f"-D{d}" for d in self.defines],
            *self.extra_cmake_flags,
        ]
        return args


class MakeConfig(CxxConfig):
    """Makefile-based build configuration."""

    target: Optional[str] = Field(
        default=None, description="Make target (e.g., all, install, clean)."
    )
    directory: Optional[Path] = Field(
        default=None, description="Directory to run make in."
    )
    jobs: int = Field(default=4, ge=1, description="Number of parallel jobs (-j).")
    variables: Dict[str, str] = Field(
        default_factory=dict, description="Make variables, e.g. CC=g++."
    )
    keep_going: bool = Field(default=True, description="Continue past errors (-k).")
    dry_run: bool = Field(
        default=False, description="Print commands without executing (-n)."
    )
    clean_before: bool = Field(
        default=False, description="Run 'make clean' before build."
    )

    def to_make_args(self) -> List[str]:
        args = []
        if self.directory:
            args += ["-C", str(self.directory)]
        args += [f"-j{self.jobs}"]
        if self.keep_going:
            args.append("-k")
        if self.dry_run:
            args.append("-n")
        for k, v in self.variables.items():
            args.append(f"{k}={v}")
        if self.target:
            args.append(self.target)
        return args
