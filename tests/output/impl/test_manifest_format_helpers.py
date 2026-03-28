# type: ignore

from __future__ import annotations

from types import SimpleNamespace

import pytest
from colorama import Fore as F

from lograder.exception import DeveloperException
from lograder.output.layout.format_helpers.manifest import (
    ManifestItemStatus,
    render_manifest_diff,
    render_manifest_tree,
)


class FakeCompareResult:
    def __init__(
        self,
        *,
        matches=None,
        extra=None,
        missing=None,
        should_be_directory=None,
        should_be_file=None,
        empty=False,
    ):
        self.matches = matches or {}
        self.extra = extra or {}
        self.missing = missing or {}
        self.should_be_directory = should_be_directory or {}
        self.should_be_file = should_be_file or {}
        self._empty = empty

    def is_empty(self) -> bool:
        return self._empty


class FakeManifestCompareEntry:
    def __init__(self, expected, received):
        self.expected = expected
        self.received = received


@pytest.mark.parametrize(
    ("attr", "expected_enum"),
    [
        ("matches", ManifestItemStatus.MATCHING),
        ("extra", ManifestItemStatus.EXTRA),
        ("missing", ManifestItemStatus.MISSING),
        ("should_be_directory", ManifestItemStatus.SHOULD_BE_DIRECTORY),
        ("should_be_file", ManifestItemStatus.SHOULD_BE_FILE),
    ],
)
def test_manifest_attr_map_complete(attr, expected_enum):
    from lograder.output.layout.format_helpers import manifest as mod

    assert mod._MANIFEST_ATTR_MAP[attr] is expected_enum


def test_render_manifest_tree_empty(monkeypatch):
    from lograder.output.layout.format_helpers import manifest as mod

    monkeypatch.setattr(
        mod.Manifest,
        "compare",
        lambda expected, received: FakeCompareResult(empty=True),
    )

    out = render_manifest_tree([], [])
    assert out == [[f"+- {F.GREEN}(EMPTY){F.RESET}"]]


def test_render_manifest_tree_plain_string_entries(monkeypatch):
    from lograder.output.layout.format_helpers import manifest as mod

    compare = FakeCompareResult(
        matches={
            "a.txt": FakeManifestCompareEntry("a.txt", "a.txt"),
        },
        extra={
            "b.txt": FakeManifestCompareEntry(None, "b.txt"),
        },
        missing={
            "c.txt": FakeManifestCompareEntry("c.txt", None),
        },
        should_be_directory={
            "d": FakeManifestCompareEntry("d", "d"),
        },
        should_be_file={
            "e": FakeManifestCompareEntry("e", "e"),
        },
    )

    monkeypatch.setattr(mod.Manifest, "compare", lambda expected, received: compare)

    out = render_manifest_tree([], [])
    flat = ["".join(line) for line in out]

    assert any("a.txt" in line for line in flat)
    assert any("b.txt (EXTRA)" in line for line in flat)
    assert any("c.txt (MISSING)" in line for line in flat)
    assert any("d (SHOULD BE A DIRECTORY BUT IS A FILE)" in line for line in flat)
    assert any("e (SHOULD BE A FILE BUT IS A DIRECTORY)" in line for line in flat)


def test_render_manifest_tree_directory_vs_file_branch_expected_dict(monkeypatch):
    from lograder.output.layout.format_helpers import manifest as mod

    compare = FakeCompareResult(
        should_be_directory={"src": FakeManifestCompareEntry({"src": ["a.py"]}, "src")}
    )

    monkeypatch.setattr(mod.Manifest, "compare", lambda expected, received: compare)

    child_calls = []

    def fake_recursive(expected, received):
        child_calls.append((expected, received))
        if expected == ["a.py"] and received == []:
            return [[f"+- {F.GREEN}(EMPTY){F.RESET}"]]
        return render_manifest_tree(expected, received)

    monkeypatch.setattr(mod, "render_manifest_tree", fake_recursive)

    out = fake_recursive([], [])
    flat = ["".join(line) for line in out]

    assert child_calls[1] == (["a.py"], [])
    assert any("src (SHOULD BE A DIRECTORY BUT IS A FILE)" in line for line in flat)


def test_render_manifest_tree_directory_vs_file_branch_received_dict(monkeypatch):
    from lograder.output.layout.format_helpers import manifest as mod

    compare = FakeCompareResult(
        should_be_file={"src": FakeManifestCompareEntry("src", {"src": ["a.py"]})}
    )

    monkeypatch.setattr(mod.Manifest, "compare", lambda expected, received: compare)

    child_calls = []

    def fake_recursive(expected, received):
        child_calls.append((expected, received))
        if expected == [] and received == ["a.py"]:
            return [[f"+- {F.GREEN}(EMPTY){F.RESET}"]]
        return render_manifest_tree(expected, received)

    monkeypatch.setattr(mod, "render_manifest_tree", fake_recursive)

    out = fake_recursive([], [])
    flat = ["".join(line) for line in out]

    assert child_calls[1] == ([], ["a.py"])
    assert any("src (SHOULD BE A FILE BUT IS A DIRECTORY)" in line for line in flat)


