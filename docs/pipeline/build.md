# Build

Build steps take a validated manifest (from a check step) and produce a `dict[str, Artifact]` -- a map from artifact name to built output.

## `CMakeBuild`

Runs `cmake --build` on the student's CMake project.

```python
from lograder.pipeline.build.cmake import CMakeBuild

pipeline.add(build := CMakeBuild())
```

`CMakeBuild` uses the CMake file API to discover build targets. It returns:
- `Ok(dict[str, Artifact])` -- one `CMakeArtifact` per discovered target
- `Err(BuildOutput)` -- if configure or build fails (pipeline stops)

### Options

```python
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.process.registry.cmake import CMakeConfigureArgs, CMakeBuildArgs

build = CMakeBuild(
    configure_args=CMakeConfigureArgs(
        build_dir=Path("build"),          # relative to submission root
        cmake_args={                      # -D flags
            "CMAKE_BUILD_TYPE": "Debug",
        },
    ),
    build_args=CMakeBuildArgs(
        parallel=4,                        # -j flag
    ),
)
```

### Accessing build artifacts

```python
# After CMakeBuild, the pipeline dict looks like:
artifacts: dict[str, Artifact]
# Key is the CMake target name (e.g. "my_program", "my_library")

artifact = artifacts["my_program"]          # CMakeArtifact
exe = artifact.executable                   # StaticExecutable
output = exe(ExecutableInput(arguments=["--help"]))
```

## `MakefileBuild`

Runs `make` on the student's Makefile project.

```python
from lograder.pipeline.build.makefile import MakefileBuild

pipeline.add(build := MakefileBuild())
```

> **Note:** `MakefileBuild` currently returns `Ok({})` -- artifact discovery from Makefile projects is not yet implemented. Use it with `PrebuiltArtifacts` to manually specify what was built.

```python
from lograder.pipeline.build.makefile import MakefileBuild
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts

pipeline.add(MakefileBuild())
# MakefileBuild returns an empty artifact dict, not a manifest -- use absolute Path:
pipeline.add(PrebuiltArtifacts({"my_program": submission_dir / "my_program"}))
```

### Make options

```python
from lograder.pipeline.build.makefile import MakefileBuild
from lograder.process.registry.makefile import MakefileArgs

build = MakefileBuild(
    args=MakefileArgs(
        target="all",
        jobs=4,
        variables={"CC": "clang"},
    )
)
```

## `BashScriptBuild`

Runs a bash script to build the project. Useful for non-standard build systems.

```python
from lograder.pipeline.build.bash_script import BashScriptBuild

pipeline.add(build := BashScriptBuild(
    script="build.sh",
    artifacts={"my_program": "my_program"},
))
```

`script` is a filename relative to `manifest.root` (the submission directory). The script runs with `cwd=manifest.root`. `artifacts` maps artifact names to paths relative to `cwd`; each path must exist after the script completes or the step fails fatally.

On success it returns `Ok(dict[str, Artifact])` containing exactly the artifacts declared. The step fails fatally (stopping the pipeline) if:
- the script file is missing from the submission
- the script exits non-zero
- an expected artifact path was not produced

### Options

```python
from lograder.process.executable import ExecutableOptions

pipeline.add(BashScriptBuild(
    script="build.sh",
    artifacts={"my_program": "my_program"},
    options=ExecutableOptions(timeout=60.0),
    make_artifacts_executable=True,  # default: chmod +x each artifact
))
```

## `PrebuiltArtifacts`

Injects artifacts into the pipeline without building anything. Useful for:

- Testing against instructor-provided binaries
- Adding artifacts after a Makefile or BashScript build
- Unit-testing your autograder locally

```python
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts

# After a manifest check step -- use a relative string (resolved against manifest.root):
pipeline.add(PrebuiltArtifacts({"my_program": "my_program"}))

# After MakefileBuild -- use an absolute Path (no manifest root available):
pipeline.add(MakefileBuild())
pipeline.add(PrebuiltArtifacts({"my_program": submission_dir / "my_program"}))

# After BashScriptBuild -- merge in additional artifacts with absolute Paths:
pipeline.add(BashScriptBuild("build.sh", artifacts={"my_program": "my_program"}))
pipeline.add(PrebuiltArtifacts({"helper_script": Path("/autograder/source/grader/check.sh")}))
```

`PrebuiltArtifacts` merges its new artifacts with any already in the dict, so it can safely follow any build step. When chaining after `MakefileBuild` (which returns an empty artifact dict, not a manifest), values must be absolute `Path` objects since there is no manifest root to resolve against.

## Artifact types

| Type | Description | Produced by |
|------|-------------|-------------|
| `FileArtifact(path)` | A file on disk | produced internally by `PrebuiltArtifacts` |
| `CMakeArtifact(name, target_type, build_dir)` | A CMake build target | `CMakeBuild` |
| `CMakeFileArtifact` | CMake target with a resolved file path | `CMakeBuild` (most targets) |

All artifact types expose `.executable -> StaticExecutable` for running.

## Full CMake pipeline example

```python
from pathlib import Path
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker
from lograder.pipeline.build.cmake import CMakeBuild
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.score import AllOrNothingScorer

make_simple_manifest_checker("sorter", required_files=["CMakeLists.txt", "sorter.cpp"])

cases = [
    OutputCompareCase(name="sorted",   args=["3", "1", "2"], expected_stdout="1 2 3\n"),
    OutputCompareCase(name="reversed", args=["3", "2", "1"], expected_stdout="1 2 3\n"),
]

pipeline = Pipeline()
pipeline.add(LocalDirectory())
pipeline.add(CMakeManifestCheck())
pipeline.add(build := CMakeBuild())
pipeline.add(tests := OutputCompareTest("sorter", cases))

build.scorer = AllOrNothingScorer(20.0, label="Build")

with config(root_directory=Path("/autograder/submission")):
    score = pipeline()
```

## Full Makefile pipeline example

```python
from lograder.pipeline.build.makefile import MakefileBuild
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts

make_simple_manifest_checker("lab1", required_files=["Makefile", "lab1.c"])

pipeline = Pipeline()
pipeline.add(LocalDirectory())
pipeline.add(MakefileManifestCheck())
pipeline.add(MakefileBuild())
# MakefileBuild returns Ok({}) -- inject the binary with an absolute path:
pipeline.add(PrebuiltArtifacts({"lab1": submission_dir / "lab1"}))
pipeline.add(tests := OutputCompareTest("lab1", cases))
```

## Full BashScriptBuild pipeline example

```python
from lograder.pipeline.build.bash_script import BashScriptBuild
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts
from lograder.pipeline.mixin.mixin import InjectStaffIntoStudent

GRADER_DIR = Path(__file__).parent

# Inject staff-provided support files before running the student script:
pipeline = Pipeline()
pipeline.add(LocalDirectory(root=submission_dir))
pipeline.add(InjectStaffIntoStudent(GRADER_DIR / "project"))
pipeline.add(build := BashScriptBuild(
    script="build.sh",
    artifacts={"my_program": "my_program"},
))
# Add grader-side helper scripts as additional artifacts (absolute paths):
pipeline.add(PrebuiltArtifacts({
    "check_script": GRADER_DIR / "check.sh",
}))
pipeline.add(tests := OutputCompareTest("my_program", cases))
```
