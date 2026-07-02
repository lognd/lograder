# Check

Check steps validate the student's submission before building. They transform a `Manifest` into a typed, validated manifest (e.g. `CMakeManifest`). If validation fails, the pipeline stops and the student gets 0 on everything downstream.

## Manifest checks

Three manifest check classes are exported directly from `simple_project` -- import and use the one matching your project type:

```python
from lograder.pipeline.check.project.simple_project import (
    CMakeManifestCheck,       # checks for CMakeLists.txt
    MakefileManifestCheck,    # checks for Makefile
    PyProjectManifestCheck,   # checks for pyproject.toml
)

pipeline.add(check := CMakeManifestCheck())
```

If the check passes it returns `Ok(CMakeManifest)` (or the equivalent typed manifest). If a required file is missing, it returns `Err(CMakeManifestCheckError)` and the pipeline stops.

### Checking for additional files

The built-in manifest checks only verify the project root file (`CMakeLists.txt`, etc.). To also require specific source files, add a `SourceCheck` step immediately after:

```python
pipeline.add(check  := CMakeManifestCheck())
pipeline.add(source := SourceCheck(
    language="cpp",
    files=["src/graph.cpp", "src/graph.h"],
    constraints=[],
))
```

### Advanced: custom manifest checkers

`make_simple_manifest_checker` generates a new check class for a specific required-files set. The valid `project_name` values are `"CMake"`, `"Makefile"`, and `"PyProject"` -- these determine the generated class names and the base manifest type.

```python
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker

_, _, _, CMakeManifestCheck = make_simple_manifest_checker(
    "CMake",
    req_files=["CMakeLists.txt", "src/main.cpp"],
)
pipeline.add(check := CMakeManifestCheck())
```

In practice, prefer the direct import + `SourceCheck` pattern above.

## Source checks

`SourceCheck` validates that the student's source code follows certain constraints -- forbidding specific language features, requiring include directives, and so on.

```python
from lograder.pipeline.check.source.source_check import SourceCheck
from lograder.pipeline.check.source.source_check import (
    OperatorConstraint,
    IdentifierConstraint,
    QualifiedNameConstraint,
    IncludeConstraint,
    ImportConstraint,
    KeywordConstraint,
)

import lograder.output.layout.check.source  # required

pipeline.add(source_check := SourceCheck(
    language="cpp",
    files=["src/graph.cpp", "src/graph.h"],
    constraints=[
        OperatorConstraint(tokens=["goto"], max_count=0),
        IdentifierConstraint(names=["malloc"], max_count=0),
    ],
))
source_check.scorer = CleanRunScorer(0.0, extra_credit=5.0, label="Clean code")
```

`SourceCheck` must come after the manifest check (it reads files from the manifest) and before the build step.

Every constraint counts matched occurrences and fails when that count exceeds `max_count`. Set `max_count=0` to forbid a feature outright, or a positive number to cap (rather than ban) its use. An optional `label` overrides the auto-generated display label.

### Constraint types

#### `OperatorConstraint`

Limits occurrences of one or more operator tokens (both languages).

```python
# Forbid goto
OperatorConstraint(tokens=["goto"], max_count=0)

# Forbid the ternary operator
OperatorConstraint(tokens=["?:"], max_count=0)
```

#### `IdentifierConstraint`

Limits uses of specific identifiers (variable names, function names, types).

```python
# Forbid calling malloc and free
IdentifierConstraint(names=["malloc", "free"], max_count=0)
```

#### `QualifiedNameConstraint`

C/C++ only: limits uses of fully-qualified names such as `std::sort`.

```python
# Forbid std::sort (student must implement their own)
QualifiedNameConstraint(qualified_names=["std::sort"], max_count=0)
```

#### `IncludeConstraint`

C/C++ only: limits `#include` directives for specific headers.

```python
# Forbid including <algorithm> (which has std::sort)
IncludeConstraint(headers=["<algorithm>"], max_count=0)
```

#### `ImportConstraint`

Python only: limits `import` / `from ... import` statements by module.

```python
# Forbid importing pickle (security issue)
ImportConstraint(modules=["pickle"], max_count=0)
```

#### `KeywordConstraint`

Limits occurrences of loop keywords, `for`/`while`/`do` (both languages). Useful for "no loops, only recursion" constraints. Python has no `do`-`while` construct.

```python
# Forbid all loops -- solution must be recursive
KeywordConstraint(keywords=["for", "while", "do"], max_count=0)
```

### Combining constraints

```python
pipeline.add(SourceCheck(
    language="cpp",
    files=["main.cpp", "utils.cpp"],
    constraints=[
        OperatorConstraint(tokens=["goto"], max_count=0),
        IdentifierConstraint(names=["malloc", "free"], max_count=0),
        IncludeConstraint(headers=["<algorithm>"], max_count=0),
        QualifiedNameConstraint(qualified_names=["std::sort"], max_count=0),
        KeywordConstraint(keywords=["for", "while", "do"], max_count=0),
    ],
))
```

### Scoring a source check

`CleanRunScorer` is the right scorer for source checks: it awards points when the check passes (no violations), and zeroes them when it fails.

```python
from lograder.pipeline.score import CleanRunScorer

source_check.scorer = CleanRunScorer(
    5.0,             # points for a clean run
    max_errors=0,    # zero tolerance
    label="No forbidden operations",
)

# Extra credit variant -- doesn't hurt the base score if it fails
source_check.scorer = CleanRunScorer(
    0.0,
    extra_credit=5.0,
    label="Clean memory management",
)
```

## Full example with both checks

