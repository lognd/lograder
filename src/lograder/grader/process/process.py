"""process.py

Implements a declarative, meta-driven build/execution pipeline system.

This module defines an extensible process framework composed of:
- Step definitions (`FunctionStep`, `CommandLineStep`) with runtime state tracking.
- A compile-time metaclass (`ProcessMeta`) that discovers and registers
  both command pipelines and Python function steps.
- Base process classes (`ProcessInterface`, `FileProcess`) that support
  binding file contexts, token resolution, and hierarchical process execution.

It provides the infrastructure for high-level builder classes (e.g., CMakeBuilder)
to define ordered build steps purely through class definitions or `@step` decorators.
"""

from __future__ import annotations

import inspect
import shlex
import shutil
import subprocess
import sys
import tempfile
import traceback
import weakref
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Union,
    cast,
    final,
    get_args,
)

from pydantic import BaseModel

from ..file_utils import (
    Command,
    Commands,
    FunctionTag,
    ProjectType,
    contains_token,
    detect_project_type,
    is_cxx_source_file,
    random_exe,
    resolve_tokens,
)
from ..logger import Logger


@final
class OrderedCommand(BaseModel):
    """Wraps a shell command with an explicit execution order.

    Attributes:
        order: Numeric order index for sequencing commands.
        command: The concrete command (list of str / Path tokens).
    """

    order: float
    command: Command


CommandDef = Union[Command, OrderedCommand]
"""Type alias for commands, allowing either raw lists or OrderedCommand objects."""


def step(n: float) -> Callable:
    """Decorator to register a method as a build step with a defined order.

    Args:
        n: Step index; lower values execute earlier.

    Returns:
        The wrapped callable with a `__step_index__` attribute.
    """

    def wrapper(func: Callable) -> Callable:
        setattr(func, "__step_index__", n)
        return func

    return wrapper


class ProcessBool:
    """Tracks success/failure state and error information for a process or step."""

    def __init__(self):
        super().__init__()
        self._success: Optional[bool] = None
        self._error: Optional[BaseException] = None
        self._traceback: Optional[str] = None

    def set_success(self):
        """Mark the process or step as successful."""
        self._success = True

    def set_failure(
        self, error: Optional[BaseException] = None, traceback: Optional[str] = None
    ):
        """Mark the process or step as failed and record exception info."""
        self._success = False
        self._error = error
        self._traceback = traceback

    @property
    def error(self) -> Optional[BaseException]:
        """The captured exception, if the step failed."""
        return self._error

    @property
    def traceback(self) -> Optional[str]:
        """The formatted traceback, if available."""
        return self._traceback

    @property
    def success(self) -> Optional[bool]:
        """Whether the step succeeded (True), failed (False), or not yet executed (None)."""
        return self._success


class StepInterface(ProcessBool, ABC):
    """Abstract base for all executable steps."""

    def __init__(self):
        super().__init__()

    @abstractmethod
    def execute(self):
        """Perform the step’s work and set success or failure."""
        ...


class FunctionStep(StepInterface):
    """Wraps a Python callable as an executable process step."""

    def __init__(self, func: Callable) -> None:
        super().__init__()
        self._func: Callable = func
        self._args: List[Any] = []
        self._kwargs: Dict[str, Any] = {}

    def execute(self) -> None:
        """Execute the bound function with stored arguments."""
        try:
            self._func(*self._args, **self._kwargs)
            self.set_success()
        except Exception as e:
            traceback_ = traceback.format_exc()
            self.set_failure(e, traceback_)
            Logger.log_function_error(self, e, traceback_)

    def bind_arguments(self, *args, **kwargs):
        """Bind runtime arguments for later invocation."""
        self._args = list(args)
        self._kwargs = kwargs


class CommandBindable(Protocol):
    """Protocol for objects that can expand command templates."""

    def bind_command(self, command: Command) -> Commands: ...


