from __future__ import annotations

from typing import Optional, Dict, List, Any, Generator
from pydantic import BaseModel, model_validator, Field, computed_field
from pathlib import Path
import json

from .tests import TestInterface, TestEntry, TextFormat, Visibility, CxxProjectBuilder, CxxExecutableTest, CxxExecutableConfig
from .leaderboard import LeaderboardEntry

class GradeEntry(BaseModel):
    score: Optional[float] = None
    output: Optional[str] = None  # Text relevant to the entire submission
    output_format: Optional[TextFormat] = "ansi"
    test_output_format: Optional[TextFormat] = "ansi"
    visibility: Optional[Visibility] = "visible"
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tests: Optional[List[TestEntry]]
    leaderboard: Optional[List[LeaderboardEntry]] = None

    @model_validator(mode="after")
    def check_score_existence(self):
        if not self.tests:
            if self.score is None:
                raise ValueError("If there are no tests specified, please pass `score` to Grade object.")
        elif all([test.is_scored for test in self.tests]):
            if self.score is not None:  # Technically, you are allowed to overwrite, but that's stupid.
                raise ValueError("You have specified tests with `tests`, but you are overwriting the score of the Grade object.")
        return self

    @computed_field
    @property
    def execution_time(self) -> float:
        total = 0.0
        for test in self.tests:
            total += test.execution_time
        return total

class Grader:
    def __init__(self):
        self.tests: List[TestInterface] = []

    def add_cxx_executables_from_generator(self, generator: Generator[CxxExecutableConfig, None, None]):
        builder = CxxProjectBuilder()
        executable = builder.get_executable_path()
        for test_config in generator:
            self.tests.append(CxxExecutableTest(test_config.name, test_config.visibility, executable, test_config.expected_output, test_config.program_input))

    def add_cxx_executables_from_config(self, config_file: Path | str):
        config_file = Path(config_file)
        config = json.load(open(config_file))

        if config["cxx-executables"]:
            builder = CxxProjectBuilder()
            executable = builder.get_executable_path()
        for test in config["cxx-executables"]:
            self.tests.append(CxxExecutableTest(test["name"], test["visibility"], executable, Path(test["output"]), Path(test["input"])))

    def grade(self) -> GradeEntry:
        test_results: List[TestEntry] = []
        for test in self.tests:
            test_results.append(test.serialize())
        points_per = 100.0 / len(self.tests)
        for test_result in test_results:
            test_result.score = points_per * test_result.score
            test_result.max_score = points_per * test_result.score
        return GradeEntry(
            tests=test_results
        )

