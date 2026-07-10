"""Forbidden-token scanning against ORIGINAL source text (no preprocessing, no AST).

``SourceCheck`` analyzes a preprocessed C/C++ translation unit, so declarations
pulled in from system headers (``printf`` from ``<stdio.h>``, ``std::stoi`` from
``<string>``) get counted against the student even when never written by hand,
and C++ keyword tokens (``throw``/``new``/``delete``/``try``/``catch``/
``template``) never match ``IdentifierConstraint`` because tree-sitter parses
them as keyword nodes, not identifier nodes.

``RawSourceCheck`` sidesteps both problems: it scans the file's own text after
stripping comments and string/char literals, and matches on literal token
patterns (regex-escaped words or ``a::b``-style qualified names), so keywords,
system-header names, and anything else lexical is fair game.

C/C++ only. Python forbidden-token scanning (``#`` comments, ``'''`` strings)
is not implemented here because Python's syntax makes safe literal-stripping
meaningfully harder (f-strings, triple-quote variants, raw strings); use
``IdentifierConstraint`` / ``KeywordConstraint`` / ``ImportConstraint`` on
``SourceCheck`` for Python instead.
"""

from __future__ import annotations

import re
from typing import Generator

from pydantic import BaseModel, Field

from lograder.common import Err, Ok, Result
from lograder.pipeline.check.check import Check, CheckError
from lograder.pipeline.check.source.source_check import (
    ConstraintResult,
    SourceCheckData,
    SourceViolation,
)
from lograder.pipeline.types.parcels import Manifest

# ---------------------------------------------------------------------------
# Constraint type
# ---------------------------------------------------------------------------


class ForbiddenTokenConstraint(BaseModel):
    """Limit occurrences of literal tokens in the ORIGINAL (unpreprocessed) source.

    ``tokens`` are matched whole-word (``\\b...\\b``); a token containing
    ``::`` (e.g. ``"std::sort"``) is matched as a qualified name, tolerant of
    whitespace around each ``::``. Matching happens after comments
    (``//...`` and ``/* ... */``) and string/char literals are stripped, and
    after ``= delete`` is neutralized so deleted special members don't count
    as uses of the ``delete`` keyword.
    """

    tokens: list[str]
    max_count: int = 0
    label: str = ""

    @property
    def display_label(self) -> str:
        return self.label or " | ".join(f"`{t}`" for t in self.tokens)

    def _pattern(self) -> re.Pattern[str]:
        parts = []
        for tok in self.tokens:
            if "::" in tok:
                segments = [re.escape(seg.strip()) for seg in tok.split("::")]
                parts.append(r"\s*::\s*".join(segments))
            else:
                parts.append(re.escape(tok))
        return re.compile(r"\b(?:" + "|".join(parts) + r")\b")


# ---------------------------------------------------------------------------
# Error model
# ---------------------------------------------------------------------------


class RawSourceCheckError(CheckError):
    check_name: str = Field(default="Raw Source Check")
    file: str
    message: str


# ---------------------------------------------------------------------------
# Text-stripping helpers
# ---------------------------------------------------------------------------

_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_STRING_LITERAL_RE = re.compile(r'"(?:\\.|[^"\\])*"')
_CHAR_LITERAL_RE = re.compile(r"'(?:\\.|[^'\\])*'")
_DELETE_MEMBER_RE = re.compile(r"=\s*delete\b")


def _strip_cpp_source(text: str) -> str:
    """Remove comments and string/char literals; neutralize ``= delete``."""
    text = _LINE_COMMENT_RE.sub("", text)
    text = _BLOCK_COMMENT_RE.sub("", text)
    text = _STRING_LITERAL_RE.sub('""', text)
    text = _CHAR_LITERAL_RE.sub("''", text)
    text = _DELETE_MEMBER_RE.sub("=", text)
    return text


# ---------------------------------------------------------------------------
# Check step
# ---------------------------------------------------------------------------


class RawSourceCheck(
    Check[
        Manifest,
        Manifest,
        RawSourceCheckError,
        SourceCheckData,
        SourceViolation,
    ]
):
    """Check C/C++ source files for forbidden tokens using literal text matching.

    Unlike ``SourceCheck``, this step never preprocesses or parses an AST -- it
    scans each file's own text (comments and string/char literals stripped
    first), so it correctly catches keyword-only tokens (``throw``, ``new``,
    ``delete``, ``try``, ``catch``, ``template``) that ``IdentifierConstraint``
    can never match, and it never penalizes system-header declarations the
    way ``SourceCheck``'s preprocessed-translation-unit analysis can.

    Violations are yielded as non-fatal ``Err(SourceViolation)`` packets (one
    per violated constraint per file); the step always returns ``Ok(manifest)``
    unless a fatal error occurs (file missing, unreadable file). Attach
    ``CleanRunScorer`` to score this step -- like ``SourceCheck``,
    ``AllOrNothingScorer`` ignores non-fatal packets and will award full
    credit regardless of violations.
    """

    def __init__(
        self,
        files: list[str],
        constraints: list[ForbiddenTokenConstraint],
        label: str = "Raw Source Check",
    ) -> None:
        self._files = files
        self._constraints = constraints
        self._label = label

    def __call__(
        self, manifest: Manifest
    ) -> Generator[
        Result[SourceCheckData, SourceViolation],
        None,
        Result[Manifest, RawSourceCheckError],
    ]:
        for file_name in self._files:
            path = manifest.root / file_name
            if not path.exists():
                return Err(
                    RawSourceCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=f"File not found: {path}",
                    )
                )

            try:
                original = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                return Err(
                    RawSourceCheckError(
                        check_name=self._label,
                        file=file_name,
                        message=f"Could not read {path}: {exc}",
                    )
                )

            stripped = _strip_cpp_source(original)

            constraint_results: list[ConstraintResult] = []
            any_violation = False

            for constraint in self._constraints:
                count = len(constraint._pattern().findall(stripped))
                constraint_results.append(
                    ConstraintResult(
                        label=constraint.display_label,
                        count=count,
                        max_count=constraint.max_count,
                    )
                )
                if count > constraint.max_count:
                    any_violation = True
                    yield Err(
                        SourceViolation(
                            check_name=self._label,
                            file=file_name,
                            label=constraint.display_label,
                            count=count,
                            max_count=constraint.max_count,
                        )
                    )

            if not any_violation:
                yield Ok(
                    SourceCheckData(
                        check_name=self._label,
                        file=file_name,
                        results=constraint_results,
                    )
                )

        return Ok(manifest)
