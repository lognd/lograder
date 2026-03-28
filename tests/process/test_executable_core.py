# type: ignore

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from lograder.exception import DeveloperException, StaffException
from lograder.process.cli_args import CLIArgs, CLIOption
from lograder.process.executable import (
    Executable,
    ExecutableInput,
    ExecutableInvocation,
    ExecutableOptions,
    ExecutableOutput,
    StaticExecutable,
    TypedExecutable,
    create_process,
    register_typed_executable,
    resolve_invocation,
)
from lograder.process.os_helpers import (
    CREATE_NEW_PROCESS_GROUP,
    NOT_APPLICABLE,
    StreamMode,
)


class ExampleArgs(CLIArgs):
    value: str = CLIOption(emit=["--value", "{}"])


def test_executable_input_stdin_text_round_trip() -> None:
    inp = ExecutableInput(encoding="utf-8")
    inp.stdin_text = "hello"
    assert inp.stdin_bytes == b"hello"
    assert inp.stdin_text == "hello"


def test_executable_output_stdout_text_round_trip() -> None:
    out = ExecutableOutput(
        command=["x"],
        stdout_bytes=b"",
        stderr_bytes=b"",
        return_code=0,
        encoding="utf-8",
    )
    out.stdout_text = "abc"
    assert out.stdout_bytes == b"abc"
    assert out.stdout_text == "abc"


def test_executable_output_stderr_text_round_trip() -> None:
    out = ExecutableOutput(
        command=["x"],
        stdout_bytes=b"",
        stderr_bytes=b"",
        return_code=0,
        encoding="utf-8",
    )
    out.stderr_text = "def"
    assert out.stderr_bytes == b"def"
    assert out.stderr_text == "def"


def test_executable_options_rejects_stdin_stdout_mode() -> None:
    with pytest.raises(ValidationError, match="stdin_mode"):
        ExecutableOptions(stdin_mode=StreamMode.STDOUT)


def test_executable_options_rejects_stdout_stdout_mode() -> None:
    with pytest.raises(ValidationError, match="stdout_mode"):
        ExecutableOptions(stdout_mode=StreamMode.STDOUT)


def test_resolve_stream_pipe() -> None:
    assert ExecutableInvocation.resolve_stream(StreamMode.PIPE) is subprocess.PIPE


def test_resolve_stream_inherit() -> None:
    assert ExecutableInvocation.resolve_stream(StreamMode.INHERIT) is None


def test_resolve_stream_null() -> None:
    assert ExecutableInvocation.resolve_stream(StreamMode.NULL) is subprocess.DEVNULL


def test_resolve_stream_stdout() -> None:
    assert ExecutableInvocation.resolve_stream(StreamMode.STDOUT) is subprocess.STDOUT


def test_resolve_invocation_builds_command_and_env() -> None:
    inp = ExecutableInput(arguments=["a", "b"], env={"X": "1"}, stdin_bytes=b"abc")
    opts = ExecutableOptions(
        cwd=Path("/tmp"),
        inherit_parent_env=False,
        timeout=12.5,
        stdin_mode=StreamMode.PIPE,
        stdout_mode=StreamMode.NULL,
        stderr_mode=StreamMode.INHERIT,
        start_new_session=False,
        restore_signals=NOT_APPLICABLE(),
        umask=NOT_APPLICABLE(),
        user_id=NOT_APPLICABLE(),
        user_name=NOT_APPLICABLE(),
        group_id=NOT_APPLICABLE(),
        group_name=NOT_APPLICABLE(),
        extra_groups=NOT_APPLICABLE(),
        creation_flags=NOT_APPLICABLE(),
        popen_kwargs={"bufsize": 0},
    )

    inv = resolve_invocation(["prog"], input=inp, options=opts)

    assert inv.command == ["prog", "a", "b"]
    assert inv.cwd == Path("/tmp")
    assert inv.env == {"X": "1"}
    assert inv.stdin_bytes == b"abc"
    assert inv.timeout == 12.5
    assert inv.stdin_mode == StreamMode.PIPE
    assert inv.stdout_mode == StreamMode.NULL
    assert inv.stderr_mode == StreamMode.INHERIT
    assert inv.creation_flags is NOT_APPLICABLE()
    assert inv.popen_kwargs == {"bufsize": 0}


