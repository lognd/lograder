# noinspection PyPep8Naming
from enum import Enum, auto
from types import NoneType
from typing import Callable, cast

from colorama import Fore as F

from ...exception import DeveloperException
from ...graph.package import DirectoryDict, DirectoryMapping, directory_name


class ManifestItemStatus(Enum):
    MATCHING = auto()
    EXTRA = auto()
    MISSING = auto()
    SHOULD_BE_DIRECTORY = auto()
    SHOULD_BE_FILE = auto()


_MANIFEST_FUZZY_COLOR_MAP: dict[ManifestItemStatus, str] = {
    ManifestItemStatus.MATCHING: F.GREEN,
    ManifestItemStatus.EXTRA: F.YELLOW,
    ManifestItemStatus.MISSING: F.RED,
    ManifestItemStatus.SHOULD_BE_DIRECTORY: F.RED,
    ManifestItemStatus.SHOULD_BE_FILE: F.RED,
}
_MANIFEST_FUZZY_BLURB_MAP: dict[ManifestItemStatus, str] = {
    ManifestItemStatus.MATCHING: "",
    ManifestItemStatus.EXTRA: " (EXTRA)",
    ManifestItemStatus.MISSING: " (MISSING)",
    ManifestItemStatus.SHOULD_BE_DIRECTORY: " (SHOULD BE A DIRECTORY BUT IS A FILE)",
    ManifestItemStatus.SHOULD_BE_FILE: " (SHOULD BE A FILE BUT IS A DIRECTORY)",
}


def render_manifest_tree(
    manifest_expected: DirectoryMapping, manifest_received: DirectoryMapping
) -> list[list[str]]:
    directory_key: Callable[[str | dict], str] = lambda item: (
        item if isinstance(item, str) else directory_name(cast(DirectoryDict, item))
    )
    manifest_expected = sorted(manifest_expected, key=directory_key)
    manifest_received = sorted(manifest_received, key=directory_key)
    if not manifest_expected and not manifest_received:
        return [[f"+- {F.GREEN}(EMPTY){F.RESET}"]]

    lines: list[list[str]] = []
    exp_keys = {directory_key(item): item for item in manifest_expected}
    rec_keys = {directory_key(item): item for item in manifest_received}
    matches = {
        key: (ManifestItemStatus.MATCHING, exp_keys[key], rec_keys[key])
        for key in exp_keys
        if key in rec_keys
    }

    extra = {
        key: (ManifestItemStatus.EXTRA, None, rec_keys[key])
        for key in rec_keys
        if key not in exp_keys
    }
    missing = {
        key: (ManifestItemStatus.MISSING, exp_keys[key], None)
        for key in exp_keys
        if key not in rec_keys
    }
    should_be_directory = {
        k: (ManifestItemStatus.SHOULD_BE_DIRECTORY, e, r)
        for k, (_, e, r) in matches.items()
        if isinstance(e, dict) and isinstance(r, str)
    }
    should_be_file = {
        k: (ManifestItemStatus.SHOULD_BE_FILE, e, r)
        for k, (_, e, r) in matches.items()
        if isinstance(e, str) and isinstance(r, dict)
    }
    summary = matches | extra | missing | should_be_directory | should_be_file

    for e_i, (_, (stat, exp, rec)) in enumerate(summary.items()):
        color = _MANIFEST_FUZZY_COLOR_MAP[stat]
        blurb = _MANIFEST_FUZZY_BLURB_MAP[stat]
        if isinstance(exp, (str, NoneType)) and isinstance(rec, (str, NoneType)):
            lines.append([f"+- {color}{exp or rec}{blurb}{F.RESET}"])
            continue
        elif isinstance(exp, dict) and isinstance(rec, (str, NoneType)):
            # Instance where mypy inferences PyCharm does not.
            dir_name = directory_name(cast(DirectoryDict, exp))  # type: ignore[redundant-cast]
            exp_dir: DirectoryMapping = exp[dir_name]
            rec_dir: DirectoryMapping = []
        elif isinstance(exp, (str, NoneType)) and isinstance(rec, dict):
            # Instance where mypy inferences PyCharm does not.
            dir_name = directory_name(cast(DirectoryDict, rec))  # type: ignore[redundant-cast]
            exp_dir = []
            rec_dir = rec[dir_name]
        elif isinstance(exp, dict) and isinstance(rec, dict):
            # Instance where mypy inferences PyCharm does not.
            dir_name = directory_name(cast(DirectoryDict, exp))  # type: ignore[redundant-cast]
            exp_dir = exp[dir_name]
            rec_dir = rec[dir_name]
        else:
            raise DeveloperException(
                f"Combination in `render_manifest_tree` that was left unmatched: type of expected was `{exp.__class__.__name__}` and type of received was `{rec.__class__.__name__}`."
            )
        lines.append([f"+- {color}{dir_name}{blurb}{F.RESET}"])
        child_start_index = len(lines)
        is_last_entry = e_i == len(summary) - 1
        lines.extend(render_manifest_tree(exp_dir, rec_dir))
        prefix = "|  " if not is_last_entry else "   "
        for line_index in range(child_start_index, len(lines)):
            lines[line_index].insert(0, prefix)
    return lines


def render_manifest_diff(
    manifest_expected: DirectoryMapping,
    manifest_received: DirectoryMapping,
) -> str:
    directory_key: Callable[[str | dict], str] = lambda item: (
        item if isinstance(item, str) else directory_name(cast(DirectoryDict, item))
    )

    exp_keys = {directory_key(item): item for item in manifest_expected}
    rec_keys = {directory_key(item): item for item in manifest_received}

    missing = sorted(k for k in exp_keys if k not in rec_keys)
    extra = sorted(k for k in rec_keys if k not in exp_keys)

    type_mismatch: list[str] = []
    for k in sorted(k for k in exp_keys if k in rec_keys):
        e = exp_keys[k]
        r = rec_keys[k]
        if isinstance(e, dict) and isinstance(r, str):
            type_mismatch.append(f"{k}:dir!=file")
        elif isinstance(e, str) and isinstance(r, dict):
            type_mismatch.append(f"{k}:file!=dir")

    parts: list[str] = []
    if missing:
        parts.append(
            f"missing={','.join(missing[:5])}{'…' if len(missing) > 5 else ''}"
        )
    if extra:
        parts.append(f"extra={','.join(extra[:5])}{'…' if len(extra) > 5 else ''}")
    if type_mismatch:
        parts.append(
            f"mismatch={','.join(type_mismatch[:5])}{'…' if len(type_mismatch) > 5 else ''}"
        )

    return " ".join(parts) if parts else "diff=(EMPTY)"
