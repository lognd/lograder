# type: ignore

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import pytest

from lograder.exception import DeveloperException
from lograder.output.handlers import HTMLHandler, HTMLItem


def make_record(*, msg: str = "hello", level: int = logging.INFO) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    record.created = 1700000000.0
    return record


@pytest.fixture
def patched_templates(monkeypatch):
    monkeypatch.setattr(
        HTMLHandler,
        "_TEMPLATE_PAGE",
        "<html><head><title>{{title}}</title></head><body>{{cards}}</body></html>",
    )
    monkeypatch.setattr(
        HTMLHandler,
        "_TEMPLATE_CARD",
        "<div class='card'><span>{{timestamp}}</span><b>{{level}}</b><section>{{fragment}}</section></div>",
    )


def test_substitute_replaces_all_placeholders():
    result = HTMLHandler._substitute("A {{x}} B {{y}}", x="1", y="2")
    assert result == "A 1 B 2"


def test_substitute_page_uses_page_template(monkeypatch, patched_templates):
    result = HTMLHandler._substitute_page(title="T", cards="C")
    assert result == "<html><head><title>T</title></head><body>C</body></html>"


def test_substitute_card_uses_card_template(monkeypatch, patched_templates):
    result = HTMLHandler._substitute_card(timestamp="ts", level="INFO", fragment="frag")
    assert (
        result
        == "<div class='card'><span>ts</span><b>INFO</b><section>frag</section></div>"
    )


def test_emit_appends_item(patched_templates):
    handler = HTMLHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))

    record = make_record(msg="abc", level=logging.WARNING)
    handler.emit(record)

    assert len(handler._items) == 1
    item = handler._items[0]
    assert isinstance(item, HTMLItem)
    assert item.level == "WARNING"
    assert item.fragment == "abc"
    assert item.timestamp == dt.datetime.fromtimestamp(
        record.created, tz=dt.timezone.utc
    )


def test_emit_calls_handle_error_on_formatter_exception(monkeypatch, patched_templates):
    handler = HTMLHandler()

    class ExplodingFormatter(logging.Formatter):
        def format(self, record):
            raise RuntimeError("boom")

    handler.setFormatter(ExplodingFormatter())

    called = {"value": False}

    def fake_handle_error(record):
        called["value"] = True

    monkeypatch.setattr(handler, "handleError", fake_handle_error)

    record = make_record()
    handler.emit(record)

    assert called["value"] is True
    assert handler._items == []


def test_render_page_with_no_items(patched_templates):
    handler = HTMLHandler()
    html = handler.render_page(title="My Title")
    assert html == "<html><head><title>My Title</title></head><body></body></html>"


def test_render_page_with_items(patched_templates):
    handler = HTMLHandler()
    handler._items.append(
        HTMLItem(
            timestamp=dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc),
            level="INFO",
            fragment="<p>a</p>",
        )
    )
    handler._items.append(
        HTMLItem(
            timestamp=dt.datetime(2024, 1, 2, tzinfo=dt.timezone.utc),
            level="ERROR",
            fragment="<p>b</p>",
        )
    )

    html = handler.render_page(title="Report")
    assert "<title>Report</title>" in html
    assert "2024-01-01T00:00:00+00:00" in html
    assert "2024-01-02T00:00:00+00:00" in html
    assert "<p>a</p>" in html
    assert "<p>b</p>" in html


def test_output_file_property_round_trip(tmp_path: Path):
    handler = HTMLHandler()
    assert handler.output_file is None

    p = tmp_path / "out.html"
    handler.output_file = p
    assert handler.output_file == p


def test_constructor_resolves_output_file(tmp_path: Path):
    rel = tmp_path / "out.html"
    handler = HTMLHandler(str(rel))
    assert handler.output_file == rel.resolve()


def test_render_page_to_file_writes_file(tmp_path: Path, patched_templates):
    output = tmp_path / "out.html"
    handler = HTMLHandler(str(output))
    handler._items.append(
        HTMLItem(
            timestamp=dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc),
            level="INFO",
            fragment="frag",
        )
    )

    handler.render_page_to_file()

    contents = output.read_text(encoding="utf-8")
    assert "<title>Lograder Report</title>" in contents
    assert "frag" in contents


def test_render_page_to_file_raises_when_no_output_file(patched_templates):
    handler = HTMLHandler()

    with pytest.raises(DeveloperException, match="there is no assigned file"):
        handler.render_page_to_file()
