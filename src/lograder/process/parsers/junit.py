"""JUnit XML parser  -  shared by CTest, Catch2, and Google Test output."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True)
class JUnitTestCase:
    suite_name: str
    test_name: str
    classname: str
    time: float | None
    failure_message: str | None
    failure_type: str | None
    failure_text: str | None
    error_message: str | None
    error_text: str | None
    skipped: bool
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return (
            self.failure_message is None
            and self.failure_text is None
            and self.error_message is None
            and not self.skipped
        )


def parse_junit_xml(content: str) -> list[JUnitTestCase]:
    """Parse JUnit XML produced by CTest, Catch2, or gtest into a flat list of test cases."""
    try:
        root = ET.fromstring(content.strip())
    except ET.ParseError as exc:
        raise ValueError(f"Malformed JUnit XML: {exc}") from exc

    # Root may be <testsuites> (wrapping) or a bare <testsuite>
    if root.tag == "testsuites":
        suites = list(root.iter("testsuite"))
    elif root.tag == "testsuite":
        suites = [root] + [el for el in root.iter("testsuite") if el is not root]
    else:
        suites = list(root.iter("testsuite"))

    cases: list[JUnitTestCase] = []
    for suite in suites:
        suite_name = suite.get("name", "")
        for tc in suite.findall("testcase"):
            name = tc.get("name", "")
            classname = tc.get("classname", suite_name)
            raw_time = tc.get("time")
            time = float(raw_time) if raw_time is not None else None

            failure_el = tc.find("failure")
            error_el = tc.find("error")
            skipped_el = tc.find("skipped")
            stdout_el = tc.find("system-out")
            stderr_el = tc.find("system-err")

            cases.append(
                JUnitTestCase(
                    suite_name=suite_name,
                    test_name=name,
                    classname=classname,
                    time=time,
                    failure_message=(
                        failure_el.get("message") if failure_el is not None else None
                    ),
                    failure_type=(
                        failure_el.get("type") if failure_el is not None else None
                    ),
                    failure_text=(
                        (failure_el.text or "").strip()
                        if failure_el is not None
                        else None
                    ),
                    error_message=(
                        error_el.get("message") if error_el is not None else None
                    ),
                    error_text=(
                        (error_el.text or "").strip() if error_el is not None else None
                    ),
                    skipped=skipped_el is not None,
                    stdout=(stdout_el.text or "") if stdout_el is not None else "",
                    stderr=(stderr_el.text or "") if stderr_el is not None else "",
                )
            )
    return cases
