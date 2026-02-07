from __future__ import annotations

import traceback
from pathlib import Path
from typing import NewType, Optional, cast

from pydantic import BaseModel

from ..common import Err, Ok, Result
from ..exception import DeveloperException


class Package:
    pass


class FileError(BaseModel):
    path: Path
    error: Optional[Exception]
    error_type: str
    error_msg: str
    error_traceback: str


class File(Package):
    def __init__(self, path: Path):
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
DirectoryDict: type[dict] = NewType("DirectoryDict", dict[str, "DirectoryMapping"])
# noinspection PyTypeHints
DirectoryMapping = list[str | DirectoryDict]


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


class Manifest(Package):
    def __init__(self, structure: DirectoryMapping):
        pass
