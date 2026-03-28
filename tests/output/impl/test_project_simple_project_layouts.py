# type: ignore

from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.project.manifest import (
    ManifestCheckDataLayout,
    ManifestCheckErrorLayout,
)
from lograder.pipeline.check.project.manifest import (
    ManifestCheckData,
    ManifestCheckError,
)
from lograder.pipeline.types.parcels import Manifest


def make_manifest(*items: str | dict) -> Manifest:
    return Manifest(list(items))


def test_manifest_check_data_layout_to_ansi(monkeypatch):
    expected = make_manifest("req.txt")
    received = make_manifest("got.txt")
    data = ManifestCheckData(
        manifest_expected=expected,
        manifest_received=received,
    )

    captured = {}

    def fake_tree(exp, rec):
        captured["expected"] = exp
        captured["received"] = rec
        return [["+- one"], ["+- two"]]

    monkeypatch.setattr(
        "lograder.output.layout.project.manifest.render_manifest_tree",
        fake_tree,
    )

    out = ManifestCheckDataLayout.to_ansi(data)

    assert captured["expected"] == expected.directory_mapping
    assert captured["received"] == received.directory_mapping
    assert f"{S.BRIGHT}< {F.CYAN}MANIFEST CHECK{F.RESET} >{S.RESET_ALL}" in out
    assert (
        f"{F.GREEN}The received manifest is compliant with the expected manifest.{F.RESET}"
        in out
    )
    assert "<project-root>/" in out
    assert "+- one" in out
    assert "+- two" in out


def test_manifest_check_data_layout_to_simple(monkeypatch):
    expected = make_manifest("req.txt")
    received = make_manifest("got.txt")
    data = ManifestCheckData(
        manifest_expected=expected,
        manifest_received=received,
    )

    captured = {}

    def fake_diff(exp, rec):
        captured["expected"] = exp
        captured["received"] = rec
        return "diff summary"

    monkeypatch.setattr(
        "lograder.output.layout.project.manifest.render_manifest_diff",
        fake_diff,
    )

    out = ManifestCheckDataLayout.to_simple(data)

    assert captured["expected"] == expected.directory_mapping
    assert captured["received"] == received.directory_mapping
    assert (
        out
        == "The received manifest is compliant with the expected manifest; diff summary"
    )


def test_manifest_check_error_layout_to_ansi(monkeypatch):
    expected = make_manifest("req.txt")
    received = make_manifest("got.txt")
    err = ManifestCheckError(
        manifest_expected=expected,
        manifest_received=received,
    )

    captured = {}

    def fake_tree(exp, rec):
        captured["expected"] = exp
        captured["received"] = rec
        return [["+- bad"]]

    monkeypatch.setattr(
        "lograder.output.layout.project.manifest.render_manifest_tree",
        fake_tree,
    )

    out = ManifestCheckErrorLayout.to_ansi(err)

    assert captured["expected"] == expected.directory_mapping
    assert captured["received"] == received.directory_mapping
    assert f"{S.BRIGHT}< {F.CYAN}MANIFEST CHECK{F.RESET} >{S.RESET_ALL}" in out
    assert (
        f"{F.RED}The received manifest does not fit the expected manifest.{F.RESET}"
        in out
    )
    assert "<project-root>/" in out
    assert "+- bad" in out


def test_manifest_check_error_layout_to_simple(monkeypatch):
    expected = make_manifest("req.txt")
    received = make_manifest("got.txt")
    err = ManifestCheckError(
        manifest_expected=expected,
        manifest_received=received,
    )

    captured = {}

    def fake_diff(exp, rec):
        captured["expected"] = exp
        captured["received"] = rec
        return "missing=x"

    monkeypatch.setattr(
        "lograder.output.layout.project.manifest.render_manifest_diff",
        fake_diff,
    )

    out = ManifestCheckErrorLayout.to_simple(err)

    assert captured["expected"] == expected.directory_mapping
    assert captured["received"] == received.directory_mapping
    assert out == "The received manifest does not fit the expected manifest; missing=x"
