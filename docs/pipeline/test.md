# Test

Test steps take `dict[str, Artifact]` in and return it unmodified on success, so multiple test steps chain on the same artifact dictionary. Each step `yield`s one `Ok` or `Err` per test case and `return`s `Ok(artifacts)` or a fatal `Err` if something goes catastrophically wrong.

---

## `OutputCompareTest`

Runs the artifact with a set of arguments and compares stdout (and optionally exit code) against expected values.

All `cases` arguments across every test step accept any `Iterable` -- lists, generators, and comprehensions all work. The iterable is consumed once per pipeline run.

```python
from lograder.pipeline.test.output_compare import (
    OutputCompareTest, OutputCompareCase, ComparisonMode,
)

cases = [
    OutputCompareCase(
        name="hello",
        args=[],
        expected_stdout="Hello, World!\n",
    ),
    OutputCompareCase(
        name="echo",
        args=["foo", "bar"],
        stdin=b"ignored\n",
        expected_stdout="foo bar\n",
        comparison=ComparisonMode.EXACT,     # STRIP (default), EXACT, IGNORE_TRAILING_WHITESPACE
        expected_exit_code=0,                # None = don't check
    ),
]

pipeline.add(tests := OutputCompareTest("my_binary", cases))
tests.scorer = TestCaseScorer({"hello": 20.0, "echo": 30.0}, label="Correctness")
```

### `ComparisonMode`

| Mode | What it does |
|------|-------------|
| `STRIP` (default) | Compare after stripping leading/trailing whitespace from both |
| `EXACT` | Byte-for-byte equality |
| `IGNORE_TRAILING_WHITESPACE` | Strip trailing whitespace from each line, then compare |

