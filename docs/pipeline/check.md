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
)

import lograder.output.layout.check.source  # required

pipeline.add(source_check := SourceCheck(
    language="cpp",
    files=["src/graph.cpp", "src/graph.h"],
    constraints=[
        OperatorConstraint(operator="goto", forbidden=True),
        IdentifierConstraint(name="malloc", forbidden=True),
    ],
))
source_check.scorer = CleanRunScorer(0.0, extra_credit=5.0, label="Clean code")
```

`SourceCheck` must come after the manifest check (it reads files from the manifest) and before the build step.

### Constraint types

#### `OperatorConstraint`

Forbids or requires a specific operator or keyword.

```python
# Forbid goto
OperatorConstraint(operator="goto", forbidden=True)

# Forbid ternary operator
OperatorConstraint(operator="?:", forbidden=True)

# Require use of new (not just malloc)
OperatorConstraint(operator="new", forbidden=False)
```

#### `IdentifierConstraint`

Forbids or requires a specific identifier (variable name, function name, etc.).

```python
# Forbid calling malloc
IdentifierConstraint(name="malloc", forbidden=True)

# Forbid calling free
IdentifierConstraint(name="free", forbidden=True)

# Require use of push_back
IdentifierConstraint(name="push_back", forbidden=False)
```

#### `QualifiedNameConstraint`

Forbids or requires a qualified name (e.g. `std::sort`).

```python
# Forbid std::sort (student must implement their own)
QualifiedNameConstraint(name="std::sort", forbidden=True)

# Forbid std::stack
QualifiedNameConstraint(name="std::stack", forbidden=True)
```

#### `IncludeConstraint`

Forbids or requires a specific `#include` directive.

```python
# Forbid including algorithm (which has std::sort)
IncludeConstraint(header="algorithm", forbidden=True)

# Require including the project header
IncludeConstraint(header="graph.h", forbidden=False)
```

#### `ImportConstraint`

For Python files: forbids or requires a specific `import` statement.

```python
# Forbid importing pickle (security issue)
ImportConstraint(module="pickle", forbidden=True)

# Require importing the module being tested
ImportConstraint(module="my_module", forbidden=False)
```

### Combining constraints

```python
pipeline.add(SourceCheck(
    language="cpp",
    files=["main.cpp", "utils.cpp"],
    constraints=[
        OperatorConstraint(operator="goto",   forbidden=True),
        IdentifierConstraint(name="malloc",   forbidden=True),
        IdentifierConstraint(name="free",     forbidden=True),
        IncludeConstraint(header="algorithm", forbidden=True),
        QualifiedNameConstraint(name="std::sort", forbidden=True),
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
            OperatorConstraint(operator="goto", forbidden=True),
            IdentifierConstraint(name="malloc", forbidden=True),
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
