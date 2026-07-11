"""Type-annotation completeness scanning for Python source files.

``ty`` (like every gradual type checker) only reports errors on annotations
that are *present* -- an entirely unannotated function is invisible to it, so a
``CleanRunScorer`` attached to a plain ``TyCheck`` awards its "type safety"
points to any correct-but-unannotated submission for free. ``ty`` therefore
cannot, on its own, back an *extra-credit* bonus that is supposed to reward the
effort of actually annotating your code.

``PythonAnnotationCheck`` closes that gap. It parses each file with the stdlib
``ast`` module (no third-party parser, no preprocessing) and, for each required
top-level function, verifies every parameter (other than ``self``/``cls``) and
the return type carry an annotation. Pair it with a ``CleanRunScorer`` to make
the annotation bonus require real typing effort, and keep a 0-point ``TyCheck``
alongside it so wrongly-typed annotations still surface as informational
diagnostics.

Python only.
"""

from __future__ import annotations

import ast
from typing import Generator

from pydantic import Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.check.check import Check, CheckError
from lograder.pipeline.check.source.source_check import (
    ConstraintResult,
    SourceCheckData,
    SourceViolation,
)
from lograder.pipeline.types.parcels import Manifest


class PythonAnnotationCheckError(CheckError):
    check_name: str = Field(default="Type Annotations")
    file: str
    message: str


# Parameters named ``self``/``cls`` are the implicit receiver of a method or
# classmethod and are conventionally left unannotated, so they are exempt.
_IMPLICIT_RECEIVERS = frozenset({"self", "cls"})


def _function_defs(
    tree: ast.Module,
) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Gradable function definitions, keyed by name.

    Includes top-level functions (keyed by bare name) and the methods of
    top-level classes (keyed by both ``ClassName.method`` and the bare
    ``method`` name, so a required-functions list can use either form). On a
    name collision the last definition seen wins.
    """
    out: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f"{node.name}.{member.name}"] = member
                    out.setdefault(member.name, member)
    return out


def _default_targets(tree: ast.Module) -> list[str]:
    """Public top-level functions plus public methods of public classes."""
    targets: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                targets.append(node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    not member.name.startswith("_") or member.name == "__init__"
                ):
                    targets.append(f"{node.name}.{member.name}")
    return targets


def _missing_annotations(
    fn: ast.FunctionDef | ast.AsyncFunctionDef, require_return: bool
) -> list[str]:
    """Names of the parts of ``fn``'s signature that lack a type annotation."""
    missing: list[str] = []
    a = fn.args
    params = [*a.posonlyargs, *a.args, *a.kwonlyargs]
    if a.vararg is not None:
        params.append(a.vararg)
    if a.kwarg is not None:
        params.append(a.kwarg)
    for i, param in enumerate(params):
        if param.annotation is None and not (
            i == 0 and param.arg in _IMPLICIT_RECEIVERS
        ):
            missing.append(param.arg)
    if require_return and fn.returns is None:
        missing.append("-> return")
    return missing


class PythonAnnotationCheck(
    Check[
        Manifest,
        Manifest,
        PythonAnnotationCheckError,
        SourceCheckData,
        SourceViolation,
    ]
):
    """Require complete type annotations on the graded Python functions.

    For each file, every function named in ``functions`` (or, when ``functions``
    is ``None``, every top-level function whose name does not start with an
    underscore) must annotate all of its parameters -- except a leading
    ``self``/``cls`` -- and, when ``require_return`` is true, its return type.

    A function that is required but absent, or present but missing any
    annotation, is reported as a non-fatal ``Err(SourceViolation)`` (count > 0
    against a ``max_count`` of 0). Attach a ``CleanRunScorer`` to award the
    bonus only when no violations are reported; ``AllOrNothingScorer`` ignores
    the non-fatal packets and awards full credit regardless. A fatal
    ``Err(PythonAnnotationCheckError)`` is returned only when a file is missing,
    unreadable, or unparseable.
    """

    def __init__(
        self,
        files: list[str],
        functions: list[str] | None = None,
        require_return: bool = True,
        label: str = "Type Annotations",
    ) -> None:
        self._files = files
        self._functions = functions
        self._require_return = require_return
        self._label = label

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[SourceCheckData, SourceViolation],
        None,
        Result[Manifest, PythonAnnotationCheckError],
    ]:
        for file_name in self._files:
            path = manifest.root / file_name
            if not path.exists():
                return Err(
                    PythonAnnotationCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=f"File not found: {path}",
                    )
                )
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                return Err(
                    PythonAnnotationCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=f"Could not read {path}: {exc}",
                    )
                )
            try:
                tree = ast.parse(source, filename=file_name)
            except SyntaxError as exc:
                return Err(
                    PythonAnnotationCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=f"Could not parse {path}: {exc}",
                    )
                )

            defs = _function_defs(tree)
            required = (
                self._functions
                if self._functions is not None
                else _default_targets(tree)
            )

            results: list[ConstraintResult] = []
            any_violation = False
            for name in required:
                fn = defs.get(name)
                if fn is None:
                    label = f"`{name}` is defined and fully annotated"
                    results.append(ConstraintResult(label=label, count=1, max_count=0))
                    any_violation = True
                    yield Err(
                        SourceViolation(
                            check_name=self._label,
                            file=file_name,
                            label=f"`{name}` is not defined",
                            count=1,
                            max_count=0,
                        )
                    )
                    continue
                missing = _missing_annotations(fn, self._require_return)
                results.append(
                    ConstraintResult(
                        label=f"`{name}` is fully annotated",
                        count=len(missing),
                        max_count=0,
                    )
                )
                if missing:
                    any_violation = True
                    yield Err(
                        SourceViolation(
                            check_name=self._label,
                            file=file_name,
                            label=f"`{name}` is missing annotations on: "
                            + ", ".join(missing),
                            count=len(missing),
                            max_count=0,
                        )
                    )

            if not any_violation:
                yield Ok(
                    SourceCheckData(
                        check_name=self._label,
                        file=file_name,
                        results=results,
                    )
                )

        return Ok(manifest)
