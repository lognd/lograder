# type: ignore

from __future__ import annotations

from pathlib import Path

from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.registry.cmake import (
    CMakeBuildArgs,
    CMakeConfigureArgs,
    CMakeExecutable,
)


def test_cmake_configure_args_defaults() -> None:
    args = CMakeConfigureArgs()
    toks = ["-S .", "-B build"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str
    assert set(args.emit()) == {"-S", ".", "-B", "build"}


def test_cmake_configure_args_custom_values() -> None:
    args = CMakeConfigureArgs(
        source_dir=Path("src"),
        build_dir=Path("out"),
    )
    toks = ["-S src", "-B out"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str
    assert set(args.emit()) == {"-S", "src", "-B", "out"}


def test_cmake_build_args_defaults() -> None:
    args = CMakeBuildArgs()
    assert args.emit() == ["--build", "build"]


def test_cmake_build_args_with_target() -> None:
    args = CMakeBuildArgs(build_dir=Path("out"), target=Path("install"))
    toks = ["--build out", "--target install"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str
    assert set(args.emit()) == {"--build", "out", "--target", "install"}


def test_cmake_build_args_omits_missing_target() -> None:
    args = CMakeBuildArgs(build_dir=Path("out"), target=CLI_ARG_MISSING())
    assert args.emit() == ["--build", "out"]


def test_cmake_executable_registered_command() -> None:
    assert CMakeExecutable.executable is not None
    assert CMakeExecutable.executable.command == ["cmake"]
