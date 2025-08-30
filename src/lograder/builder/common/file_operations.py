from typing import Optional, List
from collections import deque
from pathlib import Path
import subprocess

from ...constants import Constants

def bfs_walk(root: Path):  # pathlib defaults to dfs; must implement bfs ourselves.
    queue = deque([root])
    while queue:
        current = queue.popleft()
        if current.is_dir():
            for child in current.iterdir():
                queue.append(child)
        else:
            yield current


def is_cxx_source_file(path: Path) -> bool:
    return path.exists() and path.suffix in (".cc", ".cp", ".cxx", ".cpp", ".CPP", ".c++", ".C", ".c")

def is_cmake_file(path: Path) -> bool:
    return path.exists() and path.name == "CMakeLists.txt"

def is_valid_target(target: str) -> bool:
    return target not in (
        "all",
        "install",
        "test",
        "package",
        "package_source",
        "edit_cache",
        "rebuild_cache",
        "clean",
        "help",
        "ALL_BUILD",
        "ZERO_CHECK",
        "INSTALL",
        "RUN_TESTS",
        "PACKAGE"
    )

def run_cmd(cmd: List[str | Path], commands: Optional[List[List[str | Path]]] = None, stdout: Optional[List[str]] = None, stderr: Optional[List[str]] = None) -> List[str]:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=Constants.DEFAULT_EXECUTABLE_TIMEOUT
    )
    if commands is not None:
        commands.append(cmd)
    if stdout is not None:
        stdout.append(result.stdout)
    if stderr is not None:
        stderr.append(result.stderr)
