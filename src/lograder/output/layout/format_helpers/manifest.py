from enum import Enum, auto
from typing import Callable, cast

# noinspection PyPep8Naming
from colorama import Fore as F

from ....exception import DeveloperException
from ....pipeline.types.package import (
    DirectoryDict,
    DirectoryMapping,
    Manifest,
    directory_name,
)


class ManifestItemStatus(Enum):
    MATCHING = auto()
    EXTRA = auto()
    MISSING = auto()
    SHOULD_BE_DIRECTORY = auto()
    SHOULD_BE_FILE = auto()


_MANIFEST_ATTR_MAP: dict[str, ManifestItemStatus] = {
    "matches": ManifestItemStatus.MATCHING,
    "extra": ManifestItemStatus.EXTRA,
    "missing": ManifestItemStatus.MISSING,
    "should_be_directory": ManifestItemStatus.SHOULD_BE_DIRECTORY,
    "should_be_file": ManifestItemStatus.SHOULD_BE_FILE,
}
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
    mcs = Manifest.compare(manifest_expected, manifest_received)
    if mcs.is_empty():
        return [[f"+- {F.GREEN}(EMPTY){F.RESET}"]]

    summary = {
        key: (_MANIFEST_ATTR_MAP[attr], mce.expected, mce.received)
        for attr in (
            "matches",
            "extra",
            "missing",
            "should_be_directory",
            "should_be_file",
        )
        for key, mce in getattr(mcs, attr).items()
    }
    lines: list[list[str]] = []

    for e_i, (_, (stat, exp, rec)) in enumerate(summary.items()):
        color = _MANIFEST_FUZZY_COLOR_MAP[stat]
        blurb = _MANIFEST_FUZZY_BLURB_MAP[stat]

        match exp, rec:
            case ((str() | None), (str() | None)):
                lines.append([f"+- {color}{exp or rec}{blurb}{F.RESET}"])
                continue

            case dict() as exp_dict, (str() | None):
                dir_name = directory_name(cast(DirectoryDict, exp_dict))
                exp_dir: DirectoryMapping = exp_dict[dir_name]
                rec_dir: DirectoryMapping = []

            case ((str() | None), dict() as rec_dict):
                dir_name = directory_name(cast(DirectoryDict, rec_dict))
                exp_dir = []
                rec_dir = rec_dict[dir_name]

            case dict() as exp_dict, dict() as rec_dict:
                dir_name = directory_name(cast(DirectoryDict, exp_dict))
                exp_dir = exp_dict[dir_name]
                rec_dir = rec_dict[dir_name]

            case _:
                raise DeveloperException(
                    f"Combination in `render_manifest_tree` that was left unmatched: type of expected was `{exp.__class__.__name__}` and type of received was `{rec.__class__.__name__}`."
                )

        # noinspection PyUnboundLocalVariable
        lines.append(
            [f"+- {color}{dir_name}{blurb}{F.RESET}"]
        )  # all non-interrupting branches define `dir_name`.
        child_start_index = len(lines)
        is_last_entry = e_i == len(summary) - 1
        # noinspection PyUnboundLocalVariable
        lines.extend(
            render_manifest_tree(exp_dir, rec_dir)
        )  # all non-interrupting branches define `exp_dir` and `rec_dir`.
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