def test_resolve_invocation_inherits_parent_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PARENT_ONLY", "yes")

    inp = ExecutableInput(arguments=[], env={"CHILD": "1"})
    opts = ExecutableOptions(
        inherit_parent_env=True,
        creation_flags=NOT_APPLICABLE(),
        restore_signals=NOT_APPLICABLE(),
        umask=NOT_APPLICABLE(),
        user_id=NOT_APPLICABLE(),
        user_name=NOT_APPLICABLE(),
        group_id=NOT_APPLICABLE(),
        group_name=NOT_APPLICABLE(),
        extra_groups=NOT_APPLICABLE(),
    )

    inv = resolve_invocation(["prog"], input=inp, options=opts)
    assert inv.env["PARENT_ONLY"] == "yes"
    assert inv.env["CHILD"] == "1"


def test_resolve_invocation_ors_windows_creation_flag_when_start_new_session() -> None:
    inp = ExecutableInput()
    opts = ExecutableOptions(
        inherit_parent_env=False,
        start_new_session=True,
        creation_flags=4,
        restore_signals=NOT_APPLICABLE(),
        umask=NOT_APPLICABLE(),
        user_id=NOT_APPLICABLE(),
        user_name=NOT_APPLICABLE(),
        group_id=NOT_APPLICABLE(),
        group_name=NOT_APPLICABLE(),
        extra_groups=NOT_APPLICABLE(),
    )

    inv = resolve_invocation(["prog"], input=inp, options=opts)
    assert inv.creation_flags == (4 | CREATE_NEW_PROCESS_GROUP)


def test_create_process_windows_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    class DummyPopen:
        def __init__(self, **kwargs: Any) -> None:
            seen.update(kwargs)

    monkeypatch.setattr("lograder.process.executable.is_windows", lambda: True)
    monkeypatch.setattr("lograder.process.executable.is_posix", lambda: False)
    monkeypatch.setattr("lograder.process.executable.subprocess.Popen", DummyPopen)

    inv = ExecutableInvocation(
        command=["cmd"],
        cwd=Path("."),
        env={"A": "1"},
        stdin_bytes=b"",
        encoding="utf-8",
        timeout=1.0,
        stdin_mode=StreamMode.PIPE,
        stdout_mode=StreamMode.NULL,
        stderr_mode=StreamMode.INHERIT,
        start_new_session=False,
        restore_signals=NOT_APPLICABLE(),
        umask=NOT_APPLICABLE(),
        user_id=NOT_APPLICABLE(),
        group_id=NOT_APPLICABLE(),
        user_name=NOT_APPLICABLE(),
        group_name=NOT_APPLICABLE(),
        extra_groups=NOT_APPLICABLE(),
        creation_flags=99,
        popen_kwargs={"bufsize": 0},
    )

    create_process(inv)

    assert seen["args"] == ["cmd"]
    assert seen["cwd"] == Path(".")
    assert seen["env"] == {"A": "1"}
    assert seen["stdin"] is subprocess.PIPE
    assert seen["stdout"] is subprocess.DEVNULL
    assert seen["stderr"] is None
    assert seen["creationflags"] == 99
    assert seen["text"] is False
    assert seen["bufsize"] == 0


def test_create_process_posix_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    class DummyPopen:
        def __init__(self, **kwargs: Any) -> None:
            seen.update(kwargs)

    monkeypatch.setattr("lograder.process.executable.is_windows", lambda: False)
    monkeypatch.setattr("lograder.process.executable.is_posix", lambda: True)
    monkeypatch.setattr("lograder.process.executable.subprocess.Popen", DummyPopen)

    inv = ExecutableInvocation(
        command=["cmd"],
        cwd=Path("."),
        env={"A": "1"},
        stdin_bytes=b"",
        encoding="utf-8",
        timeout=1.0,
        stdin_mode=StreamMode.PIPE,
        stdout_mode=StreamMode.NULL,
        stderr_mode=StreamMode.INHERIT,
        start_new_session=True,
        restore_signals=True,
        umask=0o022,
        user_id=1000,
        group_id=1001,
        user_name="logan",
        group_name="users",
        extra_groups=[4, 20],
        creation_flags=NOT_APPLICABLE(),
        popen_kwargs={"bufsize": 0},
    )

    create_process(inv)

    assert seen["args"] == ["cmd"]
    assert seen["cwd"] == Path(".")
    assert seen["env"] == {"A": "1"}
    assert seen["stdin"] is subprocess.PIPE
    assert seen["stdout"] is subprocess.DEVNULL
    assert seen["stderr"] is None
    assert seen["text"] is False
    assert seen["start_new_session"] is True
    assert seen["restore_signals"] is True
    assert seen["umask"] == 0o022
    assert seen["user"] == 1000
    assert seen["group"] == 1001
    assert seen["extra_groups"] == [4, 20]
    assert seen["bufsize"] == 0


