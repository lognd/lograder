# type: ignore

from __future__ import annotations

import io
import logging
from pathlib import Path

import pytest
from pydantic import BaseModel

import lograder.output.logger as logger_mod
from lograder.output.handlers import HTMLHandler
from lograder.output.layout.layout import Layout, register_layout
from lograder.output.logger import LograderLogger, get_logger, setup_logger


class LogPacket(BaseModel):
    name: str


@register_layout("LOG")
class LogLayout(Layout[LogPacket]):
    @classmethod
    def to_ansi(cls, data: LogPacket) -> str:
        return "ANSI"

    @classmethod
    def to_simple(cls, data: LogPacket) -> str:
        return f"SIMPLE:{data.name}"


def test_lograder_logger_init_registers_atexit(monkeypatch):
    called = {"count": 0}

    def fake_register(fn):
        called["count"] += 1
        called["fn"] = fn

    monkeypatch.setattr(logger_mod.atexit, "register", fake_register)

    logger = LograderLogger("x", logging.INFO)
    assert called["count"] == 1
    assert called["fn"].__self__ is logger
    assert called["fn"].__name__ == "emit_html"


def test_lograder_logger_packet_logs_extra(monkeypatch):
    logger = LograderLogger("x", logging.INFO)

    captured = {}

    def fake_log(level, msg, extra):
        captured["level"] = level
        captured["msg"] = msg
        captured["extra"] = extra

    monkeypatch.setattr(logger, "log", fake_log)

    obj = LogPacket(name="abc")
    logger.packet(obj, level=logging.ERROR)

    assert captured["level"] == logging.ERROR
    assert captured["msg"] == "LogPacket"
    assert "packet" in captured["extra"]
    assert captured["extra"]["packet"]["header"] == "LOG"
    assert captured["extra"]["packet"]["payload"] == {"name": "abc"}


def test_emit_html_only_calls_html_handlers(monkeypatch):
    logger = LograderLogger("x", logging.INFO)

    class DummyHandler(logging.Handler):
        def emit(self, record):
            pass

    html_handler = HTMLHandler()
    other_handler = DummyHandler()

    called = {"count": 0}

    def fake_render_page_to_file():
        called["count"] += 1

    monkeypatch.setattr(html_handler, "render_page_to_file", fake_render_page_to_file)

    logger.handlers = [other_handler, html_handler]
    logger.emit_html()

    assert called["count"] == 1


def test_setup_logger_calls_dictconfig_when_path_changes(tmp_path: Path, monkeypatch):
    toml_path = tmp_path / "config.toml"
    toml_path.write_text("version = 1\n", encoding="utf-8")

    loaded = {"value": None}
    configured = {"value": None}
    set_class = {"value": None}

    def fake_load(f):
        loaded["value"] = True
        return {"version": 1}

    def fake_dict_config(cfg):
        configured["value"] = cfg

    def fake_set_logger_class(cls):
        set_class["value"] = cls

    monkeypatch.setattr(logger_mod.tomllib, "load", fake_load)
    monkeypatch.setattr(logger_mod.logging.config, "dictConfig", fake_dict_config)
    monkeypatch.setattr(logger_mod.logging, "setLoggerClass", fake_set_logger_class)

    logger_mod._PAST_SETUP = None
    setup_logger(toml_path)

    assert loaded["value"] is True
    assert configured["value"] == {"version": 1}
    assert set_class["value"] is LograderLogger
    assert logger_mod._PAST_SETUP == toml_path


def test_setup_logger_skips_when_same_path(tmp_path: Path, monkeypatch):
    toml_path = tmp_path / "config.toml"
    toml_path.write_text("version = 1\n", encoding="utf-8")

    called = {"dictConfig": 0, "setLoggerClass": 0, "load": 0}

    monkeypatch.setattr(
        logger_mod.tomllib,
        "load",
        lambda f: called.__setitem__("load", called["load"] + 1) or {"version": 1},
    )
    monkeypatch.setattr(
        logger_mod.logging.config,
        "dictConfig",
        lambda cfg: called.__setitem__("dictConfig", called["dictConfig"] + 1),
    )
    monkeypatch.setattr(
        logger_mod.logging,
        "setLoggerClass",
        lambda cls: called.__setitem__("setLoggerClass", called["setLoggerClass"] + 1),
    )

    logger_mod._PAST_SETUP = toml_path
    setup_logger(toml_path)

    assert called["load"] == 0
    assert called["dictConfig"] == 0
    assert called["setLoggerClass"] == 0


def test_get_logger_returns_lograder_logger(tmp_path):
    toml_path = tmp_path / "config.toml"
    toml_path.write_text(
        "version = 1\n[root]\nlevel = 'DEBUG'\nhandlers = []\n", encoding="utf-8"
    )

    setup_logger(toml_path)
    logger = get_logger("abc")
    assert isinstance(logger, LograderLogger)
