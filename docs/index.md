# lograder docs

Python library for building autograders. Not a CLI tool — you write a Python script that uses lograder as a library.

## Core idea

```
Pipeline: LocalDirectory → Check → Build → Test → Test → ...
          Manifest       → CMakeManifest → dict[str,Artifact] → dict[str,Artifact]
```

Each `Step` is a generator. It `yield`s non-fatal display packets (logged to HTML/stdout) and `return`s either the next step's input (`Ok`) or a fatal error (`Err`). Test steps chain: they all speak `dict[str, Artifact]`.

## Docs

| File | What's in it |
|------|-------------|
| [quickstart.md](quickstart.md) | Complete working example in 30 lines |
| [pipeline.md](pipeline.md) | Pipeline, Step protocol, Result type, EnvironmentConfig |
| [steps.md](steps.md) | All built-in steps: Input, Check, Build, Test |
| [output.md](output.md) | Layout registration, logging, HTML output |
| [process.md](process.md) | TypedExecutable, CLIArgs, StaticExecutable, ExecutableOptions |
| [examples.md](examples.md) | More complete examples |

## Install

```bash
pip install -e ".[dev]"
```

## Quick reference

```python
# Config
from lograder.pipeline.config import config
with config(root_directory=Path("/submissions/s42"), executable_timeout=30.0):
    pipeline()

# Steps
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import CMakeManifestCheck
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase
from lograder.pipeline.test.file_output import FileOutputTest, FileOutputCase
from lograder.pipeline.test.performance import PerformanceTest, PerformanceCase

# Result
from lograder.common import Ok, Err, Result

# Layouts (must import to register)
import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.test.output_compare
import lograder.output.layout.test.valgrind
import lograder.output.layout.test.file_output
import lograder.output.layout.test.performance
```
