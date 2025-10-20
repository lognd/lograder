from pathlib import Path
from typing import Callable, FrozenSet, Literal, Dict, Any, List, Tuple, Union, Optional, get_args, cast, Protocol
from collections import deque
import subprocess
import re
import sys
import random
import string

ProjectType = Literal["cxx-source", "makefile", "cmake"]
FunctionTag = Literal["executable", "temp_folder", "file_content", "file", "files", "cxx_file", "cxx_files", "root"]
Command = Union[List[Union[str, Path]], Tuple[Union[str, Path], ...]]
Commands = Union[List[Command], Tuple[Command, ...]]
TOKEN_PATTERN = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

def random_name():
    return "".join(random.choices(string.ascii_letters + string.digits, k=25))

def random_exe():
    if sys.platform.startswith("win"):
        return f"{random_name()}.exe"
    return random_name()

def contains_token(command: Command, token: FunctionTag):
    return f"${{{token}}}" in command

def resolve_tokens(command: Command, context: Dict[FunctionTag, Command]):
    def replace(token: Union[str, Path]):
        if isinstance(token, Path): return [token]
        match = TOKEN_PATTERN.match(token)
        if match:
            key = match.group(1)
            if key in context:
                return context[key]
        return [token]
    return [tok for tokens in command for tok in replace(tokens)]

def detect_project_type(project_root: Path) -> ProjectType:
    for file in bfs_walk(project_root):
        if is_cmake_file(file):
            return "cmake"
        if is_makefile_file(file):
            return "makefile"
    return "cxx-source"


def bfs_walk(root: Path):  # pathlib defaults to dfs; must implement bfs ourselves.
    queue = deque([root])
    while queue:
        current = queue.popleft()
        if current.is_dir():
            for child in current.iterdir():
                queue.append(child)
        else:
            yield current

def is_text(path: Path):
    if not path.exists():
        return False
    try:
        chunk = path.read_bytes()[:65536]  # only read the first little bit for speed
        chunk.decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    return True

def is_cxx_source_file(path: Path) -> bool:
    if not path.exists() or path.suffix not in {
        ".cc",
        ".cp",
        ".cxx",
        ".cpp",
        ".CPP",
        ".c++",
        ".C",
        ".c",
    }:
        return False
    return is_text(path)


def is_cmake_file(path: Path) -> bool:
    return path.exists() and path.name == "CMakeLists.txt" and is_text(path)


def is_catch2_file(path: Path) -> bool:
    if not is_cxx_source_file(path):
        return False
    try:
        content = open(path).read()
        if (
            "#define CATCH_CONFIG_RUNNER" in content
            or "#define CATCH_CONFIG_MAIN" in content
        ):
            return True
        return False
    except UnicodeDecodeError:
        return False


def is_makefile_file(path: Path) -> bool:
    return path.exists() and path.name == "Makefile"


def is_makefile_target(makefile: Path, target: str) -> bool:
    if not is_makefile_file(makefile):
        return False
    proc = subprocess.run(
        ["make", "-qp"], cwd=makefile.parent, capture_output=True, text=True
    )
    for line in proc.stdout.splitlines():
        if line.strip().startswith(f"{target}:"):
            return True
    return False


def is_valid_target(target: str) -> bool:
    if len(target) < 3:
        return False
    if target in (
        "all",
        "install",
        "depend",
        "package",
        "test",
        "package_source",
        "edit_cache",
        "rebuild_cache",
        "clean",
        "help",
        "build.ninja",
        "ALL_BUILD",
        "ZERO_CHECK",
        "INSTALL",
        "RUN_TESTS",
        "PACKAGE",
    ):
        return False
    if "catch2" in target.lower():
        return False
    for banned in ("experimental", "nightly", "continuous", "cache", "cmake"):
        if banned in target.lower():
            return False
    if target.endswith(".obj") or target.endswith(".i") or target.endswith(".s"):
        return False
    return True
