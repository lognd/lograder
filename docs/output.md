# Output & layouts

## How it works

Every `logger.packet(model)` call serializes the model, dispatches it to a `Layout`, and formats it for each configured output handler. At process exit, `HTMLHandler` writes `out.html`.

```
logger.packet(MyModel(...))
   → wrap_packet → {"header": "my-packet-id", "payload": {...}}
   → stdout handler:  Layout.to_simple(data)
   → HTML handler:    Layout.to_html(data)  → collected in memory
   → atexit:          write out.html
```

## Built-in layout imports

Import these modules at the top of your autograder script, **before** any step uses the corresponding packet type:

```python
import lograder.output.layout.process.executable        # ExecutableData, InstallWarning
import lograder.output.layout.project.simple_project    # CMake/Makefile/PyProject manifest checks
import lograder.output.layout.check.source              # SourceCheck packets
import lograder.output.layout.pipeline.bash_script      # BashScriptBuild packets
import lograder.output.layout.pipeline.prebuilt         # PrebuiltArtifacts packets
import lograder.output.layout.test.output_compare       # OutputCompare{Success,Failure,Error}
import lograder.output.layout.test.valgrind             # ValgrindTest{Success,Failure,Error}
import lograder.output.layout.test.file_output          # FileOutput{Success,Failure,Error}
import lograder.output.layout.test.performance          # PerformanceTest{Success,Failure,Error}
import lograder.output.layout.test.symbol               # Symbol{Success,Failure,Error}
import lograder.output.layout.test.catch2               # Catch2{Success,Failure,Error}
import lograder.output.layout.test.gtest                # GTest{Success,Failure,Error}
import lograder.output.layout.test.ctest                # CTest{Success,Failure,Error}
import lograder.output.layout.test.pytest               # Pytest{Success,Failure,Error}
```

You only need to import the layouts for the steps you actually use.

## Writing a custom layout

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
    # to_ascii: auto-strips ANSI from to_ansi()
```

Put the layout in its own module and import that module at the top of your autograder.

## Logger usage

```python
from lograder.output.logger import get_logger
import logging

_LOGGER = get_logger(__name__)

# In your Step's __call__:
_LOGGER.packet(MyResult(value=42))
_LOGGER.packet(MyError(msg="bad"), level=logging.WARNING)
```

`get_logger()` returns a `LograderLogger` (extends `logging.Logger`) with the `.packet()` method added.

## Dynamic layouts (for codegen models)

When you generate model classes programmatically (as `simple_project.py` does), use `make_dynamic_layout`:

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

## Output config

lograder reads its logging config from `src/lograder/output/config.toml`. To customize, copy and pass to `setup_logger()`:

```python
from lograder.output.logger import setup_logger
setup_logger(Path("my_config.toml"))
```

Key things to customize:
- `[handlers.student]` → `output_file` — path for the HTML report (default `out.html`)
- Handler log level — control which packets appear in which output
