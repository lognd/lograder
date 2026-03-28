# type: ignore

from __future__ import annotations

from pathlib import Path

from lograder.process.registry.curl import CURLArgs, CURLExecutable


def test_curl_args_basic_emit() -> None:
    args = CURLArgs(url="https://example.com", output=Path("out.txt"))
    assert args.emit() == ["https://example.com", "-o", "out.txt"]


def test_curl_args_with_flags() -> None:
    args = CURLArgs(
        url="https://example.com",
        output=Path("out.txt"),
        response_headers_only=True,
        follow_redirects=True,
    )
    assert args.emit() == [
        "https://example.com",
        "-o",
        "out.txt",
        "-I",
        "-L",
    ]


def test_curl_args_with_data() -> None:
    args = CURLArgs(
        url="https://example.com",
        output=Path("out.txt"),
        data={"a": 1, "b": "two"},
    )
    assert args.emit() == [
        "https://example.com",
        "-o",
        "out.txt",
        "-d",
        "a=1&b=two",
    ]


def test_curl_args_with_headers() -> None:
    args = CURLArgs(
        url="https://example.com",
        output=Path("out.txt"),
        headers={"Accept": "application/json", "X-Test": 123},
    )
    assert args.emit() == [
        "https://example.com",
        "-o",
        "out.txt",
        "-H",
        "Accept: application/json\n\rX-Test: 123",
    ]


def test_curl_args_with_data_and_headers() -> None:
    args = CURLArgs(
        url="https://example.com",
        output=Path("out.txt"),
        data={"k": "v"},
        headers={"Authorization": "Bearer token"},
        response_headers_only=True,
        follow_redirects=True,
    )
    assert args.emit() == [
        "https://example.com",
        "-o",
        "out.txt",
        "-I",
        "-L",
        "-d",
        "k=v",
        "-H",
        "Authorization: Bearer token",
    ]


def test_curl_executable_registered_command() -> None:
    assert CURLExecutable.executable is not None
    assert CURLExecutable.executable.command == ["curl"]