def test_create_process_raises_on_unknown_platform(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("lograder.process.executable.is_windows", lambda: False)
    monkeypatch.setattr("lograder.process.executable.is_posix", lambda: False)

    inv = ExecutableInvocation(
        command=["cmd"],
        cwd=Path("."),
        env={},
        stdin_bytes=b"",
        encoding="utf-8",
        timeout=1.0,
        stdin_mode=StreamMode.PIPE,
        stdout_mode=StreamMode.PIPE,
        stderr_mode=StreamMode.PIPE,
        start_new_session=False,
        restore_signals=NOT_APPLICABLE(),
        umask=NOT_APPLICABLE(),
        user_id=NOT_APPLICABLE(),
        group_id=NOT_APPLICABLE(),
        user_name=NOT_APPLICABLE(),
        group_name=NOT_APPLICABLE(),
        extra_groups=NOT_APPLICABLE(),
        creation_flags=NOT_APPLICABLE(),
        popen_kwargs={},
    )

    with pytest.raises(DeveloperException, match="neither POSIX nor Windows"):
        create_process(inv)


def test_register_typed_executable_sets_static_executable() -> None:
    @register_typed_executable(["tool"])
    class MyExec(TypedExecutable[ExampleArgs]):
        pass

    assert MyExec.executable is not None
    assert isinstance(MyExec.executable, StaticExecutable)
    assert MyExec.executable.command == ["tool"]


def test_typed_executable_collects_bound_types_for_single_type() -> None:
    @register_typed_executable(["tool"])
    class MyExec(TypedExecutable[ExampleArgs]):
        pass

    assert MyExec.bound_types == {ExampleArgs}


def test_typed_executable_collects_bound_types_for_union() -> None:
    class OtherArgs(CLIArgs):
        x: str = CLIOption(emit=["--x", "{}"])

    @register_typed_executable(["tool"])
    class MyExec(TypedExecutable[ExampleArgs | OtherArgs]):
        pass

    assert MyExec.bound_types == {ExampleArgs, OtherArgs}


def test_typed_executable_rejects_non_cliargs_generic() -> None:
    with pytest.raises(DeveloperException, match="does not inherit from `CLIArgs`"):

        class BadExec(TypedExecutable[int]):
            pass


def test_typed_executable_call_raises_without_bound_type() -> None:
    class UnboundExec(TypedExecutable):
        pass

    with pytest.raises(
        DeveloperException, match="does not specify a bound `CLIArgs` type"
    ):
        UnboundExec()(ExampleArgs(value="x"))


def test_typed_executable_call_raises_without_registered_executable() -> None:
    class NoRegisteredExec(TypedExecutable[ExampleArgs]):
        pass

    with pytest.raises(DeveloperException, match="does not specify a bound executable"):
        NoRegisteredExec()(ExampleArgs(value="x"))


def test_typed_executable_call_rejects_input_arguments() -> None:
    @register_typed_executable(["tool"])
    class MyExec(TypedExecutable[ExampleArgs]):
        pass

    with pytest.raises(StaffException, match="single source of truth"):
        MyExec()(
            ExampleArgs(value="x"),
            input=ExecutableInput(arguments=["already", "set"]),
        )


def test_typed_executable_success_path_uses_args_emit_and_static_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeResult:
        def map(self, fn):
            captured["mapped"] = fn("ignored")
            return "RESULT"

    @register_typed_executable(["tool"])
    class MyExec(TypedExecutable[ExampleArgs]):
        def is_runnable(self):
            return FakeResult()

    def fake_call(self, *, input: ExecutableInput, options: ExecutableOptions):
        captured["input_arguments"] = list(input.arguments)
        captured["options"] = options
        return "OUTPUT"

    monkeypatch.setattr(StaticExecutable, "__call__", fake_call, raising=True)

    result = MyExec()(
        ExampleArgs(value="abc"),
        input=ExecutableInput(),
        options=ExecutableOptions(),
    )

    assert captured["input_arguments"] == ["--value", "abc"]
    assert captured["mapped"] == "OUTPUT"
    assert result == "RESULT"


def test_executable_pool_rejects_length_mismatch() -> None:
    class DummyExecutable(Executable):
        @property
        def command(self) -> list[str]:
            return ["dummy"]

    exe = DummyExecutable()

    with pytest.raises(DeveloperException, match="Mismatch between number of `inputs`"):
        exe.pool(
            [ExecutableInput(), ExecutableInput()],
            options=[ExecutableOptions()],
        )
