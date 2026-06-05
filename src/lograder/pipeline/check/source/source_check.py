from __future__ import annotations

from pathlib import Path
from typing import Generator, Literal

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.check.check import Check, CheckData, CheckError
from lograder.pipeline.types.parcels import Manifest

Language = Literal["c", "cpp", "python"]


class OperatorConstraint(BaseModel):
    """One or more operator tokens with a combined maximum occurrence count."""
    tokens: list[str]
    max_count: int
    label: str = ""

    @property
    def display_label(self) -> str:
        return self.label or " | ".join(f"`{t}`" for t in self.tokens)


class ConstraintResult(BaseModel):
    label: str
    tokens: list[str]
    count: int
    max_count: int


class OperatorCheckData(CheckData):
    check_name: str = Field(default="Operator Check")
    file: str
    results: list[ConstraintResult]


class OperatorViolation(BaseModel):
    check_name: str = Field(default="Operator Check")
    file: str
    label: str
    tokens: list[str]
    count: int
    max_count: int


class OperatorCheckError(CheckError):
    check_name: str = Field(default="Operator Check")
    file: str
    message: str


class SourceOperatorCheck(
    Check[
        Manifest,
        Manifest,
        OperatorCheckError,
        OperatorCheckData,
        OperatorViolation,
    ]
):
    """Check that source files do not exceed per-operator usage limits.

    C/C++ files are run through the C preprocessor first so that #define
    aliasing is resolved before the AST is analysed.
    """

    def __init__(
        self,
        files: list[str],
        constraints: list[OperatorConstraint],
        language: Language,
        include_dirs: list[Path] | None = None,
        label: str = "Operator Check",
    ) -> None:
        self._files = files
        self._constraints = constraints
        self._language: Language = language
        self._include_dirs: list[Path] = include_dirs or []
        self._label = label

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[OperatorCheckData, OperatorViolation],
        None,
        Result[Manifest, OperatorCheckError],
    ]:
        from lograder.pipeline.check.source._ast import (
            count_operators_cpp,
            count_operators_python,
        )

        for file_name in self._files:
            path = manifest.root / file_name
            if not path.exists():
                return Err(OperatorCheckError(
                    check_name=self._label,
                    file=file_name,
                    message=f"File not found: {path}",
                ))

            if self._language in ("c", "cpp"):
                count_result = count_operators_cpp(path, self._include_dirs or None)
                if count_result.is_err:
                    return Err(OperatorCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=count_result.danger_err.message,
                    ))
            else:
                count_result = count_operators_python(path)
                if count_result.is_err:
                    return Err(OperatorCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=str(count_result.danger_err),
                    ))

            counts = count_result.danger_ok
            constraint_results: list[ConstraintResult] = []
            any_violation = False

            for constraint in self._constraints:
                combined = sum(counts.get(tok, 0) for tok in constraint.tokens)
                constraint_results.append(ConstraintResult(
                    label=constraint.display_label,
                    tokens=constraint.tokens,
                    count=combined,
                    max_count=constraint.max_count,
                ))
                if combined > constraint.max_count:
                    any_violation = True
                    yield Err(OperatorViolation(
                        check_name=self._label,
                        file=file_name,
                        label=constraint.display_label,
                        tokens=constraint.tokens,
                        count=combined,
                        max_count=constraint.max_count,
                    ))

            if not any_violation:
                yield Ok(OperatorCheckData(
                    check_name=self._label,
                    file=file_name,
                    results=constraint_results,
                ))

        return Ok(manifest)
