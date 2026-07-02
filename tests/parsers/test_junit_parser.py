from __future__ import annotations

import pytest

from lograder.process.parsers.junit import JUnitTestCase, parse_junit_xml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASSING_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="MyTests" tests="1" failures="0" errors="0">
    <testcase name="test_add" classname="MyTests" time="0.042"/>
  </testsuite>
</testsuites>
"""

FAILING_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="MyTests" tests="1" failures="1" errors="0">
    <testcase name="test_add" classname="MyTests" time="0.007">
      <failure message="REQUIRE( 1 == 2 ) failed" type="REQUIRE">at test.cpp:10</failure>
    </testcase>
  </testsuite>
</testsuites>
"""

ERROR_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="MySuite" tests="1" errors="1">
  <testcase name="test_setup" classname="MySuite" time="0.001">
    <error message="setup failed">traceback here</error>
  </testcase>
</testsuite>
"""

SKIPPED_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="MySuite" tests="1">
  <testcase name="test_skip" classname="MySuite" time="0.000">
    <skipped message="reason"/>
  </testcase>
</testsuite>
"""

MIXED_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="Suite" tests="4">
    <testcase name="test_pass" classname="Suite" time="0.001"/>
    <testcase name="test_fail" classname="Suite" time="0.002">
      <failure message="oops" type="AssertionError">line 42</failure>
    </testcase>
    <testcase name="test_skip" classname="Suite" time="0.000">
      <skipped/>
    </testcase>
    <testcase name="test_error" classname="Suite" time="0.003">
      <error message="boom">traceback</error>
    </testcase>
  </testsuite>
</testsuites>
"""

STDOUT_STDERR_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="S" tests="1">
  <testcase name="t" classname="S" time="0.010">
    <system-out>hello stdout</system-out>
    <system-err>hello stderr</system-err>
  </testcase>
</testsuite>
"""

MULTI_SUITE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="Alpha" tests="1">
    <testcase name="test_a" classname="Alpha" time="0.001"/>
  </testsuite>
  <testsuite name="Beta" tests="1">
    <testcase name="test_b" classname="Beta" time="0.002"/>
  </testsuite>
</testsuites>
"""

# Bare <testsuite> root (not wrapped in <testsuites>)
BARE_SUITE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="BareRoot" tests="2">
  <testcase name="test_one" classname="BareRoot" time="0.001"/>
  <testcase name="test_two" classname="BareRoot" time="0.002"/>
</testsuite>
"""


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------


def test_empty_string_raises_value_error():
    with pytest.raises(ValueError, match="Malformed"):
        parse_junit_xml("")


def test_whitespace_only_string_raises_value_error():
    with pytest.raises(ValueError, match="Malformed"):
        parse_junit_xml("   \n  ")


def test_malformed_xml_raises_value_error():
    with pytest.raises(ValueError, match="Malformed"):
        parse_junit_xml("<not valid xml")


def test_single_passing_testcase():
    cases = parse_junit_xml(PASSING_XML)
    assert len(cases) == 1
    tc = cases[0]
    assert tc.test_name == "test_add"
    assert tc.suite_name == "MyTests"
    assert tc.classname == "MyTests"
    assert tc.time == pytest.approx(0.042)
    assert tc.passed is True
    assert tc.skipped is False


def test_single_failing_testcase():
    cases = parse_junit_xml(FAILING_XML)
    assert len(cases) == 1
    tc = cases[0]
    assert tc.test_name == "test_add"
    assert tc.passed is False
    assert tc.failure_message == "REQUIRE( 1 == 2 ) failed"
    assert tc.failure_type == "REQUIRE"
    assert "test.cpp:10" in (tc.failure_text or "")


def test_single_error_testcase():
    cases = parse_junit_xml(ERROR_XML)
    assert len(cases) == 1
    tc = cases[0]
    assert tc.passed is False
    assert tc.error_message == "setup failed"
    assert "traceback" in (tc.error_text or "")
    assert tc.failure_message is None


def test_skipped_testcase():
    cases = parse_junit_xml(SKIPPED_XML)
    assert len(cases) == 1
    tc = cases[0]
    assert tc.skipped is True
    assert tc.passed is False


def test_mixed_cases():
    cases = parse_junit_xml(MIXED_XML)
    assert len(cases) == 4
    names = [tc.test_name for tc in cases]
    assert names == ["test_pass", "test_fail", "test_skip", "test_error"]

    passing = [tc for tc in cases if tc.passed]
    failing = [tc for tc in cases if not tc.passed and not tc.skipped]
    skipped = [tc for tc in cases if tc.skipped]
    assert len(passing) == 1
    assert len(failing) == 2  # test_fail + test_error
    assert len(skipped) == 1


def test_stdout_stderr_captured():
    cases = parse_junit_xml(STDOUT_STDERR_XML)
    assert len(cases) == 1
    tc = cases[0]
    assert tc.stdout == "hello stdout"
    assert tc.stderr == "hello stderr"


def test_missing_stdout_stderr_are_empty_strings():
    cases = parse_junit_xml(PASSING_XML)
    tc = cases[0]
    assert tc.stdout == ""
    assert tc.stderr == ""


def test_duration_parsed():
    cases = parse_junit_xml(PASSING_XML)
    assert cases[0].time == pytest.approx(0.042)


def test_missing_time_is_none():
    xml = "<testsuite name='S'><testcase name='t' classname='S'/></testsuite>"
    cases = parse_junit_xml(xml)
    assert cases[0].time is None


def test_testsuites_wrapper():
    cases = parse_junit_xml(PASSING_XML)
    assert len(cases) == 1
    assert cases[0].suite_name == "MyTests"


def test_bare_testsuite_root():
    cases = parse_junit_xml(BARE_SUITE_XML)
    assert len(cases) == 2
    assert {tc.test_name for tc in cases} == {"test_one", "test_two"}
    assert all(tc.suite_name == "BareRoot" for tc in cases)


def test_multiple_suites_flat_list():
    cases = parse_junit_xml(MULTI_SUITE_XML)
    assert len(cases) == 2
    suite_names = {tc.suite_name for tc in cases}
    assert suite_names == {"Alpha", "Beta"}


def test_classname_defaults_to_suite_name_when_missing():
    xml = "<testsuite name='S'><testcase name='t'/></testsuite>"
    cases = parse_junit_xml(xml)
    assert cases[0].classname == "S"


def test_classname_uses_explicit_value():
    cases = parse_junit_xml(PASSING_XML)
    assert cases[0].classname == "MyTests"


def test_passed_property_true_for_no_failure_or_error():
    tc = JUnitTestCase(
        suite_name="S",
        test_name="t",
        classname="S",
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
    assert tc.passed is True


def test_passed_property_false_when_failure_message():
    tc = JUnitTestCase(
        suite_name="S",
        test_name="t",
        classname="S",
        time=None,
        failure_message="oops",
        failure_type=None,
        failure_text=None,
        error_message=None,
        error_text=None,
        skipped=False,
        stdout="",
        stderr="",
    )
    assert tc.passed is False


def test_passed_property_false_when_skipped():
    tc = JUnitTestCase(
        suite_name="S",
        test_name="t",
        classname="S",
        time=None,
        failure_message=None,
        failure_type=None,
        failure_text=None,
        error_message=None,
        error_text=None,
        skipped=True,
        stdout="",
        stderr="",
    )
    assert tc.passed is False
