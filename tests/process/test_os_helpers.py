# type: ignore

from __future__ import annotations

import io

import pytest

from lograder.process import os_helpers
from lograder.process.os_helpers import NOT_APPLICABLE, StreamMode


def test_not_applicable_is_singleton() -> None:
    assert NOT_APPLICABLE() is NOT_APPLICABLE()


def test_is_windows_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers.sys, "platform", "win32", raising=False)
    assert os_helpers.is_windows() is True


def test_is_windows_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers.sys, "platform", "linux", raising=False)
    assert os_helpers.is_windows() is False


def test_is_posix_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers.os, "name", "posix", raising=False)
    assert os_helpers.is_posix() is True


def test_is_posix_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers.os, "name", "nt", raising=False)
    assert os_helpers.is_posix() is False


def test_posix_and_returns_value_on_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)
    assert os_helpers.posix_and(123) == 123


def test_posix_and_returns_not_applicable_on_non_posix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.posix_and(123) is NOT_APPLICABLE()


def test_windows_and_returns_value_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_windows", lambda: True)
    assert os_helpers.windows_and(456) == 456


def test_windows_and_returns_not_applicable_on_non_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os_helpers, "is_windows", lambda: False)
    assert os_helpers.windows_and(456) is NOT_APPLICABLE()


def test_get_current_uid_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.get_current_uid() is NOT_APPLICABLE()


def test_get_current_uid_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)
    monkeypatch.setattr(os_helpers.os, "getuid", lambda: 1000)
    assert os_helpers.get_current_uid() == 1000


def test_get_current_gid_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.get_current_gid() is NOT_APPLICABLE()


def test_get_current_gid_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)
    monkeypatch.setattr(os_helpers.os, "getgid", lambda: 1001)
    assert os_helpers.get_current_gid() == 1001


def test_get_current_groups_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.get_current_groups() is NOT_APPLICABLE()


def test_get_current_groups_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)
    monkeypatch.setattr(os_helpers.os, "getgroups", lambda: [1, 2, 3])
    assert os_helpers.get_current_groups() == [1, 2, 3]


def test_get_current_extra_groups_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.get_current_extra_groups() is NOT_APPLICABLE()


def test_get_current_extra_groups_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)
    monkeypatch.setattr(os_helpers.os, "getgroups", lambda: [4, 5])
    assert os_helpers.get_current_extra_groups() == [4, 5]


def test_get_current_username_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.get_current_username() is NOT_APPLICABLE()


def test_get_current_groupname_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.get_current_groupname() is NOT_APPLICABLE()


def test_get_current_umask_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    os_helpers.get_current_umask.cache_clear()
    monkeypatch.setattr(os_helpers, "is_posix", lambda: False)
    assert os_helpers.get_current_umask() is NOT_APPLICABLE()


def test_get_current_umask_reads_proc_status_fast_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    os_helpers.get_current_umask.cache_clear()
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)

    def fake_open(*args, **kwargs):
        return io.StringIO("Name:\tpython\nUmask:\t0022\nState:\tR\n")

    monkeypatch.setattr("builtins.open", fake_open)
    assert os_helpers.get_current_umask() == 0o022


def test_get_current_umask_falls_back_to_os_umask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    os_helpers.get_current_umask.cache_clear()
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)

    def fake_open(*args, **kwargs):
        raise FileNotFoundError

    seen: list[int] = []

    def fake_umask(value: int) -> int:
        seen.append(value)
        if value == 0:
            return 0o027
        return 0

    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr(os_helpers.os, "umask", fake_umask)

    assert os_helpers.get_current_umask() == 0o027
    assert seen == [0, 0o027]


def test_get_current_umask_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    os_helpers.get_current_umask.cache_clear()
    monkeypatch.setattr(os_helpers, "is_posix", lambda: True)

    calls = {"count": 0}

    def fake_open(*args, **kwargs):
        calls["count"] += 1
        return io.StringIO("Umask:\t0007\n")

    monkeypatch.setattr("builtins.open", fake_open)

    assert os_helpers.get_current_umask() == 0o007
    assert os_helpers.get_current_umask() == 0o007
    assert calls["count"] == 1


def test_stream_mode_members_exist() -> None:
    assert StreamMode.PIPE.name == "PIPE"
    assert StreamMode.INHERIT.name == "INHERIT"
    assert StreamMode.NULL.name == "NULL"
    assert StreamMode.STDOUT.name == "STDOUT"
