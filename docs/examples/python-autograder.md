# Example: Python autograder

A complete grader for a Python project with pytest integration, source checks, and scoring.

## Assignment spec

Students submit a Python project with:
- `graph.py` -- a `Graph` class implementing BFS and DFS
- `tests/test_graph.py` -- their own tests (ignored for grading)

## Score breakdown

| Component | Points |
|-----------|--------|
| Files present | 0 (gate) |
| No forbidden imports | 5 |
| Correctness (instructor tests) | 75 |
| Edge cases (extra credit) | +10 |
| **Total** | **80 + 10 EC** |

## Full autograder

```python
# autograder.py
from pathlib import Path

from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker
from lograder.pipeline.check.source.source_check import SourceCheck, ImportConstraint
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.test.pytest import PytestTest
from lograder.pipeline.score import (
    AllOrNothingScorer, CleanRunScorer, TestCaseScorer,
    GimmeConfig, GradescopeConfig,
)
from lograder.pipeline.pipeline import Pipeline

# -- Manifest ------------------------------------------------------------------

make_simple_manifest_checker(
    "graph",
    required_files=["graph.py"],
)

# -- Test cases ----------------------------------------------------------------

# Instructor test cases live in /autograder/source/instructor_tests/
INSTRUCTOR_TESTS = Path("/autograder/source/instructor_tests")

# We also test the CLI interface (if the assignment has one)
CLI_CASES = [
    OutputCompareCase(
        name="bfs_simple",
        args=["bfs", "A"],
        stdin=b"",
        expected_stdout="A B C\n",
    ),
    OutputCompareCase(
        name="dfs_simple",
        args=["dfs", "A"],
        stdin=b"",
        expected_stdout="A C B\n",
    ),
]

# -- Pipeline ------------------------------------------------------------------

pipeline = Pipeline()
pipeline.add(inp    := LocalDirectory())
pipeline.add(check  := PyProjectManifestCheck())
pipeline.add(source := SourceCheck(
    files=["graph.py"],
    constraints=[
        ImportConstraint(module="networkx",          forbidden=True),  # must implement from scratch
        ImportConstraint(module="collections.deque", forbidden=False),  # allowed
    ],
))
pipeline.add(pytest_step := PytestTest(
    test_paths=[INSTRUCTOR_TESTS],
))

# -- Scorers -------------------------------------------------------------------

check.scorer  = AllOrNothingScorer(0.0, label="Files present")
source.scorer = CleanRunScorer(5.0, label="No forbidden imports")
pytest_step.scorer = TestCaseScorer(
    {
        "instructor_tests/test_graph.py::test_bfs_basic":    10.0,
        "instructor_tests/test_graph.py::test_bfs_cycle":    10.0,
        "instructor_tests/test_graph.py::test_dfs_basic":    10.0,
        "instructor_tests/test_graph.py::test_dfs_cycle":    10.0,
        "instructor_tests/test_graph.py::test_path_exists":  15.0,
        "instructor_tests/test_graph.py::test_path_missing": 10.0,
        "instructor_tests/test_graph.py::test_empty_graph":  10.0,
        # Extra credit
        "instructor_tests/test_graph.py::test_large_graph":  0.0,
        "instructor_tests/test_graph.py::test_disconnected": 0.0,
    },
    extra_credit_cases={
        "instructor_tests/test_graph.py::test_large_graph":  5.0,
        "instructor_tests/test_graph.py::test_disconnected": 5.0,
    },
    gimme=GimmeConfig(min_pass_fraction=0.25, points=15.0),
    label="Correctness",
)

# -- Entry point ---------------------------------------------------------------

if __name__ == "__main__":
    with config(root_directory=Path("/autograder/submission"), executable_timeout=30.0):
        score = pipeline()

    score.write_results_json(
        config=GradescopeConfig(visibility="visible"),
    )
```

## Instructor test file

```python
# instructor_tests/test_graph.py
import sys
from pathlib import Path

# Add submission to path so we can import the student's graph.py
sys.path.insert(0, str(Path("/autograder/submission")))

import pytest
from graph import Graph


def test_bfs_basic():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    result = g.bfs("A")
    assert result == ["A", "B", "C"]


def test_bfs_cycle():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "A")
    result = g.bfs("A")
    assert "A" in result
    assert "B" in result
    assert result.count("A") == 1  # no duplicates


def test_dfs_basic():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    result = g.dfs("A")
    assert set(result) == {"A", "B", "C"}


def test_dfs_cycle():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("C", "A")
    result = g.dfs("A")
    assert set(result) == {"A", "B", "C"}


def test_path_exists():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    assert g.has_path("A", "C") is True


def test_path_missing():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("C", "D")
    assert g.has_path("A", "D") is False


def test_empty_graph():
    g = Graph()
    assert g.bfs("A") == []
    assert g.dfs("A") == []


# Extra credit
def test_large_graph():
    g = Graph()
    for i in range(1000):
        g.add_edge(str(i), str(i + 1))
    result = g.bfs("0")
    assert len(result) == 1001


def test_disconnected():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("C", "D")
    bfs_a = g.bfs("A")
    assert set(bfs_a) == {"A", "B"}
```

## Gradescope `setup.sh`

```bash
#!/usr/bin/env bash
apt-get update -qq
apt-get install -y python3 python3-pip
pip3 install lograder pytest
```

## Gradescope `run_autograder`

```bash
#!/usr/bin/env bash
cd /autograder/source
python3 autograder.py
```
