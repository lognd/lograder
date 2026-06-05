# Examples

## Makefile project with output tests

```python
from pathlib import Path
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import MakefileManifestCheck
from lograder.pipeline.build.makefile import MakefileBuild
from lograder.pipeline.test.output_compare import (
    OutputCompareTest, OutputCompareCase, ComparisonMode,
)
import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.test.output_compare


def grade(submission_dir: Path) -> None:
    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(submission_dir),
        MakefileManifestCheck(),
        MakefileBuild(),
        OutputCompareTest(
            artifact_name="calculator",
            test_cases=[
                OutputCompareCase(name="add",      stdin=b"3 + 4\n",  expected_stdout="7"),
                OutputCompareCase(name="subtract", stdin=b"10 - 3\n", expected_stdout="7"),
                OutputCompareCase(name="bad input",stdin=b"abc\n",    expected_exit_code=1),
            ],
            # MakefileBuild returns {} for artifacts; artifact lookup will fail until
            # Makefile parsing is implemented. Use CMakeBuild for real projects.
        ),
    ]
    pipeline.validate_step_types()
    pipeline()
```

## Per-student grading loop

```python
from lograder.pipeline.config import config

SUBMISSION_ROOT = Path("/autograder/submissions")

for student_dir in sorted(SUBMISSION_ROOT.iterdir()):
    if not student_dir.is_dir():
        continue
    print(f"Grading {student_dir.name}...")
    with config(
        root_directory=student_dir,
        executable_timeout=15.0,
    ):
        grade(student_dir)
```

## Custom check step

```python
from typing import Generator
from pathlib import Path
from lograder.common import Ok, Err, Result, Unreachable
from lograder.pipeline.check.check import Check
from lograder.pipeline.types.parcels import Manifest
from pydantic import BaseModel


class FileSizeData(BaseModel):
    path: Path
    size_bytes: int


class FileSizeTooLarge(BaseModel):
    path: Path
    size_bytes: int
    limit_bytes: int


class SourceSizeCheck(
    Check[Manifest, Manifest, FileSizeTooLarge, FileSizeData, Unreachable]
):
    def __init__(self, filename: str, limit_bytes: int) -> None:
        self._filename = filename
        self._limit = limit_bytes

    def __call__(
        self, input: Manifest
    ) -> Generator[
        Result[FileSizeData, Unreachable],
        None,
        Result[Manifest, FileSizeTooLarge],
    ]:
        path = input.root / self._filename
        size = path.stat().st_size if path.exists() else 0
        yield Ok(FileSizeData(path=path, size_bytes=size))
        if size > self._limit:
            return Err(FileSizeTooLarge(path=path, size_bytes=size, limit_bytes=self._limit))
        return Ok(input)
```

Then register a layout and add it to the pipeline:
```python
@register_layout("file-size-data")
class FileSizeDataLayout(Layout[FileSizeData]):
    @classmethod
    def to_simple(cls, data: FileSizeData) -> str:
        return f"{data.path.name}: {data.size_bytes} bytes"
    @classmethod
    def to_ansi(cls, data: FileSizeData) -> str:
        return f"{F.CYAN}{data.path.name}{F.RESET}: {data.size_bytes} bytes"

pipeline.steps = [
    LocalDirectory(),
    SourceSizeCheck("main.cpp", limit_bytes=10_000),
    CMakeManifestCheck(),
    CMakeBuild(),
    ...
]
```

## Chaining multiple test steps

```python
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase
from lograder.pipeline.test.performance import PerformanceTest, PerformanceCase

pipeline.steps = [
    LocalDirectory(),
    CMakeManifestCheck(),
    CMakeBuild(),
    # Correctness first
    OutputCompareTest(
        artifact_name="sort",
        test_cases=[
            OutputCompareCase(name="empty",   stdin=b"",          expected_stdout=""),
            OutputCompareCase(name="sorted",  stdin=b"3 1 2\n",   expected_stdout="1 2 3"),
            OutputCompareCase(name="one item",stdin=b"42\n",      expected_stdout="42"),
        ],
    ),
    # Memory safety
    ValgrindTest(
        artifact_name="sort",
        test_cases=[
            ValgrindCase(name="no leaks",    stdin=b"3 1 2\n"),
            ValgrindCase(name="empty input", stdin=b""),
        ],
    ),
    # Performance
    PerformanceTest(
        artifact_name="sort",
        test_cases=[
            PerformanceCase(name="1000 items", args=["1000"], time_limit=1.0),
            PerformanceCase(name="1M items",   args=["1000000"], time_limit=10.0),
        ],
    ),
]
```

## File output test

```python
from lograder.pipeline.test.file_output import FileOutputTest, FileOutputCase

FileOutputTest(
    artifact_name="csv_writer",
    test_cases=[
        FileOutputCase(
            name="writes header",
            args=["--header-only"],
            output_file=Path("output.csv"),
            expected_content="name,age,score\n",
            comparison=ComparisonMode.EXACT,
        ),
        FileOutputCase(
            name="writes data rows",
            stdin=b"Alice 20 95\nBob 22 87\n",
            output_file=Path("output.csv"),
            expected_content="Alice,20,95\nBob,22,87\n",
        ),
    ],
)
```
