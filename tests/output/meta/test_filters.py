# type: ignore

from __future__ import annotations

import logging

import pytest

from lograder.exception import DeveloperException
from lograder.output.filters import BelowLevelFilter, _coerce_level


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (logging.DEBUG, logging.DEBUG),
        (logging.INFO, logging.INFO),
        ("DEBUG", logging.DEBUG),
        (" debug ", logging.DEBUG),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("10", 10),
        ("0", 0),
        ("15", 15),
    ],
)
def test_coerce_level_accepts_valid_values(value, expected):
    assert _coerce_level(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        object(),
        "",
        "   ",
        "NOTALEVEL",
        [],
        {},
    ],
)
def test_coerce_level_rejects_invalid_values(value):
    with pytest.raises(DeveloperException, match="Invalid logging level encountered"):
        _coerce_level(value)  # type: ignore[arg-type]


def test_below_level_filter_stores_threshold():
    filt = BelowLevelFilter(below="WARNING")
    assert filt._below == logging.WARNING


def test_below_level_filter_uses_name():
    filt = BelowLevelFilter(name="abc", below="WARNING")
    assert filt.name == "abc"


@pytest.mark.parametrize(
    ("record_level", "expected"),
    [
        (logging.DEBUG, True),
        (logging.INFO, True),
        (logging.WARNING, False),
        (logging.ERROR, False),
        (logging.CRITICAL, False),
    ],
)
def test_below_level_filter_filters_by_threshold(record_level, expected):
    filt = BelowLevelFilter(below="WARNING")
    record = logging.LogRecord(
        name="x",
        level=record_level,
        pathname=__file__,
        lineno=1,
        msg="message",
        args=(),
        exc_info=None,
    )
    assert filt.filter(record) is expected
