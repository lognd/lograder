# mypy: ignore-errors
from __future__ import annotations

import pytest

from lograder.common import Empty, Ok
from lograder.pipeline.config import config
from lograder.pipeline.test.ctest import (
    CTestError,
    CTestFailure,
    CTestSuccess,
    CTestTest,
)
from lograder.pipeline.types.artifacts import CMakeArtifact, FileArtifact
from lograder.process.executable import ExecutableOutput
from lograder.process.registry.ctest import CTestExecutable

# ---------------------------------------------------------------------------
# XML samples
# ---------------------------------------------------------------------------

_PASSING_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="CTestSuite">
    <testcase name="test_math" classname="CTestSuite" time="0.100"/>
    <testcase name="test_io" classname="CTestSuite" time="0.200"/>
  </testsuite>
</testsuites>
"""

_FAILING_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="CTestSuite">
    <testcase name="test_math" classname="CTestSuite" time="0.100"/>
    <testcase name="test_bad" classname="CTestSuite" time="0.050">
      <failure message="Test failed" type="">Process exited with code 1</failure>
    </testcase>
  </testsuite>
</testsuites>
"""

_EMPTY_XML = "<testsuites><testsuite name='S'/></testsuites>"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_step(step, artifacts):
    gen = step(artifacts)
    packets = []
    try:
        while True:
            packets.append(next(gen))
    except StopIteration as e:
        return packets, e.value


def _fake_executable(monkeypatch, xml_content: str, return_code: int = 0):
    """Patch CTestExecutable so it writes xml_content to args.output_junit."""

    def fake_check_runnable(self):
        return Ok(Empty())

    def fake_call(self, args, input_data, options):
        if args.output_junit is not None and not isinstance(
            args.output_junit, type(None)
        ):
            try:
                args.output_junit.write_text(xml_content, encoding="utf-8")
            except Exception:
                pass
        return Ok(
            ExecutableOutput(
                command=["ctest"],
                stdout_bytes=b"",
                stderr_bytes=b"",
                return_code=return_code,
            )
        )

    monkeypatch.setattr(CTestExecutable, "check_runnable", fake_check_runnable)
    monkeypatch.setattr(CTestExecutable, "__call__", fake_call)


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------


def test_no_artifact_or_build_dir_raises():
    with pytest.raises(ValueError, match="artifact_name.*build_dir"):
        CTestTest()


def test_explicit_build_dir_ok(tmp_path):
    step = CTestTest(build_dir=tmp_path)
    assert step is not None


def test_artifact_name_ok():
    step = CTestTest(artifact_name="my_target")
    assert step is not None


# ---------------------------------------------------------------------------
# Build dir resolution errors
# ---------------------------------------------------------------------------


def test_non_cmake_artifact_is_fatal(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _PASSING_XML)
    (tmp_path / "f").write_text("x")
    file_art = FileArtifact(path=tmp_path / "f")
    step = CTestTest(artifact_name="prog")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"prog": file_art})

    assert result.is_err
    assert isinstance(result.danger_err, CTestError)


def test_missing_artifact_is_fatal(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _PASSING_XML)
    step = CTestTest(artifact_name="missing")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {})

    assert result.is_err
    assert isinstance(result.danger_err, CTestError)


# ---------------------------------------------------------------------------
# Integration: monkeypatched CTestExecutable
# ---------------------------------------------------------------------------


def test_passing_cases(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _PASSING_XML)
    step = CTestTest(build_dir=tmp_path)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {})

    assert result.is_ok
    assert len(packets) == 2
    assert all(p.is_ok for p in packets)
    names = {p.danger_ok.test_name for p in packets}
    assert names == {"CTestSuite/test_math", "CTestSuite/test_io"}


def test_failing_cases(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _FAILING_XML)
    step = CTestTest(build_dir=tmp_path)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {})

    assert result.is_ok
    assert len(packets) == 2
    ok_names = {p.danger_ok.test_name for p in packets if p.is_ok}
    err_names = {p.danger_err.test_name for p in packets if p.is_err}
    assert ok_names == {"CTestSuite/test_math"}
    assert err_names == {"CTestSuite/test_bad"}


def test_failure_packet_fields(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _FAILING_XML)
    step = CTestTest(build_dir=tmp_path)

    with config(root_directory=tmp_path):
        packets, _ = _run_step(step, {})

    failure = next(p.danger_err for p in packets if p.is_err)
    assert isinstance(failure, CTestFailure)
    assert failure.failure_message == "Test failed"
    assert "code 1" in failure.failure_text


def test_success_packet_fields(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _PASSING_XML)
    step = CTestTest(build_dir=tmp_path)

    with config(root_directory=tmp_path):
        packets, _ = _run_step(step, {})

    success = packets[0].danger_ok
    assert isinstance(success, CTestSuccess)
    assert success.suite_name == "CTestSuite"
    assert success.duration == pytest.approx(0.100)


def test_build_dir_resolved_from_cmake_artifact(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _PASSING_XML)
    cmake_art = CMakeArtifact(
        name="my_target",
        target_type="EXECUTABLE",
        build_dir=tmp_path,
    )
    step = CTestTest(artifact_name="my_target")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"my_target": cmake_art})

    assert result.is_ok
    assert len(packets) == 2


def test_explicit_build_dir_wins_over_artifact(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _PASSING_XML)
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    cmake_art = CMakeArtifact(name="t", target_type="EXECUTABLE", build_dir=other_dir)
    step = CTestTest(artifact_name="t", build_dir=tmp_path)

    with config(root_directory=tmp_path):
        _, result = _run_step(step, {"t": cmake_art})

    assert result.is_ok


def test_warn_no_tests_true_is_fatal(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _EMPTY_XML)
    step = CTestTest(build_dir=tmp_path, warn_no_tests=True)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {})

    assert result.is_err
    assert isinstance(result.danger_err, CTestError)


def test_warn_no_tests_false_returns_ok(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _EMPTY_XML)
    step = CTestTest(build_dir=tmp_path, warn_no_tests=False)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {})

    assert result.is_ok
    assert packets == []


def test_artifacts_returned_unchanged(tmp_path, monkeypatch):
    _fake_executable(monkeypatch, _PASSING_XML)
    cmake_art = CMakeArtifact(name="t", target_type="EXECUTABLE", build_dir=tmp_path)
    artifacts = {"t": cmake_art}
    step = CTestTest(artifact_name="t")

    with config(root_directory=tmp_path):
        _, result = _run_step(step, artifacts)

    assert result.is_ok
    assert result.danger_ok is artifacts
