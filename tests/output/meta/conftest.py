# type: ignore

from __future__ import annotations

import copy
import logging
from collections.abc import Iterator

import pytest

from lograder.output.packets import PacketAuthority


@pytest.fixture(autouse=True)
def restore_packet_authority() -> Iterator[None]:
    old_f = copy.copy(PacketAuthority._f_lookup)
    old_r = copy.copy(PacketAuthority._r_lookup)
    old_l = copy.copy(PacketAuthority._l_lookup)
    try:
        yield
    finally:
        PacketAuthority._f_lookup.clear()
        PacketAuthority._f_lookup.update(old_f)

        PacketAuthority._r_lookup.clear()
        PacketAuthority._r_lookup.update(old_r)

        PacketAuthority._l_lookup.clear()
        PacketAuthority._l_lookup.update(old_l)


@pytest.fixture(autouse=True)
def disable_lograder_atexit(monkeypatch):
    monkeypatch.setattr(
        "lograder.output.logger.atexit.register",
        lambda *args, **kwargs: None,
    )


@pytest.fixture
def configured_lograder(tmp_path):
    toml_path = tmp_path / "config.toml"
    toml_path.write_text(
        """
version = 1
disable_existing_loggers = false

[root]
level = "DEBUG"
handlers = []
""",
        encoding="utf-8",
    )
    setup_logger(toml_path)
    return toml_path


@pytest.fixture
def isolated_root_logger() -> Iterator[logging.Logger]:
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_filters = list(root.filters)
    old_level = root.level
    old_propagate = getattr(root, "propagate", True)

    try:
        for h in list(root.handlers):
            root.removeHandler(h)
        for f in list(root.filters):
            root.removeFilter(f)
        yield root
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
        for f in list(root.filters):
            root.removeFilter(f)

        for h in old_handlers:
            root.addHandler(h)
        for f in old_filters:
            root.addFilter(f)

        root.setLevel(old_level)
        root.propagate = old_propagate
