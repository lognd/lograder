# Process Execution

The process layer wraps all subprocess calls with validated arguments, platform abstraction, and automatic installation fallbacks.

## Running a command

### `StaticExecutable` — for arbitrary commands

```python
from lograder.process.executable import StaticExecutable, ExecutableInput, ExecutableOptions

exe = StaticExecutable(["/usr/bin/my-tool"])
output = exe(
    ExecutableInput(stdin_bytes=b"input data", arguments=["--flag", "arg"]),
    options=ExecutableOptions(timeout=10.0),
)
# output.stdout_text, output.stderr_text, output.return_code
```

`arguments` in `ExecutableInput` are appended to the base command.

### `TypedExecutable` — for validated commands

```python
from lograder.process.registry.cmake import CMakeExecutable, CMakeConfigureArgs

cmake = CMakeExecutable()
result = cmake(CMakeConfigureArgs(source_dir=Path("/my/project")))
# result: Result[ExecutableOutput, InstallationError]
if result.is_err:
    print(result.danger_err.message)
else:
    print(result.danger_ok.stdout_text)
```

`TypedExecutable` rejects non-empty `input.arguments` — all args come from the `CLIArgs` subclass.

## Defining a new `TypedExecutable`

```python
from lograder.process.cli_args import CLIArgs, CLIOption, CLIPresenceFlag
from lograder.process.executable import TypedExecutable, register_typed_executable

class MyToolArgs(CLIArgs):
    verbose:  bool       = CLIPresenceFlag(["-v"])
    output:   Path       = CLIOption(emit=["--output={}"])
    source:   Path       = CLIOption(position=-1)   # appended last

@register_typed_executable(["my-tool"])
class MyToolExecutable(TypedExecutable[MyToolArgs]):
    pass  # optionally add install_executable for auto-install
```

Usage:
```python
tool = MyToolExecutable()
result = tool(MyToolArgs(verbose=True, output=Path("out.bin"), source=Path("src.c")))
# Emits: ["my-tool", "-v", "--output=out.bin", "src.c"]
```

## `CLIArgs` descriptor reference

| Descriptor | Emits | Notes |
|------------|-------|-------|
| `CLIPresenceFlag(["--flag"])` | `["--flag"]` if `True`, `[]` if `False` | Field type: `bool` |
| `CLIOption(emit=["--opt={}"])` | `["--opt=<val>"]` | Omit with `CLI_ARG_MISSING` default |
| `CLIMultiOption(emit=["--val={}"])` | one token per list item | Field type: `list[...]` |
| `CLIKVOption(emit=["--def={}={}"])` | `["--def=k=v", ...]` | Field type: `dict[...]` |
| `CLIFlag(["--yes"], ["--no"])` | first list if `True`, second if `False` | |

`position` kwarg on any descriptor controls order (default 0, -1 = appended last).

`CLI_ARG_MISSING` as a field default means "omit this flag entirely":
```python
timeout: float | CLI_ARG_MISSING = CLIOption(default=CLI_ARG_MISSING(), emit=["--timeout={}"])
```

## `ExecutableOptions`

```python
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode

opts = ExecutableOptions(
    cwd=Path("/sandbox"),
    timeout=30.0,               # seconds; None = no timeout
    inherit_parent_env=True,    # merge with os.environ
    stdin_mode=StreamMode.PIPE, # PIPE, INHERIT, NULL, STDOUT
    stdout_mode=StreamMode.PIPE,
    stderr_mode=StreamMode.PIPE,
)

# Derive a modified copy:
opts2 = opts.model_copy(update={"timeout": 5.0})
```

POSIX-only fields (are `NOT_APPLICABLE()` on Windows): `umask`, `user_id`, `user_name`, `group_id`, `group_name`, `extra_groups`, `restore_signals`.

Windows-only field (is `NOT_APPLICABLE()` on POSIX): `creation_flags`.

Check with `isinstance(val, NOT_APPLICABLE)`.

## `ExecutableOutput`

```python
output.command       # list[str] — full command including arguments
output.stdout_bytes  # bytes
output.stderr_bytes  # bytes
output.return_code   # int (negative = killed by signal on POSIX)
output.stdout_text   # decoded str (encoding from ExecutableInput)
output.stderr_text   # decoded str
```

## Valgrind

`ValgrindExecutable` wraps valgrind with `ValgrindArgs` for structured use. For running student binaries under valgrind (which aren't registered CLIArgs), use `StaticExecutable` directly — see `ValgrindTest` in `pipeline/test/valgrind.py` for the pattern.

Auto-install:
```python
from lograder.process.registry.valgrind import ValgrindExecutable
vg = ValgrindExecutable()
if vg.check_runnable().is_err:
    result = vg.install()          # runs install script (POSIX only)
    vg.update_base_command(result.danger_ok)
```
