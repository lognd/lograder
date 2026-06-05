import tempfile
from pathlib import Path
from typing import Generator, final

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.config import get_config
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.process.executable import (
    ExecutableInput,
    ExecutableOptions,
    StaticExecutable,
)
from lograder.process.parsers.valgrind import (
    ErrorEvent,
    ErrorRecord,
    FatalSignal,
    Frame,
    ValgrindOutput,
)
from lograder.process.registry.valgrind import ValgrindExecutable

_VALGRIND: ValgrindExecutable = ValgrindExecutable()


class ValgrindError(BaseModel):
    kind: str
    message: str
    primary_frames: list[str]


class ValgrindCase(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    stdin: bytes = b""
    check_leaks: bool = True


class ValgrindTestSuccess(TestSuccess):
    args: list[str]


class ValgrindTestFailure(TestFailure):
    args: list[str]
    stdin_text: str
    errors: list[ValgrindError]
    crashed: bool


class ValgrindTestError(TestError):
    pass


def _build_frame_str(frame: Frame) -> str:
    if frame.function_name:
        loc = frame.function_name
        if frame.source_file and frame.source_line:
            loc += f" ({frame.source_file}:{frame.source_line})"
        return loc
    if frame.object_name:
        return f"<{frame.object_name}>"
    return frame.instruction_pointer


def _extract_valgrind_error(error: ErrorEvent) -> ValgrindError:
    message = next(
        (msg.text for msg in error.primary_messages),
        "",
    )
    frames = [_build_frame_str(f) for f in error.primary_stack.frames[:5]]
    return ValgrindError(kind=str(error.kind), message=message, primary_frames=frames)


@final
class ValgrindTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        ValgrindTestError,
        ValgrindTestSuccess,
        ValgrindTestFailure,
    ]
):
    def __init__(
        self,
        artifact_name: str,
        test_cases: list[ValgrindCase],
        options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._test_cases = test_cases
        self._options = options

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[ValgrindTestSuccess, ValgrindTestFailure],
        None,
        Result[dict[str, Artifact], ValgrindTestError],
    ]:
        artifact = artifacts.get(self._artifact_name)
        if artifact is None:
            return Err(
                ValgrindTestError(
                    artifact_name=self._artifact_name,
                    message=(
                        f"Artifact `{self._artifact_name}` not found. "
                        f"Available: {sorted(artifacts)}."
                    ),
                )
            )
        if not isinstance(artifact, FileArtifact):
            return Err(
                ValgrindTestError(
                    artifact_name=self._artifact_name,
                    message=f"Artifact `{self._artifact_name}` exists but is not a file; cannot run under valgrind.",
                )
            )

        runnable = _VALGRIND.check_runnable()
        if runnable.is_err:
            if get_config().allow_auto_install:
                install_result = _VALGRIND.install()
                if install_result.is_err:
                    return Err(
                        ValgrindTestError(
                            artifact_name=self._artifact_name,
                            message=f"Could not find or install valgrind: {install_result.danger_err.message}",
                        )
                    )
                _VALGRIND.update_base_command(install_result.danger_ok)
            else:
                return Err(
                    ValgrindTestError(
                        artifact_name=self._artifact_name,
                        message=f"valgrind not found and auto-install is disabled. Enable with config(allow_auto_install=True) or install valgrind manually.",
                    )
                )

        options = self._options or ExecutableOptions()
        binary = str(artifact.path.resolve())

        for case in self._test_cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                xml_path = Path(tmpdir) / "valgrind_output.xml"
                leak_flag = (
                    "--leak-check=full" if case.check_leaks else "--leak-check=no"
                )

                command = [
                    *_VALGRIND.get_command(),
                    "--xml=yes",
                    f"--xml-file={xml_path}",
                    leak_flag,
                    "--track-origins=yes",
                    "--error-exitcode=1",
                    binary,
                ]
                inp = ExecutableInput(stdin_bytes=case.stdin, arguments=case.args)
                StaticExecutable(command)(inp, options=options)

                if not xml_path.exists():
                    return Err(
                        ValgrindTestError(
                            artifact_name=self._artifact_name,
                            message=f"Valgrind did not produce XML output for case `{case.name}`.",
                        )
                    )

                try:
                    vg_output = ValgrindOutput.from_xml_file(xml_path)
                except Exception as exc:
                    return Err(
                        ValgrindTestError(
                            artifact_name=self._artifact_name,
                            message=f"Failed to parse valgrind XML for case `{case.name}`: {exc}",
                        )
                    )

            errors = [
                _extract_valgrind_error(ev.error)
                for ev in vg_output.runtime_events
                if isinstance(ev, ErrorRecord)
            ]
            crashed = any(
                isinstance(ev, FatalSignal) for ev in vg_output.runtime_events
            )

            if not errors and not crashed:
                yield Ok(
                    ValgrindTestSuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                    )
                )
            else:
                yield Err(
                    ValgrindTestFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        stdin_text=case.stdin.decode("utf-8", errors="replace"),
                        errors=errors,
                        crashed=crashed,
                    )
                )

        return Ok(artifacts)
