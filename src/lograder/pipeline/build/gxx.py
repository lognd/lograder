"""GXXBuild  -  compile C++ source files directly with g++, no CMake required."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator, final

from pydantic import BaseModel

from lograder.common import Err, Ok, Result, Unreachable
from lograder.pipeline.build.build import Build
from lograder.pipeline.types.artifacts import Artifact, FileArtifact
from lograder.pipeline.types.parcels import Manifest
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode
from lograder.process.registry.gcc import GNUXXStandard, GXXArgs, GXXExecutable


class GXXBuildOutput(BaseModel):
    """Non-fatal packet: compilation succeeded."""

    sources: list[str]
    output: str
    return_code: int
    stdout: str
    stderr: str
    command: str


class GXXBuildError(BaseModel):
    """Fatal packet: compilation failed or g++ is not installed."""

    sources: list[str]
    output: str
    message: str
    return_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    command: str | None = None


@final
class GXXBuild(
    Build[
        Manifest,
        dict[str, Artifact],
        GXXBuildError,
        GXXBuildOutput,
        Unreachable,
    ]
):
    """Compile C++ source files with g++ and register the binary as an artifact.

    This is the lightweight alternative to ``CMakeBuild`` for assignments
    where students submit source files without a CMakeLists.txt.  The grader
    specifies which files to compile and what to name the output binary.

    Source files listed in ``sources`` are resolved relative to
    ``manifest.root``.  Files listed in ``extra_sources`` are absolute paths
    (e.g. grader-provided ``main.cpp``).

    Example::

        pipeline.add(GXXBuild(
            sources=["student.cpp"],
            output="student",
            extra_sources=[GRADER_DIR / "main.cpp"],
            include_dirs=[GRADER_DIR / "include"],
            sanitizers=["address", "undefined"],
            standard=GNUXXStandard.CXX17,
        ))

    The output binary is placed in a temporary directory that is cleaned up
    after the pipeline run.  The artifact name in the output dict is
    ``output``.

    Args:
        sources:        Student source filenames relative to ``manifest.root``.
        output:         Artifact name and output binary filename stem.
        extra_sources:  Additional absolute source paths (grader harness files).
        include_dirs:   Additional include search paths.
        library_dirs:   Additional library search paths.
        libraries:      Libraries to link (passed as ``-l<name>``).
        sanitizers:     Sanitizer names to enable (e.g. ``["address", "undefined"]``).
                        The binary must then be tested with ``ASanTest``.
        standard:       C++ language standard (default ``CXX17``).
        debug_symbols:  Pass ``-g`` (useful for debugger-based grading).
        extra_flags:    Raw extra flags forwarded to g++ verbatim.
    """

    _gxx = GXXExecutable()

    def __init__(
        self,
        sources: list[str | Path],
        output: str,
        *,
        extra_sources: list[Path] | None = None,
        include_dirs: list[str | Path] | None = None,
        library_dirs: list[str | Path] | None = None,
        libraries: list[str] | None = None,
        sanitizers: list[str] | None = None,
        standard: GNUXXStandard = GNUXXStandard.CXX17,
        debug_symbols: bool = False,
        extra_flags: list[str] | None = None,
    ) -> None:
        self._sources = [str(s) for s in sources]
        self._output = output
        self._extra_sources = list(extra_sources or [])
        self._include_dirs = [Path(p) for p in (include_dirs or [])]
        self._library_dirs = [Path(p) for p in (library_dirs or [])]
        self._libraries = list(libraries or [])
        self._sanitizers = list(sanitizers or [])
        self._standard = standard
        self._debug_symbols = debug_symbols
        self._extra_flags = list(extra_flags or [])

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[GXXBuildOutput, Unreachable],
        None,
        Result[dict[str, Artifact], GXXBuildError],
    ]:
        runnable = self._gxx.check_runnable()
        if runnable.is_err:
            return Err(
                GXXBuildError(
                    sources=self._sources,
                    output=self._output,
                    message=f"g++ is not available: {runnable.danger_err.message}",
                )
            )

        # Resolve student source files relative to manifest root
        student_paths: list[Path] = []
        for name in self._sources:
            p = manifest.root / name
            if not p.exists():
                return Err(
                    GXXBuildError(
                        sources=self._sources,
                        output=self._output,
                        message=f"Source file not found: {p}",
                    )
                )
            student_paths.append(p)

        all_input = student_paths + self._extra_sources

        # Build output goes in a temp dir so it never pollutes the submission
        tmpdir = Path(tempfile.mkdtemp(prefix="lograder_gxx_"))
        binary_path = tmpdir / self._output

        args = GXXArgs(
            input=all_input,
            output=binary_path,
            standard=self._standard,
            include_dirs=[manifest.root] + self._include_dirs,
            library_dirs=self._library_dirs,
            libraries=self._libraries,
            sanitizers=self._sanitizers,
            debug_symbols=self._debug_symbols,
            compile_options=self._extra_flags,
        )

        options = ExecutableOptions(
            stdout_mode=StreamMode.PIPE,
            stderr_mode=StreamMode.PIPE,
        )

        raw_result = self._gxx(args, options=options)

        if raw_result.is_err:
            err = raw_result.danger_err
            return Err(
                GXXBuildError(
                    sources=self._sources,
                    output=self._output,
                    message=f"Failed to invoke g++: {err.message}",
                )
            )

        out = raw_result.danger_ok
        cmd_str = " ".join(out.command)

        if out.return_code != 0:
            return Err(
                GXXBuildError(
                    sources=self._sources,
                    output=self._output,
                    message=f"Compilation failed (exit {out.return_code}).",
                    return_code=out.return_code,
                    stdout=out.stdout_text,
                    stderr=out.stderr_text,
                    command=cmd_str,
                )
            )

        yield Ok(
            GXXBuildOutput(
                sources=self._sources,
                output=self._output,
                return_code=out.return_code,
                stdout=out.stdout_text,
                stderr=out.stderr_text,
                command=cmd_str,
            )
        )

        return Ok({self._output: FileArtifact(path=binary_path)})


import lograder.output.layout.pipeline.gxx  # noqa: E402, F401
