# Metadata & attribution

`GraderMetadata` lets you record who built the autograder, when the submission arrived, whether it was late, and any other context you want shown to students in the Gradescope output block.

Pass it to `pipeline(metadata=...)` -- the pipeline auto-stamps `submission_time` and carries the object into the returned `PipelineScore`. `write_results_json()` automatically prepends the metadata block to the `output` field.

## Quick example

```python
from lograder.pipeline.metadata import GraderMetadata, StaffAuthor

metadata = GraderMetadata(
    grader_name="CS101 Lab 3 -- Sorting",
    course="CSCI 101",
    version="2024.1",
    authors=[
        StaffAuthor(name="Prof. Smith", email="smith@uni.edu", role="Instructor"),
        StaffAuthor(name="Jane Doe", role="Teaching Assistant"),
    ],
    due_date=datetime(2024, 3, 15, 23, 59, tzinfo=timezone.utc),
    notes="Contact course staff if you believe there is a grading error.",
)

with config(root_directory=Path("/autograder/submission")):
    score = pipeline(metadata=metadata)

score.write_results_json(config=GradescopeConfig(visibility="visible"))
```

Output block shown to students:

```
--------------------------------------------------
  CS101 Lab 3 -- Sorting  (v2024.1)
--------------------------------------------------
  Course:      CSCI 101
  Submitted:   2024-03-16 01:00 UTC  !  LATE  (due 2024-03-15 23:59 UTC)
  Student(s):  Alice (12345678) <alice@uni.edu>
  Author(s):   Prof. Smith <smith@uni.edu> (Instructor)
               Jane Doe (Teaching Assistant)
  Notes:       Contact course staff if you believe there is a grading error.
  Built with:  lograder 0.2.0 -- Logan Dapp
--------------------------------------------------
```

## Reading submission metadata from Gradescope

Gradescope writes `/autograder/submission_metadata.json` before your autograder runs. Use `from_gradescope()` to populate `submission_time`, `due_date`, `assignment`, and `submitters` from that file automatically:

```python
metadata = GraderMetadata.from_gradescope(
    # Additional fields override / supplement the file
    grader_name="CS101 Lab 3",
    authors=[StaffAuthor(name="Prof. Smith", role="Instructor")],
)
```

Fields populated from the file (when present):

| JSON field | `GraderMetadata` field |
|-----------|------------------------|
| `created_at` | `submission_time` |
| `assignment.due_date` | `due_date` |
| `assignment.title` | `assignment` (only if not supplied explicitly) |
| `submitters[*]` | `submitters` |

If the file is missing or malformed, the call succeeds silently with those fields left as `None`.

## `GraderMetadata` fields

| Field | Type | Description |
|-------|------|-------------|
| `grader_name` | `str \| None` | Name for this autograder, e.g. `"CS101 Lab 3"` |
| `course` | `str \| None` | Course identifier, e.g. `"CSCI 101"` |
| `assignment` | `str \| None` | Assignment name, e.g. `"Lab 3 -- Sorting"` |
| `version` | `str \| None` | Autograder version for tracking iterations |
| `authors` | `list[StaffAuthor]` | People who wrote this autograder |
| `due_date` | `datetime \| None` | Deadline (display only; used to flag late submissions) |
| `submission_time` | `datetime \| None` | Auto-stamped to `datetime.now(UTC)` by `Pipeline.__call__()` if `None` |
| `submitters` | `list[Submitter]` | Submitter(s) (auto-populated by `from_gradescope()`) |
| `notes` | `str \| None` | Free-form text appended to the block |
| `show_lograder_attribution` | `bool` | Show the `Built with lograder...` line (default `True`) |

## `StaffAuthor` fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Full name |
| `email` | `str \| None` | Contact email |
| `role` | `str \| None` | e.g. `"Instructor"`, `"Teaching Assistant"` |

## `Submitter` fields

Populated automatically by `from_gradescope()`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Full name |
| `email` | `str \| None` | Email address |
| `sid` | `str \| None` | Student/employee ID |

## Late detection

`GraderMetadata.is_late` returns:
- `True` -- submission arrived after `due_date`
- `False` -- submission arrived on or before `due_date`
- `None` -- either `submission_time` or `due_date` is `None`

The display block shows `!  LATE (due ...)` automatically when `is_late is True`.

## Combining with `GradescopeConfig.output`

If you also set `config.output`, it is appended after the metadata block:

```python
score.write_results_json(
    config=GradescopeConfig(
        visibility="visible",
        output="Please attend office hours if you have questions.",
    ),
)
```

Output:
```
-------- ... metadata block ... --------

Please attend office hours if you have questions.
```

## Manually stamping submission time

`Pipeline.__call__()` stamps automatically, but you can also do it yourself:

```python
from datetime import datetime, timezone

metadata = GraderMetadata(
    grader_name="CS101 Lab 3",
    submission_time=datetime.now(timezone.utc),  # set explicitly
)
# Now pipeline() won't overwrite it
score = pipeline(metadata=metadata)
```

Or use the helper:

```python
metadata = GraderMetadata(grader_name="CS101 Lab 3")
metadata = metadata.with_submission_time_now()  # returns a copy
```

## Full Gradescope example

```python
from pathlib import Path
from datetime import datetime, timezone

from lograder.pipeline.metadata import GraderMetadata, StaffAuthor
from lograder.pipeline.config import config
from lograder.pipeline.score import GradescopeConfig

metadata = GraderMetadata.from_gradescope(
    grader_name="CS101 Lab 3 -- Sorting",
    course="CSCI 101",
    version="2024.2",
    authors=[
        StaffAuthor(name="Prof. Smith", email="smith@uni.edu", role="Instructor"),
        StaffAuthor(name="Jane Doe", email="jdoe@uni.edu", role="TA"),
    ],
    notes="Graded automatically. Regrade requests due within 3 days.",
)

with config(root_directory=Path("/autograder/submission")):
    score = pipeline(metadata=metadata)

score.write_results_json(
    config=GradescopeConfig(
        visibility="visible",
        stdout_visibility="hidden",
    ),
)
```
