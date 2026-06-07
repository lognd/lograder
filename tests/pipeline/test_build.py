# mypy: ignore-errors
from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.common import Err, Ok
from lograder.pipeline.build.build import BuildOutput, make_build_output
from lograder.pipeline.config import config
from lograder.pipeline.types.parcels import Manifest
from lograder.process.executable import ExecutableOutput, InstallationError


def _make_manifest(tmp_path: Path) -> Manifest:
    with config(root_directory=tmp_path):
        return Manifest.from_flat([Path("CMakeLists.txt")])


def _make_exec_output(return_code: int = 0) -> ExecutableOutput:
    return ExecutableOutput(
        command=["cmake", "."],
        stdout_bytes=b"",
        stderr_bytes=b"",
        return_code=return_code,
    )


def _make_install_error() -> InstallationError:
    return InstallationError(module=["cmake"], message="cmake not found")


def test_make_build_output_installation_error_returns_err_build_output(tmp_path):
    manifest = _make_manifest(tmp_path)
    config_file = tmp_path / "CMakeLists.txt"
    install_err = _make_install_error()
    result = make_build_output(Err(install_err), manifest, config_file)
    assert result.is_err
    bo = result.danger_err
    assert bo.install_error is install_err


def test_make_build_output_nonzero_return_code_returns_err(tmp_path):
    manifest = _make_manifest(tmp_path)
    config_file = tmp_path / "CMakeLists.txt"
    result = make_build_output(
        Ok(_make_exec_output(return_code=1)), manifest, config_file
    )
    assert result.is_err
    bo = result.danger_err
    assert bo.executable_output is not None
    assert bo.executable_output.return_code == 1


def test_make_build_output_success_returns_ok(tmp_path):
    manifest = _make_manifest(tmp_path)
    config_file = tmp_path / "CMakeLists.txt"
    exec_out = _make_exec_output(return_code=0)
    result = make_build_output(Ok(exec_out), manifest, config_file)
    assert result.is_ok
    bo = result.danger_ok
    assert bo.executable_output is exec_out


def test_build_output_data_property_returns_executable_output(tmp_path):
    manifest = _make_manifest(tmp_path)
    config_file = tmp_path / "CMakeLists.txt"
    exec_out = _make_exec_output()
    bo = BuildOutput(
        manifest=manifest, config_file=config_file, executable_output=exec_out
    )
    assert bo.data is exec_out


def test_build_output_data_property_returns_install_error(tmp_path):
    manifest = _make_manifest(tmp_path)
    config_file = tmp_path / "CMakeLists.txt"
    install_err = _make_install_error()
    bo = BuildOutput(
        manifest=manifest, config_file=config_file, install_error=install_err
    )
    assert bo.data is install_err


def test_build_output_neither_raises(tmp_path):
    manifest = _make_manifest(tmp_path)
    config_file = tmp_path / "CMakeLists.txt"
    with pytest.raises(ValidationError):
        BuildOutput(manifest=manifest, config_file=config_file)


def test_build_output_both_raises(tmp_path):
    manifest = _make_manifest(tmp_path)
    config_file = tmp_path / "CMakeLists.txt"
    with pytest.raises(ValidationError):
        BuildOutput(
            manifest=manifest,
            config_file=config_file,
            executable_output=_make_exec_output(),
            install_error=_make_install_error(),
        )
