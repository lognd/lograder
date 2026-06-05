# Process layer

The process layer wraps all subprocess calls with validated arguments, platform abstraction, and automatic installation fallbacks. You interact with it directly when writing custom steps or configuring executables.

## Running a command

### `StaticExecutable` -- for arbitrary commands

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

### `TypedExecutable` -- for validated commands

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

`TypedExecutable` rejects non-empty `input.arguments` -- all args come from the `CLIArgs` subclass.

## Defining a new `TypedExecutable`

```python
from pathlib import Path
from lograder.process.cli_args import CLIArgs, CLIOption, CLIPresenceFlag
from lograder.process.executable import TypedExecutable, register_typed_executable

class MyToolArgs(CLIArgs):
    verbose:  bool  = CLIPresenceFlag(["-v"])
    output:   Path  = CLIOption(emit=["--output={}"])
    source:   Path  = CLIOption(position=-1)   # appended last

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

| Descriptor | Field type | Emits |
|------------|-----------|-------|
| `CLIPresenceFlag(["--flag"])` | `bool` | `["--flag"]` if True, `[]` if False |
| `CLIOption(emit=["--opt={}"])` | any | `["--opt=<val>"]` |
| `CLIMultiOption(emit=["--val={}"])` | `list[...]` | one token per item |
| `CLIKVOption(emit=["--def={}={}"])` | `dict[...]` | one token per k/v pair |
| `CLIFlag(["--yes"], ["--no"])` | `bool` | first list if True, second if False |

`position` kwarg controls order (default 0, -1 = appended last).

Omit an optional flag entirely with `CLI_ARG_MISSING`:
```python
timeout: float | CLI_ARG_MISSING = CLIOption(
    default=CLI_ARG_MISSING(),
    emit=["--timeout={}"],
)
```

## `ExecutableOptions`

```python
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode

opts = ExecutableOptions(
    cwd=Path("/sandbox"),
    timeout=30.0,                 # seconds; None = no timeout
    inherit_parent_env=True,
    stdin_mode=StreamMode.PIPE,
    stdout_mode=StreamMode.PIPE,
    stderr_mode=StreamMode.PIPE,
)

# Derive a modified copy without mutating the original:
opts2 = opts.model_copy(update={"timeout": 5.0})
```

POSIX-only fields (return `NOT_APPLICABLE()` on Windows): `umask`, `user_id`, `user_name`, `group_id`, `group_name`, `extra_groups`.

Windows-only field: `creation_flags`.

Check platform fields with `isinstance(val, NOT_APPLICABLE)`.

## `ExecutableOutput`

```python
output.command       # list[str] -- full command that was run
output.stdout_bytes  # bytes
output.stderr_bytes  # bytes
output.return_code   # int (negative = killed by signal on POSIX)
output.stdout_text   # decoded str
output.stderr_text   # decoded str
```

## Auto-install pattern

All registered executables support `check_runnable()` and `install()`:

```python
from lograder.process.registry.valgrind import ValgrindExecutable

vg = ValgrindExecutable()
if vg.check_runnable().is_err:
    result = vg.install()
    if result.is_ok:
        vg.update_base_command(result.danger_ok)
    else:
        # handle install failure
        ...
```

Install scripts live in `src/lograder/data/install_scripts/` and run as bash scripts.

## Registered executables

All of these are available in `lograder.process.registry.*`:

| Class | Command | CLIArgs class |
|-------|---------|---------------|
| `CMakeExecutable` | `cmake` | `CMakeConfigureArgs`, `CMakeBuildArgs` |
| `MakefileExecutable` | `make` | `MakefileArgs` |
| `ValgrindExecutable` | `valgrind` | `ValgrindArgs` |
| `GCCExecutable` | `gcc` | `GCCArgs` |
| `GXXExecutable` | `g++` | `GXXArgs` |
| `ClangExecutable` | `clang` | `ClangArgs` |
| `ClangXXExecutable` | `clang++` | `ClangXXArgs` |
| `NasmExecutable` | `nasm` | `NasmArgs` |
| `GasExecutable` | `as` | `GasArgs` |
| `LdExecutable` | `ld` | `LdArgs` |
| `NmExecutable` | `nm` | `NmArgs` |
| `ArExecutable` | `ar` | `ArArgs` |
| `BashExecutable` | `bash` | `BashArgs`, `BashScriptArgs` |
| `CurlExecutable` | `curl` | `CurlArgs` |
| `PerfExecutable` | `perf` | `PerfRecordArgs`, `PerfStatArgs`, ... |
| `GprofngExecutable` | `gprofng` | `GprofngArgs` |
| `PipExecutable` | `pip` | `PipInstallArgs` |
| `PytestExecutable` | `pytest` | `PytestArgs` |
| `CTestExecutable` | `ctest` | `CTestArgs` |
| `GTestExecutable` | (binary name varies) | `GTestArgs` |
| `Catch2Executable` | (binary name varies) | `Catch2Args` |
