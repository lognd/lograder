# lograder documentation

## Where to start

- **New to lograder?** Read [Getting started](getting-started.md) — a complete autograder in under 60 lines.
- **Understand the model?** Jump straight to the doc for the layer you need.

## Reference

### Pipeline layer

| Doc | What it covers |
|-----|----------------|
| [Concepts](concepts.md) | Mental model: Pipeline, Step, Result, Manifest, Artifact |
| [Input](pipeline/input.md) | `LocalDirectory`, `EnvironmentConfig`, the `config()` context manager |
| [Check](pipeline/check.md) | Manifest checks (CMake/Makefile/PyProject), `SourceCheck`, all constraints |
| [Build](pipeline/build.md) | `CMakeBuild`, `MakefileBuild`, `BashScriptBuild`, `PrebuiltArtifacts` |
| [Test](pipeline/test.md) | `OutputCompareTest`, `ValgrindTest`, `FileOutputTest`, `PerformanceTest`, `SymbolTest`, `Catch2Test`, `GTestTest`, `CTestTest`, `PytestTest` |
| [Scoring](pipeline/scoring.md) | `AllOrNothingScorer`, `CleanRunScorer`, `TestCaseScorer`, gimme floors, Gradescope output |
| [Metadata](pipeline/metadata.md) | `GraderMetadata`, `StaffAuthor`, attribution, submission time, late detection |

### Supporting layers

| Doc | What it covers |
|-----|----------------|
| [Process layer](process.md) | `TypedExecutable`, `CLIArgs`, the executable registry |
| [Output / layouts](output.md) | Logging packets, HTML report, writing custom layouts |

## Examples

| Example | Description |
|---------|-------------|
| [CMake autograder](examples/cmake-autograder.md) | Full grader for a C++ CMake project with output tests, valgrind, and scoring |
| [Python autograder](examples/python-autograder.md) | Full grader for a Python project with pytest integration and source checks |
| [Makefile autograder](examples/makefile-autograder.md) | Full grader for a C Makefile project |
| [Custom step](examples/custom-step.md) | Writing, typing, and registering your own pipeline step |

## Quick import reference

```python
# Config
from lograder.pipeline.config import config
with config(root_directory=Path("/submissions/s42"), executable_timeout=30.0):
    pipeline()

# Input
from lograder.pipeline.input.local_directory import LocalDirectory

# Check
from lograder.pipeline.check.project.simple_project import CMakeManifestCheck
from lograder.pipeline.check.source.source_check import (
    SourceCheck, OperatorConstraint, IdentifierConstraint,
    QualifiedNameConstraint, IncludeConstraint, ImportConstraint,
)

# Build
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.build.makefile import MakefileBuild
from lograder.pipeline.build.bash_script import BashScriptBuild
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts

# Test
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase, ComparisonMode
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase
from lograder.pipeline.test.file_output import FileOutputTest, FileOutputCase
from lograder.pipeline.test.performance import PerformanceTest, PerformanceCase
from lograder.pipeline.test.symbol import SymbolTest, SymbolCase
from lograder.pipeline.test.catch2 import Catch2Test
from lograder.pipeline.test.gtest import GTestTest
from lograder.pipeline.test.ctest import CTestTest
from lograder.pipeline.test.pytest import PytestTest

# Scoring
from lograder.pipeline.score import (
    TestCaseScorer, AllOrNothingScorer, CleanRunScorer,
    GimmeConfig, GradescopeConfig, GradescopeTestConfig,
)

# Metadata & attribution
from lograder.pipeline.metadata import GraderMetadata, StaffAuthor, Submitter

# Result
from lograder.common import Ok, Err, Result

# Layout imports (must import to register before any logger.packet() call)
import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.test.output_compare
import lograder.output.layout.test.valgrind
import lograder.output.layout.test.file_output
import lograder.output.layout.test.performance
import lograder.output.layout.test.symbol
import lograder.output.layout.test.catch2
import lograder.output.layout.test.gtest
import lograder.output.layout.test.ctest
import lograder.output.layout.test.pytest
```
