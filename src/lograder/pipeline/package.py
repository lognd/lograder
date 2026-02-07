import traceback
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from ..common import Err, Ok, Result


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
