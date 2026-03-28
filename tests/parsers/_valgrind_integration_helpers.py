# type: ignore

from __future__ import annotations

import importlib
import shutil
import subprocess
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

VALGRIND_EXECUTABLE = shutil.which("valgrind")
GCC_EXECUTABLE = shutil.which("gcc")
GXX_EXECUTABLE = shutil.which("g++")


def has_executable(name: str) -> bool:
    return shutil.which(name) is not None


def has_valgrind() -> bool:
    return VALGRIND_EXECUTABLE is not None


def has_gcc() -> bool:
    return GCC_EXECUTABLE is not None


def has_gxx() -> bool:
    return GXX_EXECUTABLE is not None


def has_valgrind_headers() -> bool:
    if not has_gcc():
        return False

    probe_source = r"""
    #include <valgrind/valgrind.h>
    #include <valgrind/memcheck.h>

    int main(void) {
        return 0;
    }
    """

    with subprocess.Popen(
        [
            GCC_EXECUTABLE,
            "-x",
            "c",
            "-",
            "-o",
            "/dev/null",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        stdout, stderr = process.communicate(probe_source)

    return process.returncode == 0


@dataclass(slots=True, frozen=True)
class ProgramSpec:
    name: str
    language: str
    source: str
    extra_compile_args: tuple[str, ...] = ()
    run_arguments: tuple[str, ...] = ()
    expected_return_codes: tuple[int, ...] = (0, 99)
    valgrind_tool: str = "memcheck"
    valgrind_arguments: tuple[str, ...] = ()
    required_executables: tuple[str, ...] = ()
    requires_valgrind_headers: bool = False


@dataclass(slots=True)
class ValgrindRunResult:
    xml_path: Path
    binary_path: Path
    source_path: Path
    compile_completed_process: subprocess.CompletedProcess[str]
    valgrind_completed_process: subprocess.CompletedProcess[str]
    parsed_output: object
    raw_xml_text: str


def get_program_specs() -> dict[str, ProgramSpec]:
    return {
        "invalid_read": ProgramSpec(
            name="invalid_read",
            language="c",
            source=r"""
            #include <stdlib.h>

            volatile int sink = 0;

            int main(void) {
                char *buffer = (char *)malloc(1);
                for (int index = 0; index < 3; ++index) {
                    sink += buffer[8];
                }
                free(buffer);
                return 0;
            }
            """,
        ),
        "invalid_write": ProgramSpec(
            name="invalid_write",
            language="c",
            source=r"""
            #include <stdlib.h>

            int main(void) {
                char *buffer = (char *)malloc(1);
                buffer[8] = 7;
                free(buffer);
                return 0;
            }
            """,
        ),
        "invalid_free": ProgramSpec(
            name="invalid_free",
            language="c",
            source=r"""
            #include <stdlib.h>

            int main(void) {
                int value = 123;
                free(&value);
                return 0;
            }
            """,
        ),
        "mismatched_free": ProgramSpec(
            name="mismatched_free",
            language="cpp",
            source=r"""
            #include <cstdlib>

            int main() {
                int *buffer = new int[4];
                std::free(buffer);
                return 0;
            }
            """,
            required_executables=("g++",),
        ),
        "overlap": ProgramSpec(
            name="overlap",
            language="c",
            source=r"""
            #include <string.h>

            int main(void) {
                char buffer[16] = "abcdef";
                memcpy(buffer + 1, buffer, 6);
                return 0;
            }
            """,
        ),
        "syscall_parameter": ProgramSpec(
            name="syscall_parameter",
            language="c",
            source=r"""
            #include <fcntl.h>
            #include <stdlib.h>
            #include <unistd.h>

            int main(void) {
                int file_descriptor = open("syscall_parameter.tmp", O_CREAT | O_WRONLY | O_TRUNC, 0600);
                char *buffer = (char *)malloc(8);
                ssize_t ignored = write(file_descriptor, buffer, 8);
                (void)ignored;
                close(file_descriptor);
                free(buffer);
                return 0;
            }
            """,
        ),
        "fishy_value": ProgramSpec(
            name="fishy_value",
            language="c",
            source=r"""
            #include <stdint.h>
            #include <stdlib.h>

            int main(void) {
                void *pointer = malloc((size_t)-3);
                free(pointer);
                return 0;
            }
            """,
        ),
        "uninitialized_condition": ProgramSpec(
            name="uninitialized_condition",
            language="c",
            source=r"""
            #include <stdio.h>

            int main(void) {
                int value;
                if (value) {
                    puts("unexpected");
                }
                return 0;
            }
            """,
        ),
        "leaks": ProgramSpec(
            name="leaks",
            language="c",
            source=r"""
            #include <stdlib.h>

            typedef struct Node {
                char *payload;
            } Node;

            static char *global_pointer = NULL;

            int main(void) {
                void *definitely_lost = malloc(16);
                (void)definitely_lost;

                Node *indirect_outer = (Node *)malloc(sizeof(Node));
                indirect_outer->payload = (char *)malloc(32);
                indirect_outer = NULL;

                char *possibly_lost_base = (char *)malloc(32);
                global_pointer = possibly_lost_base + 1;

                static char *still_reachable = NULL;
                still_reachable = (char *)malloc(64);

                return 0;
            }
            """,
            valgrind_arguments=(
                "--leak-check=full",
                "--show-leak-kinds=all",
                "--errors-for-leak-kinds=all",
            ),
        ),
        "file_descriptors": ProgramSpec(
            name="file_descriptors",
            language="c",
            source=r"""
            #include <fcntl.h>
            #include <unistd.h>

            int main(void) {
                int file_descriptor_one = open("fd_one.tmp", O_CREAT | O_WRONLY | O_TRUNC, 0600);
                int file_descriptor_two = open("fd_two.tmp", O_CREAT | O_WRONLY | O_TRUNC, 0600);

                close(file_descriptor_one);
                close(file_descriptor_one);

                (void)file_descriptor_two;
                return 0;
            }
            """,
            valgrind_arguments=("--track-fds=yes",),
        ),
        "fatal_signal": ProgramSpec(
            name="fatal_signal",
            language="c",
            source=r"""
            int main(void) {
                volatile int *pointer = (int *)0;
                *pointer = 7;
                return 0;
            }
            """,
            expected_return_codes=(0, 99, -11, 139),
        ),
        "client_requests": ProgramSpec(
            name="client_requests",
            language="c",
            source=r"""
            #include <stdlib.h>
            #include <valgrind/memcheck.h>
            #include <valgrind/valgrind.h>

            int main(void) {
                int value;
                VALGRIND_PRINTF("client message plain\n");
                VALGRIND_PRINTF_BACKTRACE("client message backtrace\n");
                VALGRIND_CHECK_MEM_IS_DEFINED(&value, sizeof(value));

                void *pool = (void *)0x12345;
                char *buffer = (char *)malloc(8);
                VALGRIND_CREATE_MEMPOOL(pool, 0, 0);
                VALGRIND_MEMPOOL_ALLOC(pool, buffer, 8);
                VALGRIND_MEMPOOL_FREE(pool, buffer + 1);
                VALGRIND_DESTROY_MEMPOOL(pool);
                free(buffer);

                return 0;
            }
            """,
            requires_valgrind_headers=True,
        ),
        "helgrind_race": ProgramSpec(
            name="helgrind_race",
            language="c",
            source=r"""
            #include <pthread.h>

            static int shared_counter = 0;

            static void *increment(void *unused) {
                (void)unused;
                for (int index = 0; index < 100000; ++index) {
                    shared_counter++;
                }
                return 0;
            }

            int main(void) {
                pthread_t first_thread;
                pthread_t second_thread;

                pthread_create(&first_thread, 0, increment, 0);
                pthread_create(&second_thread, 0, increment, 0);

                pthread_join(first_thread, 0);
                pthread_join(second_thread, 0);

                return shared_counter == 0;
            }
            """,
            extra_compile_args=("-pthread",),
            valgrind_tool="helgrind",
            valgrind_arguments=("--history-level=full",),
        ),
    }


def get_program_spec(name: str) -> ProgramSpec:
    return get_program_specs()[name]


def required_executables_for_spec(program_spec: ProgramSpec) -> tuple[str, ...]:
    executables = {"valgrind"}

    if program_spec.language == "c":
        executables.add("gcc")
    elif program_spec.language == "cpp":
        executables.add("g++")
    else:
        raise ValueError(f"unsupported language: {program_spec.language}")

    executables.update(program_spec.required_executables)
    return tuple(sorted(executables))


def is_program_spec_available(program_spec: ProgramSpec) -> bool:
    for executable in required_executables_for_spec(program_spec):
        if not has_executable(executable):
            return False

    if program_spec.requires_valgrind_headers and not has_valgrind_headers():
        return False

    return True


def get_compiler_executable(language: str) -> str:
    if language == "c":
        if GCC_EXECUTABLE is None:
            raise RuntimeError("gcc is not available")
        return GCC_EXECUTABLE

    if language == "cpp":
        if GXX_EXECUTABLE is None:
            raise RuntimeError("g++ is not available")
        return GXX_EXECUTABLE

    raise ValueError(f"unsupported language: {language}")


def write_source_file(directory: Path, program_spec: ProgramSpec) -> Path:
    directory.mkdir(parents=True, exist_ok=True)

    extension = ".c" if program_spec.language == "c" else ".cpp"
    source_path = directory / f"{program_spec.name}{extension}"
    source_path.write_text(
        textwrap.dedent(program_spec.source).strip() + "\n",
        encoding="utf-8",
    )
    return source_path


def compile_program(
    directory: Path, program_spec: ProgramSpec
) -> tuple[Path, Path, subprocess.CompletedProcess[str]]:
    directory.mkdir(parents=True, exist_ok=True)

    source_path = write_source_file(directory, program_spec)
    binary_path = directory / program_spec.name
    compiler_executable = get_compiler_executable(program_spec.language)

    command = [
        compiler_executable,
        str(source_path),
        "-o",
        str(binary_path),
        "-g",
        "-O0",
        "-fno-omit-frame-pointer",
        "-Wall",
        "-Wextra",
        "-pedantic",
        *program_spec.extra_compile_args,
    ]

    completed_process = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        cwd=directory,
    )
    if completed_process.returncode != 0:
        raise AssertionError(
            f"compilation failed for {program_spec.name}\n"
            f"stdout:\n{completed_process.stdout}\n"
            f"stderr:\n{completed_process.stderr}"
        )

    return source_path, binary_path, completed_process


def resolve_parser_module():
    return importlib.import_module("lograder.process.parsers.valgrind")


def resolve_output_model_type():
    parser_module = resolve_parser_module()
    if hasattr(parser_module, "ValgrindOutput"):
        return parser_module.ValgrindOutput
    raise AssertionError("lograder.process.parsers.valgrind must export ValgrindOutput")


def resolve_parse_function():
    parser_module = resolve_parser_module()

    module_candidate_names = (
        "parse_valgrind_xml",
        "parse_xml_file",
        "parse_xml",
    )

    for candidate_name in module_candidate_names:
        candidate = getattr(parser_module, candidate_name, None)
        if callable(candidate):
            return candidate

    output_model_type = resolve_output_model_type()

    classmethod_candidate_names = (
        "from_xml_file",
        "from_xml_string",
        "from_xml_element",
    )

    for candidate_name in classmethod_candidate_names:
        candidate = getattr(output_model_type, candidate_name, None)
        if callable(candidate):
            return candidate

    raise AssertionError(
        "Could not find an XML parser entrypoint in lograder.process.parsers.valgrind. "
        "Expected a module-level function such as parse_valgrind_xml, or a "
        "ValgrindOutput classmethod such as from_xml_file."
    )


def parse_xml_file(xml_path: Path) -> object:
    parse_function = resolve_parse_function()
    output_model_type = resolve_output_model_type()

    last_exception: Exception | None = None

    for candidate_argument in (xml_path, str(xml_path)):
        try:
            parsed_output = parse_function(candidate_argument)
        except Exception as exception:
            last_exception = exception
            continue

        if isinstance(parsed_output, output_model_type):
            return parsed_output

        raise AssertionError(
            f"Parser returned {type(parsed_output)!r}, expected {output_model_type!r}"
        )

    raise AssertionError(
        f"Could not parse {xml_path}. Last exception: {last_exception!r}"
    )


def run_under_valgrind(
    directory: Path, binary_path: Path, program_spec: ProgramSpec
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    if VALGRIND_EXECUTABLE is None:
        raise RuntimeError("valgrind is not available")

    xml_path = directory / f"{program_spec.name}.xml"

    command = [
        VALGRIND_EXECUTABLE,
        "--xml=yes",
        f"--xml-file={xml_path}",
        "--child-silent-after-fork=yes",
        "-q",
        f"--tool={program_spec.valgrind_tool}",
        "--error-exitcode=99",
        *program_spec.valgrind_arguments,
        str(binary_path),
        *program_spec.run_arguments,
    ]

    completed_process = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        cwd=directory,
    )

    if not xml_path.exists():
        raise AssertionError(
            f"Valgrind did not emit XML at {xml_path}\n"
            f"stdout:\n{completed_process.stdout}\n"
            f"stderr:\n{completed_process.stderr}"
        )

    if completed_process.returncode not in program_spec.expected_return_codes:
        raise AssertionError(
            f"Unexpected exit code for {program_spec.name}: {completed_process.returncode}\n"
            f"stdout:\n{completed_process.stdout}\n"
            f"stderr:\n{completed_process.stderr}"
        )

    return xml_path, completed_process


def compile_run_and_parse(
    directory: Path, program_spec: ProgramSpec
) -> ValgrindRunResult:
    directory.mkdir(parents=True, exist_ok=True)

    source_path, binary_path, compile_completed_process = compile_program(
        directory, program_spec
    )
    xml_path, valgrind_completed_process = run_under_valgrind(
        directory, binary_path, program_spec
    )
    parsed_output = parse_xml_file(xml_path)
    raw_xml_text = xml_path.read_text(encoding="utf-8")

    return ValgrindRunResult(
        xml_path=xml_path,
        binary_path=binary_path,
        source_path=source_path,
        compile_completed_process=compile_completed_process,
        valgrind_completed_process=valgrind_completed_process,
        parsed_output=parsed_output,
        raw_xml_text=raw_xml_text,
    )


def get_all_events(parsed_output: object) -> list[object]:
    runtime_events = list(getattr(parsed_output, "runtime_events", []))
    postrun_events = list(getattr(parsed_output, "postrun_events", []))
    return [*runtime_events, *postrun_events]


def get_error_records(parsed_output: object) -> list[object]:
    return [
        event
        for event in get_all_events(parsed_output)
        if getattr(event, "event_type", None) == "error"
    ]


def get_error_objects(parsed_output: object) -> list[object]:
    return [error_record.error for error_record in get_error_records(parsed_output)]


def get_error_kinds(parsed_output: object) -> list[str]:
    return [str(error.kind) for error in get_error_objects(parsed_output)]


def get_event_types(parsed_output: object) -> list[str]:
    return [
        str(getattr(event, "event_type", type(event).__name__))
        for event in get_all_events(parsed_output)
    ]


def find_events_by_type(parsed_output: object, event_type: str) -> list[object]:
    return [
        event
        for event in get_all_events(parsed_output)
        if getattr(event, "event_type", None) == event_type
    ]


def has_summary_records(parsed_output: object) -> bool:
    summaries = getattr(parsed_output, "summaries", None)
    return bool(summaries)


def assert_protocol_is_modern(parsed_output: object) -> None:
    protocol_version = getattr(parsed_output, "protocol_version", None)
    assert protocol_version is not None


def assert_has_error_kind(parsed_output: object, expected_kind: str) -> None:
    actual_error_kinds = get_error_kinds(parsed_output)
    assert expected_kind in actual_error_kinds, (
        f"Expected error kind {expected_kind!r}, "
        f"actual kinds were {actual_error_kinds!r}"
    )


def assert_has_any_error_kind(
    parsed_output: object, expected_kinds: Iterable[str]
) -> None:
    actual_error_kinds = set(get_error_kinds(parsed_output))
    expected_kind_set = set(expected_kinds)
    assert actual_error_kinds & expected_kind_set, (
        f"Expected one of {sorted(expected_kind_set)!r}, "
        f"actual kinds were {sorted(actual_error_kinds)!r}"
    )
