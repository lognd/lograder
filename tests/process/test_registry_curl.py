# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.cli_args import CLI_ARG_MISSING
from lograder.process.registry.curl import CURLArgs, CURLExecutable


def test_curl_args_minimal_emit() -> None:
    args = CURLArgs(url="https://example.com")
    assert args.emit() == ["https://example.com"]


def test_curl_args_with_output() -> None:
    args = CURLArgs(
        url="https://example.com/file.txt",
        output=Path("file.txt"),
    )

    toks = ["-o file.txt", "https://example.com/file.txt"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == ["-o", "file.txt", "https://example.com/file.txt"]


def test_curl_args_full_emit() -> None:
    args = CURLArgs(
        url="https://example.com/api",
        output=Path("resp.json"),
        response_headers_only=True,
        follow_redirects=True,
        fail=True,
        silent=True,
        show_error=True,
        method="POST",
        data={
            "a": 1,
            "b": "two",
        },
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer token",
        },
    )

    toks = [
        "-o resp.json",
        "-I",
        "-L",
        "-f",
        "-s",
        "-S",
        "-X POST",
        "--data a=1",
        "--data b=two",
        "-H Accept: application/json",
        "-H Authorization: Bearer token",
        "https://example.com/api",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = args.emit()
    assert emitted[-1] == "https://example.com/api"
    assert "-o" in emitted
    assert "resp.json" in emitted
    assert "-I" in emitted
    assert "-L" in emitted
    assert "-f" in emitted
    assert "-s" in emitted
    assert "-S" in emitted
    assert "-X" in emitted
    assert "POST" in emitted
    assert "--data" in emitted
    assert "-H" in emitted


def test_curl_args_omits_missing_optional_fields() -> None:
    args = CURLArgs(
        url="https://example.com",
        output=CLI_ARG_MISSING(),
        method=CLI_ARG_MISSING(),
        response_headers_only=False,
        follow_redirects=False,
        fail=False,
        silent=False,
        show_error=False,
    )
    assert args.emit() == ["https://example.com"]


def test_curl_args_with_only_headers() -> None:
    args = CURLArgs(
        url="https://example.com",
        headers={"Accept": "application/json"},
    )
    assert args.emit() == [
        "-H",
        "Accept: application/json",
        "https://example.com",
    ]


def test_curl_args_with_only_data() -> None:
    args = CURLArgs(
        url="https://example.com",
        data={"q": "search", "page": 2},
    )

    toks = [
        "--data q=search",
        "--data page=2",
        "https://example.com",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = args.emit()
    assert emitted[-1] == "https://example.com"


def test_curl_executable_registered_command() -> None:
    assert CURLExecutable.executable is not None
    assert CURLExecutable.executable.command == ["curl"]


def test_curl_rejects_blank_url() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(url="   ")


def test_curl_rejects_blank_method() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(url="https://example.com", method="")


def test_curl_rejects_blank_output_path() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(url="https://example.com", output=" ")


def test_curl_rejects_blank_header_key() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(
            url="https://example.com",
            headers={"": "application/json"},
        )


def test_curl_rejects_blank_header_value() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(
            url="https://example.com",
            headers={"Accept": "   "},
        )


def test_curl_rejects_header_key_with_newline() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(
            url="https://example.com",
            headers={"Bad\nHeader": "value"},
        )


def test_curl_rejects_header_value_with_newline() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(
            url="https://example.com",
            headers={"Accept": "bad\nvalue"},
        )


def test_curl_rejects_blank_data_key() -> None:
    with pytest.raises(ValidationError):
        CURLArgs(
            url="https://example.com",
            data={"": 1},
        )


def test_curl_show_error_implies_silent() -> None:
    args = CURLArgs(
        url="https://example.com",
        show_error=True,
        silent=False,
    )
    emitted = args.emit()
    assert "-S" in emitted
    assert "-s" in emitted
