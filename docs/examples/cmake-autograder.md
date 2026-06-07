# Example: CMake autograder

A complete grader for a C++ CMake project with output tests, Valgrind memory checking, performance tests, and source code checks.

## Assignment spec

Students submit a CMake project with:
- `CMakeLists.txt`
- `src/sorter.cpp`
- `src/sorter.h`

The project builds a `sorter` binary that reads integers from stdin and prints them sorted.

## Score breakdown

| Component | Points |
|-----------|--------|
| Files present | 0 (required gate) |
| No forbidden operations | 10 |
| Build | 10 |
| Correctness | 60 |
| Performance | 20 |
| No memory leaks (extra credit) | +10 |
| **Total** | **100 + 10 EC** |

## Full autograder

```python
# pipeline.py
from pathlib import Path

from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.check.project.simple_project import CMakeManifestCheck
from lograder.pipeline.check.source.source_check import (
    IncludeConstraint,
    IdentifierConstraint,
    OperatorConstraint,
    QualifiedNameConstraint,
    SourceCheck,
)
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.metadata import GraderMetadata, StaffAuthor
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.score import (
    AllOrNothingScorer,
    CleanRunScorer,
    GimmeConfig,
    GradescopeConfig,
    TestCaseScorer,
)
from lograder.pipeline.test.output_compare import ComparisonMode, OutputCompareCase, OutputCompareTest
from lograder.pipeline.test.performance import PerformanceCase, PerformanceTest
from lograder.pipeline.test.valgrind import ValgrindCase, ValgrindTest

_SUBMISSION_DIR = Path("/autograder/submission")

# -- Test cases ----------------------------------------------------------------

OUTPUT_CASES = [
    OutputCompareCase(name="empty",          args=[], stdin=b"",           expected_stdout=""),
    OutputCompareCase(name="single",         args=[], stdin=b"42\n",       expected_stdout="42\n"),
    OutputCompareCase(name="already_sorted", args=[], stdin=b"1\n2\n3\n",  expected_stdout="1\n2\n3\n"),
    OutputCompareCase(name="reverse_sorted", args=[], stdin=b"3\n2\n1\n",  expected_stdout="1\n2\n3\n"),
    OutputCompareCase(name="duplicates",     args=[], stdin=b"5\n3\n3\n1\n", expected_stdout="1\n3\n3\n5\n"),
    OutputCompareCase(
        name="negatives",
        args=[],
        stdin=b"-2\n0\n-1\n",
        expected_stdout="-2\n-1\n0\n",
        comparison=ComparisonMode.EXACT,
    ),
]

VALGRIND_CASES = [
    ValgrindCase(name="no_leaks_empty",  args=[], stdin=b"",          check_leaks=True),
    ValgrindCase(name="no_leaks_normal", args=[], stdin=b"3\n1\n2\n", check_leaks=True),
]

PERF_CASES = [
    PerformanceCase(name="perf_1k",   args=[], stdin="\n".join(str(i) for i in range(1000,  0, -1)).encode() + b"\n", time_limit=1.0),
    PerformanceCase(name="perf_100k", args=[], stdin="\n".join(str(i) for i in range(100000, 0, -1)).encode() + b"\n", time_limit=5.0),
]

# -- Pipeline ------------------------------------------------------------------


def make_pipeline(submission_dir: Path = _SUBMISSION_DIR) -> Pipeline:
    pipeline = Pipeline()
    pipeline.add(LocalDirectory(root=submission_dir))
    pipeline.add(check  := CMakeManifestCheck())
    pipeline.add(source := SourceCheck(
        language="cpp",
        files=["src/sorter.cpp", "src/sorter.h"],
        constraints=[
            OperatorConstraint(operator="goto",       forbidden=True),
            IdentifierConstraint(name="malloc",       forbidden=True),
            IdentifierConstraint(name="free",         forbidden=True),
            QualifiedNameConstraint(name="std::sort", forbidden=True),
            IncludeConstraint(header="algorithm",     forbidden=True),
        ],
    ))
    pipeline.add(build  := CMakeBuild())
    pipeline.add(tests  := OutputCompareTest("sorter", OUTPUT_CASES))
    pipeline.add(vg     := ValgrindTest("sorter", VALGRIND_CASES))
    pipeline.add(perf   := PerformanceTest("sorter", PERF_CASES))

    check.scorer  = AllOrNothingScorer(0.0, label="Files present")
    source.scorer = CleanRunScorer(10.0, label="No forbidden operations")
    build.scorer  = AllOrNothingScorer(10.0, label="Build")
    tests.scorer  = TestCaseScorer(
        {
            "empty":          10.0,
            "single":         10.0,
            "already_sorted": 10.0,
            "reverse_sorted": 10.0,
            "duplicates":     10.0,
            "negatives":      10.0,
        },
        gimme=GimmeConfig(min_pass_fraction=0.25, points=10.0),
        label="Correctness",
    )
    vg.scorer   = AllOrNothingScorer(0.0, extra_credit=10.0, label="No memory leaks")
    perf.scorer = TestCaseScorer(
        {"perf_1k": 10.0, "perf_100k": 10.0},
        label="Performance",
    )
    return pipeline


# -- Entry point ---------------------------------------------------------------

if __name__ == "__main__":
    metadata = GraderMetadata.from_gradescope(
        grader_name="CS101 Lab 3 -- Sorter",
        course="CSCI 101",
        version="2024.1",
        authors=[StaffAuthor(name="Prof. Smith", email="smith@uni.edu", role="Instructor")],
        notes="Contact course staff if you believe there is a grading error.",
    )

    with config(root_directory=_SUBMISSION_DIR, executable_timeout=60.0):
        score = make_pipeline()(metadata=metadata)

    score.write_results_json(
        config=GradescopeConfig(
            visibility="visible",
            stdout_visibility="hidden",
        ),
    )
```

## Testing locally

Run against a reference solution:

```python
from pathlib import Path
from lograder.pipeline.config import config
from pipeline import make_pipeline

with config(root_directory=Path("/path/to/reference_solution"), executable_timeout=60.0):
    score = make_pipeline(submission_dir=Path("/path/to/reference_solution"))()

total = score.total()
print(f"Score: {total.earned}/{total.possible} + {total.extra_credit} EC")

for step, contrib in score.contributions:
    status = "check" if contrib.earned >= contrib.possible else "x"
    print(f"  {status} {type(step).__name__}: {contrib.earned}/{contrib.possible}")
```

## Gradescope `setup.sh`

```bash
#!/usr/bin/env bash
apt-get update -qq
apt-get install -y cmake g++ valgrind python3 python3-pip
pip3 install lograder
```

## Gradescope `run_autograder`

```bash
#!/usr/bin/env bash
cd /autograder/source
python3 pipeline.py
```
