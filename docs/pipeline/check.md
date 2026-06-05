# Check

Check steps validate the student's submission before building. They transform a `Manifest` into a typed, validated manifest (e.g. `CMakeManifest`). If validation fails, the pipeline stops and the student gets 0 on everything downstream.

## Manifest checks

### Generated manifest checkers

The easiest way to create a manifest checker is `make_simple_manifest_checker`. It generates the check class and injects it into the caller's module globals.

```python
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker

make_simple_manifest_checker(
    "my_project",
    required_files=["CMakeLists.txt", "main.cpp", "utils.cpp"],
)
# Now available in this module's namespace:
#   CMakeManifest, CMakeManifestData, CMakeManifestCheckError, CMakeManifestCheck
pipeline.add(check := CMakeManifestCheck())
```

Available project types: `cmake`, `makefile`, `pyproject` (determined automatically from the required files or overridable).

```python
make_simple_manifest_checker(
    "my_project",
    required_files=["Makefile", "lab.c"],
    # produces: MakefileManifest, MakefileManifestCheck, etc.
)
pipeline.add(MakefileManifestCheck())
```

### What the check validates

- All `required_files` are present in the submission
- No required file is a directory instead of a file
- (For CMake projects) `CMakeLists.txt` is present

If the check passes it returns `Ok(CMakeManifest)` (or the equivalent for other project types). If it fails, it returns `Err(CMakeManifestCheckError)` and the pipeline stops.

### Custom required files

```python
make_simple_manifest_checker(
    "graph_project",
    required_files=[
        "CMakeLists.txt",
        "src/graph.cpp",
        "src/graph.h",
        "tests/test_graph.cpp",
    ],
)
```

## Source checks

`SourceCheck` validates that the student's source code follows certain constraints — forbidding specific language features, requiring include directives, and so on.

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

# Extra credit variant — doesn't hurt the base score if it fails
source_check.scorer = CleanRunScorer(
    0.0,
    extra_credit=5.0,
    label="Clean memory management",
)
```

## Full example with both checks

```python
import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.check.source
import lograder.output.layout.test.output_compare

from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker
from lograder.pipeline.check.source.source_check import (
    SourceCheck, OperatorConstraint, IdentifierConstraint, IncludeConstraint,
)
from lograder.pipeline.score import AllOrNothingScorer, CleanRunScorer, TestCaseScorer

make_simple_manifest_checker("lab3", required_files=["CMakeLists.txt", "lab3.cpp"])

pipeline = Pipeline()
pipeline.add(LocalDirectory())
pipeline.add(manifest := CMakeManifestCheck())
pipeline.add(source   := SourceCheck(
    files=["lab3.cpp"],
    constraints=[
        OperatorConstraint(operator="goto", forbidden=True),
        IdentifierConstraint(name="malloc", forbidden=True),
    ],
))
pipeline.add(build := CMakeBuild())
pipeline.add(tests := OutputCompareTest("lab3", cases))

manifest.scorer = AllOrNothingScorer(0.0, label="Files present")
source.scorer   = CleanRunScorer(10.0, label="Code quality")
build.scorer    = AllOrNothingScorer(10.0, label="Build")
tests.scorer    = TestCaseScorer({"case1": 20.0, "case2": 20.0}, label="Correctness")
```
