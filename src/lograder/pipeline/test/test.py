from abc import ABC
from typing import TypeVar

from pydantic import BaseModel

from lograder.common import Err, Ok, Result
from lograder.pipeline.step import Step
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.executable import (
    ExecutableInput,
    ExecutableOptions,
    ExecutableOutput,
)

__test__: bool = False


InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


class TestSuccess(BaseModel):
    __test__: bool = False
    test_name: str
    artifact_name: str


class TestFailure(BaseModel):
    __test__: bool = False
    test_name: str
    artifact_name: str


class TestError(BaseModel):
    __test__: bool = False
    artifact_name: str
    message: str


class Test(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC):
    @staticmethod
    def _resolve_artifact(
        artifacts: dict[str, Artifact], name: str
    ) -> Result[FileArtifact, str]:
        """Look up a required FileArtifact by name; message is caller's to wrap in its own Error type."""
        artifact = artifacts.get(name)
        if artifact is None:
            return Err(f"Artifact `{name}` not found. Available: {sorted(artifacts)}.")
        if not isinstance(artifact, FileArtifact):
            return Err(
                f"Artifact `{name}` exists but is not a file; cannot execute it."
            )
        return Ok(artifact)

    @staticmethod
    def _invoke(
        artifact: FileArtifact,
        args: list[str],
        stdin: bytes,
        options: ExecutableOptions,
    ) -> ExecutableOutput:
        inp = ExecutableInput(stdin_bytes=stdin, arguments=args)
        return artifact.executable(inp, options=options)

    @staticmethod
    def _exit_code_ok(expected: int | None, actual: int) -> bool:
        return expected is None or expected == actual

    @staticmethod
    def _decode_stdin(stdin: bytes) -> str:
        return stdin.decode("utf-8", errors="replace")


class JUnitTestSuccess(TestSuccess):
    __test__: bool = False
    duration: float | None


class JUnitTestFailure(TestFailure):
    __test__: bool = False
    duration: float | None
    failure_message: str
    failure_text: str


class JUnitTestError(TestError):
    __test__: bool = False
