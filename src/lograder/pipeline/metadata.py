"""
Grader metadata and attribution.

Attach a ``GraderMetadata`` to your pipeline call to record who wrote the
autograder, when the submission arrived, whether it was late, and any other
display information you want shown to students in the Gradescope output.

Lograder's own author information is available as ``LOGRADER_ATTRIBUTION``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _pkg_version

    def _lograder_version() -> str:
        try:
            return _pkg_version("lograder")
        except PackageNotFoundError:
            return "unknown"

except ImportError:  # Python < 3.8 fallback

    def _lograder_version() -> str:
        return "unknown"


# ---------------------------------------------------------------------------
# Library attribution (built-in, always present)
# ---------------------------------------------------------------------------

LOGRADER_AUTHOR = "Logan Dapp"


# ---------------------------------------------------------------------------
# Per-autograder attribution
# ---------------------------------------------------------------------------


@dataclass
class StaffAuthor:
    """One person who authored or maintains this autograder."""

    name: str
    email: str | None = None
    role: str | None = None  # e.g. "Instructor", "Teaching Assistant"

    def display(self) -> str:
        parts = [self.name]
        if self.email:
            parts[-1] = f"{self.name} <{self.email}>"
        if self.role:
            parts.append(f"({self.role})")
        return " ".join(parts)


@dataclass
class Submitter:
    """A single submitter as reported by Gradescope."""

    name: str
    email: str | None = None
    sid: str | None = None  # student/employee ID


# ---------------------------------------------------------------------------
# GraderMetadata
# ---------------------------------------------------------------------------


@dataclass
class GraderMetadata:
    """
    Metadata about the autograder run.

    Pass to ``pipeline(metadata=...)`` so the pipeline auto-stamps
    ``submission_time`` and carries the metadata into the score object.
    Then ``score.write_results_json()`` / ``score.to_gradescope_dict()``
    automatically prepend the metadata block to the ``output`` field.

    Fields
    ------
    grader_name
        Short name for this autograder, e.g. ``"CS101 Lab 3"``.
    course
        Course identifier, e.g. ``"CSCI 101"``.
    assignment
        Assignment name, e.g. ``"Lab 3 -- Sorting"``.
    version
        Autograder version string. Useful when you ship multiple iterations.
    authors
        People who wrote this autograder.
    due_date
        Deadline for display only; used to flag late submissions.
    submission_time
        When the submission was received. ``Pipeline.__call__()`` stamps this
        to ``datetime.now(timezone.utc)`` if it is ``None`` at call time.
    submitters
        Submitter(s) as reported by Gradescope (populated by
        ``GraderMetadata.from_gradescope()``).
    notes
        Free-form text appended to the metadata block.
    show_lograder_attribution
        Whether to append the ``Built with lograder ...`` line. Default True.
    """

    grader_name: str | None = None
    course: str | None = None
    assignment: str | None = None
    version: str | None = None
    authors: list[StaffAuthor] = field(default_factory=list)
    due_date: datetime | None = None
    submission_time: datetime | None = None
    submitters: list[Submitter] = field(default_factory=list)
    notes: str | None = None
    show_lograder_attribution: bool = True

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_gradescope(
        cls,
        path: Path = Path("/autograder/submission_metadata.json"),
        **kwargs: Any,
    ) -> "GraderMetadata":
        """
        Build a ``GraderMetadata`` from Gradescope's ``submission_metadata.json``.

        Any additional keyword arguments are forwarded to the constructor, so
        you can mix Gradescope-sourced fields with manually set ones::

            metadata = GraderMetadata.from_gradescope(
                authors=[StaffAuthor(name="Prof. Smith", role="Instructor")],
                grader_name="CS101 Lab 3",
            )

        Fields populated from the file (when present):
        - ``submission_time`` from ``created_at``
        - ``due_date`` from ``assignment.due_date``
        - ``assignment`` name from ``assignment.title`` (if not supplied)
        - ``submitters`` from ``submitters``
        """
        submission_time: datetime | None = None
        due_date: datetime | None = None
        assignment: str | None = kwargs.pop("assignment", None)
        submitters: list[Submitter] = []

        if path.is_file():
            try:
                data: dict[str, Any] = json.loads(path.read_text())
                if "created_at" in data:
                    submission_time = _parse_iso(data["created_at"])
                asgn = data.get("assignment", {})
                if isinstance(asgn, dict):
                    if "due_date" in asgn:
                        due_date = _parse_iso(asgn["due_date"])
                    if assignment is None and "title" in asgn:
                        assignment = asgn["title"]
                for sub in data.get("submitters", []):
                    if isinstance(sub, dict):
                        submitters.append(
                            Submitter(
                                name=sub.get("name", ""),
                                email=sub.get("email"),
                                sid=str(sub["sid"]) if "sid" in sub else None,
                            )
                        )
            except Exception:
                pass  # If the file is malformed, proceed silently

        return cls(
            submission_time=submission_time,
            due_date=due_date,
            assignment=assignment,
            submitters=submitters,
            **kwargs,
        )

    def with_submission_time_now(self) -> "GraderMetadata":
        """Return a copy with ``submission_time`` set to the current UTC time."""
        return replace(self, submission_time=datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    @property
    def is_late(self) -> bool | None:
        """
        True if submission arrived after the due date, False if on time,
        None if either timestamp is missing.
        """
        if self.submission_time is None or self.due_date is None:
            return None
        sub = _ensure_tz(self.submission_time)
        due = _ensure_tz(self.due_date)
        return sub > due

    def to_display_string(self) -> str:
        """
        Format the metadata block as a plain-text string suitable for
        inclusion in the Gradescope ``output`` field.
        """
        lines: list[str] = []
        sep = "-" * 50

        lines.append(sep)

        # Title line
        title = self.grader_name or "Autograder"
        if self.version:
            title = f"{title}  (v{self.version})"
        lines.append(f"  {title}")
        lines.append(sep)

        if self.course:
            lines.append(f"  Course:      {self.course}")
        if self.assignment:
            lines.append(f"  Assignment:  {self.assignment}")

        # Timing
        if self.submission_time:
            ts = _fmt_dt(self.submission_time)
            late = self.is_late
            suffix = ""
            if late is True and self.due_date:
                suffix = f"  !  LATE  (due {_fmt_dt(self.due_date)})"
            elif late is False and self.due_date:
                suffix = f"  (due {_fmt_dt(self.due_date)})"
            lines.append(f"  Submitted:   {ts}{suffix}")
        elif self.due_date:
            lines.append(f"  Due:         {_fmt_dt(self.due_date)}")

        # Submitters
        if self.submitters:
            sub_parts = []
            for s in self.submitters:
                part = s.name
                if s.sid:
                    part += f" ({s.sid})"
                if s.email:
                    part += f" <{s.email}>"
                sub_parts.append(part)
            lines.append(f"  Student(s):  {',  '.join(sub_parts)}")

        # Authors
        if self.authors:
            indent = "               "
            first = self.authors[0].display()
            lines.append(f"  Author(s):   {first}")
            for a in self.authors[1:]:
                lines.append(f"{indent}{a.display()}")

        # Notes
        if self.notes:
            lines.append(f"  Notes:       {self.notes}")

        # lograder attribution
        if self.show_lograder_attribution:
            ver = _lograder_version()
            lines.append(f"  Built with:  lograder {ver} -- {LOGRADER_AUTHOR}")

        lines.append(sep)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_iso(s: str) -> datetime | None:
    """Parse an ISO 8601 datetime string. Returns None on failure."""
    try:
        # Python 3.11+ has full ISO parsing; handle the common Gradescope format
        s = s.strip()
        # Replace space with T for compatibility
        s = s.replace(" ", "T")
        # fromisoformat handles +HH:MM offsets in 3.7+ but not Z until 3.11
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except (ValueError, AttributeError):
        return None


def _ensure_tz(dt: datetime) -> datetime:
    """If dt is naive, assume UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _fmt_dt(dt: datetime) -> str:
    dt = _ensure_tz(dt)
    return dt.strftime("%Y-%m-%d %H:%M %Z")
