from pathlib import Path
from typing import Optional

from ....data.paths import PathConfig
from ....types import Command
from ...unit_testers.catch2 import Catch2UnitTester
from .catch2 import Catch2UnitTest


def make_unit_test_from_directory(
    *,
    name: str,
    directory: Path,
    weight: float = 1.0,
    visible: bool = True,
    stdin: str = "",
    args: Optional[Command] = None,
    wrap_args: bool = False,
) -> Catch2UnitTest:
    tester = Catch2UnitTester()
    tester.set_testing_root(directory)
    tester.set_project_root(PathConfig.DEFAULT_SUBMISSION_PATH)

    test = Catch2UnitTest.make(
        name=name,
        tester=tester,
        weight=weight,
        stdin=stdin,
        args=args,
        wrap_args=wrap_args,
    )
    test.set_visibility(visible)

    return test
