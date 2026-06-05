# Scoring

lograder's scoring system is a set of `Scorer` objects you attach to step instances before running the pipeline. After `pipeline()` returns, you get a `PipelineScore` with all contributions.

## Quick example

```python
from lograder.pipeline.score import (
    AllOrNothingScorer, CleanRunScorer, TestCaseScorer,
    GimmeConfig, GradescopeConfig,
)

build.scorer  = AllOrNothingScorer(10.0, label="Build")
source.scorer = CleanRunScorer(5.0, label="No goto")
tests.scorer  = TestCaseScorer(
    {"case1": 20.0, "case2": 20.0, "case3": 20.0, "bonus": 0.0},
    extra_credit_cases={"bonus": 10.0},
    gimme=GimmeConfig(min_pass_fraction=0.25, points=5.0),
    label="Correctness",
)

score = pipeline()
score.write_results_json(config=GradescopeConfig(visibility="visible"))
```

---

## Scorers

### `AllOrNothingScorer`

Awards full points if the step returns `Ok`, zero if it returns `Err`. Use for build steps and manifest checks.

```python
AllOrNothingScorer(
    points=10.0,         # points awarded on success
    extra_credit=0.0,    # bonus points on top (optional)
    label="Build",       # displayed in Gradescope
)
```

The scorer fires on the step's final `return` value, not on yields. A step that yields warnings but returns `Ok` gets full points.

### `CleanRunScorer`

Awards points if the number of non-fatal `Err` yields is at or below `max_errors`. Use for source/check steps where a clean run earns credit.

```python
CleanRunScorer(
    points=5.0,              # points awarded on clean run
    max_errors=0,            # tolerated error count (default 0)
    require_ok_return=True,  # also zero out if step returns Err (default True)
    extra_credit=0.0,
    label="No forbidden operations",
)
```

Example: award 5 points if zero `goto` violations found, 0 points otherwise:

```python
source_check.scorer = CleanRunScorer(5.0, label="Code quality")
```