class CommandLineStep(StepInterface):
    """Represents a subprocess command to be executed as a step."""

    def __init__(
        self,
        command: Command,
        working_directory: Optional[Path] = None,
        stdin: str = "",
        timeout: float = 300.0,
    ):
        """
        Args:
            command: The base command sequence to execute.
            working_directory: Optional working directory for subprocess.
            stdin: Optional string to feed into the process’s stdin.
            timeout: Maximum allowed runtime in seconds.
        """
        super().__init__()
        self._command: Command = command
        self._working_directory: Optional[Path] = working_directory
        self._stdin: str = stdin
        self._timeout: float = timeout
        self._bind_callback: Optional[CommandBindable] = None

        self.stdout: Optional[str] = None
        self.stderr: Optional[str] = None
        self.return_code: Optional[int] = None

    def bind_object(self, obj: CommandBindable):
        """Attach an object providing command resolution context."""
        self._bind_callback = obj

    @property
    def command(self) -> Command:
        """The command to execute."""
        return self._command

    @property
    def working_directory(self) -> Optional[Path]:
        """Working directory for the subprocess."""
        return self._working_directory

    @property
    def stdin(self) -> str:
        """String passed to stdin."""
        return self._stdin

    @property
    def timeout(self) -> float:
        """Timeout for command execution, in seconds."""
        return self._timeout

    def execute(self):
        """Run the command, capturing stdout/stderr and exit code."""
        try:
            cmds: Commands = [self.command]
            if self._bind_callback is not None:
                cmds = self._bind_callback.bind_command(cmds[0])

            if sys.platform.startswith("win"):
                cmds = [["cmd", "/c"] + list(cmd) for cmd in cmds]

            for cmd in cmds:
                result = subprocess.run(
                    cmd,
                    cwd=self.working_directory,
                    input=self.stdin,
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout,
                )

                self.stdout = result.stdout
                self.stderr = result.stderr
                self.return_code = result.returncode

            self.set_success()

        except subprocess.CalledProcessError as e:
            traceback_ = traceback.format_exc()
            Logger.log_subprocess_error(self, e.returncode, e.stdout, e.stderr)
            self.set_failure(e, traceback_)

        except subprocess.TimeoutExpired as e:
            traceback_ = traceback.format_exc()
            stderr = e.stderr or b""
            Logger.log_subprocess_timeout(
                self, e.timeout, e.output, stderr.decode(errors="ignore")
            )
            self.set_failure(e, traceback_)

        except Exception as e:
            traceback_ = traceback.format_exc()
            Logger.log_function_error(self, e, traceback_)
            self.set_failure(e, traceback_)


