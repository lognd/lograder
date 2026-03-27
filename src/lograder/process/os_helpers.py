from __future__ import annotations

import os
import sys
from enum import Enum, auto
from functools import lru_cache
from typing import Final, TypeVar, final

from lograder.common import Singleton

# noinspection PyPep8Naming
@final
class NOT_APPLICABLE(Singleton): ...

T = TypeVar("T")

# from winapi
CREATE_NEW_PROCESS_GROUP: Final = 0x200
SIGKILL = 137


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_posix() -> bool:
    return os.name == "posix"


def posix_and(val: T, /) -> NOT_APPLICABLE | T:
    if is_posix():
        return val
    return NOT_APPLICABLE()


def windows_and(val: T, /) -> NOT_APPLICABLE | T:
    if is_windows():
        return val
    return NOT_APPLICABLE()


def get_current_uid() -> int | NOT_APPLICABLE:
    if not is_posix():
        return NOT_APPLICABLE()
    return os.getuid()


def get_current_gid() -> int | NOT_APPLICABLE:
    if not is_posix():
        return NOT_APPLICABLE()
    return os.getgid()


def get_current_groups() -> list[int] | NOT_APPLICABLE:
    if not is_posix():
        return NOT_APPLICABLE()
    return os.getgroups()


def get_current_username() -> str | NOT_APPLICABLE:
    if not is_posix():
        return NOT_APPLICABLE()
    import pwd

    return pwd.getpwuid(os.getuid()).pw_name


def get_current_groupname() -> str | NOT_APPLICABLE:
    if not is_posix():
        return NOT_APPLICABLE()
    import grp

    return grp.getgrgid(os.getgid()).gr_name


def get_current_extra_groups() -> list[int] | NOT_APPLICABLE:
    if not is_posix():
        return NOT_APPLICABLE()
    return os.getgroups()


@lru_cache(maxsize=1)
def get_current_umask() -> int | NOT_APPLICABLE:
    if not is_posix():
        return NOT_APPLICABLE()

    # Try Linux fast path first
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("Umask:"):
                    return int(line.split()[1], 8)
    except Exception:
        pass

    # Portable fallback
    current = os.umask(0)
    os.umask(current)
    return current


class StreamMode(Enum):
    PIPE = auto()
    INHERIT = auto()
    NULL = auto()
    STDOUT = auto()
