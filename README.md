# lograder

A Python library for building programming assignment autograders. The central abstraction is a `Pipeline` of `Step` instances -- each step validates input, runs a process, and passes results forward.

```
Input -> Check -> Mixin -> Build -> Test
```

---

## Installation

```bash
pip install lograder
# or for development:
pip install -e ".[dev]"
```

---

## Minimal example

```python
from pathlib import Path
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import CMakeManifestCheck
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.score import TestCaseScorer, AllOrNothingScorer, GradescopeConfig
from lograder.pipeline.pipeline import Pipeline

# Define test cases
cases = [
    OutputCompareCase(name="hello", args=[], expected_stdout="Hello, World!\n"),
    OutputCompareCase(name="echo",  args=["foo"], expected_stdout="foo\n"),
]

# Build the pipeline
pipeline = Pipeline()
pipeline.add(inp   := LocalDirectory())
pipeline.add(check := CMakeManifestCheck())
pipeline.add(build := CMakeBuild())
pipeline.add(tests := OutputCompareTest("hello", cases))

# Attach scorers
build.scorer = AllOrNothingScorer(10.0, label="Build")
tests.scorer = TestCaseScorer({"hello": 40.0, "echo": 50.0}, label="Correctness")

# Run
with config(root_directory=Path("/autograder/submission")):
    score = pipeline()

score.write_results_json(config=GradescopeConfig(visibility="visible"))
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [Getting started](docs/getting-started.md) | First autograder in 5 minutes |
| [Concepts](docs/concepts.md) | Pipeline, Step, Result, Manifest, Artifact |
| [Input](docs/pipeline/input.md) | `LocalDirectory`, `EnvironmentConfig` |
| [Check](docs/pipeline/check.md) | Manifest checks, `SourceCheck`, constraints |
| [Build](docs/pipeline/build.md) | `CMakeBuild`, `MakefileBuild`, `BashScriptBuild`, `PrebuiltArtifacts` |
| [Test](docs/pipeline/test.md) | All 9 test step types with full examples |
| [Scoring](docs/pipeline/scoring.md) | Scorers, Gradescope output, `results.json` |
| [Process layer](docs/process.md) | `TypedExecutable`, `CLIArgs`, registry |
| [Output / layouts](docs/output.md) | Logging, HTML report, custom layouts |
| [Examples](docs/examples/) | Complete worked autograders |

---

## Design principles

- **Errors as values.** Steps return `Result[Ok, Err]` rather than raising. A fatal `Err` return stops the pipeline; a yielded `Err` is logged and execution continues.
- **Typed data flow.** Each step declares its input and output types. `pipeline.validate_step_types()` catches mismatches before the first submission runs.
- **No magic.** Every process invocation goes through a `TypedExecutable` with validated `CLIArgs`. You can see exactly what command was run and what it produced.
- **Library only.** lograder has no CLI and no service. You write a Python script; lograder is a collection of reusable building blocks.