def test_render_manifest_tree_directory_vs_directory_branch(monkeypatch):
    from lograder.output.layout.format_helpers import manifest as mod

    compare = FakeCompareResult(
        matches={"src": FakeManifestCompareEntry({"src": ["a.py"]}, {"src": ["a.py"]})}
    )

    monkeypatch.setattr(mod.Manifest, "compare", lambda expected, received: compare)

    child_calls = []

    def fake_recursive(expected, received):
        child_calls.append((expected, received))
        if expected == ["a.py"] and received == ["a.py"]:
            return [[f"+- {F.GREEN}a.py{F.RESET}"]]
        return render_manifest_tree(expected, received)

    monkeypatch.setattr(mod, "render_manifest_tree", fake_recursive)

    out = fake_recursive([], [])
    flat = ["".join(line) for line in out]

    assert child_calls[1] == (["a.py"], ["a.py"])
    assert any("src" in line for line in flat)
    assert any("a.py" in line for line in flat)


def test_render_manifest_tree_prefixes_children_for_non_last_and_last(monkeypatch):
    from lograder.output.layout.format_helpers import manifest as mod

    compare = FakeCompareResult(
        matches={
            "dir1": FakeManifestCompareEntry({"dir1": ["x"]}, {"dir1": ["x"]}),
            "dir2": FakeManifestCompareEntry({"dir2": ["y"]}, {"dir2": ["y"]}),
        }
    )

    monkeypatch.setattr(mod.Manifest, "compare", lambda expected, received: compare)

    def fake_recursive(expected, received):
        if expected == ["x"] and received == ["x"]:
            return [["+- child1"]]
        if expected == ["y"] and received == ["y"]:
            return [["+- child2"]]
        return render_manifest_tree(expected, received)

    monkeypatch.setattr(mod, "render_manifest_tree", fake_recursive)

    out = fake_recursive([], [])
    flat = ["".join(line) for line in out]

    assert any(line.startswith("|  ") and "child1" in line for line in flat)
    assert any(line.startswith("   ") and "child2" in line for line in flat)


def test_render_manifest_tree_unmatched_combination_raises(monkeypatch):
    from lograder.output.layout.format_helpers import manifest as mod

    compare = FakeCompareResult(matches={"weird": FakeManifestCompareEntry(123, 456)})

    monkeypatch.setattr(mod.Manifest, "compare", lambda expected, received: compare)

    with pytest.raises(DeveloperException, match="left unmatched"):
        render_manifest_tree([], [])


def test_render_manifest_diff_empty():
    assert render_manifest_diff([], []) == "diff=(EMPTY)"


def test_render_manifest_diff_missing_only():
    out = render_manifest_diff(["a", "b"], ["a"])
    assert out == "missing=b"


def test_render_manifest_diff_extra_only():
    out = render_manifest_diff(["a"], ["a", "b"])
    assert out == "extra=b"


def test_render_manifest_diff_type_mismatch_dir_vs_file():
    out = render_manifest_diff([{"src": []}], ["src"])
    assert out == "mismatch=src:dir!=file"


def test_render_manifest_diff_type_mismatch_file_vs_dir():
    out = render_manifest_diff(["src"], [{"src": []}])
    assert out == "mismatch=src:file!=dir"


def test_render_manifest_diff_combines_sections_in_order():
    out = render_manifest_diff(
        ["a", "b", {"src": []}],
        ["a", "c", "src"],
    )
    assert out == "missing=b extra=c mismatch=src:dir!=file"


def test_render_manifest_diff_truncates_missing_after_five():
    exp = ["a", "b", "c", "d", "e", "f"]
    rec = []
    out = render_manifest_diff(exp, rec)
    assert out == "missing=a,b,c,d,e…"


def test_render_manifest_diff_truncates_extra_after_five():
    exp = []
    rec = ["a", "b", "c", "d", "e", "f"]
    out = render_manifest_diff(exp, rec)
    assert out == "extra=a,b,c,d,e…"


def test_render_manifest_diff_truncates_mismatch_after_five():
    exp = [{"a": []}, {"b": []}, {"c": []}, {"d": []}, {"e": []}, {"f": []}]
    rec = ["a", "b", "c", "d", "e", "f"]
    out = render_manifest_diff(exp, rec)
    assert (
        out == "mismatch=a:dir!=file,b:dir!=file,c:dir!=file,d:dir!=file,e:dir!=file…"
    )
