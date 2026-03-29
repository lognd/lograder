# type: ignore

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from lograder.process.os_helpers import is_posix

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not is_posix(),
        reason="Installer scripts are only implemented for POSIX so far.",
    ),
]


def _reload_module(module_name: str):
    module = importlib.import_module(module_name)
    return importlib.reload(module)


def _tail_lines(text: str | None, n: int = 80) -> str:
    if not text:
        return "<empty>"
    return "\n".join(text.splitlines()[-n:])


def _assert_successful_install_result(res, expected_path: Path, base_name: str) -> None:
    assert res.is_ok, (
        f"Expected installation to succeed, but got error:\n"
        f"module={res.danger_err.module!r}\n"
        f"message={res.danger_err.message}\n"
        f"stdout_tail={_tail_lines(res.danger_err.stdout)!r}\n"
        f"stderr_tail={_tail_lines(res.danger_err.stderr)!r}"
    )

    assert expected_path.exists(), (
        f"Installed executable does not exist at {expected_path}"
    )
    assert expected_path.is_file(), f"Installed path is not a file: {expected_path}"
    assert res.danger_ok in ([str(expected_path)], [base_name])

    assert expected_path.exists(), (
        f"Installed executable does not exist at {expected_path}"
    )
    assert expected_path.is_file(), f"Installed path is not a file: {expected_path}"

    # Current implementation may return the original command even after successful install.
    assert res.danger_ok in ([str(expected_path)], [base_name])


def _tail(text: str | None, n: int = 4000) -> str:
    if not text:
        return "<empty>"
    return text[-n:]


def test_valgrind_actual_installer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """
    Real installer test for Valgrind.

    Important:
    - We chdir before import/reload so the registry's class-level Path.cwd()-based
      install location points inside tmp_path.
    - This executes the actual installer script through BashExecutable.
    """
    monkeypatch.chdir(tmp_path)

    mod = _reload_module("lograder.process.registry.valgrind")
    ValgrindExecutable = mod.ValgrindExecutable

    exe = ValgrindExecutable()
    expected_path = tmp_path / ".valgrind" / "bin" / "valgrind"

    # Defensive sanity check against accidental import-time cwd capture.
    install_executable = ValgrindExecutable.install_executable
    assert install_executable is not None
    assert install_executable._install_location == expected_path

    res = exe.install()
    _assert_successful_install_result(res, expected_path, "valgrind")


def test_cmake_actual_installer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """
    Real installer test for CMake.
    """
    monkeypatch.chdir(tmp_path)

    mod = _reload_module("lograder.process.registry.cmake")
    CMakeExecutable = mod.CMakeExecutable

    exe = CMakeExecutable()
    expected_path = tmp_path / ".cmake" / "bin" / "cmake"

    install_executable = CMakeExecutable.install_executable
    assert install_executable is not None
    assert install_executable._install_location == expected_path

    res = exe.install()
    _assert_successful_install_result(res, expected_path, "cmake")
