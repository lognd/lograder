# Input

The input step reads the student submission from disk and produces a `Manifest`.

## `LocalDirectory`

```python
from lograder.pipeline.input.local_directory import LocalDirectory

pipeline.add(inp := LocalDirectory())
```

`LocalDirectory` resolves its root directory lazily from `get_config()` at call time, so it is safe to construct before entering the `config()` context manager.

### What it does

1. Reads `config().root_directory` to find the submission.
2. Recursively scans the directory tree.
3. Returns `Ok(Manifest)` — an immutable snapshot of all files in the submission.

On error (directory missing, unreadable) it returns a fatal `Err`.

## `EnvironmentConfig`

The pipeline's runtime settings live in `EnvironmentConfig`:

```python
from lograder.pipeline.config import EnvironmentConfig, config, get_config

# Fields and their defaults
config_obj = EnvironmentConfig(
    root_directory=Path("/autograder/submission"),
    executable_timeout=60.0,      # seconds; None = no timeout
    executable_max_workers=16,    # max concurrent subprocess workers
)
```

### Reading the current config

```python
cfg = get_config()
print(cfg.root_directory)
print(cfg.executable_timeout)
```

### Setting config with the context manager

```python
from lograder.pipeline.config import config

with config(root_directory=Path("/autograder/submission"), executable_timeout=30.0):
    score = pipeline()
```

`config(**changes)` patches the current `EnvironmentConfig` for the duration of the `with` block. Changes are thread-local (via a context variable), so nested calls work correctly.

### Nesting configs

```python
with config(root_directory=Path("/submissions")):
    with config(executable_timeout=5.0):
        # root_directory="/submissions", executable_timeout=5.0
        pipeline()
    # back to root_directory="/submissions", executable_timeout=default
```

### Loading from TOML

```python
from lograder.pipeline.config import config_from_toml

with config_from_toml(Path("grader_config.toml")):
    pipeline()
```

`grader_config.toml`:
```toml
root_directory = "/autograder/submission"
executable_timeout = 30.0
executable_max_workers = 8
```

## Typical usage

```python
from pathlib import Path
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.pipeline import Pipeline

pipeline = Pipeline()
pipeline.add(LocalDirectory())
# ... add more steps

with config(root_directory=Path("/autograder/submission")):
    score = pipeline()
```

## `Manifest` reference

`LocalDirectory` returns `Ok(Manifest)`. You rarely construct manifests directly, but here's what you can do with one:

```python
from lograder.pipeline.types.parcels import Manifest

m = Manifest.from_directory(Path("/submission"))
m.root            # Path — the directory the manifest was built from
m["main.cpp"]     # Path to the file, relative to root
"main.cpp" in m   # True/False

# Equality and subset
m == m2           # exact match (same files)
required <= m     # subset check (m has at least the files in required)

# Build a minimal manifest for checking
required = Manifest.from_flat(["CMakeLists.txt", "main.cpp"])
assert required <= m

# Manifest from TOML (for testing)
m2 = Manifest.from_toml(Path("manifest.toml"))
```
