from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple, TypeGuard, cast

from ....os.cmd import run_cmd
from ....types import Command, UnitTestCase, UnitTestSuite
from ..interfaces.cli_test import CLITest
from ..interfaces.unit_test import UnitTestInterface

if TYPE_CHECKING:
    from ...unit_testers.unit_tester import UnitTesterInterface
    from ...addons.addon import ExecAddonInterface


def _is_suite(entry: UnitTestCase | UnitTestSuite) -> TypeGuard[UnitTestSuite]:
    return "cases" in entry


class Catch2UnitTest(UnitTestInterface, CLITest):
    HEADER_PATTERN = re.compile(
        r"-{79}\s*\n(.*?)\n-{79}\s*\n(.*?)(?=-{79}|={79}|$)",
        re.DOTALL,
    )

    def __init__(self):
        super().__init__()
        self._name: Optional[str] = None
        self._output: Optional[str] = None

    @classmethod
    def make(
        cls,
        name: str,
        tester: UnitTesterInterface,
        stdin: str,
        weight: float = 1.0,
        args: Optional[Command] = None,
        working_dir: Optional[Path] = None,
        wrap_args: bool = False,
    ) -> Catch2UnitTest:
        test = cls()

        test.set_name(name)
        test.set_tester(tester)
        test.set_input(stdin)
        test.set_weight(weight)

        test.set_wrap_args(wrap_args)
        if working_dir is not None:
            test.set_working_dir(working_dir)
        if args is not None:
            test.set_args(args)

        return test

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
            block = match.group(2).strip()

            # Look for assertion lines
            assertions = []
            for line in block.splitlines():
                if "PASSED" in line or "FAILED" in line:
                    assertions.append(line.strip())

            failed = any("FAILED" in a for a in assertions)
            sections = assertions if assertions else ["Unnamed Case"]

            insert_nested_case(
                top_suite,
                suite_name,
                sections,
                success=not failed,
                output=block,
            )

        return top_suite

    def get_args(self):
        return []

    def get_input(self):
        return ""

    def _run_test(self) -> Tuple[int, Command]:
        builder = self.get_tester()
        builder.build_project()
        if builder.get_build_error():
            self.force_fail()
            self.add_to_output("build-fail", {})
            return 1, []

        self.set_working_dir(builder.get_instance_root())

        command = builder.get_start_command() + self.get_args()

        _tmp_stdout: List[str] = []
        try:
            result = run_cmd(command, self.get_input(), [], _tmp_stdout, [])
        except FileNotFoundError:
            self.force_fail()
            builder.set_build_error()
            self.add_to_output("build-fail", {})
            return 1, []

        self._output = _tmp_stdout.pop()

        return result.returncode, command

    def get_output(self) -> str:
        if self._output is None:
            _, _ = self._run_test()
        assert self._output is not None
        return self._output

    def get_name(self) -> str:
        assert self._name is not None
        return self._name

    def add_exec_addon(self, addon: ExecAddonInterface):
        addon.set_builder(self.get_tester())
        addon.set_args(self.get_args())
        addon.set_input(self.get_input())
        self.add_addon(addon)
