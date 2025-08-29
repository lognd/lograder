import os
from collections import deque
from pathlib import Path


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
    return path.suffix in (".cc", ".cp", ".cxx", ".cpp", ".CPP", ".c++", ".C", ".c")


def is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def is_default_target(target: str) -> bool:
    return target in (
        "all",
        "help",
        "ALL_BUILD",
        "clean",
        "install",
        "INSTALL",
        "ZERO_CHECK",
        "RUN_TESTS",
    )
