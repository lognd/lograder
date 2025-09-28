import re
from typing import List, Optional, TypeGuard, cast

from ....types import UnitTestCase, UnitTestSuite
from ..interfaces.unit_test import UnitTestInterface


def _is_suite(entry: UnitTestCase | UnitTestSuite) -> TypeGuard[UnitTestSuite]:
    return "cases" in entry


class Catch2UnitTest(UnitTestInterface):
    HEADER_PATTERN = re.compile(
        r"-{70,}\s*\n"  # line of dashes
        r"([^\n]*)\n"  # suite (can be empty)
        r"((?:\s+[^\n]+\n?)+)",  # one or more indented lines (case + nested sections)
        re.MULTILINE,
    )

    def __init__(self):
        super().__init__()
        self._name: Optional[str] = None
        self._output: Optional[str] = None

    def set_name(self, name: str) -> None:
        self._name = name

    def set_output(self, output: str) -> None:
        self._output = output

    def collect_tests(self) -> UnitTestSuite:
        raw = self.get_output()

        def insert_nested_case(
            root: UnitTestSuite,
            suite_name: str,
            sections: List[str],
            success: bool,
            output: str,
        ) -> None:
            if not sections:
                case: UnitTestCase = {
                    "name": suite_name,
                    "success": success,
                    "output": output,
                }
                root["cases"].append(case)
                return

            section = sections[0]
            child_suite: UnitTestSuite | None = None

            for entry in root["cases"]:
                if _is_suite(entry) and entry["name"] == section:
                    child_suite = entry
                    break

            if child_suite is None:
                child_suite = cast(UnitTestSuite, {"name": section, "cases": []})
                root["cases"].append(child_suite)
            assert child_suite is not None
            insert_nested_case(child_suite, suite_name, sections[1:], success, output)

        top_suite: UnitTestSuite = {"name": self.get_name(), "cases": []}

        for match in self.HEADER_PATTERN.finditer(raw):
            suite_name = match.group(1).strip() or "Unnamed Suite"
            case_lines = [
                line.strip() for line in match.group(2).splitlines() if line.strip()
            ]
            sections = case_lines if case_lines else ["Unnamed Case"]

            start = match.end()
            end = raw.find("-" * 70, start)
            if end == -1:
                end = len(raw)
            block = raw[start:end].strip()

            failed = "FAILED" in block
            case_output = block if block else "Test passed"

            insert_nested_case(
                top_suite,
                suite_name,
                sections,
                success=not failed,
                output=case_output,
            )

        return top_suite

    def get_output(self) -> str:
        assert self._output is not None
        return self._output

    def get_name(self) -> str:
        assert self._name is not None
        return self._name
