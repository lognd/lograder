#!/usr/bin/env python3
"""Bump the patch component of the ``version`` in pyproject.toml.

Rewrites ``version = "X.Y.Z"`` to ``version = "X.Y.(Z+1)"`` in place and prints
the new version to stdout (the Makefile's ``upload`` target captures it for the
commit message). Kept regex-based so the file's formatting is otherwise
untouched.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
_VERSION_RE = re.compile(r'^(version\s*=\s*")(\d+)\.(\d+)\.(\d+)(")', re.MULTILINE)


def main() -> int:
    text = _PYPROJECT.read_text(encoding="utf-8")
    match = _VERSION_RE.search(text)
    if match is None:
        print("error: could not find a 'version = \"X.Y.Z\"' line", file=sys.stderr)
        return 1
    major, minor, patch = int(match.group(2)), int(match.group(3)), int(match.group(4))
    new_version = f"{major}.{minor}.{patch + 1}"
    new_text = text[: match.start()] + f'{match.group(1)}{new_version}{match.group(5)}' + text[match.end():]
    _PYPROJECT.write_text(new_text, encoding="utf-8")
    print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
