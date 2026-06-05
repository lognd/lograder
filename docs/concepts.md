# Concepts

This page explains the mental model behind lograder. Once these five ideas click, the rest of the API makes sense.

## Pipeline

A `Pipeline` is an ordered list of `Step` instances. Calling `pipeline()` runs each step in sequence, threading results from one step into the next.

```
LocalDirectory -> CMakeManifestCheck ->     CMakeBuild     -> OutputCompareTest  -> ValgrindTest
    Manifest   ->    CMakeManifest   -> dict[str,Artifact] -> dict[str,Artifact] -> dict[str,Artifact]
```

The type annotation above each arrow shows what flows between steps. The pipeline validates these types before running (via `pipeline.validate_step_types()`).

If any step returns a fatal error (`Err`), the pipeline stops there. Downstream steps are skipped but still appear in the score as `0 / possible`.

## Step

Every step is a Python generator with a strict signature:

```python
class MyStep(SomeBase[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT]):
    def __call__(self, input: InputT) -> Generator[
        Result[OkDisplayT, ErrDisplayT], None, Result[OkOutputT, ErrOutputT]
    ]:
        yield Ok(OkDisplayT(...))    # non-fatal -- logged, pipeline continues
        yield Err(ErrDisplayT(...))  # non-fatal -- logged, pipeline continues
        return Ok(OkOutputT(...))    # passed as input to the next step
        # return Err(ErrOutputT(...)) -> logged, pipeline STOPS
```

The 5 generic parameters are:
- `InputT` -- what the step receives
- `OkOutputT` -- what it returns on success (next step's input)
- `ErrOutputT` -- what it returns on fatal failure (pipeline stops)
- `OkDisplayT` -- what it yields as non-fatal success packets (logged)
- `ErrDisplayT` -- what it yields as non-fatal error packets (logged)

**Yielded values** are logged immediately and don't affect control flow. They let the step report partial results (e.g. "test A passed, test B failed") while continuing.

**The return value** either passes control to the next step (`Ok`) or stops the pipeline (`Err`).

## Result

`Result[T, E]` is lograder's error type. It's either `Ok(value)` or `Err(error)` -- never both.

```python
from lograder.common import Ok, Err, Result

r: Result[int, str] = Ok(42)
r.is_ok    # True
r.is_err   # False
r.danger_ok   # 42  (asserts is_ok first)
r.danger_err  # AssertionError

# Transform
r.map(lambda x: x * 2)          # Ok(84)
r.map_err(lambda e: e.upper())  # Ok(42) unchanged
r.and_then(lambda x: Ok(x + 1)) # Ok(43)

# Swap the contained type without changing Ok/Err
r.swap_ok(float)   # Ok(42) but typed as Result[float, str]
```

There are no exceptions inside lograder's pipeline logic -- everything is `Ok` or `Err`.

## Manifest

A `Manifest` is an immutable snapshot of a directory's file tree. It's what `LocalDirectory` produces and what check steps validate.

```python
from lograder.pipeline.types.parcels import Manifest

m = Manifest.from_directory(Path("/submission"))
m.root          # Path("/submission")
m["main.cpp"]   # Path to the file (relative to root)

# Subset check -- does the manifest contain at least these files?
required = Manifest.from_flat(["CMakeLists.txt", "main.cpp"])
assert required <= m
```

Check steps transform a `Manifest` into a more specific manifest type (e.g. `CMakeManifest`) that carries additional validated structure (like which CMake targets exist).

## Artifact

An `Artifact` represents a built output. After a successful build, steps receive `dict[str, Artifact]` -- a mapping from artifact name to artifact.

```python
from lograder.pipeline.types.artifacts import CMakeArtifact, FileArtifact

# CMakeArtifact is what CMakeBuild produces
artifact: CMakeArtifact

# Turn it into a runnable executable
exe = artifact.executable  # -> StaticExecutable

# Run it
output = exe(
    ExecutableInput(arguments=["arg1", "arg2"]),
    options=ExecutableOptions(timeout=10.0),
)
output.stdout_text
output.return_code
```

Test steps take `dict[str, Artifact]` in and return it unmodified on success, so multiple test steps can chain on the same artifact dictionary.

## Data flow summary

```
PIPELINE_START
  -> LocalDirectory(root_directory=config.root_directory)
      returns Ok(Manifest) or Err(LocalDirectoryError)

  -> CMakeManifestCheck(required=["CMakeLists.txt", "main.cpp"])
      receives Manifest
      returns Ok(CMakeManifest) or Err(CMakeManifestCheckError)  <- STOP if Err

  -> CMakeBuild()
      receives CMakeManifest
      returns Ok(dict[str,Artifact]) or Err(BuildOutput)  <- STOP if Err

  -> OutputCompareTest("binary", cases)
      receives dict[str,Artifact]
      yields Ok(OutputCompareSuccess) or Err(OutputCompareFailure) per case
      returns Ok(dict[str,Artifact]) pass-through or Err(OutputCompareError) <- STOP

  -> ValgrindTest("binary", cases)
      receives dict[str,Artifact]
      (same pattern)
```

Each step knows its own input/output types. The pipeline checks type compatibility at startup, before any student code runs.
