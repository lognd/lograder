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

### `SourceCheck`

Parses source files with a language-aware AST and enforces constraints on operators, identifiers, qualified names, `#include` directives, and Python imports. C/C++ files are preprocessed first (via `cpp` → `clang++ -E -P` → naive `#define` expansion fallback) so `#define`-based aliasing is caught.

```python
from lograder.pipeline.check.source import (
    SourceCheck,
    OperatorConstraint,
    IdentifierConstraint,
    QualifiedNameConstraint,
    IncludeConstraint,
    ImportConstraint,
)
```

**Constraint types:**

| Class | Applies to | Description |
|-------|-----------|-------------|
| `OperatorConstraint(tokens, max_count)` | C/C++, Python | Ban/limit operator tokens (combined count across all tokens in the list) |
| `IdentifierConstraint(names, max_count)` | C/C++, Python | Ban identifier usage (`list`, `malloc`, custom names) |
| `QualifiedNameConstraint(qualified_names, max_count)` | C/C++ only | Ban qualified names like `std::vector`, `std::sort` |
| `IncludeConstraint(headers, max_count)` | C/C++ only | Ban `#include` directives by header string, e.g. `"<vector>"` |
| `ImportConstraint(modules, max_count)` | Python only | Ban `import`/`from … import` by module name |

All constraints accept an optional `label: str` used in violation messages. The `tokens`/`names`/`qualified_names`/`headers`/`modules` list is a group — the **combined** count across all entries in the list is checked against `max_count`.

**Usage — C++ operator and library ban:**

```python
SourceCheck(
    files=["collatz.cpp"],
    constraints=[
        OperatorConstraint(tokens=["/", "%"], max_count=0, label="Division/modulo forbidden"),
        IncludeConstraint(headers=["<algorithm>", "<numeric>"], max_count=0),
        QualifiedNameConstraint(qualified_names=["std::sort", "std::reduce"], max_count=0),
    ],
    language="cpp",
    include_dirs=[Path("/usr/include")],  # optional; passed to preprocessor
    label="Operator Check",
)
```

**Usage — Python identity ban:**

```python
SourceCheck(
    files=["solution.py"],
    constraints=[
        ImportConstraint(modules=["numpy", "scipy"], max_count=0),
        IdentifierConstraint(names=["list", "sorted", "sum"], max_count=0),
    ],
    language="python",
)
```

- Violations are yielded as non-fatal `Err(SourceViolation)` packets — one per violated constraint per file. The step always returns `Ok(manifest)` unless a fatal error occurs (file missing or unreadable).
- The step returns `Err(SourceCheckError)` fatally only if a file is missing or cannot be read.
- `language` is `"c"`, `"cpp"`, or `"python"`. `"c"` and `"cpp"` use the C++ tree-sitter grammar and preprocessor chain.
- Import the layout module before running: `import lograder.output.layout.check.source`

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

### `BashScriptBuild`

Runs a student-submitted bash script and then collects the files it produced as named artifacts. Use this when the submission is a `build.sh` that compiles source files, creates static/shared libraries, or prepares any binaries the grader needs to test.

```python
from lograder.pipeline.build.bash_script import BashScriptBuild

BashScriptBuild(
    script="build.sh",           # path relative to manifest.root
    artifacts={                  # name → path relative to cwd (manifest.root by default)
        "hello":    "hello",
        "libmath":  "libmath.a",
    },
    make_artifacts_executable=True,  # chmod +x each collected artifact (default True)
)
```

The script is invoked as `bash build.sh` — the file does not need to have the execute bit set in the submission. `stdout` and `stderr` are captured and logged.

**Fatal error (`Err(BashScriptBuildError)`) when:**
- `bash` is not installed
- The script file is not found in the submission
- The script exits non-zero
- An artifact path listed in `artifacts` does not exist after the script completes

**Normal output (`Ok(BashScriptBuildOutput)`):** one non-fatal packet with the script name, exit code, and captured output.

Pass `options` to control the working directory, timeout, or environment:

```python
from lograder.process.executable import ExecutableOptions

BashScriptBuild(
    script="build.sh",
    artifacts={"prog": "prog"},
    options=ExecutableOptions(timeout=60.0),
)
```

Import the layout module before running: `import lograder.output.layout.pipeline.bash_script`

### `PrebuiltArtifacts`

Wraps already-compiled files from the submission as `FileArtifact` instances without running any build tool. Useful when students submit pre-built binaries, static libraries (`.a`), or shared libraries (`.so`).

```python
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts

PrebuiltArtifacts(
    files=["hello", "libmath.a"],   # relative to manifest.root
    set_executable=True,            # chmod +x each file (default True)
)
```

- `files` are looked up in the manifest and wrapped as `FileArtifact(path=...)`.
- Returns `Err(PrebuiltArtifactsError)` fatally if any file is missing from the manifest.
- Import the layout module before running: `import lograder.output.layout.pipeline.prebuilt`

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

### `SymbolTest`

Runs `nm` on a `FileArtifact` (object file, static library, or shared library) and checks for required or forbidden exported symbols.

```python
from lograder.pipeline.test.symbol import SymbolTest, SymbolCase

SymbolTest(
    artifact_name="libmath.a",
    cases=[
        SymbolCase(
            name="exports add and subtract",
            required=["add", "subtract"],
            forbidden=["internal_helper"],
        ),
        SymbolCase(
            name="no undefined refs",
            undefined_only=True,   # only inspect undefined symbols
            forbidden=["malloc"],
        ),
        SymbolCase(
            name="dynamic exports",
            dynamic=True,          # use -D for shared library symbol table
            required=["my_api_fn"],
        ),
    ],
)
```

`SymbolCase` fields:

| Field | Default | Description |
|-------|---------|-------------|
| `required` | `[]` | Symbol names that must be present |
| `forbidden` | `[]` | Symbol names that must not be present |
| `dynamic` | `False` | Pass `-D` to inspect the dynamic symbol table (shared libraries) |
| `defined_only` | `True` | Exclude undefined (`U`) symbols from the result set |
| `demangle` | `False` | Pass `--demangle` to nm before matching |

- Returns `Err(SymbolError)` fatally if the artifact is not a `FileArtifact` or `nm` is not installed.
- Import the layout module before running: `import lograder.output.layout.test.symbol`

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
