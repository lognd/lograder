from __future__ import annotations

import stat
from pathlib import Path

import pytest

from lograder.pipeline.config import config
from lograder.pipeline.test.catch2 import (
    Catch2Args,
    Catch2Error,
    Catch2Failure,
    Catch2Success,
    Catch2Test,
    _full_name,
)
from lograder.pipeline.types.artifacts import CMakeArtifact, FileArtifact
from lograder.process.parsers.junit import JUnitTestCase

# ---------------------------------------------------------------------------
# XML samples
# ---------------------------------------------------------------------------

_PASSING_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="MyTest">
    <testcase name="adds" classname="MyTest" time="0.001"/>
    <testcase name="subtracts" classname="MyTest" time="0.002"/>
  </testsuite>
</testsuites>
"""

_FAILING_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="MyTest">
    <testcase name="adds" classname="MyTest" time="0.001"/>
    <testcase name="bad" classname="MyTest" time="0.005">
      <failure message="1 != 2" type="REQUIRE">at test.cpp:10</failure>
    </testcase>
  </testsuite>
</testsuites>
"""

_SKIPPED_XML = """\
<?xml version="1.0"?>
<testsuites>
  <testsuite name="MyTest">
    <testcase name="pass" classname="MyTest" time="0.001"/>
    <testcase name="skip" classname="MyTest" time="0.000">
      <skipped/>
    </testcase>
  </testsuite>
</testsuites>
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_step(step, artifacts):
    """Drive a generator step to completion, returning (packets, final_result)."""
    gen = step(artifacts)
    packets = []
    try:
        while True:
            packets.append(next(gen))
    except StopIteration as e:
        return packets, e.value


def _make_fake_bin(tmp_path: Path, xml_content: str, exit_code: int = 0) -> Path:
    """Create a Python script that writes xml_content to the --out path and exits."""
    script = tmp_path / f"fake_catch2_{id(xml_content)}"
    script.write_text(
        f"""\
#!/usr/bin/env python3
import sys
args = sys.argv[1:]
out_path = None
i = 0
while i < len(args):
    if args[i] == "--out" and i + 1 < len(args):
        out_path = args[i + 1]
        break
    i += 1
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
# Catch2Args emit
# ---------------------------------------------------------------------------


def test_default_args_emit_empty():
    assert Catch2Args().emit() == []


def test_reporter_flag():
    args = Catch2Args(reporter="junit")
    tokens = args.emit()
    assert "--reporter" in tokens
    assert "junit" in tokens


def test_out_flag(tmp_path):
    p = tmp_path / "out.xml"
    args = Catch2Args(out=p)
    tokens = args.emit()
    assert "--out" in tokens
    assert str(p) in tokens


def test_test_spec_is_positional():
    args = Catch2Args(test_spec="[math]")
    tokens = args.emit()
    assert "[math]" in tokens
    assert tokens[-1] == "[math]"


def test_abort_flag():
    args = Catch2Args(abort=True)
    assert "--abort" in args.emit()


def test_order_flag():
    args = Catch2Args(order="rand")
    tokens = args.emit()
    assert "--order" in tokens
    assert "rand" in tokens


def test_rng_seed_flag():
    args = Catch2Args(rng_seed="42")
    tokens = args.emit()
    assert "--rng-seed" in tokens
    assert "42" in tokens


def test_warn_flag():
    args = Catch2Args(warn="NoTests")
    tokens = args.emit()
    assert "--warn" in tokens
    assert "NoTests" in tokens


def test_shard_count_and_index():
    args = Catch2Args(shard_count=4, shard_index=1)
    tokens = args.emit()
    assert "--shard-count" in tokens and "4" in tokens
    assert "--shard-index" in tokens and "1" in tokens


def test_false_flags_not_emitted():
    args = Catch2Args(abort=False, list_tests=False)
    tokens = args.emit()
    assert "--abort" not in tokens
    assert "--list-tests" not in tokens


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


def test_full_name_different_suite_and_name():
    assert _full_name(_tc("Suite", "test_add")) == "Suite/test_add"


def test_full_name_same_suite_and_name():
    assert _full_name(_tc("test_add", "test_add")) == "test_add"


def test_full_name_empty_suite():
    assert _full_name(_tc("", "test_add")) == "test_add"


# ---------------------------------------------------------------------------
# Step error paths (no real binary needed)
# ---------------------------------------------------------------------------


def test_missing_artifact_is_fatal():
    step = Catch2Test("missing")
    packets, result = _run_step(step, {})
    assert result.is_err
    assert isinstance(result.danger_err, Catch2Error)
    assert packets == []


