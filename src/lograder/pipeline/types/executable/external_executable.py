import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import which
from typing import Callable, Iterable, Literal, Optional, cast, get_args

from pydantic import computed_field

from lograder.pipeline.types.executable.base_executable import Executable

from ....exception import DeveloperException

Platform = Literal["windows", "linux", "macos"]


def get_platform() -> Platform:
    if os.name == "nt":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    elif os.name == "posix":
        return "linux"
    raise DeveloperException(f"Unknown platform, {os.name=}, {sys.platform=}")


def _user_home() -> Path:
    return Path.home()


UNIX_DEFAULTS: list[Path] = [
    Path("/usr/bin"),
    Path("/usr/local/bin"),
    Path("/bin"),
    Path("/usr/local/sbin"),
    Path("/usr/sbin"),
    Path("/sbin"),
    _user_home() / ".local" / "bin",
]

LINUX_DEFAULTS: list[Path] = [
    *UNIX_DEFAULTS,
    Path("/snap/bin"),
    Path("/var/lib/flatpak/exports/bin"),
    Path("/usr/lib/jvm/*/bin"),
    Path("/opt/*/bin"),
    Path("/opt/homebrew/bin"),  # occasionally present via shared mounts / odd setups
    Path("/nix/var/nix/profiles/default/bin"),
    _user_home() / ".nix-profile" / "bin",
    Path("/run/current-system/sw/bin"),  # NixOS common profile path
]

MACOS_DEFAULTS: list[Path] = [
    *UNIX_DEFAULTS,
    Path("/opt/homebrew/bin"),
    Path("/opt/homebrew/sbin"),
    Path("/opt/local/bin"),
    Path("/opt/local/sbin"),
    Path("/Applications/Xcode.app/Contents/Developer/usr/bin"),
]

WINDOWS_DEFAULTS: list[Path] = [
    Path(r"C:\Windows\System32"),
    Path(r"C:\Windows"),
    Path(r"C:\Windows\SysWOW64"),
    _user_home() / r"AppData\Local\Microsoft\WinGet\Links",
    Path(r"C:\Program Files\Git\cmd"),
    Path(r"C:\Program Files\Git\bin"),
    Path(r"C:\Program Files\LLVM\bin"),
    Path(r"C:\Program Files (x86)\LLVM\bin"),
    Path(r"C:\Program Files\*\bin"),
    Path(r"C:\Program Files (x86)\*\bin"),
    Path(r"C:\Program Files\*"),
    Path(r"C:\Program Files (x86)\*"),
    Path(
        r"C:\Program Files\Microsoft Visual Studio\*\*\VC\Tools\MSVC\*\bin\Hostx64\x64"
    ),
    Path(
        r"C:\Program Files\Microsoft Visual Studio\*\*\VC\Tools\MSVC\*\bin\Hostx86\x86"
    ),
    Path(
        r"C:\Program Files (x86)\Microsoft Visual Studio\*\*\VC\Tools\MSVC\*\bin\Hostx64\x64"
    ),
    Path(
        r"C:\Program Files (x86)\Microsoft Visual Studio\*\*\VC\Tools\MSVC\*\bin\Hostx86\x86"
    ),
    _user_home() / r"AppData\Local\Programs\Python\Python*",
    _user_home() / r"AppData\Local\Programs\Python\Python*\Scripts",
    _user_home() / r"AppData\Roaming\Python\Python*\Scripts",
    _user_home() / r"AppData\Roaming\npm",
]

PLATFORM_DEFAULTS: dict[Platform, list[Path]] = {
    "windows": WINDOWS_DEFAULTS,
    "macos": MACOS_DEFAULTS,
    "linux": LINUX_DEFAULTS,
}


def default_executable_dirs() -> list[Path]:
    if get_platform() == "windows":
        return WINDOWS_DEFAULTS
    if get_platform() == "macos":
        return MACOS_DEFAULTS
    return LINUX_DEFAULTS


