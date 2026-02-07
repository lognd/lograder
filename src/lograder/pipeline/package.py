from __future__ import annotations

import traceback
from abc import ABC, abstractmethod
from pathlib import Path
from typing import NewType, Optional, cast

from pydantic import BaseModel

from ..common import Err, Ok, Result
from ..exception import DeveloperException, StaffException
from .config import get_config


class Package:
    pass


class FileError(BaseModel):
    path: Path
    error: Optional[Exception]
    error_type: str
    error_msg: str
    error_traceback: str


class FileContent(Package, ABC):
    @property
    @abstractmethod
    def utf8_contents(self) -> Result[str, FileError]: ...

    @property
    def bytes_contents(self) -> Result[bytes, FileError]:
        return self.utf8_contents.map(lambda s: s.encode("utf-8"))


class Text(FileContent):
    def __init__(self, content: str):
        self._content = content

    @property
    def utf8_contents(self) -> Result[str, FileError]:
        return Ok(self._content)


class File(FileContent):
    def __init__(self, path: Path):
        config = get_config()
        if not path.is_relative_to(config.root_directory):
            path = config.root_directory / path
        if not path.resolve().exists():
            raise StaffException(
                f"Could not find the file corresponding to the path, `{str(path)}`."
            )
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def stem(self) -> str:
        return self._path.stem

    @property
    def extension(self) -> str:
        return self._path.suffix

    def _file_error(self, e: Exception) -> FileError:
        return FileError(
            path=self._path,
            error=e,
            error_type=e.__class__.__name__,
            error_msg=str(e),
            error_traceback=traceback.format_exc(),
        )

    @property
    def bytes_contents(self) -> Result[bytes, FileError]:
        try:
            return Ok(self._path.read_bytes())
        except Exception as e:
            return Err(self._file_error(e))

    @property
    def utf8_contents(self) -> Result[str, FileError]:
        try:
            return Ok(self._path.read_text(encoding="utf8"))
        except Exception as e:
            return Err(self._file_error(e))


# PyCharm is wrong here; it's having trouble deducing the recursive typing structure.
# noinspection PyTypeChecker
DirectoryDict = NewType("DirectoryDict", dict[str, "DirectoryMapping"])
# noinspection PyTypeHints
DirectoryMapping = list[str | DirectoryDict]


# noinspection PyTypeHints
def validate_directory_dict(x: dict[str, DirectoryMapping], /) -> DirectoryDict:
    if len(x) == 0:
        raise DeveloperException(
            f"Tried to make a `DictionaryDict` out of an empty dictionary. Please ensure that lines before the listed calling line create a properly formatted `DictionaryDict`; a `DirectoryDict` is a dictionary with a single key corresponding to the super-directory and a value of a list containing strings (corresponding to file names) or other `DirectoryDicts` (corresponding to nested folders)."
        )
    if len(x) > 1:
        raise DeveloperException(
            f"Tried to make a `DictionaryDict` out of a non-singleton dictionary (with keys, `{'`, `'.join(str(k) for k in x)}`, and values, `{'`, `'.join(str(k) for k in x.values())}`). Please ensure that lines before the listed calling line create a properly formatted `DictionaryDict`; a `DirectoryDict` is a dictionary with a single key corresponding to the super-directory and a value of a list containing strings (corresponding to file names) or other `DirectoryDicts` (corresponding to nested folders)."
        )
    return cast(DirectoryDict, x)


# noinspection PyTypeHints
def directory_name(x: DirectoryDict, /) -> str:
    return next(iter(x.keys()))


class Manifest(Package):
    def __init__(self, structure: DirectoryMapping):
        super().__init__()
        self._files, self._dirs = self._explore_directory(structure)

    @property
    def files(self) -> list[File]:
        return [File(f) for f in self._files]

    @staticmethod
    def _explore_directory(
        directory: DirectoryMapping, *, root: Optional[Path] = None
    ) -> tuple[list[Path], list[Path]]:
        if root is None:
            config = get_config()
            root = Path(config.root_directory)
        files: list[Path] = []
        dirs: list[Path] = [root]
        for child in directory:
            if isinstance(child, dict):
                sup = directory_name(child)
                sub_f, sub_d = Manifest._explore_directory(child[sup], root=root / sup)
                files += sub_f
                dirs += sub_d
            else:
                files.append(root / child)
        return files, dirs