### `OutputCompareCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique test case name |
| `args` | `list[str]` | `[]` | Command-line arguments |
| `stdin` | `bytes` | `b""` | Data to feed to stdin |
| `expected_stdout` | `str` | `""` | Expected program output |
| `comparison` | `ComparisonMode` | `STRIP` | How to compare outputs |
| `expected_exit_code` | `int \| None` | `None` | Expected exit code (None = don't check) |

---

## `ValgrindTest`

Re-runs the artifact under Valgrind, checking for memory errors and optionally memory leaks.

```python
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase

cases = [
    ValgrindCase(name="basic",  args=[],          check_leaks=True),
    ValgrindCase(name="input",  args=["foo"],     check_leaks=True),
    ValgrindCase(name="stress", args=["1000"],    check_leaks=False),  # don't check leaks
]

pipeline.add(vg := ValgrindTest("my_binary", cases))
vg.scorer = AllOrNothingScorer(0.0, extra_credit=10.0, label="No memory errors")
```

`ValgrindTest` skips gracefully if Valgrind is not installed. If you want it to auto-install:

```python
from lograder.process.registry.valgrind import ValgrindExecutable

vg_exe = ValgrindExecutable()
if vg_exe.check_runnable().is_err:
    result = vg_exe.install()
    if result.is_ok:
        vg_exe.update_base_command(result.danger_ok)
```

### `ValgrindCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique test case name |
| `args` | `list[str]` | `[]` | Arguments to pass to the binary |
| `stdin` | `bytes` | `b""` | Data to feed to stdin |
| `check_leaks` | `bool` | `True` | Whether to fail on memory leaks |

---

## `FileOutputTest`

Runs the artifact and checks a file it writes to disk, rather than its stdout.

```python
from lograder.pipeline.test.file_output import FileOutputTest, FileOutputCase

cases = [
    FileOutputCase(
        name="write_sorted",
        args=["input.txt", "output.txt"],
        stdin=b"",
        output_file=Path("output.txt"),      # relative to cwd
        expected_content="1\n2\n3\n",
        comparison=ComparisonMode.STRIP,
        expected_exit_code=0,
    ),
]

pipeline.add(FileOutputTest("my_binary", cases))
```

### `FileOutputCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique test case name |
| `args` | `list[str]` | `[]` | Command-line arguments |
| `stdin` | `bytes` | `b""` | Data to feed to stdin |
| `output_file` | `Path` | required | Path to the file the program writes |
| `expected_content` | `str` | required | Expected file contents |
| `comparison` | `ComparisonMode` | `STRIP` | How to compare |
| `expected_exit_code` | `int \| None` | `None` | Expected exit code |

---

## `PerformanceTest`

Runs the artifact and checks that it completes within a time limit.

```python
from lograder.pipeline.test.performance import PerformanceTest, PerformanceCase

cases = [
    PerformanceCase(name="small",  args=["100"],   time_limit=1.0),   # seconds
    PerformanceCase(name="medium", args=["10000"], time_limit=5.0),
    PerformanceCase(name="large",  args=["1000000"], time_limit=30.0),
]

pipeline.add(perf := PerformanceTest("my_binary", cases))
perf.scorer = TestCaseScorer({"small": 5.0, "medium": 5.0, "large": 10.0}, label="Performance")
```

Safety kill fires at `time_limit + 30s` -- the process is killed and the test fails. Wall time is measured with `perf_counter`.

### `PerformanceCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique test case name |
| `args` | `list[str]` | `[]` | Command-line arguments |
| `stdin` | `bytes` | `b""` | Data to feed to stdin |
| `time_limit` | `float` | required | Maximum wall time in seconds |

---

## `SymbolTest`

Checks that specific symbols are (or are not) present in a compiled binary/library.

```python
from lograder.pipeline.test.symbol import SymbolTest, SymbolCase

cases = [
    SymbolCase(name="has_sort",       symbol="my_sort",   must_exist=True),
    SymbolCase(name="no_std_sort",    symbol="_ZSt4sortI", must_exist=False),  # mangled
    SymbolCase(name="dynamic_malloc", symbol="malloc",    dynamic=True, must_exist=False),
]

pipeline.add(sym := SymbolTest("my_binary", cases))
sym.scorer = CleanRunScorer(10.0, label="No forbidden symbols")
```

Uses `nm` under the hood to inspect the symbol table.

### `SymbolCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique test case name |
| `symbol` | `str` | required | Symbol name or prefix to search for |
| `must_exist` | `bool` | `True` | Whether the symbol must be present |
| `dynamic` | `bool` | `False` | Check dynamic symbols only (`nm -D`) |

---

## `Catch2Test`

Runs a Catch2 test binary and parses its XML output.

```python
from lograder.pipeline.test.catch2 import Catch2Test

pipeline.add(catch2 := Catch2Test("my_tests"))
catch2.scorer = TestCaseScorer(
    {"[unit] my_function": 10.0, "[unit] edge_case": 5.0},
    label="Unit tests",
)
```

The artifact must be a Catch2 test binary (compiled with Catch2 and a `main` that calls `Catch::Session().run(argc, argv)`). Catch2Test runs it with `--reporter xml` to parse structured output.

Test case names in the scorer map to Catch2 test names (the string you pass to `TEST_CASE`).

---

## `GTestTest`

Runs a Google Test binary and parses its XML output.

```python
from lograder.pipeline.test.gtest import GTestTest

pipeline.add(gtest := GTestTest("my_tests"))
gtest.scorer = TestCaseScorer(
    {"MyTest.BasicCase": 10.0, "MyTest.EdgeCase": 10.0},
    label="Unit tests",
)
```

GTestTest runs the binary with `--gtest_output=xml:results.xml` and parses the JUnit-format XML. Test case names in the scorer map match `<ClassName>.<TestName>` from Google Test.

---

## `CTestTest`

Runs CMake's CTest test runner on the build directory.

```python
from lograder.pipeline.test.ctest import CTestTest

pipeline.add(ctest := CTestTest())
ctest.scorer = TestCaseScorer(
    {"test_basic": 10.0, "test_advanced": 20.0},
    label="CTest suite",
)
```

CTestTest runs `ctest --output-on-failure` in the CMake build directory and parses the results. Requires that CMake tests are registered with `add_test()` in `CMakeLists.txt`.

---

## `PytestTest`

Runs pytest on a Python project and parses the JUnit XML output.

```python
from lograder.pipeline.test.pytest import PytestTest

pipeline.add(pytest_step := PytestTest(test_paths=[Path("tests/")]))
pytest_step.scorer = TestCaseScorer(
    {"tests/test_graph.py::test_bfs": 10.0, "tests/test_graph.py::test_dfs": 10.0},
    label="Python tests",
)
```

PytestTest runs `pytest --junit-xml=results.xml` and parses the output. Test IDs in the scorer map match pytest's `<file>::<function>` format.

---

## Test case helpers

### `OracleInput` / `oracle_cases`

When you have a staff solution, use `oracle_cases` to run it and capture its stdout as expected output -- no hand-coded expected strings needed.

```python
from lograder.pipeline.test.oracle import OracleInput, oracle_cases

cases = oracle_cases(
    Path("staff/bin/solution"),
    [
        OracleInput(name="empty",    args=[]),
        OracleInput(name="small",    args=["5"]),
        OracleInput(name="negative", args=["-3"], comparison=ComparisonMode.EXACT),
        # generators work too -- runs oracle fresh for every submission build
        *(OracleInput(name=f"rand_{i}", args=[str(random.randint(1, 1000))]) for i in range(50)),
    ],
)
pipeline.add(OutputCompareTest("myprogram", cases))
```

`oracle_cases` returns `list[OutputCompareCase]` with `expected_stdout` and `expected_exit_code` filled in from the oracle run.

### `cases_from_matrix`

Generate test cases from the cartesian product of argument pools. Raises `ValueError` if the total would exceed `max_cases` (default 500) to catch accidental combinatorial explosions.

```python
from lograder.pipeline.test.oracle import cases_from_matrix

# 3 * 4 = 12 cases, names like "add_1", "sub_10", "mul_100"
inputs = cases_from_matrix(["add", "sub", "mul"], ["1", "10", "100", "999"])

# custom name function
inputs = cases_from_matrix(
    ["insert", "delete", "search"],
    ["empty", "small", "large"],
    name_fn=lambda args: f"{args[0]}_{args[1]}",
)

# increase the guard for intentionally large suites
inputs = cases_from_matrix(range_pool, value_pool, max_cases=2000)
```

`cases_from_matrix` returns `list[OracleInput]`, which feeds directly into `oracle_cases` or `DifferentialTest`:

```python
# pre-capture expected outputs
cases = oracle_cases(Path("staff/bin/solution"), cases_from_matrix(...))
pipeline.add(OutputCompareTest("myprogram", cases))

# or compare live at grading time
pipeline.add(DifferentialTest("myprogram", Path("staff/bin/solution"), cases_from_matrix(...)))
```

---

## `DifferentialTest`

Runs both the student binary and a reference binary for each case and compares their stdout. Unlike `OutputCompareTest`, no expected output is pre-computed -- the reference binary runs live per submission.

```python
from lograder.pipeline.test.differential import DifferentialTest
from lograder.pipeline.test.oracle import OracleInput, cases_from_matrix

pipeline.add(diff := DifferentialTest(
    "myprogram",
    Path("staff/bin/solution"),
    cases_from_matrix(["add", "sub", "mul"], ["1", "10", "100"]),  # 9 cases
))
diff.scorer = TestCaseScorer(
    {f"{op}_{n}": 5.0 for op in ["add", "sub", "mul"] for n in ["1", "10", "100"]},
    label="Correctness",
)
```

Exit codes are not compared by default. Pass `check_exit_codes=True` to require the student's exit code to match the reference:

```python
DifferentialTest("myprogram", reference, cases, check_exit_codes=True)
```

Use `reference_options` to give the reference binary a different working directory or timeout from the student binary:

```python
DifferentialTest(
    "myprogram",
    Path("staff/bin/solution"),
    cases,
    options=ExecutableOptions(timeout=10.0),
    reference_options=ExecutableOptions(timeout=60.0),  # generous timeout for reference
)
```

### `OracleInput` fields (used by both `oracle_cases` and `DifferentialTest`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique test case name |
| `args` | `list[str]` | `[]` | Command-line arguments |
| `stdin` | `bytes` | `b""` | Data to feed to stdin |
| `comparison` | `ComparisonMode` | `STRIP` | How to compare outputs |

### `DifferentialTest` parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `artifact_name` | `str` | required | Key in `artifacts` dict for the student binary |
| `reference` | `Path \| str` | required | Path to the reference binary |
| `test_cases` | `Iterable[OracleInput]` | required | Cases to run |
| `options` | `ExecutableOptions \| None` | `None` | Options for the student binary |
| `reference_options` | `ExecutableOptions \| None` | `None` | Options for the reference binary (defaults to `options`) |
| `check_exit_codes` | `bool` | `False` | Whether to also require matching exit codes |

---

## Chaining test steps

All test steps take and return `dict[str, Artifact]`, so they chain naturally:

```python
pipeline.add(LocalDirectory())
pipeline.add(CMakeManifestCheck())
pipeline.add(build       := CMakeBuild())
pipeline.add(correctness := OutputCompareTest("sorter", output_cases))
pipeline.add(leaks       := ValgrindTest("sorter", valgrind_cases))
pipeline.add(perf        := PerformanceTest("sorter", perf_cases))
pipeline.add(symbols     := SymbolTest("sorter", symbol_cases))

correctness.scorer = TestCaseScorer({"case1": 20.0, "case2": 20.0}, label="Correctness")
leaks.scorer       = AllOrNothingScorer(0.0, extra_credit=10.0, label="No leaks")
perf.scorer        = TestCaseScorer({"small": 5.0, "large": 10.0}, label="Performance")
symbols.scorer     = CleanRunScorer(5.0, label="Symbol check")
```

## `ExecutableOptions` for test steps

All test steps accept an `options` parameter to configure how the artifact is run:

```python
from lograder.process.executable import ExecutableOptions

pipeline.add(OutputCompareTest(
    "my_binary",
    cases,
    options=ExecutableOptions(
        timeout=10.0,           # override per-step timeout
        cwd=Path("/sandbox"),   # working directory
        inherit_parent_env=False,
    ),
))
```

---

## `ASanTest`

Runs test cases against an AddressSanitizer-instrumented binary and detects heap overflows, use-after-free errors, and memory leaks.

The binary **must** be compiled with `-fsanitize=address`. Use `GXXBuild(sanitizers=["address"])` or set the flag in `CMakeLists.txt`. Running an uninstrumented binary never triggers failures.

```python
from lograder.pipeline.test.asan import ASanTest, ASanCase

cases = [
    ASanCase(name="no_overflow", args=["10"], stdin=b""),
    ASanCase(name="no_leaks",    args=["5"],  stdin=b"", expected_exit_code=0),
]

pipeline.add(asan := ASanTest("my_binary", cases))
asan.scorer = AllOrNothingScorer(20.0, label="Memory Safety")
```

### `ASanCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique case name |
| `args` | `list[str]` | `[]` | Command-line arguments |
| `stdin` | `bytes \| str` | `b""` | stdin (str is auto-encoded to UTF-8) |
| `expected_exit_code` | `int \| None` | `None` | If set, also assert exit code matches |

---

## `CompileCheckTest`

Compiles small code snippets with g++ and asserts whether each one should succeed or fail to compile. Useful for testing const correctness, deleted constructors, access specifiers, template constraints, and SFINAE.

The step does not use the artifacts dict -- it compiles each snippet independently with g++. The artifacts dict is passed through unchanged.

```python
from lograder.pipeline.test.compile_check import CompileCheckTest, CompileCase
from lograder.process.registry.gcc import GNUXXStandard

cases = [
    CompileCase(
        name="const_read_ok",
        preamble="#include <MyClass.hpp>",
        code="const MyClass obj; (void)obj.get_value();",
        should_compile=True,
    ),
    CompileCase(
        name="const_mutation_forbidden",
        preamble="#include <MyClass.hpp>",
        code="const MyClass obj; obj.set_value(1);",
        should_compile=False,
    ),
]

pipeline.add(cc := CompileCheckTest(
    cases,
    include_dirs=[submission_dir],  # so g++ can find the student header
))
cc.scorer = TestCaseScorer(
    {"const_read_ok": 10.0, "const_mutation_forbidden": 10.0},
    label="Compile-Time Rules",
)
```

By default each snippet is wrapped in `int main() { ... return 0; }`. To supply a full translation unit, put `// NO_MAIN` anywhere in `preamble`:

```python
CompileCase(
    name="full_tu",
    preamble="#include <MyClass.hpp>\n// NO_MAIN",
    code="int main() { MyClass obj; return 0; }",
    should_compile=True,
)
```

### `CompileCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique case name |
| `code` | `str` | required | Code snippet (placed inside main unless `// NO_MAIN`) |
| `should_compile` | `bool` | required | Expected compilation outcome |
| `preamble` | `str` | `""` | Code before main (includes, type decls). `"// NO_MAIN"` skips main wrapper. |
| `standard` | `GNUXXStandard` | `CXX17` | C++ standard |
| `extra_flags` | `list[str]` | `[]` | Additional raw compiler flags |

---

## `ComplexityTest`

Measures empirical algorithmic complexity by timing a binary at increasing input sizes, fitting a log-log regression, and checking the estimated exponent against expected bounds.

```python
from lograder.pipeline.test.complexity import ComplexityTest, ComplexityCase, ComplexityClass

cases = [
    ComplexityCase(
        name="sort_is_nlogn",
        input_fn=lambda n: "\n".join(str(i) for i in range(n, 0, -1)).encode() + b"\n",
        sizes=[100, 500, 2000, 10000, 50000],
        expected=ComplexityClass.O_N_LOG_N,
        runs_per_size=3,
    ),
]

pipeline.add(comp := ComplexityTest("sorter", cases))
comp.scorer = TestCaseScorer({"sort_is_nlogn": 20.0}, label="Complexity")
```

### `ComplexityClass` values

| Value | Exponent bounds (log-log slope) |
|-------|-------------------------------|
| `O_1` | alpha < 0.15 |
| `O_LOG_N` | 0.05 -- 0.35 |
| `O_N` | 0.75 -- 1.35 |
| `O_N_LOG_N` | 0.90 -- 1.55 (overlaps O_N intentionally) |
| `O_N_SQUARED` | 1.75 -- 2.35 |
| `O_N_CUBED` | 2.70 -- 3.30 |

O(n) and O(n log n) bounds overlap because they are nearly indistinguishable at small sizes. Use input sizes spanning >= 3 orders of magnitude for reliable classification.

### `ComplexityCase` fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Unique case name |
| `input_fn` | `Callable[[int], bytes]` | required | Returns stdin bytes for a given size n |
| `sizes` | `list[int]` | required | Increasing input sizes to measure at |
| `expected` | `ComplexityClass` | required | Expected complexity class |
| `args` | `list[str]` | `[]` | Command-line arguments |
| `runs_per_size` | `int` | `3` | Timed runs per size; median is used |
| `timeout` | `float \| None` | `None` | Per-run timeout (defaults to pipeline timeout) |

**Tip:** timing-based tests are noisy on shared CI machines. Use `runs_per_size >= 3` and generous `sizes` spans. Consider using `AllOrNothingScorer` rather than `TestCaseScorer` if you want all-or-nothing credit for complexity.