def test_non_file_artifact_is_fatal(tmp_path):
    cmake_art = CMakeArtifact(
        name="tests", target_type="EXECUTABLE", build_dir=tmp_path
    )
    step = Catch2Test("tests")
    packets, result = _run_step(step, {"tests": cmake_art})
    assert result.is_err
    assert isinstance(result.danger_err, Catch2Error)


# ---------------------------------------------------------------------------
# Integration: fake binary
# ---------------------------------------------------------------------------


def test_passing_cases(tmp_path):
    binary = _make_fake_bin(tmp_path, _PASSING_XML)
    artifact = FileArtifact(path=binary)
    step = Catch2Test("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert len(packets) == 2
    assert all(p.is_ok for p in packets)
    names = {p.danger_ok.test_name for p in packets}
    assert names == {"MyTest/adds", "MyTest/subtracts"}


def test_failing_cases(tmp_path):
    binary = _make_fake_bin(tmp_path, _FAILING_XML)
    artifact = FileArtifact(path=binary)
    step = Catch2Test("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert len(packets) == 2
    ok_names = {p.danger_ok.test_name for p in packets if p.is_ok}
    err_names = {p.danger_err.test_name for p in packets if p.is_err}
    assert ok_names == {"MyTest/adds"}
    assert err_names == {"MyTest/bad"}


def test_failure_packet_fields(tmp_path):
    binary = _make_fake_bin(tmp_path, _FAILING_XML)
    artifact = FileArtifact(path=binary)
    step = Catch2Test("tests")

    with config(root_directory=tmp_path):
        packets, _ = _run_step(step, {"tests": artifact})

    failure = next(p.danger_err for p in packets if p.is_err)
    assert isinstance(failure, Catch2Failure)
    assert failure.failure_message == "1 != 2"
    assert "test.cpp:10" in failure.failure_text
    assert failure.suite_name == "MyTest"


def test_skipped_cases_not_yielded(tmp_path):
    binary = _make_fake_bin(tmp_path, _SKIPPED_XML)
    artifact = FileArtifact(path=binary)
    step = Catch2Test("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert len(packets) == 1
    assert packets[0].is_ok
    assert packets[0].danger_ok.test_name == "MyTest/pass"


def test_no_xml_produced_is_fatal(tmp_path):
    # Binary that writes nothing
    script = tmp_path / "no_xml"
    script.write_text("#!/usr/bin/env python3\nimport sys; sys.exit(0)\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    artifact = FileArtifact(path=script)
    step = Catch2Test("tests")

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_err
    assert isinstance(result.danger_err, Catch2Error)
    assert packets == []


def test_artifacts_returned_unchanged(tmp_path):
    binary = _make_fake_bin(tmp_path, _PASSING_XML)
    artifact = FileArtifact(path=binary)
    artifacts = {"tests": artifact, "other": artifact}
    step = Catch2Test("tests")

    with config(root_directory=tmp_path):
        _, result = _run_step(step, artifacts)

    assert result.is_ok
    assert result.danger_ok is artifacts


def test_success_packet_fields(tmp_path):
    binary = _make_fake_bin(tmp_path, _PASSING_XML)
    artifact = FileArtifact(path=binary)
    step = Catch2Test("tests")

    with config(root_directory=tmp_path):
        packets, _ = _run_step(step, {"tests": artifact})

    success = packets[0].danger_ok
    assert isinstance(success, Catch2Success)
    assert success.artifact_name == "tests"
    assert success.suite_name == "MyTest"
    assert success.duration == pytest.approx(0.001)


def test_warn_no_tests_true_is_fatal(tmp_path):
    # Binary that writes valid XML with no test cases
    empty_xml = "<testsuites><testsuite name='S'/></testsuites>"
    binary = _make_fake_bin(tmp_path, empty_xml)
    artifact = FileArtifact(path=binary)
    step = Catch2Test("tests", warn_no_tests=True)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_err
    assert isinstance(result.danger_err, Catch2Error)


def test_warn_no_tests_false_returns_ok(tmp_path):
    empty_xml = "<testsuites><testsuite name='S'/></testsuites>"
    binary = _make_fake_bin(tmp_path, empty_xml)
    artifact = FileArtifact(path=binary)
    step = Catch2Test("tests", warn_no_tests=False)

    with config(root_directory=tmp_path):
        packets, result = _run_step(step, {"tests": artifact})

    assert result.is_ok
    assert packets == []
