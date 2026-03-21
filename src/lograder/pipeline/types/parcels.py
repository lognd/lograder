from __future__ import annotations

import traceback
from abc import ABC, abstractmethod
from os.path import normpath
from pathlib import Path
from typing import Any, Callable, Iterable, NewType, Optional, cast

from pydantic import BaseModel, Field

from ...common import Err, Ok, Result
from ...exception import DeveloperException, StaffException
from ..config import get_config

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


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


# noinspection PyTypeHints
def directory_key(x: str | dict, /) -> str:
    return x if isinstance(x, str) else directory_name(cast(DirectoryDict, x))


class ManifestComparisonEntry(BaseModel):
    expected: Optional[str | DirectoryDict]
    received: Optional[str | DirectoryDict]


class ManifestComparisonSummary(BaseModel):
    matches: dict[str, ManifestComparisonEntry] = Field(default_factory=dict)
    extra: dict[str, ManifestComparisonEntry] = Field(default_factory=dict)
    missing: dict[str, ManifestComparisonEntry] = Field(default_factory=dict)
    should_be_directory: dict[str, ManifestComparisonEntry] = Field(
        default_factory=dict
    )
    should_be_file: dict[str, ManifestComparisonEntry] = Field(default_factory=dict)

    def is_empty(self) -> bool:
        return not (
            self.matches
            or self.extra
            or self.missing
            or self.should_be_directory
            or self.should_be_file
        )


