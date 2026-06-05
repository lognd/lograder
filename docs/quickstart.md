# Quickstart

A complete autograder for a CMake project in ~30 lines.

```python
from pathlib import Path
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import CMakeManifestCheck
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.test.output_compare import (
    OutputCompareTest, OutputCompareCase, ComparisonMode,
)
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase

# Layout imports register the packet→display mapping at import time.
import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.test.output_compare
import lograder.output.layout.test.valgrind


def grade(submission_dir: Path) -> None:
    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(submission_dir),
        CMakeManifestCheck(),
        CMakeBuild(),
        OutputCompareTest(
            artifact_name="hello",
            test_cases=[
                OutputCompareCase(
                    name="no args",
                    expected_stdout="Hello, world!\n",
                ),
                OutputCompareCase(
                    name="with name",
                    args=["Alice"],
                    expected_stdout="Hello, Alice!\n",
                ),
            ],
        ),
        ValgrindTest(
            artifact_name="hello",
            test_cases=[
                ValgrindCase(name="no leaks"),
                ValgrindCase(name="no leaks with arg", args=["Alice"]),
            ],
        ),
    ]
    pipeline.validate_step_types()
    pipeline()


if __name__ == "__main__":
    import sys
    grade(Path(sys.argv[1]))
```

Run it:
```bash
python grader.py /submissions/student_42/
```

This produces an HTML report at `./out.html`.

To grade multiple students in a loop:
```python
from lograder.pipeline.config import config

for student_dir in Path("/submissions").iterdir():
    with config(root_directory=student_dir, executable_timeout=10.0):
        grade(student_dir)
```

> **Note:** `LocalDirectory()` with no argument reads `get_config().root_directory` at call time, not at construction time, so the `config()` context manager works correctly.