Extra credit variant (doesn't affect `possible` total):

```python
source_check.scorer = CleanRunScorer(0.0, extra_credit=5.0, label="Bonus: clean code")
```

### `TestCaseScorer`

Awards points based on individual test case pass/fail. Use for `OutputCompareTest`, `ValgrindTest`, `PerformanceTest`, and other test steps.

```python
TestCaseScorer(
    points_per_case={"case1": 20.0, "case2": 30.0},
    extra_credit_cases={"bonus": 10.0},      # optional; not counted in possible
    gimme=GimmeConfig(min_pass_fraction=0.25, points=5.0),  # optional floor
    label="Correctness",
)
```

#### Flat points (all cases worth the same)

```python
TestCaseScorer(
    points_per_case=10.0,   # each case worth 10 points
    num_cases=5,            # required when using flat points
    label="Tests",
)
```

#### Extra credit cases

Cases in `extra_credit_cases` don't count toward `possible` — they're pure bonus:

```python
TestCaseScorer(
    {"case1": 20.0, "case2": 20.0, "bonus": 0.0},
    extra_credit_cases={"bonus": 10.0},
)
# possible = 40.0, max earned = 50.0 (40 base + 10 bonus)
```

#### Gimme floor

If a student passes at least `min_pass_fraction` of attempted cases, their earned score is floored up to `gimme.points`:

```python
TestCaseScorer(
    {"case1": 20.0, "case2": 20.0, "case3": 20.0},
    gimme=GimmeConfig(min_pass_fraction=0.25, points=10.0),
    label="Correctness",
)
# Student who passes 1/3 cases (33% > 25%) earns max(20, 10) = 20 points
# Student who passes 0 cases earns 0 (below threshold)
```

Cases skipped due to a fatal `TestError` don't count against the student in the gimme fraction calculation.

---

## `ScoreContribution`

Each scorer produces a `ScoreContribution`:

```python
contribution.earned        # float — base points earned
contribution.possible      # float — maximum possible base points
contribution.extra_credit  # float — bonus earned
contribution.total         # earned + extra_credit
```

---

## `PipelineScore`

```python
score: PipelineScore = pipeline()

# Individual contributions
for step, contrib in score.contributions:
    print(f"{step}: {contrib.earned}/{contrib.possible} (+{contrib.extra_credit})")

# Totals
total = score.total()   # ScoreContribution
total.earned
total.possible
total.total    # earned + extra_credit

# Steps skipped by early exit appear as 0/possible
# so total().possible is always the full assignment total
```

---

## Metadata block

Attach a `GraderMetadata` to automatically include authorship, submission time, late detection, and library attribution in the Gradescope output. See [Metadata](metadata.md) for the full reference.

```python
from lograder.pipeline.metadata import GraderMetadata, StaffAuthor

metadata = GraderMetadata(
    grader_name="CS101 Lab 3",
    authors=[StaffAuthor(name="Prof. Smith", role="Instructor")],
    due_date=datetime(2024, 3, 15, 23, 59, tzinfo=timezone.utc),
)

with config(root_directory=Path("/autograder/submission")):
    score = pipeline(metadata=metadata)   # auto-stamps submission_time

score.write_results_json(config=GradescopeConfig(visibility="visible"))
# → metadata block is prepended to the output field automatically
```

---

## Gradescope output

### `GradescopeConfig`

Global settings for the Gradescope output:

```python
from lograder.pipeline.score import GradescopeConfig

config = GradescopeConfig(
    visibility="visible",          # "visible", "hidden", "after_due_date", "after_published"
    stdout_visibility="visible",   # same options
    output_format="simple_format", # "simple_format", "md", "html", "ansi"
    output="",                     # extra text at the top of the results
    execution_time=None,           # float, optional
)
```

### `GradescopeTestConfig`

Per-scorer (per-step) Gradescope settings. Attach to the scorer:

```python
from lograder.pipeline.score import GradescopeTestConfig

tests.scorer = TestCaseScorer({"case1": 20.0}, label="Correctness")
tests.scorer.gradescope = GradescopeTestConfig(
    visibility="after_due_date",
    output="Check your output carefully.",
    status=None,       # "passed", "failed", or None (computed from score)
    number="1",        # display ordering in Gradescope UI
    tags=["output"],
)
```

### Writing `results.json`

```python
# Write to /autograder/results/results.json (default Gradescope path)
score.write_results_json(config=GradescopeConfig(visibility="visible"))

# Write to a custom path
score.write_results_json(
    config=GradescopeConfig(visibility="visible"),
    path=Path("/tmp/results.json"),
)

# Get the dict without writing
d = score.to_gradescope_dict(config=GradescopeConfig())
```

### Example `results.json`

```json
{
  "score": 70.0,
  "output": "",
  "visibility": "visible",
  "tests": [
    {"name": "Build",        "score": 10.0, "max_score": 10.0, "status": "passed"},
    {"name": "Correctness",  "score": 40.0, "max_score": 60.0, "status": "failed"},
    {"name": "No memory leaks", "score": 0.0, "max_score": 0.0,
     "extra_credit": 10.0, "status": "passed"}
  ]
}
```

---

## Full scoring example

```python
from lograder.pipeline.score import (
    AllOrNothingScorer, CleanRunScorer, TestCaseScorer,
    GimmeConfig, GradescopeConfig, GradescopeTestConfig,
)

# Step scorers
check.scorer  = AllOrNothingScorer(0.0, label="Files submitted")
source.scorer = CleanRunScorer(10.0, label="No goto/malloc")
build.scorer  = AllOrNothingScorer(10.0, label="Build")
tests.scorer  = TestCaseScorer(
    points_per_case={"test_a": 20.0, "test_b": 20.0, "test_c": 20.0, "bonus": 0.0},
    extra_credit_cases={"bonus": 10.0},
    gimme=GimmeConfig(min_pass_fraction=0.25, points=10.0),
    label="Correctness",
)
vg.scorer     = AllOrNothingScorer(0.0, extra_credit=10.0, label="No memory leaks")

# Per-scorer Gradescope settings
tests.scorer.gradescope = GradescopeTestConfig(number="3", visibility="visible")
vg.scorer.gradescope    = GradescopeTestConfig(number="4", visibility="after_due_date")

# Run and write
with config(root_directory=Path("/autograder/submission")):
    score = pipeline()

score.write_results_json(
    config=GradescopeConfig(visibility="visible", stdout_visibility="hidden"),
    output="Graded automatically by lograder.",
)

# Manual inspection
total = score.total()
print(f"Score: {total.earned}/{total.possible} + {total.extra_credit} extra credit")
```