```python
import lograder.output.layout.check.source  # noqa: F401
import lograder.output.layout.pipeline.build  # noqa: F401
import lograder.output.layout.project.simple_project  # noqa: F401
import lograder.output.layout.test.output_compare  # noqa: F401

from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.check.project.simple_project import CMakeManifestCheck
from lograder.pipeline.check.source.source_check import (
    IdentifierConstraint,
    OperatorConstraint,
    SourceCheck,
)
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.score import AllOrNothingScorer, CleanRunScorer, TestCaseScorer
from lograder.pipeline.test.output_compare import OutputCompareTest


def make_pipeline(submission_dir):
    pipeline = Pipeline()
    pipeline.add(LocalDirectory(root=submission_dir))
    pipeline.add(check  := CMakeManifestCheck())
    pipeline.add(source := SourceCheck(
        language="cpp",
        files=["lab3.cpp"],
        constraints=[
            OperatorConstraint(tokens=["goto"], max_count=0),
            IdentifierConstraint(names=["malloc"], max_count=0),
        ],
    ))
    pipeline.add(build := CMakeBuild())
    pipeline.add(tests := OutputCompareTest("lab3", cases))

    check.scorer  = AllOrNothingScorer(0.0, label="Files present")
    source.scorer = CleanRunScorer(10.0, label="Code quality")
    build.scorer  = AllOrNothingScorer(10.0, label="Build")
    tests.scorer  = TestCaseScorer({"case1": 20.0, "case2": 20.0}, label="Correctness")
    return pipeline
```

---

## `MypyCheck`

Runs mypy static type analysis on Python source files and yields a violation packet for each type error. Useful for Python assignments where type annotation correctness is graded.

```python
from lograder.pipeline.check.mypy_check import MypyCheck
from lograder.pipeline.score import CleanRunScorer

pipeline.add(mypy := MypyCheck(
    files=["graph.py"],
    ignore_missing_imports=True,   # recommended on Gradescope (no third-party stubs)
))
mypy.scorer = CleanRunScorer(10.0, label="Type Safety")
```

`MypyCheck` always returns `Ok(manifest)` unless mypy cannot be installed or a listed file is missing. Each mypy error is yielded as a non-fatal `Err(MypyViolation)` packet, so `CleanRunScorer(points, max_errors=0)` awards points only on a clean run.

### With strict mode

```python
pipeline.add(mypy := MypyCheck(
    files=["solution.py"],
    strict=True,                   # enables all strictness flags at once
    ignore_missing_imports=True,
))
mypy.scorer = CleanRunScorer(0.0, extra_credit=5.0, label="Strict Types")
```

### Individual strictness flags

```python
MypyCheck(
    files=["module.py"],
    disallow_untyped_defs=True,    # require annotations on all functions
    disallow_incomplete_defs=True, # require complete annotations (no partial)
    check_untyped_defs=True,       # type-check unannotated function bodies
    ignore_missing_imports=True,
)
```

### `MypyCheck` parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | `list[str]` | required | Python files relative to manifest root |
| `strict` | `bool` | `False` | Enable `--strict` (all strictness flags) |
| `disallow_untyped_defs` | `bool` | `False` | Require annotations on all functions |
| `disallow_incomplete_defs` | `bool` | `False` | Require complete annotations |
| `check_untyped_defs` | `bool` | `False` | Check bodies of unannotated functions |
| `ignore_missing_imports` | `bool` | `True` | Suppress missing stub errors |
| `extra_args` | `MypyArgs \| None` | `None` | Additional mypy args (overrides per-field) |
| `options` | `ExecutableOptions \| None` | `None` | Options for mypy invocation |

mypy is auto-installed via the install script in `data/install_scripts/install_mypy.sh` if not found on PATH.

---

## `TyCheck`

Runs [ty](https://docs.astral.sh/ty/) static type analysis on Python source files and yields a violation packet for each type error. `ty` is Astral's fast, modern type checker -- the same tool lograder itself is checked with. Prefer this over `MypyCheck` for new assignments; use `MypyCheck` only when you specifically need mypy's behavior.

```python
from lograder.pipeline.check.ty_check import TyCheck
from lograder.pipeline.score import CleanRunScorer

pipeline.add(ty := TyCheck(
    files=["graph.py"],
    ignore=["unresolved-import"],   # recommended on Gradescope (no third-party stubs)
))
ty.scorer = CleanRunScorer(10.0, label="Type Safety")
```

`TyCheck` always returns `Ok(manifest)` unless ty cannot be installed or a listed file is missing. Each ty error is yielded as a non-fatal `Err(TyViolation)` packet, so `CleanRunScorer(points, max_errors=0)` awards points only on a clean run.

### Adjusting rule severity

```python
pipeline.add(ty := TyCheck(
    files=["solution.py"],
    error=["possibly-unbound-attribute"],  # promote a rule to error severity
    warn=["redundant-cast"],               # demote a rule to warning (non-fatal, not counted)
    ignore=["unresolved-import"],
))
ty.scorer = CleanRunScorer(0.0, extra_credit=5.0, label="Strict Types")
```

### `TyCheck` parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | `list[str]` | required | Python files relative to manifest root |
| `python_version` | `str \| None` | `None` | Python version ty should assume (e.g. `"3.10"`); defaults to ty's own detection |
| `ignore` | `list[str] \| None` | `None` | Rule names to suppress entirely |
| `error` | `list[str] \| None` | `None` | Rule names to force to error severity |
| `warn` | `list[str] \| None` | `None` | Rule names to force to warning severity |
| `extra_args` | `TyArgs \| None` | `None` | Additional ty args (overrides per-field) |
| `options` | `ExecutableOptions \| None` | `None` | Options for ty invocation |

Only `severity == "error"` diagnostics are yielded as violations; warnings are recorded on the summary packet but don't fail the check.

ty is auto-installed via the install script in `data/install_scripts/install_ty.sh` if not found on PATH.
