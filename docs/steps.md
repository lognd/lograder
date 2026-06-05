# Built-in Steps

## Input

### `LocalDirectory`

Reads a directory from disk and produces a `Manifest`.

```python
from lograder.pipeline.input.local_directory import LocalDirectory

# Explicit path:
LocalDirectory(Path("/submissions/student_42"))

# Reads get_config().root_directory at call time (use with config() context manager):
LocalDirectory()
```

## Check

### `CMakeManifestCheck` / `MakefileManifestCheck` / `PyProjectManifestCheck`

Validates that the submission contains the required build file.

```python
from lograder.pipeline.check.project.simple_project import (
    CMakeManifestCheck,    # checks for CMakeLists.txt → produces CMakeManifest
    MakefileManifestCheck, # checks for Makefile        → produces MakefileManifest
    PyProjectManifestCheck,# checks for pyproject.toml  → produces PyProjectManifest
)
```

On failure, returns `Err(CMakeManifestCheckError)` — a logged fatal error.

### Custom manifest check

```python
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker

ManifestCls, DataCls, ErrorCls, CheckCls = make_simple_manifest_checker(
    "CMake",
    ["CMakeLists.txt", "src/main.cpp"],
)
```

## Build

### `CMakeBuild`

Runs `cmake --preset ...` then `cmake --build`. Returns `dict[str, Artifact]` keyed by CMake target name. Prefers `FileArtifact` over non-file artifacts for the same target name.

```python
from lograder.pipeline.build.cmake import CMakeBuild
CMakeBuild()
```

### `MakefileBuild`

Runs `make`. Returns `dict[str, Artifact]` (currently empty — artifact parsing not yet implemented).

```python
from lograder.pipeline.build.makefile import MakefileBuild
MakefileBuild()
```

## Test

All test steps:
- Accept `dict[str, Artifact]` and pass it through on success
- Yield `Ok(SuccessModel)` / `Err(FailureModel)` per test case (non-fatal)
- Return `Err(ErrorModel)` if setup fails (fatal — stops pipeline)
- Chain freely: `CMakeBuild → OutputCompareTest → ValgrindTest → PerformanceTest`

### `OutputCompareTest`

Runs an executable with given args/stdin and compares stdout (and optionally exit code).

```python
from lograder.pipeline.test.output_compare import (
    OutputCompareTest, OutputCompareCase, ComparisonMode,
)

OutputCompareTest(
    artifact_name="my_program",
    test_cases=[
        OutputCompareCase(
            name="hello world",
            expected_stdout="Hello, world!\n",
            comparison=ComparisonMode.STRIP,  # default
        ),
        OutputCompareCase(
            name="addition",
            args=["3", "4"],
            stdin=b"",
            expected_stdout="7",
            expected_exit_code=0,             # also check exit code
        ),
        OutputCompareCase(
            name="bad input exits 1",
            args=["bad"],
            expected_exit_code=1,
        ),
    ],
)
```

`ComparisonMode`:
- `STRIP` — strip leading/trailing whitespace from both sides (default)
- `EXACT` — byte-for-byte
- `IGNORE_TRAILING_WHITESPACE` — strip each line's trailing whitespace, preserve structure

### `ValgrindTest`

Runs the executable under Valgrind (memcheck). Auto-installs valgrind if not found (POSIX only).

```python
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase

ValgrindTest(
    artifact_name="my_program",
    test_cases=[
        ValgrindCase(name="basic run", args=["input.txt"]),
        ValgrindCase(name="with leaks check", check_leaks=True),   # default
        ValgrindCase(name="no leak check",    check_leaks=False),
    ],
)
```

Reports: `ValgrindError(kind, message, primary_frames)` per memory error, and `crashed: bool` for fatal signals.

> **Note:** Valgrind is Linux/macOS only. On Windows this step will fail at `check_runnable()`.

### `FileOutputTest`

Runs the executable and checks a file it writes to disk.

```python
from lograder.pipeline.test.file_output import FileOutputTest, FileOutputCase

FileOutputTest(
    artifact_name="writer",
    test_cases=[
        FileOutputCase(
            name="creates output.txt",
            output_file=Path("output.txt"),   # relative to options.cwd
            expected_content="done\n",
        ),
    ],
)
```

If the file doesn't exist after the run, `actual_content` is `None` and the test fails.

### `PerformanceTest`

Times the executable and fails if it exceeds a wall-clock limit.

```python
from lograder.pipeline.test.performance import PerformanceTest, PerformanceCase

PerformanceTest(
    artifact_name="sorter",
    test_cases=[
        PerformanceCase(name="small input", args=["100"],   time_limit=1.0),
        PerformanceCase(name="large input", args=["10000"], time_limit=5.0),
    ],
)
```

A safety kill fires at `time_limit + 30s` to prevent hangs. Wall time is measured with `perf_counter`. The `PerformanceTestFailure` packet includes `elapsed` and `time_limit` for partial credit scoring.

### `ExecutableOptions` for test steps

All test steps accept an `options: ExecutableOptions | None` parameter.

```python
from lograder.process.executable import ExecutableOptions

opts = ExecutableOptions(
    cwd=Path("/tmp/sandbox"),
    timeout=60.0,
)
OutputCompareTest("prog", cases, options=opts)
```

`PerformanceTest` uses `base_options` and overrides `timeout` internally — don't set `timeout` in `base_options` for performance tests; it will be overridden anyway.
