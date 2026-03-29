# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest

from lograder.common import Err, Ok
from lograder.exception import DeveloperException
from lograder.process.cli_args import CLIArgs, CLIOption
from lograder.process.executable import (
    ExecutableInput,
    ExecutableOptions,
    ExecutableOutput,
    InstallationError,
    InstallationExecutable,
    TypedExecutable,
    register_typed_executable,
)
from lograder.process.install_script import InstallScript, PlatformInstallScript


class DummyArgs(CLIArgs):
    token: str = CLIOption(default="hello", emit=["{}"])


@register_typed_executable(["dummy-exe"])
class DummyTypedExecutable(TypedExecutable[DummyArgs]):
    pass


class SpyTypedExecutable(TypedExecutable[DummyArgs]):
    def __init__(self, result):
        self._result = result

    def __call__(
        self,
        args: DummyArgs,
        input: ExecutableInput = ExecutableInput(),
        options: ExecutableOptions = ExecutableOptions(),
    ):
        return self._result


def make_platform_install(
    *,
    install_location: Path | None,
    append_command_arguments: list[str] | None = None,
    input: ExecutableInput | None = None,
    options: ExecutableOptions | None = None,
) -> PlatformInstallScript:
    return PlatformInstallScript(
        executable=DummyTypedExecutable(),
        args=DummyArgs(token="arg-token"),
        install_location=install_location,
        append_command_arguments=append_command_arguments or [],
        input=input or ExecutableInput(),
        options=options or ExecutableOptions(),
    )


def test_install_script_selects_matching_platform(tmp_path: Path) -> None:
    chosen_location = tmp_path / "chosen" / "bin" / "tool"

    script = InstallScript(
        {
            lambda: True: make_platform_install(
                install_location=chosen_location,
                append_command_arguments=["--x"],
            ),
            lambda: False: make_platform_install(
                install_location=tmp_path / "other" / "bin" / "tool",
                append_command_arguments=["--y"],
            ),
        }
    )

    assert script._install_location == chosen_location
    assert script._append_command_arguments == ["--x"]
    assert isinstance(script._input, ExecutableInput)
    assert isinstance(script._options, ExecutableOptions)
    assert isinstance(script._args, DummyArgs)


def test_install_script_uses_first_true_platform_only(tmp_path: Path) -> None:
    first_location = tmp_path / "first" / "bin" / "tool"
    second_location = tmp_path / "second" / "bin" / "tool"

    script = InstallScript(
        {
            lambda: True: make_platform_install(install_location=first_location),
            lambda: True: make_platform_install(install_location=second_location),
        }
    )

    assert script._install_location == first_location


def test_install_script_no_matching_platform_leaves_defaults() -> None:
    script = InstallScript(
        {
            lambda: False: make_platform_install(install_location=Path("/tmp/nope")),
        }
    )

    assert script._install_location is None
    assert script._append_command_arguments == []


def test_get_command_err_when_expected_install_location_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workdir = tmp_path / "wd"
    workdir.mkdir()
    (workdir / "alpha.txt").write_text("a", encoding="utf-8")
    (workdir / "beta").mkdir()

    missing_location = workdir / ".valgrind" / "bin" / "valgrind"

    script = InstallScript(
        {
            lambda: True: make_platform_install(install_location=missing_location),
        }
    )

    monkeypatch.chdir(workdir)

    output = ExecutableOutput(
        command=["install-valgrind.sh"],
        stdout_bytes=b"",
        stderr_bytes=b"",
        return_code=0,
    )

    res = script.get_command(output)

    assert res.is_err
    err = res.danger_err
    assert isinstance(err, InstallationError)
    assert err.module == ["install-valgrind.sh"]
    assert "installation succeeded" in err.message.lower()
    assert str(missing_location) in err.message
    assert str(workdir) in err.message
    assert "alpha.txt" in err.message
    assert "beta" in err.message


def test_get_command_err_when_expected_install_location_missing_and_cwd_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workdir = tmp_path / "emptywd"
    workdir.mkdir()
    missing_location = workdir / ".cmake" / "bin" / "cmake"

    script = InstallScript(
        {
            lambda: True: make_platform_install(install_location=missing_location),
        }
    )

    monkeypatch.chdir(workdir)

    output = ExecutableOutput(
        command=["install-cmake.sh"],
        stdout_bytes=b"",
        stderr_bytes=b"",
        return_code=0,
    )

    res = script.get_command(output)

    assert res.is_err
    assert "is empty." in res.danger_err.message


def test_get_command_ok_path_when_install_location_exists(tmp_path: Path) -> None:
    install_location = tmp_path / ".tool" / "bin" / "tool"
    install_location.parent.mkdir(parents=True)
    install_location.write_text("", encoding="utf-8")

    script = InstallScript(
        {
            lambda: True: make_platform_install(install_location=install_location),
        }
    )

    output = ExecutableOutput(
        command=["installer"],
        stdout_bytes=b"",
        stderr_bytes=b"",
        return_code=0,
    )

    res = script.get_command(output)

    assert res.is_ok
    assert res.danger_ok is not None