class ProcessMeta(ABCMeta):
    """Metaclass that auto-discovers and registers process steps.

    It scans class attributes for:
        - Static `commands` definitions (raw or OrderedCommand).
        - Property-based `commands` definitions (evaluated safely).
        - Methods decorated with `@step(...)`.

    The resulting steps are collected and ordered into `_steps`.
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> ProcessMeta:
        steps: List[Tuple[float, str, StepInterface]] = []

        for attr_name, obj in namespace.items():
            # 1. Static or property-based "commands"
            if attr_name == "commands":
                if mcs.validate_nested_command(obj):
                    for i, cmd in enumerate(obj):
                        steps.append(
                            (i, shlex.join(map(str, cmd)), CommandLineStep(cmd))
                        )
                elif isinstance(obj, (list, tuple)) and all(
                    isinstance(c, OrderedCommand) for c in obj
                ):
                    for oc in obj:
                        steps.append(
                            (
                                oc.order,
                                shlex.join(map(str, oc.command)),
                                CommandLineStep(oc.command),
                            )
                        )
                elif isinstance(obj, property):
                    dummy_cls: type = super().__new__(mcs, name, bases, dict(namespace))
                    dummy_self: object = object.__new__(dummy_cls)  # type: ignore[call-overload]
                    try:
                        fget = obj.fget
                        if fget is None:
                            raise TypeError(
                                f"Property 'commands' in {name} has no getter."
                            )
                        value = fget(dummy_self)
                    except Exception as e:
                        raise TypeError(
                            f"Failed to evaluate @property 'commands' for {name}: {e}"
                        ) from e

                    if mcs.validate_nested_command(value):
                        for i, cmd in enumerate(value):
                            steps.append(
                                (i, shlex.join(map(str, cmd)), CommandLineStep(cmd))
                            )
                    elif all(isinstance(c, OrderedCommand) for c in value):
                        for oc in value:
                            steps.append(
                                (
                                    oc.order,
                                    shlex.join(map(str, oc.command)),
                                    CommandLineStep(oc.command),
                                )
                            )
                    else:
                        raise TypeError(
                            f"@property 'commands' in {name} did not return a valid list of Command or OrderedCommand."
                        )

            # 2. Function steps marked with @step(...)
            elif callable(obj) and hasattr(obj, "__step_index__"):
                tags = mcs.get_function_tags(obj)
                callback = lambda self: namespace["bind_step"](self, obj, tags)()
                steps.append(
                    (getattr(obj, "__step_index__"), attr_name, FunctionStep(callback))
                )

        steps.sort(key=lambda x: x[0])
        namespace["_steps"] = {s_[1]: s_[2] for s_ in steps}

        # Create the new class
        cls = super().__new__(mcs, name, bases, namespace)

        # Auto-register class if it defines an 'id'
        process_id = getattr(cls, "id", None)
        if process_id is not None:
            ProcessRegistry.register(process_id, cast(type[ProcessInterface], cls))

        return cls

    @staticmethod
    def validate_command(cmd: Any) -> bool:
        """Check if an object is a valid Command sequence."""
        return isinstance(cmd, (list, tuple)) and all(
            isinstance(tok, (str, Path)) for tok in cmd
        )

    @classmethod
    def validate_nested_command(mcs, cmds: Any) -> bool:
        """Validate a nested list of commands."""
        return isinstance(cmds, (list, tuple)) and all(
            mcs.validate_command(cmd) for cmd in cmds
        )

    @staticmethod
    def get_function_tags(obj: Callable) -> FrozenSet[FunctionTag]:
        """Extract FunctionTag arguments from a function’s signature."""
        tags: Set[FunctionTag] = set()
        for name, param in inspect.signature(obj).parameters.items():
            if name not in get_args(FunctionTag):
                continue
            name = cast(FunctionTag, name)
            if param.kind not in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ):
                continue
            tags.add(name)
        return frozenset(tags)


class ProcessInterface(ProcessBool, ABC, metaclass=ProcessMeta):
    """Abstract base for all process pipelines."""

    def __init__(self):
        super().__init__()

    @property
    def steps(self) -> Dict[str, StepInterface]:
        """All compiled steps, keyed by name."""
        return getattr(self, "_steps", {})

    @abstractmethod
    def bind_command(self, command: Command) -> Commands:
        """Resolve template tokens in a command."""
        ...

    @abstractmethod
    def bind_step(
        self, func: Callable, tags: FrozenSet[FunctionTag]
    ) -> Callable[[], Any]:
        """Bind contextual arguments for a function step."""
        ...

    def run(self) -> None:
        """Execute all registered steps sequentially."""
        for name, step in self.steps.items():
            if isinstance(step, FunctionStep):
                step.bind_arguments(self)
            elif isinstance(step, CommandLineStep):
                step.bind_object(self)
            step.execute()
            if not step.success:
                self.set_failure()
                return
        self.set_success()


class ProcessRegistry:
    """Global registry for process types.

    This registry maps string identifiers (like 'cmake-project', 'make-project', 'cxx-project')
    to concrete subclasses of `ProcessInterface`. It also supports instantiation and
    automatic project-type detection using file-system heuristics from `file_utils`.
    """

    _registry: Dict[str, type[ProcessInterface]] = {}

    # -------------------------------------------------------------------------
    # Registration and lookup
    # -------------------------------------------------------------------------

    @classmethod
    def register(cls, process_id: str, process_cls: type[ProcessInterface]) -> None:
        """Register a process class with its unique identifier.

        Args:
            process_id: The unique ID (e.g., 'cmake-project').
            process_cls: The class derived from `ProcessInterface` to register.

        Raises:
            ValueError: If the ID has already been registered.
        """
        if process_id in cls._registry:
            raise ValueError(f"Duplicate process id '{process_id}' already registered.")
        cls._registry[process_id] = process_cls

    @classmethod
    def get(cls, process_id: str) -> Optional[type[ProcessInterface]]:
        """Retrieve a registered process class by its identifier."""
        return cls._registry.get(process_id)

    @classmethod
    def list_ids(cls) -> List[str]:
        """Return all registered process identifiers."""
        return list(cls._registry.keys())

    # -------------------------------------------------------------------------
    # Creation and detection
    # -------------------------------------------------------------------------

    @classmethod
    def create(cls, process_id: str, *args: Any, **kwargs: Any) -> ProcessInterface:
        """Instantiate a registered process class by its ID.

        Args:
            process_id: Identifier of the process class (e.g., 'make-project').
            *args: Positional arguments to pass to the process constructor.
            **kwargs: Keyword arguments to pass to the process constructor.

        Returns:
            An initialized instance of the requested process type.

        Raises:
            ValueError: If the process_id is not registered.
        """
        proc_cls = cls.get(process_id)
        if proc_cls is None:
            raise ValueError(f"Unknown process type '{process_id}'.")
        return proc_cls(*args, **kwargs)

    @classmethod
    def detect(cls, root: Path) -> Optional[type[ProcessInterface]]:
        """Auto-detect a process class based on filesystem heuristics.

        Uses the `detect_project_type()` function from `file_utils` to infer
        whether the given directory represents a CMake, Makefile, or plain
        C/C++ source project.

        Args:
            root: The project root directory to analyze.

        Returns:
            The corresponding registered process class, or None if no match.
        """
        project_type: ProjectType = detect_project_type(root)

        # Map the detected type to a known process id
        mapping: Dict[ProjectType, str] = {
            "cmake": "cmake-project",
            "makefile": "make-project",
            "cxx-source": "cxx-project",
        }

        process_id = mapping.get(project_type)
        if process_id is None:
            return None

        return cls.get(process_id)


class FileProcess(ProcessInterface):
    """Concrete process that operates on a file tree.

    Handles discovery of files, C++ sources, and content iteration.
    Provides token binding utilities for commands and steps.
    """

    def __init__(self, root_dir: Path):
        """
        Args:
            root_dir: Root directory for the file process context.
        """
        super().__init__()
        self._root: Path = root_dir
        self._temp_folder: Optional[Path] = None
        self._executable: Optional[Path] = None

    def collect_files(self) -> List[Path]:
        """Return all files recursively under the root directory."""
        paths = []
        for path in self._root.rglob("*"):
            if path.is_file():
                paths.append(path)
        return paths

    def collect_cxx_files(self) -> List[Path]:
        """Return all C++ source files detected under the root."""
        return [path for path in self.collect_files() if is_cxx_source_file(path)]

    def collect_contents(self) -> List[str]:
        """Read and return text contents of all UTF-8-decodable files."""
        contents = []
        for path in self.collect_files():
            try:
                text = path.read_text(encoding="utf-8")
                contents.append(text)
            except UnicodeDecodeError:
                continue
        return contents

    def _init_temp_folder(self) -> None:
        """Create a temporary directory for intermediate build artifacts."""
        self._temp_folder = Path(tempfile.mkdtemp())

        def _cleanup(self):
            shutil.rmtree(self._temp_folder, ignore_errors=True)
            self._temp_folder = None

        weakref.finalize(self, _cleanup, self)

    def _init_executable_file_path(self) -> Path:
        """Initialize a random executable file path within the root directory."""
        if self._executable is None:
            self._executable = self.root / random_exe()
        assert (
            self._executable is not None
        ), "self._init_executable_file_path() did not update self._executable"
        return self._executable

    @property
    def executable(self) -> Commands:
        """Return the generated executable path as a command."""
        self._init_executable_file_path()
        assert (
            self._executable is not None
        ), "self.executable() did not update self._executable"
        return [[self._executable]]

    @property
    def temp_folder(self) -> Path:
        """Return a persistent temporary build folder, creating one if needed."""
        if self._temp_folder is None:
            self._init_temp_folder()
        assert (
            self._temp_folder is not None
        ), "self._init_temp_folder() did not update self._temp_folder"
        return self._temp_folder

    @staticmethod
    def _wrap_file_iter(func: Callable, paths: Iterable[Path], *args, **kwargs) -> None:
        """Apply a callable to each file in the given iterable."""
        for path in paths:
            func(file=path, *args, **kwargs)

    def _wrap_file_content(self, func: Callable, *args, **kwargs) -> None:
        """Apply a callable to the content of each file."""
        for path in self.collect_files():
            try:
                text = path.read_text(encoding="utf-8")
                func(file_content=text, *args, **kwargs)
            except UnicodeDecodeError:
                continue

    def _wrap_temp_folder(self, func: Callable, *args, **kwargs) -> None:
        """Invoke a callable once with the current temp folder."""
        func(temp_folder=self.temp_folder, *args, **kwargs)

    def bind_command(self, command: Command) -> Commands:
        """Resolve tokens in a command definition using this process’s context."""
        ctx: Dict[FunctionTag, Command] = {
            "executable": [self._init_executable_file_path()],
            "root": [self.root],
            "files": self.collect_files(),
            "cxx_files": self.collect_cxx_files(),
        }

        commands = [resolve_tokens(command, ctx)]

        if contains_token(commands[0], "file"):
            commands = [
                resolve_tokens(cmd, {"file": [file]})
                for cmd in commands
                for file in self.collect_files()
            ]
        elif contains_token(commands[0], "cxx_file"):
            commands = [
                resolve_tokens(cmd, {"cxx_file": [file]})
                for cmd in commands
                for file in self.collect_cxx_files()
            ]
        elif contains_token(commands[0], "file_content"):
            commands = [
                resolve_tokens(cmd, {"file_content": [file_content]})
                for cmd in commands
                for file_content in self.collect_contents()
            ]
        elif contains_token(commands[0], "temp_folder"):
            commands = [
                resolve_tokens(cmd, {"temp_folder": [self.temp_folder]})
                for cmd in commands
            ]

        return commands

    @property
    def root(self) -> Path:
        """Root directory path for this process context."""
        return self._root

    def bind_step(
        self, func: Callable, tags: FrozenSet[FunctionTag]
    ) -> Callable[[], Any]:
        """Wrap a function with contextual argument binding for use as a step."""
        kw: Dict[FunctionTag, Any] = {}
        if "executable" in tags:
            kw["executable"] = self._init_executable_file_path()
        if "root" in tags:
            kw["root"] = self.root
        if "files" in tags:
            kw["files"] = self.collect_files()
        if "cxx_files" in tags:
            kw["cxx_files"] = self.collect_cxx_files()

        ofn = lambda *args, **kwargs: func(
            *args, **{str(k): v for k, v in kw.items()}, **kwargs
        )

        if "file" in tags:
            ofn = lambda *args, **kwargs: self._wrap_file_iter(
                ofn, self.collect_files(), *args, **kwargs
            )
        if "cxx_file" in tags:
            ofn = lambda *args, **kwargs: self._wrap_file_iter(
                ofn, self.collect_cxx_files(), *args, **kwargs
            )
        if "file_content" in tags:
            ofn = lambda *args, **kwargs: self._wrap_file_content(ofn, *args, **kwargs)
        if "temp_folder" in tags:
            ofn = lambda *args, **kwargs: self._wrap_temp_folder(ofn, *args, **kwargs)

        cfn = lambda: ofn()
        return cfn
