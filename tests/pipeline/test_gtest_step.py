# mypy: ignore-errors
from __future__ import annotations

import stat
from pathlib import Path

from lograder.pipeline.config import config
from lograder.pipeline.test.gtest import (
    GTestError,
    GTestFailure,
    GTestSuccess,
    GTestTest,
    _full_name,
)
from lograder.pipeline.types.artifacts import CMakeArtifact, FileArtifact
from lograder.process.parsers.junit import JUnitTestCase
from lograder.process.registry.gtest import GTestArgs

# ---------------------------------------------------------------------------
# XML samples (gtest uses SuiteName.TestName for classname)
# ---------------------------------------------------------------------------

_PASSING_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="MathTest">
    <testcase name="Add" classname="MathTest" time="0.001"/>
    <testcase name="Sub" classname="MathTest" time="0.002"/>
  </testsuite>
</testsuites>
"""

_FAILING_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="MathTest">
    <testcase name="Add" classname="MathTest" time="0.001"/>
    <testcase name="BadAssert" classname="MathTest" time="0.003">
      <failure message="Expected: 1&#10;  Actual: 2" type=""><![CDATA[test.cc:42
Expected: 1
  Actual: 2]]></failure>
    </testcase>
  </testsuite>
</testsuites>
"""

_SKIPPED_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="S">
    <testcase name="pass" classname="S" time="0.001"/>
    <testcase name="disabled" classname="S" time="0.000">
      <skipped/>
    </testcase>
  </testsuite>
</testsuites>
"""

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


def _make_fake_bin(tmp_path: Path, xml_content: str, exit_code: int = 0) -> Path:
    """Fake gtest binary: reads --gtest_output=xml:<path>, writes XML there."""
    script = tmp_path / f"fake_gtest_{id(xml_content)}"
    script.write_text(
        f"""\
#!/usr/bin/env python3
import sys
out_path = None
for arg in sys.argv[1:]:
    if arg.startswith("--gtest_output=xml:"):
        out_path = arg.split("xml:", 1)[1]
        break
if out_path:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write({repr(xml_content)})
sys.exit({exit_code})
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


# ---------------------------------------------------------------------------
# _full_name helper
# ---------------------------------------------------------------------------


def _tc(suite_name: str, test_name: str) -> JUnitTestCase:
    return JUnitTestCase(
        suite_name=suite_name,
        test_name=test_name,
        classname=suite_name,
        time=None,
        failure_message=None,
        failure_type=None,
        failure_text=None,
        error_message=None,
        error_text=None,
        skipped=False,
        stdout="",
        stderr="",
    )


def test_full_name_uses_dot_separator():
    assert _full_name(_tc("MathTest", "Add")) == "MathTest.Add"


def test_full_name_same_suite_and_name():
    assert _full_name(_tc("Add", "Add")) == "Add"


def test_full_name_empty_suite():
    assert _full_name(_tc("", "Add")) == "Add"


# ---------------------------------------------------------------------------
# Step error paths
# ---------------------------------------------------------------------------


def test_missing_artifact_is_fatal():
    step = GTestTest("missing")
    packets, result = _run_step(step, {})
    assert result.is_err
    assert isinstance(result.danger_err, GTestError)
    assert packets == []


def test_non_file_artifact_is_fatal(tmp_path):
    cmake_art = CMakeArtifact(
        name="tests", target_type="EXECUTABLE", build_dir=tmp_path
    )
    step = GTestTest("tests")
    packets, result = _run_step(step, {"tests": cmake_art})
    assert result.is_err
    assert isinstance(result.danger_err, GTestError)


# ---------------------------------------------------------------------------
# Integration: fake binary
# ---------------------------------------------------------------------------


