from __future__ import annotations

import os
import subprocess
import sys
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Any, TypeVar, cast

from pydantic import BaseModel, Field, field_validator

from lograder.exception import DeveloperException
from lograder.process.os_helpers import is_windows, is_posix, CREATE_NEW_PROCESS_GROUP, SIGKILL, StreamMode, posix_and, windows_and, get_current_umask, get_current_uid, get_current_username, get_current_gid, get_current_groupname, get_current_extra_groups
from lograder.pipeline.config import get_config
from lograder.pipeline.types.sentinel import NOT_APPLICABLE

T = TypeVar("T")


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
        return subprocess.Popen(
            args=inv.command,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=inv.cwd,
            env=inv.env,
            text=False,
            start_new_session=cast(bool, inv.start_new_session),
            restore_signals=cast(bool, inv.restore_signals),
            umask=cast(int, inv.umask),
            user=cast(int, inv.user_id),
            group=cast(int, inv.group_id),
            extra_groups=cast(list[int], inv.extra_groups),
            **inv.popen_kwargs,
        )
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
    return ExecutableOutput(
        command=inv.command,
        stdout_bytes=stdout,
        stderr_bytes=stderr,
        return_code=retcode or SIGKILL,
    )


class ExecutableOptions(BaseModel):
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
    user_id: int | NOT_APPLICABLE = Field(default_factory=get_current_uid)
    user_name: str | NOT_APPLICABLE = Field(default_factory=get_current_username)
    group_id: int | NOT_APPLICABLE = Field(default_factory=get_current_gid)
    group_name: str | NOT_APPLICABLE = Field(default_factory=get_current_groupname)
    extra_groups: list[int] | NOT_APPLICABLE = Field(
        default_factory=get_current_extra_groups
    )

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
