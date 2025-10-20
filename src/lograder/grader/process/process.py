from __future__ import annotations

import string
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Callable, FrozenSet, Iterable, Literal, Dict, Any, List, Tuple, Union, Optional, get_args, cast, Protocol
import inspect
import subprocess
import sys
import tempfile
import shlex
import traceback
import random
import shutil
import weakref
import re

from ..logger import Logger
from ..file_utils import is_cxx_source_file, random_exe, contains_token, resolve_tokens, FunctionTag, Command, Commands

def step(n: float) -> Callable:
    def wrapper(func: Callable) -> Callable:
        setattr(func, "__step_index__", n)
        return func
    return wrapper

class ProcessBool:
    def __init__(self):
        super().__init__()
        self._success: Optional[bool] = None
        self._error: Optional[BaseException] = None
        self._traceback: Optional[str] = None

    def set_success(self):
        self._success = True

    def set_failure(self, error: Optional[BaseException] = None, traceback: Optional[str] = None):
        self._success = False
        self._error = error
        self._traceback = traceback

    @property
    def error(self) -> Optional[BaseException]:
        return self._error

    @property
    def traceback(self) -> Optional[str]:
        return self._traceback

    @property
    def success(self) -> Optional[bool]:
        return self._success

class StepInterface(ProcessBool, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def execute(self): ...

class FunctionStep(StepInterface):
    def __init__(self, func: Callable) -> None:
        super().__init__()
        self._func: Callable = func
        self._args: List[Any] = []
        self._kwargs: Dict[str, Any] = {}

    def execute(self) -> None:
        try:
            self._func(*self._args, **self._kwargs)
            self.set_success()
        except Exception as e:
            traceback_ = traceback.format_exc()
            self.set_failure(e, traceback_)
            Logger.log_function_error(self, e, traceback_)

    def bind_arguments(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

class CommandBindable(Protocol):
    def bind_command(self, command: Command) -> Commands:
        ...

class CommandLineStep(StepInterface):
    def __init__(self,
                 command: Command,
                 working_directory: Optional[Path] = None,
                 stdin: str = "",
                 timeout: float = 300.0):
        super().__init__()
        self._command: List[str] = [str(c_) for c_ in command]
        self._working_directory: Optional[Path] = working_directory
        self._stdin: str = stdin
        self._timeout: float = timeout
        self._bind_callback: Optional[CommandBindable] = None

        self.stdout: Optional[str] = None
        self.stderr: Optional[str] = None
        self.return_code: Optional[str] = None

    def bind_object(self, obj: CommandBindable):
        self._bind_callback = obj

    @property
    def command(self) -> List[str]:
        return self._command

    @property
    def working_directory(self) -> Optional[Path]:
        return self._working_directory

    @property
    def stdin(self) -> str:
        return self._stdin

    @property
    def timeout(self) -> float:
        return self._timeout

    def execute(self):
        try:
            cmds = [self.command]
            if self._bind_callback is not None:
                cmds = self._bind_callback.bind_command(cmds[0])

            if sys.platform.startswith("win"):
                cmds = [["cmd", "/c"] + cmd for cmd in cmds]

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
            Logger.log_subprocess_timeout(self, e.timeout, e.output, e.stderr.decode(errors="ignore"))
            self.set_failure(e, traceback_)

        except Exception as e:
            traceback_ = traceback.format_exc()
            Logger.log_function_error(self, e, traceback_)
            self.set_failure(e, traceback_)


class ProcessMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> ProcessMeta:

        steps: List[Tuple[float, str, StepInterface]] = []

        for attr_name, obj in namespace.items():

            # Collect all the CLI commands
            if attr_name == "commands" and mcs.validate_nested_command(obj):
                cmds = cast(Commands, obj)
                for cmd in cmds:
                    steps.append((0, shlex.join(cmd), CommandLineStep(cmd)))

            # Collect and sort functions marked as `@step(...)`
            elif callable(obj) and hasattr(obj, "__step_index__"):
                tags = mcs.get_function_tags(obj)

                # It's kind of goofy because the base class needs to have a "bind_step" function
                # and "bind_command" and I don't really outline it here; however, the ABC that inherits from
                # this metaclass has the full signature and everything.

                callback = lambda self: namespace["bind_step"](self, obj, tags)()
                steps.append((getattr(obj, "__step_index__"), attr_name, FunctionStep(callback)))

        # Sort steps in order.
        steps.sort(key=lambda x: x[0])
        namespace["_steps"] = {s_[1]: s_[2] for s_ in steps}

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def validate_command(cmd: Any) -> bool:
        return isinstance(cmd, (list, tuple)) and all(isinstance(tok, (str, Path)) for tok in cmd)

    @classmethod
    def validate_nested_command(mcs, cmds: Any) -> bool:
        return isinstance(cmds, (list, tuple)) and all(mcs.validate_command(cmd) for cmd in cmds)

    @staticmethod
    def get_function_tags(obj: Callable) -> FrozenSet[FunctionTag]:
        tags = set()
        for name, param in inspect.signature(obj).parameters.items():
            if name not in get_args(FunctionTag):
                continue
            if param.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                continue
            tags.add(name)
        return frozenset(tags)

class ProcessInterface(ProcessBool, ABC, metaclass=ProcessMeta):
    def __init__(self):
        super().__init__()

    @property
    def steps(self) -> Dict[str, StepInterface]:
        return getattr(self, "_steps", {})

    @abstractmethod
    def bind_command(self, command: Command) -> Commands:
        ...

    @abstractmethod
    def bind_step(self, func: Callable, tags: FrozenSet[FunctionTag]) -> Callable[[], Any]:
        ...

    def run(self) -> None:
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

class FileProcess(ProcessInterface):
    def __init__(self, root_dir: Path):
        super().__init__()
        self._root: Path = root_dir
        self._temp_folder: Optional[Path] = None
        self._executable: Optional[Path] = None

    def collect_files(self) -> List[Path]:
        paths = []
        for path in self._root.rglob("*"):
            if path.is_file():
                paths.append(path)
        return paths

    def collect_cxx_files(self) -> List[Path]:
        return [path for path in self.collect_files() if is_cxx_source_file(path)]

    def collect_contents(self) -> List[str]:
        contents = []
        for path in self.collect_files():
            try:
                text = path.read_text(encoding="utf-8")
                contents.append(text)
            except UnicodeDecodeError:
                continue
        return contents

    def _init_temp_folder(self) -> None:
        self._temp_folder = Path(tempfile.mkdtemp())
        def _cleanup(self):
            shutil.rmtree(self._temp_folder, ignore_errors=True)
            self._temp_folder = None
        weakref.finalize(self, _cleanup, self)

    @property
    def executable(self) -> Commands:
        if self._executable is None:
            self._executable = self.root / random_exe()
        assert self._executable is not None, "self.executable() did not update self._executable"
        return [[self._executable]]

    @property
    def temp_folder(self) -> Path:
        if self._temp_folder is None:
            self._init_temp_folder()
        assert self._temp_folder is not None, "self._init_temp_folder() did not update self._temp_folder"
        return self._temp_folder

    @staticmethod
    def _wrap_file_iter(func: Callable, paths: Iterable[Path], *args, **kwargs) -> None:
        for path in paths:
            func(file=path, *args, **kwargs)

    def _wrap_file_content(self, func: Callable, *args, **kwargs) -> None:
        for path in self.collect_files():
            try:
                text = path.read_text(encoding="utf-8")
                func(file_content=text, *args, **kwargs)
            except UnicodeDecodeError:
                continue

    def _wrap_temp_folder(self, func: Callable, *args, **kwargs) -> None:
        func(temp_folder=self.temp_folder, *args, **kwargs)

    def bind_command(self, command: Command) -> Commands:

        ctx: Dict[FunctionTag, Command] = {
            "executable": [self.executable],
            "root": [self.root],
            "files": self.collect_files(),
            "cxx_files": self.collect_cxx_files(),
        }

        commands = [resolve_tokens(command, ctx)]

        if contains_token(commands[0], "file"):
            commands = [resolve_tokens(cmd, {"file": [file]}) for cmd in commands for file in self.collect_files()]
        elif contains_token(commands[0], "cxx_file"):
            commands = [resolve_tokens(cmd, {"cxx_file": [file]}) for cmd in commands for file in self.collect_cxx_files()]
        elif contains_token(commands[0], "file_content"):
            commands = [resolve_tokens(cmd, {"file_content": [file_content]}) for cmd in commands for file_content in self.collect_contents()]
        elif contains_token(commands[0], "temp_folder"):
            commands = [resolve_tokens(cmd, {"temp_folder": [self.temp_folder]}) for cmd in commands]

        return commands

    @property
    def root(self) -> Path:
        return self._root

    def bind_step(self, func: Callable, tags: FrozenSet[FunctionTag]) -> Callable[[], Any]:
        kw = {}
        if "executable" in tags:
            kw["executable"] = self.executable
        if "root" in tags:
            kw["root"] = self.root
        if "files" in tags:
            kw["files"] = self.collect_files()
        if "cxx_files" in tags:
            kw["cxx_files"] = self.collect_cxx_files()

        ofn = lambda *args, **kwargs: func(*args, **kw, **kwargs)

        if "file" in tags:
            ofn = lambda *args, **kwargs: self._wrap_file_iter(ofn, self.collect_files(), *args, **kwargs)
        if "cxx_file" in tags:
            ofn = lambda *args, **kwargs: self._wrap_file_iter(ofn, self.collect_cxx_files(), *args, **kwargs)
        if "file_content" in tags:
            ofn = lambda *args, **kwargs: self._wrap_file_content(ofn, *args, **kwargs)
        if "temp_folder" in tags:
            ofn = lambda *args, **kwargs: self._wrap_temp_folder(ofn, *args, **kwargs)

        cfn = lambda: ofn()
        return cfn

