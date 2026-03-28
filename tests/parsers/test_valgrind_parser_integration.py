# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from _valgrind_integration_helpers import (
    assert_has_any_error_kind,
    assert_has_error_kind,
    assert_protocol_is_modern,
    compile_run_and_parse,
    find_events_by_type,
    get_all_events,
    get_error_kinds,
    get_event_types,
    get_program_spec,
    has_valgrind,
    is_program_spec_available,
)

pytestmark = pytest.mark.skipif(
    not has_valgrind(),
    reason="valgrind executable is not available",
)


def run_case(tmp_path: Path, case_name: str):
    program_spec = get_program_spec(case_name)
    if not is_program_spec_available(program_spec):
        missing_parts: list[str] = []
        if program_spec.language == "c":
            missing_parts.append("gcc")
        elif program_spec.language == "cpp":
            missing_parts.append("g++")
        if program_spec.requires_valgrind_headers:
            missing_parts.append("valgrind headers")
        pytest.skip(
            f"required tools are not available for {case_name}: {', '.join(sorted(set(missing_parts)))}"
        )
    return compile_run_and_parse(tmp_path / case_name, program_spec)


@pytest.mark.parametrize(
    ("case_name", "expected_kind"),
    [
        ("invalid_read", "InvalidRead"),
        ("invalid_write", "InvalidWrite"),
        ("invalid_free", "InvalidFree"),
        ("mismatched_free", "MismatchedFree"),
        ("overlap", "Overlap"),
        ("syscall_parameter", "SyscallParam"),
        ("fishy_value", "FishyValue"),
        ("uninitialized_condition", "UninitCondition"),
    ],
)
def test_memcheck_error_kinds_are_parsed_from_real_xml(
    tmp_path: Path,
    case_name: str,
    expected_kind: str,
) -> None:
    result = run_case(tmp_path, case_name)
    parsed_output = result.parsed_output

    assert_protocol_is_modern(parsed_output)
    assert getattr(parsed_output, "tool_name") == "memcheck"
    assert_has_error_kind(parsed_output, expected_kind)
    assert getattr(parsed_output, "suppression_counts") is not None
    assert len(get_all_events(parsed_output)) > 0


def test_leak_kinds_are_parsed_from_real_xml(tmp_path: Path) -> None:
    result = run_case(tmp_path, "leaks")
    parsed_output = result.parsed_output
    actual_error_kinds = set(get_error_kinds(parsed_output))

    assert getattr(parsed_output, "tool_name") == "memcheck"
    assert "Leak_DefinitelyLost" in actual_error_kinds
    assert "Leak_IndirectlyLost" in actual_error_kinds
    assert "Leak_PossiblyLost" in actual_error_kinds
    assert "Leak_StillReachable" in actual_error_kinds


def test_error_counts_record_is_parsed_from_real_xml(tmp_path: Path) -> None:
    result = run_case(tmp_path, "invalid_read")
    parsed_output = result.parsed_output
    error_count_events = find_events_by_type(parsed_output, "error_counts")

    assert error_count_events, "expected at least one parsed error-counts record"
    first_error_counts = error_count_events[0].error_counts
    assert first_error_counts.counts, "expected non-empty error counts"
    assert any(error_count.count >= 1 for error_count in first_error_counts.counts)


def test_protocol_six_summary_records_are_parsed_when_present(tmp_path: Path) -> None:
    result = run_case(tmp_path, "invalid_read")
    parsed_output = result.parsed_output

    protocol_version = getattr(parsed_output, "protocol_version")
    if int(getattr(protocol_version, "value", protocol_version)) < 6:
        pytest.skip("installed valgrind is not emitting protocol 6 XML")

    summaries = getattr(parsed_output, "summaries", None)
    assert summaries is not None
    assert isinstance(summaries, list)


def test_core_file_descriptor_errors_are_parsed_from_real_xml(tmp_path: Path) -> None:
    result = run_case(tmp_path, "file_descriptors")
    parsed_output = result.parsed_output

    protocol_version = getattr(parsed_output, "protocol_version")
    protocol_value = (
        protocol_version.value
        if hasattr(protocol_version, "value")
        else int(protocol_version)
    )

    if protocol_value < 5:
        pytest.skip(
            "installed valgrind emits protocol 4 XML; file-descriptor core errors require protocol 5+"
        )

    assert_has_error_kind(parsed_output, "FdBadClose")
    assert_has_error_kind(parsed_output, "FdNotClosed")

    error_objects = [
        error_record.error
        for error_record in find_events_by_type(parsed_output, "error")
    ]
    fd_errors = [
        error
        for error in error_objects
        if str(error.kind) in {"FdBadClose", "FdNotClosed"}
    ]

    assert fd_errors
    assert any(
        getattr(error, "file_descriptor", None) is not None for error in fd_errors
    )


def test_fatal_signal_event_is_parsed_from_real_xml(tmp_path: Path) -> None:
    result = run_case(tmp_path, "fatal_signal")
    parsed_output = result.parsed_output

    fatal_signal_events = find_events_by_type(parsed_output, "fatal_signal")
    assert fatal_signal_events, "expected a fatal_signal event"
    fatal_signal = fatal_signal_events[0]

    assert fatal_signal.signal_number > 0
    assert fatal_signal.stack.frames


def test_client_messages_and_client_check_paths_are_parsed_from_real_xml(
    tmp_path: Path,
) -> None:
    result = run_case(tmp_path, "client_requests")
    parsed_output = result.parsed_output

    client_message_events = find_events_by_type(parsed_output, "client_message")
    assert client_message_events, "expected at least one client message event"
    assert any("client message" in event.text for event in client_message_events)

    assert_has_error_kind(parsed_output, "ClientCheck")
    assert_has_any_error_kind(parsed_output, {"InvalidMemPool", "ClientCheck"})


def test_helgrind_events_are_parsed_from_real_xml(tmp_path: Path) -> None:
    result = run_case(tmp_path, "helgrind_race")
    parsed_output = result.parsed_output

    assert getattr(parsed_output, "tool_name") == "helgrind"
    assert_has_any_error_kind(
        parsed_output, {"Race", "Possible data race", "Misc", "LockOrder"}
    )

    event_types = set(get_event_types(parsed_output))
    assert "announced_thread" in event_types or "announce_thread" in event_types


def test_top_level_metadata_and_arguments_are_parsed_from_real_xml(
    tmp_path: Path,
) -> None:
    result = run_case(tmp_path, "invalid_write")
    parsed_output = result.parsed_output

    assert getattr(parsed_output, "process_identifier") > 0
    assert getattr(parsed_output, "parent_process_identifier") >= 0

    arguments = getattr(parsed_output, "arguments")
    assert arguments.valgrind_arguments
    assert arguments.client_arguments
    assert (
        result.binary_path.name in arguments.client_arguments[0]
        or str(result.binary_path) in arguments.client_arguments[0]
    )

    assert getattr(parsed_output, "start_status").state.value == "RUNNING"
    assert getattr(parsed_output, "finish_status").state.value == "FINISHED"


def test_leak_records_can_appear_after_finished_status(tmp_path: Path) -> None:
    result = run_case(tmp_path, "leaks")
    parsed_output = result.parsed_output

    postrun_events = getattr(parsed_output, "postrun_events")
    error_kinds = [
        str(event.error.kind)
        for event in postrun_events
        if getattr(event, "event_type", None) == "error"
    ]

    assert any(kind.startswith("Leak_") for kind in error_kinds)
