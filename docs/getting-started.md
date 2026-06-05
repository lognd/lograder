# Getting started

This guide walks through building a complete autograder for a C++ CMake project in about 60 lines of Python. By the end you will have an autograder that:

- Validates the student submitted the right files
- Builds with CMake
- Runs output-comparison tests
- Checks for memory leaks with Valgrind
- Produces a Gradescope `results.json`

## Install

```bash
pip install lograder
```

For a dev install from source:

```bash
git clone https://github.com/lognd/lograder
cd lograder
pip install -e ".[dev]"
```

## Step 1 — Create the autograder script

Create `autograder.py`:

```python
from pathlib import Path

# Layout imports must come first — they register packet types
import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.test.output_compare
import lograder.output.layout.test.valgrind

from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase
from lograder.pipeline.score import AllOrNothingScorer, TestCaseScorer, GradescopeConfig
from lograder.pipeline.pipeline import Pipeline
```

## Step 2 — Declare what files you expect

```python
# Generates CMakeManifest, CMakeManifestCheck, etc. in this module's globals
make_simple_manifest_checker(
    "hello_world",
    required_files=["CMakeLists.txt", "main.cpp"],
)
# After this call you can use CMakeManifestCheck directly
```

## Step 3 — Define your test cases

```python
OUTPUT_CASES = [
    OutputCompareCase(name="no_args",    args=[],          expected_stdout="Hello, World!\n"),
    OutputCompareCase(name="name_arg",   args=["Alice"],   expected_stdout="Hello, Alice!\n"),
    OutputCompareCase(name="empty_arg",  args=[""],        expected_stdout="Hello, !\n"),
]

VALGRIND_CASES = [
    ValgrindCase(name="no_leaks",  args=[],        check_leaks=True),
    ValgrindCase(name="arg_leaks", args=["Alice"], check_leaks=True),
]
```

## Step 4 — Assemble the pipeline

```python
pipeline = Pipeline()
pipeline.add(inp    := LocalDirectory())
pipeline.add(check  := CMakeManifestCheck())
pipeline.add(build  := CMakeBuild())
pipeline.add(tests  := OutputCompareTest("hello_world", OUTPUT_CASES))
pipeline.add(vg     := ValgrindTest("hello_world", VALGRIND_CASES))
```

## Step 5 — Attach scorers

```python
build.scorer = AllOrNothingScorer(10.0, label="Build")
tests.scorer = TestCaseScorer(
    {"no_args": 30.0, "name_arg": 30.0, "empty_arg": 30.0},
    label="Correctness",
)
vg.scorer = AllOrNothingScorer(0.0, extra_credit=10.0, label="No memory leaks")
```

## Step 6 — Run it

```python
if __name__ == "__main__":
    with config(root_directory=Path("/autograder/submission")):
        score = pipeline()

    score.write_results_json(
        config=GradescopeConfig(visibility="visible"),
    )
```

## Full script

```python
from pathlib import Path

import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.test.output_compare
import lograder.output.layout.test.valgrind

from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase
from lograder.pipeline.score import AllOrNothingScorer, TestCaseScorer, GradescopeConfig
from lograder.pipeline.pipeline import Pipeline

make_simple_manifest_checker(
    "hello_world",
    required_files=["CMakeLists.txt", "main.cpp"],
)

OUTPUT_CASES = [
    OutputCompareCase(name="no_args",   args=[],        expected_stdout="Hello, World!\n"),
    OutputCompareCase(name="name_arg",  args=["Alice"], expected_stdout="Hello, Alice!\n"),
    OutputCompareCase(name="empty_arg", args=[""],      expected_stdout="Hello, !\n"),
]

VALGRIND_CASES = [
    ValgrindCase(name="no_leaks",  args=[],        check_leaks=True),
    ValgrindCase(name="arg_leaks", args=["Alice"], check_leaks=True),
]

pipeline = Pipeline()
pipeline.add(inp   := LocalDirectory())
pipeline.add(check := CMakeManifestCheck())
pipeline.add(build := CMakeBuild())
pipeline.add(tests := OutputCompareTest("hello_world", OUTPUT_CASES))
pipeline.add(vg    := ValgrindTest("hello_world", VALGRIND_CASES))

build.scorer = AllOrNothingScorer(10.0, label="Build")
tests.scorer = TestCaseScorer(
    {"no_args": 30.0, "name_arg": 30.0, "empty_arg": 30.0},
    label="Correctness",
)
vg.scorer = AllOrNothingScorer(0.0, extra_credit=10.0, label="No memory leaks")

if __name__ == "__main__":
    with config(root_directory=Path("/autograder/submission")):
        score = pipeline()
    score.write_results_json(config=GradescopeConfig(visibility="visible"))
```

## What happens when it runs

1. `LocalDirectory` reads the submission directory and produces a `Manifest` (a snapshot of the file tree).
2. `CMakeManifestCheck` verifies that `CMakeLists.txt` and `main.cpp` are present. If not, the pipeline stops and the student gets 0 on everything downstream.
3. `CMakeBuild` runs `cmake --build`. If the build fails, the pipeline stops.
4. `OutputCompareTest` runs the compiled binary with each set of arguments and compares stdout.
5. `ValgrindTest` re-runs the binary under Valgrind and checks for memory errors.
6. `write_results_json` writes `/autograder/results/results.json` in the format Gradescope expects.

## Next steps

- Add a source check (forbid `goto`, require specific headers): [Check](pipeline/check.md)
- Add file output tests, performance tests, or unit test framework integration: [Test](pipeline/test.md)
- Understand scoring in detail: [Scoring](pipeline/scoring.md)
- See a complete Makefile or Python example: [Examples](examples/)