class Manifest(Package):
    def __init__(self, structure: DirectoryMapping):
        super().__init__()
        self._mapping = structure
        self._files, self._dirs = self._explore_directory(structure)

    # noinspection PyShadowingBuiltins
    @classmethod
    def from_directory(cls, dir: Path) -> Manifest:
        config = get_config()
        root = Path(config.root_directory).resolve()
        dir = dir.resolve()

        if not dir.exists():
            raise StaffException(f"Could not find directory, `{str(dir)}`.")
        if not dir.is_dir():
            raise StaffException(f"Path, `{str(dir)}` exists, but is not a directory.")
        if not dir.is_relative_to(root):
            raise StaffException(
                f"Directory, `{str(dir)}`, is outside configured root directory, `{str(root)}`."
            )

        def build_mapping(current: Path) -> DirectoryMapping:
            items: DirectoryMapping = []

            for child in sorted(
                current.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold())
            ):
                if child.is_dir():
                    items.append(
                        validate_directory_dict({child.name: build_mapping(child)})
                    )
                else:
                    items.append(child.name)

            return items

        return cls(build_mapping(dir))

    @classmethod
    def from_toml(cls, toml: Path) -> Manifest:
        """
        Here's an example `.toml` format.

        ```toml
        manifest = [
          "main.py",
          "README.md",
          { src = [
            "app.py",
            { utils = ["helpers.py"] }
          ] }
        ]
        ```

        Note that this matches the following directory:
        ```text
        <project-root>/
        +- main.py
        +- README.md
        +- src/
           +- app.py
           +- utils/
              +- helpers.py
        ```
        """
        try:
            if not toml.is_file():
                raise StaffException(
                    f"Could not find provided toml file, `{str(toml)}`."
                )

            with toml.open("rb") as f:
                data = tomllib.load(f)
        except StaffException:
            raise
        except Exception as e:
            raise StaffException(
                f"Provided toml file (`{str(toml)}`) was unparsable. "
                f"(See traceback for more info.)"
            ) from e

        def parse_node(node: Any, *, where: str = "root") -> DirectoryMapping:
            if isinstance(node, list):
                out: DirectoryMapping = []
                for i, item in enumerate(node):
                    item_where = f"{where}[{i}]"
                    if isinstance(item, str):
                        out.append(item)
                    elif isinstance(item, dict):
                        out.append(parse_directory_dict(item, where=item_where))
                    else:
                        raise StaffException(
                            f"Manifest TOML entry at `{item_where}` must be either a file name string "
                            f"or a singleton table/dict representing a directory; got "
                            f"`{type(item).__name__}`."
                        )
                return out

            raise StaffException(
                f"Manifest TOML node at `{where}` must be a list; got `{type(node).__name__}`."
            )

        def parse_directory_dict(node: Any, *, where: str) -> DirectoryDict:
            if not isinstance(node, dict):
                raise StaffException(
                    f"Manifest TOML directory node at `{where}` must be a table/dict; "
                    f"got `{type(node).__name__}`."
                )
            if len(node) != 1:
                raise StaffException(
                    f"Manifest TOML directory node at `{where}` must be a singleton table/dict; "
                    f"got keys `{', '.join(repr(k) for k in node.keys())}`."
                )

            name, value = next(iter(node.items()))
            if not isinstance(name, str):
                raise StaffException(
                    f"Manifest TOML directory key at `{where}` must be a string; "
                    f"got `{type(name).__name__}`."
                )

            return validate_directory_dict(
                {name: parse_node(value, where=f"{where}.{name}")}
            )

        if "manifest" in data:
            mapping = parse_node(data["manifest"], where="manifest")
        else:
            # Treat the whole document as the manifest body if no top-level "manifest" key exists.
            mapping = parse_node(data, where="root")

        return cls(mapping)

    @classmethod
    def from_flat(cls, flat: list[Path]) -> Manifest:
        config = get_config()
        root = Path(config.root_directory).resolve()

        TrieNode = dict[str, Any]

        def make_node() -> TrieNode:
            return {"dirs": {}, "files": set()}

        trie: TrieNode = make_node()

        def normalize_rel(path: Path) -> Path:
            p = Path(path)

            if p.is_absolute():
                resolved = p.resolve()
                try:
                    return resolved.relative_to(root)
                except ValueError as e:
                    raise StaffException(
                        f"Flat manifest path `{str(path)}` is outside configured root directory, `{str(root)}`."
                    ) from e

            # Lexical normalization for relative paths.
            rel = Path(normpath(str(p)))

            if rel == Path("."):
                raise StaffException(
                    "Flat manifest contains an empty/current-directory path (`.`), which is not a file."
                )

            # Any remaining `..` means the path still escapes upward relative to the manifest root.
            if any(part == ".." for part in rel.parts):
                raise StaffException(
                    f"Flat manifest path `{str(path)}` escapes above the manifest root."
                )

            if rel.is_absolute():
                raise StaffException(
                    f"Flat manifest path `{str(path)}` normalized to an absolute path unexpectedly."
                )

            return rel

        def insert_file(rel: Path) -> None:
            if not rel.parts:
                raise StaffException(
                    "Flat manifest contained an empty path after normalization."
                )

            node = trie

            for part in rel.parts[:-1]:
                if part in node["files"]:
                    raise StaffException(
                        f"Flat manifest path conflict: `{str(rel)}` requires `{part}` to be a directory, "
                        "but it was already recorded as a file."
                    )
                node = node["dirs"].setdefault(part, make_node())

            file_name = rel.parts[-1]
            if file_name in node["dirs"]:
                raise StaffException(
                    f"Flat manifest path conflict: `{str(rel)}` requires `{file_name}` to be a file, "
                    "but it was already recorded as a directory."
                )
            node["files"].add(file_name)

        def emit_mapping(node: TrieNode) -> DirectoryMapping:
            out: DirectoryMapping = []

            for dir_name in sorted(node["dirs"], key=lambda s: s.casefold()):
                out.append(
                    validate_directory_dict(
                        {dir_name: emit_mapping(node["dirs"][dir_name])}
                    )
                )

            for file_name in sorted(node["files"], key=lambda s: s.casefold()):
                out.append(file_name)

            return out

        for raw_path in flat:
            rel_path = normalize_rel(raw_path)
            insert_file(rel_path)

        return cls(emit_mapping(trie))

    def __contains__(self, item: Any) -> bool:
        if not isinstance(item, (str, Path)):
            return False
        path = Path(normpath(item)).parts
        current = self._mapping
        for i, sub in enumerate(path):
            current_keys = [p for p in current if directory_key(p) == sub]
            if sub not in current_keys:
                return False
            sub_item: dict | str = current_keys[0]
            final_item: bool = i == len(path) - 1
            if isinstance(sub_item, str) and not final_item:
                return False
            elif isinstance(sub_item, dict):
                current = sub_item[sub]
        return True

    # noinspection PyTypeHints
    @staticmethod
    def compare(
        expected: DirectoryMapping, received: DirectoryMapping
    ) -> ManifestComparisonSummary:
        manifest_expected = sorted(expected, key=directory_key)
        manifest_received = sorted(received, key=directory_key)
        if not manifest_expected and not manifest_received:
            return ManifestComparisonSummary()

        exp_keys = {directory_key(item): item for item in manifest_expected}
        rec_keys = {directory_key(item): item for item in manifest_received}

        matches = {
            key: ManifestComparisonEntry(expected=exp_keys[key], received=rec_keys[key])
            for key in exp_keys
            if key in rec_keys
        }
        extra = {
            key: ManifestComparisonEntry(expected=None, received=rec_keys[key])
            for key in rec_keys
            if key not in exp_keys
        }
        missing = {
            key: ManifestComparisonEntry(expected=exp_keys[key], received=None)
            for key in exp_keys
            if key not in rec_keys
        }
        should_be_directory = {
            k: mce
            for k, mce in matches.items()
            if isinstance(mce.expected, dict) and isinstance(mce.received, str)
        }
        should_be_file = {
            k: mce
            for k, mce in matches.items()
            if isinstance(mce.expected, str) and isinstance(mce.received, dict)
        }
        for k in should_be_directory | should_be_file:
            del matches[k]

        return ManifestComparisonSummary(
            matches=matches,
            extra=extra,
            missing=missing,
            should_be_directory=should_be_directory,
            should_be_file=should_be_file,
        )

    # noinspection PyTypeHints
    @staticmethod
    def _mapping_cmp(
        expected: DirectoryMapping,
        received: DirectoryMapping,
        fail_attrs: Iterable[str],
    ) -> bool:
        mcs = Manifest.compare(expected, received)
        if mcs.is_empty():
            return True
        if any(getattr(mcs, fa) for fa in fail_attrs):
            return False

        for mce in mcs.matches.values():
            match mce.expected, mce.received:
                case (
                    (str() | None),
                    (str() | None),
                ):  # `matches` variant implicitly means both are equal and non-`None`.
                    continue

                case dict() as exp_dict, dict() as rec_dict:
                    dir_name = directory_name(cast(DirectoryDict, exp_dict))
                    exp_dir = exp_dict[dir_name]
                    rec_dir = rec_dict[dir_name]
                    if not Manifest._mapping_cmp(exp_dir, rec_dir, fail_attrs):
                        return False
                    continue

                case _:  # `matches` mean both expected and received should match, thus all options have been exhausted.
                    raise DeveloperException(
                        f"Combination in `render_manifest_tree` that was left unmatched: type of expected was `{mce.expected.__class__.__name__}` and type of received was `{mce.received.__class__.__name__}`."
                    )
        return True

    @staticmethod
    def _mapping_eq(expected: DirectoryMapping, received: DirectoryMapping) -> bool:
        return Manifest._mapping_cmp(
            expected,
            received,
            fail_attrs=("missing", "extra", "should_be_directory", "should_be_file"),
        )

    @staticmethod
    def _mapping_le(expected: DirectoryMapping, received: DirectoryMapping) -> bool:
        return Manifest._mapping_cmp(
            expected,
            received,
            fail_attrs=("missing", "should_be_directory", "should_be_file"),
        )  # Ignore extra

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Manifest):
            return False
        return self._mapping_eq(self._mapping, other._mapping)

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Manifest):
            return NotImplemented
        return self._mapping_le(self._mapping, other._mapping)

    @property
    def paths(self) -> list[Path]:
        return self._files + self._dirs

    @property
    def files(self) -> list[File]:
        return [File(f) for f in self._files]

    @property
    def directory_mapping(self) -> DirectoryMapping:
        return self._mapping

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
