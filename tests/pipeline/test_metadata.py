# mypy: ignore-errors
"""Unit tests for GraderMetadata."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lograder.pipeline.metadata import (
    GraderMetadata,
    StaffAuthor,
    Submitter,
    _fmt_dt,
    _parse_iso,
)

# ---------------------------------------------------------------------------
# _parse_iso
# ---------------------------------------------------------------------------


def test_parse_iso_utc_z():
    dt = _parse_iso("2024-03-15T10:00:00Z")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 3
    assert dt.day == 15


def test_parse_iso_with_offset():
    dt = _parse_iso("2024-03-15T10:00:00+05:30")
    assert dt is not None
    assert dt.utcoffset() is not None


def test_parse_iso_invalid_returns_none():
    assert _parse_iso("not-a-date") is None
    assert _parse_iso("") is None


# ---------------------------------------------------------------------------
# StaffAuthor.display
# ---------------------------------------------------------------------------


def test_staff_author_name_only():
    a = StaffAuthor(name="Prof. Smith")
    assert a.display() == "Prof. Smith"


def test_staff_author_with_email():
    a = StaffAuthor(name="Prof. Smith", email="smith@uni.edu")
    assert a.display() == "Prof. Smith <smith@uni.edu>"


def test_staff_author_with_role():
    a = StaffAuthor(name="Jane Doe", role="Teaching Assistant")
    assert a.display() == "Jane Doe (Teaching Assistant)"


def test_staff_author_full():
    a = StaffAuthor(name="Jane Doe", email="jd@uni.edu", role="TA")
    assert a.display() == "Jane Doe <jd@uni.edu> (TA)"


# ---------------------------------------------------------------------------
# GraderMetadata.is_late
# ---------------------------------------------------------------------------


_DUE = datetime(2024, 3, 15, 23, 59, tzinfo=timezone.utc)
_EARLY = datetime(2024, 3, 15, 20, 0, tzinfo=timezone.utc)
_LATE_TS = datetime(2024, 3, 16, 1, 0, tzinfo=timezone.utc)


def test_is_late_true():
    m = GraderMetadata(submission_time=_LATE_TS, due_date=_DUE)
    assert m.is_late is True


def test_is_late_false():
    m = GraderMetadata(submission_time=_EARLY, due_date=_DUE)
    assert m.is_late is False


def test_is_late_none_when_no_due():
    m = GraderMetadata(submission_time=_EARLY)
    assert m.is_late is None


def test_is_late_none_when_no_submission():
    m = GraderMetadata(due_date=_DUE)
    assert m.is_late is None


# ---------------------------------------------------------------------------
# GraderMetadata.with_submission_time_now
# ---------------------------------------------------------------------------


def test_with_submission_time_now_stamps_utc():
    m = GraderMetadata(grader_name="Test")
    stamped = m.with_submission_time_now()
    assert stamped.submission_time is not None
    assert stamped.submission_time.tzinfo is not None
    # Original unchanged
    assert m.submission_time is None
    # Name preserved
    assert stamped.grader_name == "Test"


# ---------------------------------------------------------------------------
# GraderMetadata.to_display_string
# ---------------------------------------------------------------------------


def test_display_string_contains_grader_name():
    m = GraderMetadata(grader_name="CS101 Lab 3")
    s = m.to_display_string()
    assert "CS101 Lab 3" in s


def test_display_string_contains_course_and_assignment():
    m = GraderMetadata(course="CSCI 101", assignment="Lab 3")
    s = m.to_display_string()
    assert "CSCI 101" in s
    assert "Lab 3" in s


def test_display_string_late_flag():
    m = GraderMetadata(submission_time=_LATE_TS, due_date=_DUE)
    s = m.to_display_string()
    assert "LATE" in s


def test_display_string_on_time_no_late_flag():
    m = GraderMetadata(submission_time=_EARLY, due_date=_DUE)
    s = m.to_display_string()
    assert "LATE" not in s


def test_display_string_includes_author():
    m = GraderMetadata(authors=[StaffAuthor(name="Prof. Smith", role="Instructor")])
    s = m.to_display_string()
    assert "Prof. Smith" in s
    assert "Instructor" in s


def test_display_string_lograder_attribution():
    m = GraderMetadata(show_lograder_attribution=True)
    s = m.to_display_string()
    assert "lograder" in s
    assert "Logan Dapp" in s


def test_display_string_no_lograder_attribution():
    m = GraderMetadata(show_lograder_attribution=False)
    s = m.to_display_string()
    assert "Logan Dapp" not in s


def test_display_string_version():
    m = GraderMetadata(grader_name="MyGrader", version="2024.1")
    s = m.to_display_string()
    assert "2024.1" in s


def test_display_string_notes():
    m = GraderMetadata(notes="Contact staff if you have questions.")
    s = m.to_display_string()
    assert "Contact staff if you have questions." in s


def test_display_string_submitter():
    m = GraderMetadata(submitters=[Submitter(name="Alice", sid="12345")])
    s = m.to_display_string()
    assert "Alice" in s
    assert "12345" in s


# ---------------------------------------------------------------------------
# GraderMetadata.from_gradescope
# ---------------------------------------------------------------------------


def test_from_gradescope_reads_file(tmp_path):
    data = {
        "created_at": "2024-03-16T01:00:00Z",
        "assignment": {
            "due_date": "2024-03-15T23:59:00Z",
            "title": "Lab 3",
        },
        "submitters": [{"name": "Alice", "email": "alice@uni.edu", "sid": "12345"}],
    }
    mf = tmp_path / "submission_metadata.json"
    mf.write_text(json.dumps(data))

    m = GraderMetadata.from_gradescope(path=mf, grader_name="CS101")
    assert m.grader_name == "CS101"
    assert m.assignment == "Lab 3"
    assert m.submission_time is not None
    assert m.due_date is not None
    assert m.is_late is True
    assert len(m.submitters) == 1
    assert m.submitters[0].name == "Alice"
    assert m.submitters[0].sid == "12345"


def test_from_gradescope_missing_file(tmp_path):
    m = GraderMetadata.from_gradescope(path=tmp_path / "missing.json")
    assert m.submission_time is None
    assert m.due_date is None
    assert m.submitters == []


def test_from_gradescope_kwargs_override_title(tmp_path):
    data = {
        "assignment": {"title": "From file"},
    }
    mf = tmp_path / "submission_metadata.json"
    mf.write_text(json.dumps(data))

    # Explicit assignment= kwarg should win over the file's title
    m = GraderMetadata.from_gradescope(path=mf, assignment="Explicit")
    assert m.assignment == "Explicit"


# ---------------------------------------------------------------------------
# PipelineScore integration
# ---------------------------------------------------------------------------


def test_pipeline_score_carries_metadata():
    from lograder.pipeline.score import GradescopeConfig, PipelineScore

    m = GraderMetadata(grader_name="TestGrader")
    score = PipelineScore(metadata=m)
    d = score.to_gradescope_dict(config=GradescopeConfig())
    assert "TestGrader" in d.get("output", "")


def test_pipeline_score_metadata_kwarg_override():
    from lograder.pipeline.score import GradescopeConfig, PipelineScore

    m1 = GraderMetadata(grader_name="Grader1")
    m2 = GraderMetadata(grader_name="Grader2")
    score = PipelineScore(metadata=m1)
    d = score.to_gradescope_dict(config=GradescopeConfig(), metadata=m2)
    assert "Grader2" in d.get("output", "")
    assert "Grader1" not in d.get("output", "")


def test_pipeline_score_output_combines_with_config_output():
    from lograder.pipeline.score import GradescopeConfig, PipelineScore

    m = GraderMetadata(grader_name="MyGrader")
    score = PipelineScore(metadata=m)
    d = score.to_gradescope_dict(
        config=GradescopeConfig(output="Extra message from staff.")
    )
    out = d.get("output", "")
    assert "MyGrader" in out
    assert "Extra message from staff." in out
