# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.registry.cmake import (
    CMakeBuildArgs,
    CMakeConfigureArgs,
    CMakeExecutable,
    CMakeInstallArgs,
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


def test_cmake_configure_args_full_emit() -> None:
    args = CMakeConfigureArgs(
        source_dir=Path("src"),
        build_dir=Path("out"),
        generator="Ninja",
        toolchain_file=Path("cmake/toolchain.cmake"),
        install_prefix=Path("dist"),
        build_type="Debug",
        warnings_as_errors=True,
        warn_uninitialized=True,
        warn_unused_vars=True,
        fresh=True,
        trace=True,
        trace_expand=True,
        debug_output=True,
        debug_find=True,
        cache_entries={
            "CMAKE_EXPORT_COMPILE_COMMANDS": True,
            "BUILD_SHARED_LIBS": False,
            "MY_LEVEL": 3,
            "MY_STRING": "abc",
        },
    )

    toks = [
        "-S src",
        "-B out",
        "-G Ninja",
        "-DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake",
        "-DCMAKE_INSTALL_PREFIX=dist",
        "-DCMAKE_BUILD_TYPE=Debug",
        "-Werror=dev",
        "--warn-uninitialized",
        "--warn-unused-vars",
        "--fresh",
        "--trace",
        "--trace-expand",
        "--debug-output",
        "--debug-find",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DMY_LEVEL=3",
        "-DMY_STRING=abc",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = set(args.emit())
    assert "-S" in emitted
    assert "src" in emitted
    assert "-B" in emitted
    assert "out" in emitted
    assert "-G" in emitted
    assert "Ninja" in emitted
    assert "-DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake" in emitted
    assert "-DCMAKE_INSTALL_PREFIX=dist" in emitted
    assert "-DCMAKE_BUILD_TYPE=Debug" in emitted
    assert "-Werror=dev" in emitted
    assert "--warn-uninitialized" in emitted
    assert "--warn-unused-vars" in emitted
    assert "--fresh" in emitted
    assert "--trace" in emitted
    assert "--trace-expand" in emitted
    assert "--debug-output" in emitted
    assert "--debug-find" in emitted
    assert "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON" in emitted
    assert "-DBUILD_SHARED_LIBS=OFF" in emitted
    assert "-DMY_LEVEL=3" in emitted
    assert "-DMY_STRING=abc" in emitted


def test_cmake_configure_args_with_preset() -> None:
    args = CMakeConfigureArgs(
        preset="dev",
    )
    toks = ["-S .", "-B build", "--preset dev"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str
    assert "--preset" in args.emit()
    assert "dev" in args.emit()


def test_cmake_build_args_defaults() -> None:
    args = CMakeBuildArgs()
    assert args.emit() == ["--build", "build"]


def test_cmake_build_args_with_target() -> None:
    args = CMakeBuildArgs(build_dir=Path("out"), target="install")
    toks = ["--build out", "--target install"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str
    assert set(args.emit()) == {"--build", "out", "--target", "install"}


def test_cmake_build_args_full_emit() -> None:
    args = CMakeBuildArgs(
        build_dir=Path("out"),
        target="my_target",
        config="Release",
        parallel=8,
        clean_first=True,
        verbose=True,
        native_args=["-j", "8", "VERBOSE=1"],
    )

    toks = [
        "--build out",
        "--target my_target",
        "--config Release",
        "--parallel 8",
        "--clean-first",
        "--verbose",
        "-- -j 8 VERBOSE=1",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == [
        "--build",
        "out",
        "--target",
        "my_target",
        "--config",
        "Release",
        "--parallel",
        "8",
        "--clean-first",
        "--verbose",
        "--",
        "-j",
        "8",
        "VERBOSE=1",
    ]


def test_cmake_build_args_omits_missing_optional_fields() -> None:
    args = CMakeBuildArgs(
        build_dir=Path("out"),
        target=CLI_ARG_MISSING(),
        config=CLI_ARG_MISSING(),
        parallel=CLI_ARG_MISSING(),
    )
    assert args.emit() == ["--build", "out"]


def test_cmake_build_args_with_only_native_args() -> None:
    args = CMakeBuildArgs(
        build_dir=Path("out"),
        native_args=["-k"],
    )
    assert args.emit() == ["--build", "out", "--", "-k"]


def test_cmake_install_args_defaults() -> None:
    args = CMakeInstallArgs()
    assert args.emit() == ["--install", "build"]


def test_cmake_install_args_full_emit() -> None:
    args = CMakeInstallArgs(
        build_dir=Path("out"),
        config="Debug",
        component="runtime",
        prefix=Path("dist"),
        strip=True,
    )

    toks = [
        "--install out",
        "--config Debug",
        "--component runtime",
        "--prefix dist",
        "--strip",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == [
        "--install",
        "out",
        "--config",
        "Debug",
        "--component",
        "runtime",
        "--prefix",
        "dist",
        "--strip",
    ]


def test_cmake_install_args_omits_missing_optional_fields() -> None:
    args = CMakeInstallArgs(
        build_dir=Path("out"),
        config=CLI_ARG_MISSING(),
        component=CLI_ARG_MISSING(),
        prefix=CLI_ARG_MISSING(),
        strip=False,
    )
    assert args.emit() == ["--install", "out"]


def test_cmake_executable_registered_command() -> None:
    assert CMakeExecutable.executable is not None
    assert CMakeExecutable.executable.command == ["cmake"]


def test_cmake_configure_rejects_blank_generator() -> None:
    with pytest.raises(ValidationError):
        CMakeConfigureArgs(generator="   ")


def test_cmake_configure_rejects_blank_build_type() -> None:
    with pytest.raises(ValidationError):
        CMakeConfigureArgs(build_type="")


def test_cmake_configure_rejects_blank_preset() -> None:
    with pytest.raises(ValidationError):
        CMakeConfigureArgs(preset=" ")


def test_cmake_configure_rejects_blank_cache_key() -> None:
    with pytest.raises(ValidationError):
        CMakeConfigureArgs(cache_entries={"": True})


def test_cmake_configure_rejects_cache_key_containing_equals() -> None:
    with pytest.raises(ValidationError):
        CMakeConfigureArgs(cache_entries={"BAD=KEY": True})


def test_cmake_configure_rejects_preset_with_explicit_source_override() -> None:
    with pytest.raises(ValidationError):
        CMakeConfigureArgs(
            preset="dev",
            source_dir=Path("src"),
        )


def test_cmake_configure_rejects_preset_with_explicit_build_override() -> None:
    with pytest.raises(ValidationError):
        CMakeConfigureArgs(
            preset="dev",
            build_dir=Path("out"),
        )


def test_cmake_configure_rejects_source_dir_that_is_a_file(tmp_path: Path) -> None:
    source_file = tmp_path / "CMakeLists.txt"
    source_file.write_text("cmake_minimum_required(VERSION 3.20)\n")

    with pytest.raises(ValidationError):
        CMakeConfigureArgs(source_dir=source_file)


def test_cmake_configure_rejects_build_dir_that_is_a_file(tmp_path: Path) -> None:
    build_file = tmp_path / "build"
    build_file.write_text("not a directory\n")

    with pytest.raises(ValidationError):
        CMakeConfigureArgs(build_dir=build_file)


def test_cmake_configure_rejects_toolchain_file_that_is_directory(
    tmp_path: Path,
) -> None:
    toolchain_dir = tmp_path / "toolchain_dir"
    toolchain_dir.mkdir()

    with pytest.raises(ValidationError):
        CMakeConfigureArgs(toolchain_file=toolchain_dir)


def test_cmake_build_rejects_blank_target() -> None:
    with pytest.raises(ValidationError):
        CMakeBuildArgs(target=" ")


def test_cmake_build_rejects_blank_config() -> None:
    with pytest.raises(ValidationError):
        CMakeBuildArgs(config="")


def test_cmake_build_rejects_nonpositive_parallel_zero() -> None:
    with pytest.raises(ValidationError):
        CMakeBuildArgs(parallel=0)


def test_cmake_build_rejects_nonpositive_parallel_negative() -> None:
    with pytest.raises(ValidationError):
        CMakeBuildArgs(parallel=-3)


def test_cmake_build_rejects_build_dir_that_is_a_file(tmp_path: Path) -> None:
    build_file = tmp_path / "out"
    build_file.write_text("not a directory\n")

    with pytest.raises(ValidationError):
        CMakeBuildArgs(build_dir=build_file)


def test_cmake_build_rejects_empty_native_arg() -> None:
    with pytest.raises(ValidationError):
        CMakeBuildArgs(native_args=["-j", "", "8"])


def test_cmake_install_rejects_blank_config() -> None:
    with pytest.raises(ValidationError):
        CMakeInstallArgs(config=" ")


def test_cmake_install_rejects_blank_component() -> None:
    with pytest.raises(ValidationError):
        CMakeInstallArgs(component="")


def test_cmake_install_rejects_blank_prefix_path() -> None:
    with pytest.raises(ValidationError):
        CMakeInstallArgs(prefix=" ")


def test_cmake_install_omits_missing_values() -> None:
    args = CMakeInstallArgs(
        config=CLI_ARG_MISSING(),
        component=CLI_ARG_MISSING(),
        prefix=CLI_ARG_MISSING(),
    )
    assert args.emit() == ["--install", "build"]
