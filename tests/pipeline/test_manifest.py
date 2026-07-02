from pathlib import Path

import pytest

from lograder.exception import StaffException
from lograder.pipeline.config import config
from lograder.pipeline.types.parcels import Manifest


def test_from_flat_single_file(tmp_path):
    with config(root_directory=tmp_path):
        m = Manifest.from_flat([Path("foo.c")])
    assert "foo.c" in m


def test_from_flat_nested_path(tmp_path):
    with config(root_directory=tmp_path):
        m = Manifest.from_flat([Path("src/foo.c")])
    assert "src" in m


def test_from_flat_multiple_files(tmp_path):
    with config(root_directory=tmp_path):
        m = Manifest.from_flat([Path("a.c"), Path("b.c")])
    assert "a.c" in m
    assert "b.c" in m


def test_from_flat_escape_raises(tmp_path):
    with config(root_directory=tmp_path):
        with pytest.raises(StaffException):
            Manifest.from_flat([Path("../escape.c")])


def test_from_flat_empty_path_raises(tmp_path):
    with config(root_directory=tmp_path):
        with pytest.raises(StaffException):
            Manifest.from_flat([Path(".")])


def test_from_flat_absolute_outside_root_raises(tmp_path):
    with config(root_directory=tmp_path):
        with pytest.raises(StaffException):
            Manifest.from_flat([Path("/etc/passwd")])


def test_manifest_equality_exact(tmp_path):
    with config(root_directory=tmp_path):
        m1 = Manifest.from_flat([Path("a.c"), Path("b.c")])
        m2 = Manifest.from_flat([Path("a.c"), Path("b.c")])
    assert m1 == m2


def test_manifest_inequality_extra_file(tmp_path):
    with config(root_directory=tmp_path):
        m1 = Manifest.from_flat([Path("a.c")])
        m2 = Manifest.from_flat([Path("a.c"), Path("b.c")])
    assert m1 != m2


def test_manifest_inequality_missing_file(tmp_path):
    with config(root_directory=tmp_path):
        m1 = Manifest.from_flat([Path("a.c"), Path("b.c")])
        m2 = Manifest.from_flat([Path("a.c")])
    assert m1 != m2


def test_manifest_subset_le_equal(tmp_path):
    with config(root_directory=tmp_path):
        m = Manifest.from_flat([Path("a.c"), Path("b.c")])
    assert m <= m


def test_manifest_subset_le_superset(tmp_path):
    with config(root_directory=tmp_path):
        m_sub = Manifest.from_flat([Path("a.c")])
        m_sup = Manifest.from_flat([Path("a.c"), Path("b.c")])
    assert m_sub <= m_sup


def test_manifest_subset_le_fails_on_missing(tmp_path):
    with config(root_directory=tmp_path):
        m_required = Manifest.from_flat([Path("a.c"), Path("missing.c")])
        m_actual = Manifest.from_flat([Path("a.c")])
    assert not (m_required <= m_actual)


def test_manifest_contains_file(tmp_path):
    with config(root_directory=tmp_path):
        m = Manifest.from_flat([Path("foo.c")])
    assert "foo.c" in m


def test_manifest_contains_missing_file(tmp_path):
    with config(root_directory=tmp_path):
        m = Manifest.from_flat([Path("foo.c")])
    assert "nonexistent.c" not in m


def test_from_directory_creates_manifest(tmp_path):
    (tmp_path / "main.c").write_text("int main(){}", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "helper.c").write_text("", encoding="utf-8")
    with config(root_directory=tmp_path):
        m = Manifest.from_directory(tmp_path)
    assert "main.c" in m
    assert m.root == tmp_path


def test_from_directory_outside_root_raises(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    with config(root_directory=root):
        with pytest.raises(StaffException):
            Manifest.from_directory(other)


def test_manifest_root_property(tmp_path):
    (tmp_path / "a.c").write_text("", encoding="utf-8")
    with config(root_directory=tmp_path):
        m = Manifest.from_directory(tmp_path)
    assert m.root == tmp_path


def test_manifest_paths_includes_files_and_dirs(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "file.c").write_text("", encoding="utf-8")
    with config(root_directory=tmp_path):
        m = Manifest.from_directory(tmp_path)
    paths = m.paths
    assert any(p.name == "file.c" for p in paths)
    assert any(p.name == "sub" for p in paths)