def test_passing_cases(tmp_path):
    binary = _make_fake_bin(tmp_path, _PASSING_XML)
    artifact = FileArtifact(path=binary)
    step = GTestTest("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert len(packets) == 2
    assert all(p.is_ok for p in packets)
    names = {p.danger_ok.test_name for p in packets}
    assert names == {"MathTest.Add", "MathTest.Sub"}


def test_failing_cases(tmp_path):
    binary = _make_fake_bin(tmp_path, _FAILING_XML)
    artifact = FileArtifact(path=binary)
    step = GTestTest("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert len(packets) == 2
    ok_names = {p.danger_ok.test_name for p in packets if p.is_ok}
    err_names = {p.danger_err.test_name for p in packets if p.is_err}
    assert ok_names == {"MathTest.Add"}
    assert err_names == {"MathTest.BadAssert"}


def test_failure_packet_fields(tmp_path):
    binary = _make_fake_bin(tmp_path, _FAILING_XML)
    artifact = FileArtifact(path=binary)
    step = GTestTest("tests")

    with config(root_directory=tmp_path):
        packets, _ = _run_step(step, {"tests": artifact})

    failure = next(p.danger_err for p in packets if p.is_err)
    assert isinstance(failure, GTestFailure)
    assert "Expected" in failure.failure_message or "Expected" in failure.failure_text
    assert failure.suite_name == "MathTest"
    assert failure.artifact_name == "tests"


def test_skipped_cases_not_yielded(tmp_path):
    binary = _make_fake_bin(tmp_path, _SKIPPED_XML)
    artifact = FileArtifact(path=binary)
    step = GTestTest("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert len(packets) == 1
    assert packets[0].is_ok
    assert packets[0].danger_ok.test_name == "S.pass"


def test_no_xml_produced_is_fatal(tmp_path):
    script = tmp_path / "no_xml"
    script.write_text("#!/usr/bin/env python3\nimport sys; sys.exit(0)\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    artifact = FileArtifact(path=script)
    step = GTestTest("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_err
    assert isinstance(result.danger_err, GTestError)
    assert packets == []


def test_artifacts_returned_unchanged(tmp_path):
    binary = _make_fake_bin(tmp_path, _PASSING_XML)
    artifact = FileArtifact(path=binary)
    artifacts = {"tests": artifact}
    step = GTestTest("tests")

    with config(root_directory=tmp_path):
        _, result = _run_step(step, artifacts)

    assert result.is_ok
    assert result.danger_ok is artifacts


def test_success_packet_fields(tmp_path):
    binary = _make_fake_bin(tmp_path, _PASSING_XML)
    artifact = FileArtifact(path=binary)
    step = GTestTest("tests")

    with config(root_directory=tmp_path):
        packets, _ = _run_step(step, {"tests": artifact})

    success = packets[0].danger_ok
    assert isinstance(success, GTestSuccess)
    assert success.artifact_name == "tests"
    assert success.suite_name == "MathTest"


def test_gtest_output_arg_is_overridden(tmp_path):
    """base_args.gtest_output is always replaced internally."""
    binary = _make_fake_bin(tmp_path, _PASSING_XML)
    artifact = FileArtifact(path=binary)
    # If gtest_output were not overridden, the binary would write to a
    # user-specified path and not the internal tmpfile, causing parse failure.
    step = GTestTest("tests", base_args=GTestArgs(gtest_output="xml:/dev/null"))

    with config(root_directory=tmp_path):
        _, result = _run_step(step, {"tests": artifact})

    assert result.is_ok


def test_warn_no_tests_true_is_fatal(tmp_path):
    empty_xml = "<testsuites><testsuite name='S'/></testsuites>"
    binary = _make_fake_bin(tmp_path, empty_xml)
    artifact = FileArtifact(path=binary)
    step = GTestTest("tests", warn_no_tests=True)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_err
    assert isinstance(result.danger_err, GTestError)


def test_warn_no_tests_false_returns_ok(tmp_path):
    empty_xml = "<testsuites><testsuite name='S'/></testsuites>"
    binary = _make_fake_bin(tmp_path, empty_xml)
    artifact = FileArtifact(path=binary)
    step = GTestTest("tests", warn_no_tests=False)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert packets == []
