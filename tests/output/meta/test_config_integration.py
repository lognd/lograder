# type: ignore

from __future__ import annotations

import logging
from pathlib import Path

import lograder.output.logger as logger_mod
from lograder.output.filters import BelowLevelFilter
from lograder.output.formatters import PacketFormatter
from lograder.output.handlers import HTMLHandler


def test_setup_logger_builds_expected_root_objects(tmp_path: Path):
    toml_path = tmp_path / "config.toml"
    toml_path.write_text(
        """
version = 1
disable_existing_loggers = false

[filters.below_warning]
"()" = "lograder.output.filters.BelowLevelFilter"
below = "WARNING"

[formatters.simple]
"()" = "lograder.output.formatters.PacketFormatter"
mode = "simple"

[handlers.stdout]
class = "logging.StreamHandler"
formatter = "simple"
stream = "ext://sys.stdout"
level = "DEBUG"
filters = ["below_warning"]

[handlers.student]
"()" = "lograder.output.handlers.HTMLHandler"
formatter = "simple"
level = "INFO"
output_file = "./out.html"

[root]
level = "DEBUG"
handlers = ["stdout", "student"]
""",
        encoding="utf-8",
    )

    logger_mod._PAST_SETUP = None
    logger_mod.setup_logger(toml_path)

    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) >= 2

    assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)
    assert any(isinstance(h, HTMLHandler) for h in root.handlers)

    stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
    assert any(
        any(isinstance(f, BelowLevelFilter) for f in h.filters) for h in stream_handlers
    )

    assert any(
        isinstance(getattr(h, "formatter", None), PacketFormatter)
        for h in root.handlers
    )
