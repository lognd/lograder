# Scoring & Gradescope Output

## Overview

Attach a `Scorer` to any step before running the pipeline. After `pipeline()` returns a `PipelineScore`, call `write_results_json()` to produce `/autograder/results/results.json` in the format Gradescope expects.

```python
from lograder.pipeline.score import (
    AllOrNothingScorer,
    CleanRunScorer,
    GimmeConfig,
    GradescopeConfig,
    GradescopeTestConfig,
    TestCaseScorer,
)

build.scorer = AllOrNothingScorer(10.0, label="Build")
check.scorer = CleanRunScorer(0.0, extra_credit=5.0, label="No forbidden operators")
tests.scorer = TestCaseScorer(
    {"test_a": 10.0, "test_b": 10.0, "bonus": 0.0},
    extra_credit_cases={"bonus": 5.0},
    gimme=GimmeConfig(min_pass_fraction=0.25, points=5.0),
    label="Correctness",
)

pipeline.validate_step_types()
score = pipeline()

score.write_results_json(
    config=GradescopeConfig(
        output="See the HTML report for details.",
        visibility="after_due_date",
        stdout_visibility="hidden",
    )
)
```

---

## Scorers

All scorers implement `on_packet(result)`, `on_complete(result)`, and `contribution() → ScoreContribution`. Set `scorer.label` to control the test name in Gradescope output.

### `AllOrNothingScorer(points, *, extra_credit=0.0, label=None)`

Awards full `points` if the step's return is `Ok`, otherwise 0. Useful for build steps.

```python
build.scorer = AllOrNothingScorer(10.0, label="Compilation")
```

### `CleanRunScorer(points, *, max_errors=0, require_ok_return=True, extra_credit=0.0, label=None)`

Awards points if the number of non-fatal `Err` yields is ≤ `max_errors`. Use for check steps where a clean run earns credit (e.g. "no forbidden instructions").

```python
check.scorer = CleanRunScorer(5.0, max_errors=0, label="Style Check")
```

`require_ok_return=True` (default): also zeroes the score if the step fatally returns `Err`.

### `TestCaseScorer(points_per_case, *, num_cases=None, extra_credit_cases=None, gimme=None, label=None)`

Awards points per passing test case. Recognises `TestSuccess` and `TestFailure` packets from any test step.

`points_per_case` can be:
- `dict[str, float]` — maps case name → points
- `float` — flat points per case (requires `num_cases`)

```python
tests.scorer = TestCaseScorer(
    {"add": 5.0, "subtract": 5.0, "edge_cases": 10.0},
    label="Correctness",
)

# Flat points
tests.scorer = TestCaseScorer(5.0, num_cases=4, label="Tests")
```

**Extra credit cases** — pass in `extra_credit_cases` as `{case_name: bonus_points}`. These are NOT counted in `possible`.

```python
tests.scorer = TestCaseScorer(
    {"a": 10.0, "b": 10.0},
    extra_credit_cases={"bonus": 5.0},
    label="Correctness",
)
```

**Gimme floor** — if the student passes ≥ `min_pass_fraction` of *attempted* (non-error) cases, `earned` is raised to at least `gimme.points`. Cases that failed with a fatal `TestError` don't count against the fraction.

```python
tests.scorer = TestCaseScorer(
    5.0, num_cases=10,
    gimme=GimmeConfig(min_pass_fraction=0.5, points=10.0),
    label="Tests",
)
```

---

## ScoreContribution

`ScoreContribution(earned, possible, extra_credit=0.0)` — `.total` = earned + extra_credit.

`PipelineScore.total()` sums all contributions. Steps skipped by early pipeline exit contribute `0 / possible` so `total().possible` always equals the full assignment total.

---

## Gradescope output

### `GradescopeConfig` — top-level settings

| Field | Default | Notes |
|-------|---------|-------|
| `output` | `""` | Text above the test list on the Gradescope page |
| `output_format` | `"simple_format"` | `"text"`, `"html"`, `"simple_format"`, `"md"`, `"ansi"` |
| `test_output_format` | `"text"` | Default format for per-test output strings |
| `test_name_format` | `"text"` | Default format for test names |
| `visibility` | `"visible"` | Default visibility for all tests |
| `stdout_visibility` | `"hidden"` | Whether run_autograder stdout is shown to students |
| `execution_time` | `None` | Seconds (optional) |
| `extra_data` | `{}` | Arbitrary extra data |
| `leaderboard` | `[]` | `[{"name": "Accuracy", "value": 0.93}, ...]` |

