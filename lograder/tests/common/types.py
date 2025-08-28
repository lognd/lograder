from typing import Union
from pathlib import Path
from os import PathLike

FilePath = Union[str, bytes, PathLike[str], PathLike[bytes], Path]
