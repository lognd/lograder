# Pipeline & Steps

## Pipeline

`Pipeline` holds an ordered list of `Step` instances and threads data through them.

```python
pipeline = Pipeline()
pipeline.steps = [step_a, step_b, step_c]
pipeline.validate_step_types()  # raises StaffException on type mismatch
pipeline()
```

Each step's `Ok` return value becomes the next step's input. If any step returns `Err`, the pipeline stops and logs the error value.

## Step protocol

Every step is a Python generator with exactly 5 type parameters:

```python
class MyStep(Base[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT]):
    def __call__(self, input: InputT) -> Generator[
        Result[OkDisplayT, ErrDisplayT],
        None,
        Result[OkOutputT, ErrOutputT],
    ]:
        ...
```

| What | How | Effect |
|------|-----|--------|
| Log a passing packet | `yield Ok(my_ok_display)` | Logged. Pipeline continues. |
| Log a failing packet | `yield Err(my_err_display)` | Logged. Pipeline continues. |
| Finish, pass data forward | `return Ok(my_ok_output)` | Value becomes next step's input. |
| Finish, abort pipeline | `return Err(my_err_output)` | Logged. Pipeline stops here. |

All yielded/returned values are Pydantic `BaseModel` instances. They must have a matching `@register_layout(...)` or `logger.packet()` will raise.

## Type chaining

`Pipeline.validate_step_types()` checks that each step can follow the previous one. A step can follow its predecessor if the predecessor's `OkOutputT` is in the step's `InputT`. Union inputs work:

```python
class MyFlexStep(
    SomeBase[Manifest | CMakeManifest, ...]  # accepts either
):
    ...
```

Type checking uses **exact equality**, not subtyping.

## Stage base classes

Each stage has a thin abstract base that just aliases `Step`:

| Stage | Base class | Module |
|-------|-----------|--------|
| Input | `Input` | `pipeline/input/input.py` |
| Check | `Check` | `pipeline/check/check.py` |
| Build | `Build` | `pipeline/build/build.py` |
| Test  | `Test`  | `pipeline/test/test.py` |

## Result type

```python
from lograder.common import Ok, Err, Result

r = Ok(42)
r.is_ok        # True
r.danger_ok    # 42  (asserts is_ok first)

r = Err("oops")
r.is_err       # True
r.danger_err   # "oops"

r.map(lambda v: v * 2)             # Result with transformed Ok
r.map_err(lambda e: e.upper())     # Result with transformed Err
r.and_then(lambda v: Ok(v + 1))   # chained computation, short-circuits on Err
r.swap_ok(NewOkType)               # reinterpret Err as a different Ok type (type-level only)
```

## EnvironmentConfig

Global configuration threaded via a `contextvars.ContextVar`:

```python
from lograder.pipeline.config import config, config_from_toml

with config(root_directory=Path("/submissions/s42"), executable_timeout=30.0):
    pipeline()

# or from TOML:
with config_from_toml(Path("grader.toml")):
    pipeline()
```

Fields: `root_directory: Path`, `executable_timeout: float | None`, `executable_max_workers: int = 16`.
