from __future__ import annotations

import os
import subprocess
import sys
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Any, Callable, Generic, Optional, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from lograder.common import Empty, Err, Ok, Result, get_bound_types, unwrap_union_types
from lograder.exception import DeveloperException, StaffException
from lograder.output import get_logger
from lograder.pipeline.config import get_config
from lograder.process.cli_args import CLIArgs
from lograder.process.os_helpers import (
    CREATE_NEW_PROCESS_GROUP,
    NOT_APPLICABLE,
    SIGKILL,
    StreamMode,
    command_to_str,
    get_current_extra_groups,
    get_current_gid,
    get_current_groupname,
    get_current_uid,
    get_current_umask,
    get_current_username,
    is_command_runnable,
    is_posix,
    is_windows,
    posix_and,
    windows_and,
)

T = TypeVar("T")


_LOGGER = get_logger(__name__)


def resolve_invocation(
    command: list[str],
    *,
    input: ExecutableInput,
    options: ExecutableOptions,
) -> ExecutableInvocation:
    env: dict[str, str] = {}
    if options.inherit_parent_env:
        env.update(os.environ)
    env.update(input.env)

    return ExecutableInvocation(
        command=[*command, *input.arguments],
        cwd=options.cwd,
        env=env,
        stdin_bytes=input.stdin_bytes,
        encoding=input.encoding,
        timeout=options.timeout,
        stdin_mode=options.stdin_mode,
        stdout_mode=options.stdout_mode,
        stderr_mode=options.stderr_mode,
        start_new_session=options.start_new_session,
        restore_signals=options.restore_signals,
        umask=options.umask,
        user_id=options.user_id,
        user_name=options.user_name,
        group_id=options.group_id,
        group_name=options.group_name,
        extra_groups=options.extra_groups,
        creation_flags=(
            NOT_APPLICABLE()
            if options.creation_flags is NOT_APPLICABLE()
            else cast(int, options.creation_flags)
            | (options.start_new_session * CREATE_NEW_PROCESS_GROUP)
        ),
        popen_kwargs=options.popen_kwargs,
    )


def create_process(inv: ExecutableInvocation, /) -> subprocess.Popen:
    stdin = ExecutableInvocation.resolve_stream(inv.stdin_mode)
    stdout = ExecutableInvocation.resolve_stream(inv.stdout_mode)
    stderr = ExecutableInvocation.resolve_stream(inv.stderr_mode)
    if is_windows():
        return subprocess.Popen(
            args=inv.command,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=inv.cwd,
            env=inv.env,
            creationflags=cast(int, inv.creation_flags),
            text=False,
            **inv.popen_kwargs,
        )
    elif is_posix():
        kwargs: dict[str, Any] = {
            "args": inv.command,
            "stdin": stdin,
            "stdout": stdout,
            "stderr": stderr,
            "cwd": inv.cwd,
            "env": inv.env,
            "text": False,
            "start_new_session": cast(bool, inv.start_new_session),
            "restore_signals": cast(bool, inv.restore_signals),
            **inv.popen_kwargs,
        }

        if not isinstance(inv.umask, NOT_APPLICABLE):
            kwargs["umask"] = inv.umask
        if not isinstance(inv.user_id, NOT_APPLICABLE):
            kwargs["user"] = inv.user_id
        if not isinstance(inv.group_id, NOT_APPLICABLE):
            kwargs["group"] = inv.group_id
        if not isinstance(inv.extra_groups, NOT_APPLICABLE):
            kwargs["extra_groups"] = inv.extra_groups

        return subprocess.Popen(**kwargs)
    else:
        raise DeveloperException(
            f"Platform is neither POSIX nor Windows ({sys.platform=}, {os.name=}); please implement a command runner."
        )


def invoke_command(inv: ExecutableInvocation, /) -> ExecutableOutput:
    with create_process(inv) as process:
        try:  # Kind of copied from `subprocess.py`
            stdout, stderr = process.communicate(inv.stdin_bytes, timeout=inv.timeout)
        except TimeoutExpired:
            process.kill()
            if is_windows():
                stdout, stderr = process.communicate()
            else:
                process.wait()
        except:
            process.kill()
            raise
        retcode = process.poll()
        if retcode is None:
            retcode = SIGKILL
    return ExecutableOutput(
        command=inv.command,
        stdout_bytes=stdout,
        stderr_bytes=stderr,
        return_code=retcode,
    )


