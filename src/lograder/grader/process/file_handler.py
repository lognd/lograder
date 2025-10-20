from __future__ import annotations

import shutil
import traceback
from abc import ABC, abstractmethod
from pathlib import Path
import tempfile
import weakref
from typing import Optional, List, Dict, Union, TypeAlias, TypedDict, Callable
from .process import ProcessBool

DirectoryType: TypeAlias = Dict[str, Union[List[str], "DirectoryType"]]

class DirectoryMatch(TypedDict):
    ok: bool
    missing_files: List[Path]
    extra_files: List[Path]
    missing_dirs: List[Path]
    extra_dirs: List[Path]

class Directory:
    def __init__(self, name: str, parent: Optional[Directory] = None):
        if parent is None:
            self._path = Path(name)
        else:
            self._path = parent.path / name
        self._files: List[Path] = []
        self._subdirectories: List[Directory] = []

    def add_file(self, file: str):
        self._files.append(self.path / file)

    def add_subdirectory(self, directory: Directory):
        self._subdirectories.append(directory)

    def match(self, directory: Path, strict: bool = False) -> DirectoryMatch:
        actual_files = {p for p in directory.glob("*") if p.is_file()}
        actual_dirs = {p for p in directory.glob("*") if p.is_dir()}

        expected_files = {self.path / f.name for f in self.files}
        expected_dirs = {self.path / d.path.name for d in self.subdirectories}

        missing_files = [f for f in expected_files if not (directory / f.name).exists()]
        extra_files = [f for f in actual_files if f.name not in {ef.name for ef in expected_files}]

        missing_dirs = [d for d in expected_dirs if not (directory / d.name).exists()]
        extra_dirs = [d for d in actual_dirs if d.name not in {ed.name for ed in expected_dirs}]

        for sub in self.subdirectories:
            real_sub = directory / sub.path.name
            if real_sub.exists() and real_sub.is_dir():
                subresult = sub.match(real_sub, strict)
                missing_files += subresult["missing_files"]
                extra_files += subresult["extra_files"]
                missing_dirs += subresult["missing_dirs"]
                extra_dirs += subresult["extra_dirs"]

        if strict:
            ok = not (missing_files or missing_dirs or extra_files or extra_dirs)
        else:
            ok = not (missing_files or missing_dirs)

        return {
            "ok": ok,
            "missing_files": missing_files,
            "extra_files": extra_files,
            "missing_dirs": missing_dirs,
            "extra_dirs": extra_dirs,
        }

    @property
    def path(self) -> Path:
        return self._path

    @property
    def subdirectories(self) -> List[Directory]:
        return self._subdirectories

    @property
    def files(self) -> List[Path]:
        return self._files

    @classmethod
    def read(cls, tree: DirectoryType) -> Directory:
        root = Directory("/")
        files = tree.get("_files", [])
        if files and isinstance(files, list):
            for file in files:
                root.add_file(file)
        for name, item in tree.items():
            if isinstance(item, dict):
                subdir = cls(name, root).read(item)
                root.add_subdirectory(subdir)
        return root

class FileHandlerInterface(ProcessBool, ABC):
    def __init__(self):
        super().__init__()
        self._root_dir: Optional[Path] = Path(tempfile.mkdtemp())

        def _cleanup(self):
            shutil.rmtree(self._root_dir, ignore_errors=True)
            self._root_dir = None

        weakref.finalize(self, _cleanup, self)

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    def move_file(self, file: Path, root: Path) -> Optional[Path]:
        relative_path: Path = file.relative_to(root)
        new_path: Path = self.root_dir / relative_path
        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(file, new_path)
            return new_path
        except PermissionError as e:
            self.set_failure(e, "Could not make new directories or copy files.")
        return None

    @abstractmethod
    def setup(self): ...

class ProjectFileHandler(FileHandlerInterface):
    def __init__(self, project_root: Path):
        super().__init__()
        self._project_root = project_root

    @property
    def project_root(self) -> Path:
        return self._project_root

    def setup(self):
        for file in self.project_root.rglob("*"):
            if file.is_file():
                self.move_file(file, self.project_root)

class MixinFileHandler(FileHandlerInterface):
    def __init__(self, base: Path, submission: Path, mixin_callback: Optional[Callable[[Path], None]] = None):
        super().__init__()
        self._base = base
        self._mixin = submission
        if mixin_callback is None:
            mixin_callback = lambda _: None
        self._callback = mixin_callback

    @property
    def base(self) -> Path:
        return self._base

    @property
    def mixin(self) -> Path:
        return self._mixin

    def setup(self):
        for file in self.base.rglob("*"):
            if file.is_file():
                self.move_file(file, self.base)
        for file in self.mixin.rglob("*"):
            if file.is_file():
                dest = self.root_dir / file.relative_to(self.mixin)
                if dest.exists():
                    self.set_failure(traceback=f"File `{file}` already exists.")
                    continue
                new_path = self.move_file(file, self.mixin)
                if new_path is not None:
                    try:
                        self._callback(new_path)
                    except Exception as e:
                        self.set_failure(e, traceback=traceback.format_exc())