class ExternalExecutable(Executable, ABC):
    @property
    def command(self) -> list[str]:
        return self.get_command()

    @classmethod
    def get_command(cls) -> list[str]:
        loc = cls.locate()
        if loc is None:
            raise DeveloperException(
                f"Command, `{cls.__class__.__name__}`, is not available."
            )
        return [str(loc)]

    @classmethod
    @abstractmethod
    def locate(cls) -> Optional[Path]: ...

    @classmethod
    def is_installed(cls) -> bool:
        return cls.locate() is not None

    @classmethod
    @abstractmethod
    def install(cls) -> bool: ...


class FixedLocationExecutable(ExternalExecutable, ABC):
    name: str
    directories: list[Path] = default_executable_dirs()
    _locate_cache: Optional[Path] | Literal[True] = True
    __allowed_platforms__: dict[Platform, bool] = {p: True for p in get_args(Platform)}

    @classmethod
    def _is_runnable_file(cls, path: Path) -> bool:
        if not path.is_file():
            return False

        if get_platform() == "windows":
            pathext = {
                ext.lower()
                for ext in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
                if ext
            }
            return path.suffix.lower() in pathext and os.access(path, os.F_OK)

        return os.access(path, os.X_OK)

    @classmethod
    def iter_directories(cls) -> Iterable[Path]:
        for entry in cls.directories:
            text = os.fspath(entry)

            if any(ch in text for ch in "*?[]"):
                for match in Path().glob(text):
                    if match.is_dir():
                        yield match
            else:
                expanded = entry.expanduser()
                if expanded.is_dir():
                    yield expanded

    @classmethod
    def compute_location(cls) -> Optional[Path]:
        if not cls.__allowed_platforms__[get_platform()]:
            return None

        path = which(os.fspath(cls.name))
        if path is not None:
            resolved = Path(path).resolve()
            if cls._is_runnable_file(resolved):
                return resolved

        for directory in cls.iter_directories():
            candidate = directory / cls.name
            if cls._is_runnable_file(candidate):
                return candidate.resolve()

            if get_platform() == "windows" and candidate.suffix == "":
                for ext in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";"):
                    if not ext:
                        continue
                    candidate_with_ext = candidate.with_suffix(ext.lower())
                    if cls._is_runnable_file(candidate_with_ext):
                        return candidate_with_ext.resolve()

        return None

    @classmethod
    def locate(cls) -> Optional[Path]:
        if cls._locate_cache is True:
            loc = cls.compute_location()
            cls._locate_cache = loc
        return cast(Optional[Path], cls._locate_cache)


def exclude(
    platforms: Iterable[Platform],
) -> Callable[[type[FixedLocationExecutable]], type[FixedLocationExecutable]]:
    def wrapper(cls: type[FixedLocationExecutable]) -> type[FixedLocationExecutable]:
        setattr(
            cls,
            "__allowed_platforms__",
            {
                p: v and p not in platforms
                for p, v in getattr(cls, "__allowed_platforms__", {})
            },
        )
        return cls

    return wrapper


def windows_exclusive(
    cls: type[FixedLocationExecutable],
) -> type[FixedLocationExecutable]:
    setattr(
        cls, "__allowed_platforms__", {p: p == "windows" for p in get_args(Platform)}
    )
    return cls


def linux_exclusive(
    cls: type[FixedLocationExecutable],
) -> type[FixedLocationExecutable]:
    setattr(cls, "__allowed_platforms__", {p: p == "macos" for p in get_args(Platform)})
    return cls


def macos_exclusive(
    cls: type[FixedLocationExecutable],
) -> type[FixedLocationExecutable]:
    setattr(cls, "__allowed_platforms__", {p: p == "linux" for p in get_args(Platform)})
    return cls


class BuiltInExecutable(FixedLocationExecutable):
    @classmethod
    def install(cls) -> bool:  # "Installing" a built-in will always fail.
        return False
