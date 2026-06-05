# Output & Logging

## How it works

Every `logger.packet(model)` call serializes the model, dispatches it to a `Layout`, and formats it for each configured output handler. At process exit, `HTMLHandler` writes `out.html`.

```
logger.packet(MyModel(...))
   → wrap_packet → {"header": "my-packet-id", "payload": {...}}
   → stdout handler: Layout.to_simple(data)
   → student handler: Layout.to_html(data) → collected in memory
   → atexit: write out.html
```

## Registering layouts

Every `BaseModel` you pass to `logger.packet()` needs a registered `Layout`. Register it with the decorator:

```python
from lograder.output.layout.layout import Layout, register_layout
from mypackage.models import MyResult

@register_layout("my-result")        # unique string ID
class MyResultLayout(Layout[MyResult]):
    @classmethod
    def to_simple(cls, data: MyResult) -> str:
        return f"Result: {data.value}"

    @classmethod
    def to_ansi(cls, data: MyResult) -> str:
        from colorama import Fore as F, Style as S
        return f"{S.BRIGHT}{F.GREEN}Result:{F.RESET}{S.RESET_ALL} {data.value}"
    # to_html: auto-converts to_ansi() via ansi2html — override only for custom HTML
    # to_ascii: auto-strips ANSI codes from to_ansi()
```

**Import the module** that defines the layout before any `logger.packet()` call with that type:

```python
import mypackage.layouts.my_result  # registers MyResultLayout at import time
```

Built-in layouts and their import paths:

| Model types | Import |
|-------------|--------|
| `ExecutableData`, `InstallWarning` | `lograder.output.layout.process.executable` |
| `CMake/Makefile/PyProjectManifestCheck{Data,Error}` | `lograder.output.layout.project.simple_project` |
| `SourceCheckData`, `SourceViolation`, `SourceCheckError` | `lograder.output.layout.check.source` |
| `BashScriptBuildOutput`, `BashScriptBuildError` | `lograder.output.layout.pipeline.bash_script` |
| `PrebuiltArtifactsData`, `PrebuiltArtifactsError` | `lograder.output.layout.pipeline.prebuilt` |
| `OutputCompare{Success,Failure,Error}` | `lograder.output.layout.test.output_compare` |
| `ValgrindTest{Success,Failure,Error}` | `lograder.output.layout.test.valgrind` |
| `FileOutput{Success,Failure,Error}` | `lograder.output.layout.test.file_output` |
| `PerformanceTest{Success,Failure,Error}` | `lograder.output.layout.test.performance` |
| `SymbolSuccess`, `SymbolFailure`, `SymbolError` | `lograder.output.layout.test.symbol` |

## Logger usage

```python
from lograder.output import get_logger

_LOGGER = get_logger(__name__)

# In your Step's __call__:
_LOGGER.packet(MyResult(value=42))  # INFO level
_LOGGER.packet(MyError(msg="bad"), level=logging.WARNING)
```

`LograderLogger` extends `logging.Logger` with the `.packet()` method. `get_logger()` calls `setup_logger()` on first use (configures from `output/config.toml`).

## Custom output config

Copy `src/lograder/output/config.toml` and pass it to `setup_logger()`:

```python
from lograder.output.logger import setup_logger
setup_logger(Path("my_config.toml"))
```

Key handler to customize: `[handlers.student]` — change `output_file` to set HTML output path. Add a Gradescope handler by implementing a custom handler class.

## Dynamic layouts (for codegen models)

When you generate model classes programmatically (like `simple_project.py` does), use `make_dynamic_layout`:

```python
from lograder.output.layout.dynamic import make_dynamic_layout
from lograder.output.layout.layout import LayoutLike

layout = make_dynamic_layout(
    layout_id="my-dynamic-packet",
    layout_type=GeneratedModelClass,
    layout_cls_name="GeneratedModelClassLayout",
    layout_like=LayoutLike(
        to_ansi=lambda cls, data: f"value={data.x}",
        to_simple=lambda cls, data: f"value={data.x}",
    ),
)
```