class ExecutableOptions(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    cwd: Path = Field(default_factory=Path.cwd)
    timeout: float | None = Field(
        default_factory=lambda: get_config().executable_timeout
    )
    inherit_parent_env: bool = True

    stdin_mode: StreamMode = StreamMode.PIPE
    stdout_mode: StreamMode = StreamMode.PIPE
    stderr_mode: StreamMode = StreamMode.PIPE

    start_new_session: bool = False

    # POSIX
    restore_signals: bool | NOT_APPLICABLE = posix_and(True)
    umask: int | NOT_APPLICABLE = Field(default_factory=get_current_umask)
    user_id: int | NOT_APPLICABLE = Field(default_factory=NOT_APPLICABLE)
    user_name: str | NOT_APPLICABLE = Field(default_factory=NOT_APPLICABLE)
    group_id: int | NOT_APPLICABLE = Field(default_factory=NOT_APPLICABLE)
    group_name: str | NOT_APPLICABLE = Field(default_factory=NOT_APPLICABLE)
    extra_groups: list[int] | NOT_APPLICABLE = Field(default_factory=NOT_APPLICABLE)

    # WINDOWS
    creation_flags: int | NOT_APPLICABLE = windows_and(0)

    # EXTRA
    popen_kwargs: dict[str, Any] = Field(default_factory=dict)

    @field_validator("stdin_mode", mode="after")
    @classmethod
    def validate_stdin_must_not_be_stdout_mode(cls, v: StreamMode) -> StreamMode:
        if v == StreamMode.STDOUT:
            raise ValueError("`stdin_mode` cannot be `StreamMode.STDOUT`.")
        return v

    @field_validator("stdout_mode", mode="after")
    @classmethod
    def validate_stdout_must_not_be_stdout_mode(cls, v: StreamMode) -> StreamMode:
        if v == StreamMode.STDOUT:
            raise ValueError("`stdout_mode` cannot be `StreamMode.STDOUT`.")
        return v


class ExecutableInput(BaseModel):
    stdin_bytes: bytes = b""
    arguments: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    encoding: str = "utf-8"

    @property
    def stdin_text(self) -> str:
        return self.stdin_bytes.decode(self.encoding, errors="ignore")

    @stdin_text.setter
    def stdin_text(self, text: str) -> None:
        self.stdin_bytes = text.encode(self.encoding, errors="ignore")


class ExecutableOutput(BaseModel):
    command: list[str]
    stdout_bytes: bytes
    stderr_bytes: bytes
    return_code: int
    encoding: str = Field(default="utf-8")

    @property
    def stdout_text(self) -> str:
        return self.stdout_bytes.decode(self.encoding, errors="ignore")

    @stdout_text.setter
    def stdout_text(self, text: str) -> None:
        self.stdout_bytes = text.encode(self.encoding, errors="ignore")

    @property
    def stderr_text(self) -> str:
        return self.stderr_bytes.decode(self.encoding, errors="ignore")

    @stderr_text.setter
    def stderr_text(self, text: str) -> None:
        self.stderr_bytes = text.encode(self.encoding, errors="ignore")


class ExecutableInvocation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    command: list[str]
    cwd: Path
    env: dict[str, str]
    stdin_bytes: bytes
    encoding: str
    timeout: float | None

    stdin_mode: StreamMode
    stdout_mode: StreamMode
    stderr_mode: StreamMode

    # POSIX
    start_new_session: bool | NOT_APPLICABLE
    restore_signals: bool | NOT_APPLICABLE
    umask: int | NOT_APPLICABLE
    user_id: int | NOT_APPLICABLE
    group_id: int | NOT_APPLICABLE
    user_name: str | NOT_APPLICABLE
    group_name: str | NOT_APPLICABLE
    extra_groups: list[int] | NOT_APPLICABLE

    # WINDOWS
    creation_flags: int | NOT_APPLICABLE

    # EXTRA
    popen_kwargs: dict[str, Any]

    @staticmethod
    def resolve_stream(mode: StreamMode) -> Any:
        if mode == StreamMode.PIPE:
            return subprocess.PIPE
        if mode == StreamMode.INHERIT:
            return None
        if mode == StreamMode.NULL:
            return subprocess.DEVNULL
        if mode == StreamMode.STDOUT:
            return subprocess.STDOUT
        raise DeveloperException(f"Unsupported stream mode: {mode}")


class Executable(ABC):
    @property
    @abstractmethod
    def command(self) -> list[str]: ...

    def __call__(
        self,
        input: ExecutableInput,
        *,
        options: ExecutableOptions = ExecutableOptions(),
    ) -> ExecutableOutput:
        invocation = resolve_invocation(self.command, input=input, options=options)
        return invoke_command(invocation)

    def pool(
        self,
        inputs: list[ExecutableInput],
        *,
        options: ExecutableOptions | list[ExecutableOptions] = ExecutableOptions(),
    ) -> list[Future[ExecutableOutput]]:
        if isinstance(options, ExecutableOptions):
            options = [options] * len(inputs)
        if len(inputs) != len(options):
            raise DeveloperException(
                f"Mismatch between number of `inputs` ({len(inputs)}) and number of `options` ({len(options)})."
            )
        executor = ThreadPoolExecutor(max_workers=get_config().executable_max_workers)
        futures: list[Future[ExecutableOutput]] = []
        for input, option in zip(inputs, options):
            invocation = resolve_invocation(self.command, input=input, options=option)
            futures.append(executor.submit(invoke_command, invocation))
        return futures


class StaticExecutable(Executable):
    def __init__(self, command: list[str]) -> None:
        self._command = command

    @property
    def command(self) -> list[str]:
        return self._command

    @command.setter
    def command(self, command: list[str]) -> None:
        self._command = command


_ORIGINAL_COMMANDS: dict[type[TypedExecutable], list[str]] = {}


def register_typed_executable(
    base_command: list[str],
) -> Callable[[type[TypedExecutable]], type[TypedExecutable]]:
    def wrapper(cls: type[TypedExecutable]) -> type[TypedExecutable]:
        _ORIGINAL_COMMANDS[cls] = base_command
        cls.executable = StaticExecutable(command=base_command)
        return cls

    return wrapper


class InstallationError(BaseModel):
    module: list[str]
    message: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class InstallWarning(BaseModel):
    command: list[str]
    calling_object: str


class InstallationExecutable(ABC):
    def __init__(
        self,
        executable: TypedExecutable[T],
        args: T,
        input: ExecutableInput = ExecutableInput(),
        options: ExecutableOptions = ExecutableOptions(),
    ) -> None:
        self._executable = executable
        self._args = args
        self._input = input
        self._options = options

    def validate_runnable(self) -> None:
        return

    @abstractmethod
    def get_command(
        self, output: ExecutableOutput
    ) -> Result[Optional[list[str]], InstallationError]: ...

    def __call__(self) -> Result[Optional[list[str]], InstallationError]:
        res = self._executable(
            args=self._args, input=self._input, options=self._options
        )
        if res.is_err:
            return res.swap_ok(list[str])
        output = res.danger_ok
        if output.return_code != 0:
            return Err(
                InstallationError(
                    module=output.command,
                    message=f"The installation executable exited with code, `{output.return_code}`.",
                    stdout=output.stdout_text,
                    stderr=output.stderr_text,
                )
            )
        return self.get_command(output)


class TypedExecutable(Generic[T]):
    bound_types: Optional[set[type[CLIArgs]]] = None
    executable: Optional[StaticExecutable] = None
    install_executable: Optional[InstallationExecutable] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        _generic_bound_types = get_bound_types(cls, TypedExecutable)
        _generic_bound_type = _generic_bound_types[0] if _generic_bound_types else None

        _bound_type = getattr(cls, "__meta_bound_type__", None) or _generic_bound_type
        _bound_types = unwrap_union_types(_bound_type) if _bound_type else None

        if _bound_types is not None:
            for typ in _bound_types:
                if isinstance(typ, type) and not issubclass(typ, CLIArgs):
                    raise DeveloperException(
                        f"A `TypedExecutable` subclass, `{cls.__name__}`, uses `{typ.__name__}` as a generic parameter, but "
                        f"`{typ.__name__}` does not inherit from `CLIArgs`."
                    )
        # noinspection PyUnnecessaryCast
        cls.bound_types = cast(Optional[set[type[CLIArgs]]], _bound_types)

    @classmethod
    def get_original_command(cls) -> list[str]:
        return _ORIGINAL_COMMANDS.get(cls, [])

    @classmethod
    def get_command(cls) -> list[str]:
        return cls.executable.command if cls.executable is not None else []

    def install(self) -> Result[list[str], InstallationError]:
        """
        Provides a method to install an executable. Either calls the `InstallationExecutable` at `self.install_executable`
        or whatever overrides this method.
        Changes `self.executable.command` to be whatever is correct.
        """
        if self.install_executable is not None and self.executable is not None:
            _LOGGER.packet(
                InstallWarning(
                    command=self.executable.command,
                    calling_object=self.__class__.__name__,
                )
            )
            res = self.install_executable()
            if res.is_ok and res.danger_ok is None:
                return Ok(self.get_command())
            # noinspection PyUnnecessaryCast
            return cast(Result[list[str], InstallationError], res)
        if self.executable is None:
            raise DeveloperException(
                f"Cannot `.install()` a `{self.__class__.__name__}` instance because the class does not specify a bound executable with `@register_typed_executable([<command-goes-here>])`."
            )
        return Err(
            InstallationError(
                module=self.executable.command,
                message=f"`{self.__class__.__name__}` was unable to attempt an installation because default installation method, `.install()`, was not overridden.",
            )
        )

    def validate_existent_executable(self, source: str) -> None:
        if self.executable is None:
            raise DeveloperException(
                f"Cannot `.{source}(...)` a `{self.__class__.__name__}` instance because the class does not specify a bound executable with `@register_typed_executable([<command-goes-here>])`."
            )

    def update_base_command(self, command: list[str]) -> None:
        self.validate_existent_executable("update_base_command")
        assert self.executable is not None
        self.executable.command = command

    def check_runnable(self) -> Result[Empty, InstallationError]:
        """
        Provides a method for platform checking or any sort of pre-run validation.
        """
        self.validate_existent_executable("check_runnable")
        assert self.executable is not None

        if not is_command_runnable(self.executable.command):
            original_command = self.get_original_command()
            if self.executable.command == original_command or not original_command:
                return Err(
                    InstallationError(
                        module=self.executable.command,
                        message=f"Could not find executable `{self.executable.command[0]}`.",
                    )
                )
            else:
                return Err(
                    InstallationError(
                        module=self.executable.command,
                        message=f"Could not find executable `{self.executable.command[0]}` even after installation. Original search location was `{original_command[0]}`.",
                    )
                )
        return Ok(Empty())

    def __call__(
        self,
        args: T,
        input: ExecutableInput = ExecutableInput(),
        options: ExecutableOptions = ExecutableOptions(),
    ) -> Result[ExecutableOutput, InstallationError]:
        if self.bound_types is None:
            raise DeveloperException(
                f"Cannot call a `{self.__class__.__name__}` instance because the class does not specify a bound `CLIArgs` type or union type with `class <your-executable>(TypedExecutable[<CLIArgs-type-or-union-of-CLIArgs-type>])."
            )
        if self.executable is None:
            raise DeveloperException(
                f"Cannot call a `{self.__class__.__name__}` instance because the class does not specify a bound executable with `@register_typed_executable([<command-goes-here>])`."
            )
        if input.arguments:
            raise StaffException(
                f"Call to `{self.__class__.__name__}` with non-empty arguments (`{'`, `'.join(e for e in input.arguments)}`) in `input` parameter is not allowed because "
                f"the arguments must be provided by the `args` parameter of one of the type(s): `{'`, `'.join(t.__name__ for t in self.bound_types)}`. This is to "
                f"enforce a single source of truth for the arguments."
            )
        # noinspection PyUnnecessaryCast
        input.arguments = cast(
            CLIArgs, args
        ).emit()  # This is guaranteed by `__init_subclass__`
        may_run = self.check_runnable()
        if may_run.err:
            install = self.install()
            if install.err:
                return install.swap_ok(ExecutableOutput)
            self.update_base_command(install.danger_ok)
            may_run = self.check_runnable()
        if may_run.err:
            return may_run.swap_ok(ExecutableOutput)

        return Ok(self.executable(input=input, options=options))