def test_installation_executable_propagates_underlying_err() -> None:
    underlying_err = Err(
        InstallationError(
            module=["bash"],
            message="failed before execution result materialized",
        )
    )

    class ForwardingInstallationExecutable(InstallationExecutable):
        def __init__(self) -> None:
            super().__init__(DummyTypedExecutable(), DummyArgs())

        def get_command(self, output: ExecutableOutput):
            return Ok(["installed-bin"])

        def __call__(self):
            return underlying_err

    inst = ForwardingInstallationExecutable()
    res = inst()

    assert res.is_err
    assert res.danger_err.module == ["bash"]
    assert res.danger_err.message == "failed before execution result materialized"


def test_installation_executable_wraps_nonzero_exit() -> None:
    fake_exec = SpyTypedExecutable(
        Ok(
            ExecutableOutput(
                command=["bash", "install.sh"],
                stdout_bytes=b"out",
                stderr_bytes=b"err",
                return_code=17,
            )
        )
    )

    class NonzeroExitInstallationExecutable(InstallationExecutable):
        def __init__(self) -> None:
            super().__init__(fake_exec, DummyArgs())

        def get_command(self, output: ExecutableOutput):
            pytest.fail("get_command should not be called on nonzero exit")

    inst = NonzeroExitInstallationExecutable()
    res = inst()

    assert res.is_err
    err = res.danger_err
    assert err.module == ["bash", "install.sh"]
    assert "exited with code, `17`" in err.message
    assert err.stdout == "out"
    assert err.stderr == "err"


def test_installation_executable_calls_get_command_on_zero_exit() -> None:
    fake_exec = SpyTypedExecutable(
        Ok(
            ExecutableOutput(
                command=["bash", "install.sh"],
                stdout_bytes=b"",
                stderr_bytes=b"",
                return_code=0,
            )
        )
    )

    class SuccessInstallationExecutable(InstallationExecutable):
        def __init__(self) -> None:
            self.seen_output = None
            super().__init__(fake_exec, DummyArgs())

        def get_command(self, output: ExecutableOutput):
            self.seen_output = output
            return Ok(["/installed/tool"])

    inst = SuccessInstallationExecutable()
    res = inst()

    assert res.is_ok
    assert res.danger_ok == ["/installed/tool"]
    assert inst.seen_output is not None
    assert inst.seen_output.command == ["bash", "install.sh"]


def test_platform_install_script_preserves_custom_input_and_options(
    tmp_path: Path,
) -> None:
    custom_input = ExecutableInput(arguments=["--extra"], env={"A": "B"})
    custom_options = ExecutableOptions(cwd=tmp_path)

    script = InstallScript(
        {
            lambda: True: make_platform_install(
                install_location=tmp_path / "bin" / "tool",
                input=custom_input,
                options=custom_options,
            ),
        }
    )

    assert script._input is custom_input
    assert script._options is custom_options


def test_valgrind_install_executable_is_install_script() -> None:
    from lograder.process.registry.valgrind import ValgrindExecutable

    assert isinstance(ValgrindExecutable.install_executable, InstallScript)


def test_valgrind_install_script_points_at_expected_install_location() -> None:
    from lograder.process.registry.valgrind import ValgrindExecutable

    inst = ValgrindExecutable.install_executable
    assert isinstance(inst, InstallScript)
    assert inst._install_location == Path.cwd() / ".valgrind/bin/valgrind"


def test_cmake_install_executable_is_install_script() -> None:
    from lograder.process.registry.cmake import CMakeExecutable

    assert isinstance(CMakeExecutable.install_executable, InstallScript)


def test_cmake_install_script_points_at_expected_install_location() -> None:
    from lograder.process.registry.cmake import CMakeExecutable

    inst = CMakeExecutable.install_executable
    assert isinstance(inst, InstallScript)
    assert inst._install_location == Path.cwd() / ".cmake/bin/cmake"


def test_validate_runnable_should_succeed_when_platform_matches(tmp_path: Path) -> None:
    script = InstallScript(
        {
            lambda: True: make_platform_install(
                install_location=tmp_path / "bin" / "tool"
            ),
        }
    )
    script.validate_runnable()


def test_get_command_with_no_install_location_should_return_ok_none() -> None:
    script = InstallScript(
        {
            lambda: True: make_platform_install(install_location=None),
        }
    )
    output = ExecutableOutput(
        command=["installer"],
        stdout_bytes=b"",
        stderr_bytes=b"",
        return_code=0,
    )
    res = script.get_command(output)
    assert res.is_ok
    assert res.danger_ok is None