Visibility options: `"hidden"`, `"after_due_date"`, `"after_published"`, `"visible"`.

### `GradescopeTestConfig` — per-test settings

Attach to a scorer before running:

```python
build.scorer = AllOrNothingScorer(10.0, label="Compilation")
build.scorer.gradescope = GradescopeTestConfig(
    output="If this fails, check that your CMakeLists.txt is present.",
    visibility="visible",   # always visible even if top-level is after_due_date
    number="1",
)

tests.scorer = TestCaseScorer({"a": 10.0, "b": 10.0}, label="Correctness")
tests.scorer.gradescope = GradescopeTestConfig(
    visibility="after_due_date",
    tags=["correctness"],
    output_format="ansi",
)
```

| Field | Default | Notes |
|-------|---------|-------|
| `output` | `""` | Student-facing text for this test entry |
| `visibility` | `None` (inherit top-level) | Overrides top-level visibility for this test |
| `status` | `None` (auto) | Force `"passed"` or `"failed"` regardless of score |
| `number` | `""` | e.g. `"1.1"` — controls display order |
| `tags` | `[]` | Arbitrary tag strings |
| `output_format` | `None` (inherit) | Format for this test's output string |
| `name_format` | `None` (inherit) | Format for this test's name |
| `extra_data` | `{}` | Arbitrary extra data |

### `PipelineScore.to_gradescope_dict(config=None, output="")`

Returns the results dict without writing it. Use when you need to post-process (add per-test output dynamically, merge leaderboard data, etc.) before serialising.

```python
data = score.to_gradescope_dict(config=GradescopeConfig(visibility="after_due_date"))
data["tests"][0]["output"] = build_log_text   # enrich before writing
import json, pathlib
pathlib.Path("/autograder/results/results.json").write_text(json.dumps(data))
```

### `PipelineScore.write_results_json(config=None, output="", path=None)`

Writes directly to `/autograder/results/results.json` (or `path` if given). Creates parent directories automatically.

```python
score.write_results_json(
    config=GradescopeConfig(
        output="Grading complete.",
        visibility="after_due_date",
        stdout_visibility="hidden",
    )
)
```

---

## Full example

```python
import json
from pathlib import Path
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import CMakeManifestCheck
from lograder.pipeline.check.source import SourceCheck, OperatorConstraint
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.score import (
    AllOrNothingScorer, CleanRunScorer, TestCaseScorer,
    GradescopeConfig, GradescopeTestConfig, GimmeConfig,
)
import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.check.source
import lograder.output.layout.test.output_compare


def grade(submission_dir: Path) -> None:
    check = SourceCheck(
        files=["solution.cpp"],
        constraints=[OperatorConstraint(tokens=["/", "%"], max_count=0)],
        language="cpp",
        label="No division",
    )
    build = CMakeBuild()
    tests = OutputCompareTest(
        artifact_name="solution",
        cases=[
            OutputCompareCase(name="basic", args=["5"], expected_stdout="8\n"),
            OutputCompareCase(name="zero",  args=["0"], expected_stdout="0\n"),
            OutputCompareCase(name="bonus", args=["100"], expected_stdout="1597\n"),
        ],
    )

    check.scorer = CleanRunScorer(5.0, label="No division operators")
    check.scorer.gradescope = GradescopeTestConfig(
        visibility="visible",
        output="Points deducted if / or % operators are used.",
    )

    build.scorer = AllOrNothingScorer(10.0, label="Compilation")
    build.scorer.gradescope = GradescopeTestConfig(visibility="visible")

    tests.scorer = TestCaseScorer(
        {"basic": 10.0, "zero": 10.0, "bonus": 0.0},
        extra_credit_cases={"bonus": 5.0},
        gimme=GimmeConfig(min_pass_fraction=0.5, points=5.0),
        label="Correctness",
    )
    tests.scorer.gradescope = GradescopeTestConfig(visibility="after_due_date")

    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(submission_dir),
        CMakeManifestCheck(),
        check,
        build,
        tests,
    ]
    pipeline.validate_step_types()

    with config(root_directory=submission_dir, executable_timeout=10.0):
        score = pipeline()

    score.write_results_json(
        config=GradescopeConfig(
            output="Autograding complete. See test details below.",
            visibility="after_due_date",
            stdout_visibility="hidden",
        )
    )


if __name__ == "__main__":
    grade(Path("/autograder/submission"))
```
