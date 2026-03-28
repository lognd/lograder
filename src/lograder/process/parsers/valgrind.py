from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from xml.etree import ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from _strenum_compat import StrEnum
else:
    try:
        from enum import StrEnum
    except ImportError:
        from strenum import StrEnum


class ValgrindBaseModel(BaseModel):
    """
    Shared base model for all parsed Valgrind XML models.

    Models use snake_case field names internally and accept the original XML
    element names through aliases.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class ProtocolVersion(Enum):
    VERSION_4 = 4
    VERSION_5 = 5
    VERSION_6 = 6


class ToolName(StrEnum):
    MEMCHECK = "memcheck"
    HELGRIND = "helgrind"
    DRD = "drd"
    EXP_PTRCHECK = "exp-ptrcheck"


class StatusState(StrEnum):
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"


class Frame(ValgrindBaseModel):
    """
    One stack frame from a Valgrind stack trace.

    Valgrind only guarantees the instruction pointer. All symbolic source and
    object metadata may be absent.
    """

    instruction_pointer: str = Field(
        alias="ip",
        description="Raw hexadecimal instruction pointer exactly as emitted by Valgrind.",
    )
    object_name: str | None = Field(
        default=None,
        alias="obj",
        description="Object file, executable, or shared library that contains the frame.",
    )
    function_name: str | None = Field(
        default=None,
        alias="fn",
        description="Resolved function or symbol name for the frame, if available.",
    )
    source_directory: str | None = Field(
        default=None,
        alias="dir",
        description="Directory that contains the source file for this frame, if available.",
    )
    source_file: str | None = Field(
        default=None,
        alias="file",
        description="Source file name for this frame, if available.",
    )
    source_line: int | None = Field(
        default=None,
        alias="line",
        description="1-based source line number for this frame, if available.",
    )

    @property
    def instruction_pointer_as_integer(self) -> int:
        return int(self.instruction_pointer, 16)


class Stack(ValgrindBaseModel):
    """
    Ordered call stack.

    Frames are typically emitted from innermost to outermost.
    """

    frames: list[Frame] = Field(
        default_factory=list,
        description="Ordered stack frames as emitted by Valgrind.",
    )


class Status(ValgrindBaseModel):
    """
    Run state marker emitted by Valgrind.

    The time string is human-readable and should not be treated as a stable
    machine-readable timestamp format.
    """

    state: StatusState
    elapsed_time_text: str = Field(
        alias="time",
        description="Human-readable elapsed time text emitted by Valgrind.",
    )


class LogFileQualifier(ValgrindBaseModel):
    """
    A resolved logfile qualifier from the XML preamble.
    """

    variable_name: str = Field(
        alias="var",
        description="Qualifier variable name.",
    )
    value: str = Field(
        description="Resolved qualifier value.",
    )


class ArgumentsBlock(ValgrindBaseModel):
    """
    Command-line arguments for both Valgrind itself and the client program.
    """

    valgrind_arguments: list[str] = Field(
        default_factory=list,
        description="Tokenized argv used to launch Valgrind itself.",
    )
    client_arguments: list[str] = Field(
        default_factory=list,
        description="Tokenized argv of the program being analyzed.",
    )


class ErrorCount(ValgrindBaseModel):
    """
    Incremental count update for an already-seen error.
    """

    count: int
    unique_error_identifier: str = Field(
        alias="unique",
        description="Raw hexadecimal error identifier emitted in the corresponding error record.",
    )

    @property
    def unique_error_identifier_as_integer(self) -> int:
        return int(self.unique_error_identifier, 16)


class ErrorCounts(ValgrindBaseModel):
    """
    Snapshot of one or more error occurrence counts.

    These records may be partial updates rather than complete totals for all
    known errors.
    """

    counts: list[ErrorCount] = Field(
        default_factory=list,
        alias="pairs",
        description="Per-error occurrence counts keyed by unique error identifier.",
    )


class SuppressionCount(ValgrindBaseModel):
    """
    Count of how many times a suppression matched.
    """

    count: int
    suppression_name: str = Field(
        alias="name",
        description="User-visible suppression name from the suppression file.",
    )


class SuppressionCounts(ValgrindBaseModel):
    """
    Final suppression usage counts emitted at the end of the document.
    """

    counts: list[SuppressionCount] = Field(
        default_factory=list,
        alias="pairs",
        description="Suppression usage counts.",
    )


class SuppressionFrameKind(StrEnum):
    OBJECT = "obj"
    FUNCTION = "fun"


class SuppressionFrame(ValgrindBaseModel):
    """
    One symbolic frame pattern inside a suggested suppression.
    """

    frame_kind: SuppressionFrameKind = Field(
        alias="kind",
        description="Whether the frame pattern matches an object or a function.",
    )
    pattern: str = Field(
        description="Suppression pattern text exactly as emitted.",
    )


class Suppression(ValgrindBaseModel):
    """
    Suggested suppression attached to an error.

    The raw suppression text is the concatenation of all XML CDATA chunks in
    document order.
    """

    name: str
    kind: str = Field(
        description="Primary suppression kind string.",
    )
    auxiliary_kind: str | None = Field(
        default=None,
        alias="auxkind",
        description="Optional secondary suppression kind string.",
    )
    frames: list[SuppressionFrame] = Field(
        default_factory=list,
        description="Symbolic suppression frames.",
    )
    raw_text: str = Field(
        description="Full raw suppression text reconstructed from CDATA blocks.",
    )


class PlainTextMessage(ValgrindBaseModel):
    """
    Plain WHAT or AUXWHAT message.
    """

    variant: Literal["plain"] = "plain"
    text: str


class ExtendedTextMessage(ValgrindBaseModel):
    """
    Structured XWHAT or XAUXWHAT message.

    The text field is always the human-readable message. The structured_fields
    mapping stores any additional tagged data emitted by the tool.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    variant: Literal["extended"] = "extended"
    text: str
    structured_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra structured fields that accompany the human-readable text.",
    )


Message = PlainTextMessage | ExtendedTextMessage


class AuxiliaryTextItem(ValgrindBaseModel):
    """
    One auxiliary text item inside an error.

    Auxiliary items are ordered and should be preserved exactly in document order.
    """

    item_type: Literal["auxiliary_text"] = "auxiliary_text"
    message: Message


class AuxiliaryStackItem(ValgrindBaseModel):
    """
    One auxiliary stack item inside an error.

    Auxiliary items are ordered and should be preserved exactly in document order.
    """

    item_type: Literal["auxiliary_stack"] = "auxiliary_stack"
    stack: Stack


AuxiliaryItem = AuxiliaryTextItem | AuxiliaryStackItem


class MemcheckErrorKind(StrEnum):
    UNINITIALIZED_VALUE = "UninitValue"
    UNINITIALIZED_CONDITION = "UninitCondition"
    CORE_MEMORY_ERROR = "CoreMemError"
    INVALID_READ = "InvalidRead"
    INVALID_WRITE = "InvalidWrite"
    INVALID_JUMP = "InvalidJump"
    SYSCALL_PARAMETER = "SyscallParam"
    CLIENT_CHECK = "ClientCheck"
    INVALID_FREE = "InvalidFree"
    MISMATCHED_FREE = "MismatchedFree"
    OVERLAP = "Overlap"
    LEAK_DEFINITELY_LOST = "Leak_DefinitelyLost"
    LEAK_INDIRECTLY_LOST = "Leak_IndirectlyLost"
    LEAK_POSSIBLY_LOST = "Leak_PossiblyLost"
    LEAK_STILL_REACHABLE = "Leak_StillReachable"
    INVALID_MEMORY_POOL = "InvalidMemPool"
    FISHY_VALUE = "FishyValue"


class HelgrindErrorKind(StrEnum):
    RACE = "Race"
    UNLOCK_UNLOCKED = "UnlockUnlocked"
    UNLOCK_FOREIGN = "UnlockForeign"
    UNLOCK_BOGUS = "UnlockBogus"
    PTHREAD_API_ERROR = "PthAPIerror"
    LOCK_ORDER = "LockOrder"
    MISCELLANEOUS = "Misc"


class CoreFileDescriptorErrorKind(StrEnum):
    FILE_DESCRIPTOR_BAD_CLOSE = "FdBadClose"
    FILE_DESCRIPTOR_NOT_CLOSED = "FdNotClosed"


class ErrorBase(BaseModel):
    """
    Shared structure for a modern Valgrind error record.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    unique_error_identifier: str = Field(
        alias="unique",
        description="Raw hexadecimal identifier used to correlate this error with later error-count updates.",
    )
    thread_identifier: int = Field(
        alias="tid",
        description="Valgrind thread identifier, not necessarily an operating-system thread identifier.",
    )
    thread_name: str | None = Field(
        default=None,
        alias="threadname",
        description="Client-provided thread name, if one was attached.",
    )
    kind: str = Field(
        description="Tool-specific error kind string.",
    )
    primary_messages: list[Message] = Field(
        default_factory=list,
        alias="primary",
        description="One or two primary WHAT or XWHAT messages for this error.",
    )
    primary_stack: Stack = Field(
        alias="stack",
        description="Primary stack trace for the error.",
    )
    auxiliary_items: list[AuxiliaryItem] = Field(
        default_factory=list,
        alias="aux_items",
        description="Ordered auxiliary messages and stacks associated with the error.",
    )
    suppression: Suppression | None = Field(
        default=None,
        description="Suggested suppression attached to the error, if present.",
    )

    @property
    def unique_error_identifier_as_integer(self) -> int:
        return int(self.unique_error_identifier, 16)


class MemcheckError(ErrorBase):
    tool: Literal["memcheck"] = "memcheck"
    kind: MemcheckErrorKind | str


class HelgrindError(ErrorBase):
    tool: Literal["helgrind"] = "helgrind"
    kind: HelgrindErrorKind | str


class DrdError(ErrorBase):
    tool: Literal["drd"] = "drd"
    kind: str


class CoreFileDescriptorError(ErrorBase):
    """
    Tool-agnostic core error introduced by newer XML protocols.
    """

    tool: Literal["core"] = "core"
    kind: CoreFileDescriptorErrorKind
    file_descriptor: int = Field(
        alias="fd",
        description="Numeric file descriptor referenced by the error.",
    )
    path: str | None = Field(
        default=None,
        description="Optional filesystem path associated with the file descriptor.",
    )


ErrorEvent = MemcheckError | HelgrindError | DrdError | CoreFileDescriptorError


class AnnouncedThread(ValgrindBaseModel):
    """
    Helgrind thread announcement record.

    This thread identifier is Helgrind-specific and is distinct from the normal
    Valgrind thread identifier field used in other records.
    """

    event_type: Literal["announced_thread"] = "announced_thread"
    helgrind_thread_identifier: int = Field(
        alias="hthreadid",
        description="Helgrind-specific thread identifier used in Helgrind metadata.",
    )
    creation_stack: Stack = Field(
        alias="stack",
        description="Stack trace associated with the thread announcement or creation site.",
    )


class ClientMessage(ValgrindBaseModel):
    """
    Message emitted by the client through Valgrind client request APIs.
    """

    event_type: Literal["client_message"] = "client_message"
    thread_identifier: int = Field(
        alias="tid",
        description="Valgrind thread identifier associated with the client message.",
    )
    thread_name: str | None = Field(
        default=None,
        alias="threadname",
        description="Client-provided thread name, if available.",
    )
    text: str
    stack: Stack | None = Field(
        default=None,
        description="Optional backtrace attached to the client message.",
    )


class FatalSignal(ValgrindBaseModel):
    """
    Fatal signal record emitted by Valgrind.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    event_type: Literal["fatal_signal"] = "fatal_signal"
    thread_identifier: int = Field(
        alias="tid",
        description="Valgrind thread identifier that received the signal.",
    )
    thread_name: str | None = Field(
        default=None,
        alias="threadname",
        description="Client-provided thread name, if available.",
    )
    signal_number: int = Field(
        alias="signum",
        description="Numeric signal value.",
    )
    signal_name: str | None = Field(
        default=None,
        alias="signame",
        description="Decoded signal name, if available.",
    )
    signal_code: int | None = Field(
        default=None,
        alias="sicode",
        description="Numeric si_code value associated with the signal.",
    )
    signal_code_name: str | None = Field(
        default=None,
        alias="sicodename",
        description="Decoded si_code name, if available.",
    )
    fault_address: str | None = Field(
        default=None,
        alias="faultaddr",
        description="Raw fault address as emitted by Valgrind, if present.",
    )
    stack: Stack = Field(
        description="Stack trace at the point the fatal signal was reported.",
    )

    @property
    def fault_address_as_integer(self) -> int | None:
        if self.fault_address is None:
            return None
        return int(self.fault_address, 16)


class ErrorRecord(ValgrindBaseModel):
    """
    Wrapper event for a parsed error record.
    """

    event_type: Literal["error"] = "error"
    error: ErrorEvent


class ErrorCountsRecord(ValgrindBaseModel):
    """
    Wrapper event for incremental error-count updates.
    """

    event_type: Literal["error_counts"] = "error_counts"
    error_counts: ErrorCounts = Field(
        alias="errorcounts",
        description="Incremental error-count data keyed by unique error identifier.",
    )


Event = ErrorRecord | ErrorCountsRecord | ClientMessage | AnnouncedThread | FatalSignal


class ErrorSummary(BaseModel):
    """
    Protocol-6-era summary information.

    This remains intentionally permissive because modern Valgrind summary output
    is less stable than the core event records.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    summary_type: str = Field(
        description="Classifier for the kind of summary record.",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw structured summary payload preserved without lossy normalization.",
    )


class ValgrindOutput(BaseModel):
    """
    Normalized representation of a modern Valgrind XML document.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    protocol_version: ProtocolVersion = Field(
        alias="protocolversion",
        description="XML protocol version declared at the top of the document.",
    )
    protocol_tool_name: ToolName | None = Field(
        default=None,
        alias="protocoltool",
        description="Early tool identifier used for protocol dispatch in modern XML protocols.",
    )

    preamble_lines: list[str] = Field(
        default_factory=list,
        alias="preamble",
        description="Opaque human-readable preamble lines emitted before structured records.",
    )
    process_identifier: int = Field(
        alias="pid",
        description="Process identifier of the client process being analyzed.",
    )
    parent_process_identifier: int = Field(
        alias="ppid",
        description="Parent process identifier of the client process being analyzed.",
    )
    tool_name: str = Field(
        alias="tool",
        description="Tool name emitted later in the preamble portion of the document.",
    )

    log_file_qualifiers: list[LogFileQualifier] = Field(
        default_factory=list,
        alias="logfilequalifiers",
        description="Resolved logfile qualifiers, if any were emitted.",
    )
    user_comment: str | None = Field(
        default=None,
        alias="usercomment",
        description="Optional user-provided XML comment payload preserved as text.",
    )

    arguments: ArgumentsBlock = Field(
        alias="args",
        description="Command-line arguments for Valgrind and the client program.",
    )
    start_status: Status = Field(
        description="Status record that marks the beginning of the run.",
    )
    runtime_events: list[Event] = Field(
        default_factory=list,
        description="Structured records emitted between the RUNNING and FINISHED status markers.",
    )
    finish_status: Status = Field(
        description="Status record that marks the end of the run.",
    )
    postrun_events: list[Event] = Field(
        default_factory=list,
        description="Structured records emitted after FINISHED but before final suppression counts.",
    )
    suppression_counts: SuppressionCounts = Field(
        alias="suppcounts",
        description="Final suppression usage counts.",
    )

    summaries: list[ErrorSummary] = Field(
        default_factory=list,
        description="Protocol-6-style summary records, preserved in a forward-compatible form.",
    )

    @classmethod
    def from_xml_file(cls, path: str | Path) -> ValgrindOutput:
        xml_path = Path(path)
        root = ET.parse(xml_path).getroot()
        return cls.from_xml_element(root)

    @classmethod
    def from_xml_string(cls, xml_text: str) -> ValgrindOutput:
        root = ET.fromstring(xml_text)
        return cls.from_xml_element(root)

    @classmethod
    def from_xml_element(cls, root: ET.Element) -> ValgrindOutput:
        if root.tag != "valgrindoutput":
            raise ValueError(f"expected <valgrindoutput>, got <{root.tag}>")

        children = list(root)
        if not children:
            raise ValueError("valgrindoutput is empty")

        protocol_version_element = children[0]
        if protocol_version_element.tag != "protocolversion":
            raise ValueError("first child of valgrindoutput must be <protocolversion>")

        protocol_version_value = cls._require_int_text(protocol_version_element)
        protocol_version = ProtocolVersion(protocol_version_value)

        child_index = 1
        protocol_tool_name: ToolName | None = None

        if protocol_version_value >= 4 and child_index < len(children):
            possible_protocol_tool_element = children[child_index]
            if possible_protocol_tool_element.tag not in {
                "preamble",
                "pid",
                "ppid",
                "tool",
                "logfilequalifier",
                "usercomment",
                "args",
                "status",
                "error",
                "errorcounts",
                "suppcounts",
            }:
                protocol_tool_text = cls._normalized_text(
                    possible_protocol_tool_element
                )
                if protocol_tool_text:
                    try:
                        protocol_tool_name = ToolName(protocol_tool_text)
                    except ValueError:
                        protocol_tool_name = None
                    child_index += 1

        preamble_lines: list[str] = []
        log_file_qualifiers: list[LogFileQualifier] = []
        user_comment: str | None = None
        process_identifier: int | None = None
        parent_process_identifier: int | None = None
        tool_name: str | None = None
        arguments: ArgumentsBlock | None = None
        start_status: Status | None = None
        finish_status: Status | None = None
        suppression_counts: SuppressionCounts | None = None
        runtime_events: list[Event] = []
        postrun_events: list[Event] = []
        summaries: list[ErrorSummary] = []

        has_seen_finished_status = False

        while child_index < len(children):
            child = children[child_index]
            tag_name = child.tag

            if tag_name == "preamble":
                preamble_text = cls._normalized_text(child)
                if preamble_text is not None:
                    preamble_lines.append(preamble_text)
            elif tag_name == "pid":
                process_identifier = cls._require_int_text(child)
            elif tag_name == "ppid":
                parent_process_identifier = cls._require_int_text(child)
            elif tag_name == "tool":
                tool_name = cls._require_text(child)
            elif tag_name == "logfilequalifier":
                log_file_qualifiers.append(cls._parse_log_file_qualifier(child))
            elif tag_name == "usercomment":
                user_comment = cls._raw_inner_text(child)
            elif tag_name == "args":
                arguments = cls._parse_arguments_block(child)
            elif tag_name == "status":
                parsed_status = cls._parse_status(child)
                if parsed_status.state == StatusState.RUNNING:
                    start_status = parsed_status
                elif parsed_status.state == StatusState.FINISHED:
                    finish_status = parsed_status
                    has_seen_finished_status = True
            elif tag_name in {"error", "coreerror", "core_error"}:
                parsed_event = cls._parse_error_record(
                    child, protocol_tool_name, protocol_version
                )
                if has_seen_finished_status:
                    postrun_events.append(parsed_event)
                else:
                    runtime_events.append(parsed_event)
            elif tag_name == "errorcounts":
                parsed_counts_event = cls._parse_error_counts_record(child)
                if has_seen_finished_status:
                    postrun_events.append(parsed_counts_event)
                else:
                    runtime_events.append(parsed_counts_event)
            elif tag_name in {"clientmsg", "client_message"}:
                parsed_client_message_event = cls._parse_client_message(child)
                if has_seen_finished_status:
                    postrun_events.append(parsed_client_message_event)
                else:
                    runtime_events.append(parsed_client_message_event)
            elif tag_name in {"announcethread", "announce_thread", "announced_thread"}:
                parsed_announce_thread_event = cls._parse_announced_thread(child)
                if has_seen_finished_status:
                    postrun_events.append(parsed_announce_thread_event)
                else:
                    runtime_events.append(parsed_announce_thread_event)
            elif tag_name in {"fatal_signal", "fatalsignal"}:
                parsed_fatal_signal_event = cls._parse_fatal_signal(child)
                if has_seen_finished_status:
                    postrun_events.append(parsed_fatal_signal_event)
                else:
                    runtime_events.append(parsed_fatal_signal_event)
            elif tag_name == "suppcounts":
                suppression_counts = cls._parse_suppression_counts(child)
            else:
                summaries.append(cls._parse_summary_like_record(child))

            child_index += 1

        if process_identifier is None:
            raise ValueError("missing <pid>")
        if parent_process_identifier is None:
            raise ValueError("missing <ppid>")
        if tool_name is None:
            raise ValueError("missing <tool>")
        if arguments is None:
            arguments = ArgumentsBlock()
        if start_status is None:
            raise ValueError("missing RUNNING <status>")
        if finish_status is None:
            raise ValueError("missing FINISHED <status>")
        if suppression_counts is None:
            suppression_counts = SuppressionCounts()

        return cls.model_validate(
            {
                "protocol_version": protocol_version,
                "protocol_tool_name": protocol_tool_name,
                "preamble_lines": preamble_lines,
                "process_identifier": process_identifier,
                "parent_process_identifier": parent_process_identifier,
                "tool_name": tool_name,
                "log_file_qualifiers": log_file_qualifiers,
                "user_comment": user_comment,
                "arguments": arguments,
                "start_status": start_status,
                "runtime_events": runtime_events,
                "finish_status": finish_status,
                "postrun_events": postrun_events,
                "suppression_counts": suppression_counts,
                "summaries": summaries,
            }
        )

    @staticmethod
    def _normalized_text(element: ET.Element) -> str | None:
        if element.text is None:
            return None
        return element.text.strip()

    @staticmethod
    def _require_text(element: ET.Element) -> str:
        text = ValgrindOutput._normalized_text(element)
        if text is None:
            raise ValueError(f"expected text in <{element.tag}>")
        return text

    @staticmethod
    def _require_int_text(element: ET.Element) -> int:
        return int(ValgrindOutput._require_text(element))

    @staticmethod
    def _raw_inner_text(element: ET.Element) -> str:
        parts: list[str] = []
        if element.text:
            parts.append(element.text)
        for child in list(element):
            serialized_child = ET.tostring(child, encoding="unicode")
            parts.append(serialized_child)
            if child.tail:
                parts.append(child.tail)
        return "".join(parts).strip()

    @classmethod
    def _parse_frame(cls, element: ET.Element) -> Frame:
        data: dict[str, Any] = {}

        for child in list(element):
            if child.tag == "ip":
                data["ip"] = cls._require_text(child)
            elif child.tag == "obj":
                data["obj"] = cls._require_text(child)
            elif child.tag == "fn":
                data["fn"] = cls._require_text(child)
            elif child.tag == "dir":
                data["dir"] = cls._require_text(child)
            elif child.tag == "file":
                data["file"] = cls._require_text(child)
            elif child.tag == "line":
                data["line"] = cls._require_int_text(child)

        return Frame.model_validate(data)

    @classmethod
    def _parse_stack(cls, element: ET.Element) -> Stack:
        frames = [
            cls._parse_frame(frame_element)
            for frame_element in list(element)
            if frame_element.tag == "frame"
        ]
        return Stack(frames=frames)

    @classmethod
    def _parse_status(cls, element: ET.Element) -> Status:
        state_text = element.findtext("state")
        time_text = element.findtext("time")

        if state_text is None:
            raise ValueError("status missing <state>")
        if time_text is None:
            raise ValueError("status missing <time>")

        return Status.model_validate(
            {
                "state": StatusState(state_text.strip()),
                "elapsed_time_text": time_text.strip(),
            }
        )

    @classmethod
    def _parse_log_file_qualifier(cls, element: ET.Element) -> LogFileQualifier:
        variable_name = element.findtext("var")
        value = element.findtext("value")

        if variable_name is None:
            variable_name = element.get("var")
        if value is None:
            value = element.get("value")

        if variable_name is None or value is None:
            children = list(element)
            if len(children) >= 2:
                variable_name = variable_name or cls._normalized_text(children[0])
                value = value or cls._normalized_text(children[1])

        if variable_name is None or value is None:
            raise ValueError("logfilequalifier missing variable name or value")

        return LogFileQualifier.model_validate(
            {
                "variable_name": variable_name,
                "value": value,
            }
        )

    @classmethod
    def _parse_arguments_block(cls, element: ET.Element) -> ArgumentsBlock:
        def collect_argument_texts(parent: ET.Element) -> list[str]:
            arguments: list[str] = []

            for child in list(parent):
                if child.tag in {"exe", "arg"}:
                    child_text = cls._normalized_text(child)
                    if child_text:
                        arguments.append(child_text)
                else:
                    child_text = cls._normalized_text(child)
                    if child_text:
                        arguments.append(child_text)

            return arguments

        valgrind_arguments: list[str] = []
        client_arguments: list[str] = []

        for child in list(element):
            if child.tag == "vargv":
                valgrind_arguments.extend(collect_argument_texts(child))
            elif child.tag == "argv":
                client_arguments.extend(collect_argument_texts(child))

        return ArgumentsBlock.model_validate(
            {
                "valgrind_arguments": valgrind_arguments,
                "client_arguments": client_arguments,
            }
        )

    @classmethod
    def _parse_error_count(cls, element: ET.Element) -> ErrorCount:
        count_text = element.findtext("count")
        unique_text = element.findtext("unique")

        if count_text is None or unique_text is None:
            raise ValueError("errorcounts pair missing count or unique")

        return ErrorCount.model_validate(
            {
                "count": int(count_text.strip()),
                "unique_error_identifier": unique_text.strip(),
            }
        )

    @classmethod
    def _parse_error_counts_record(cls, element: ET.Element) -> ErrorCountsRecord:
        counts = [
            cls._parse_error_count(pair_element)
            for pair_element in list(element)
            if pair_element.tag == "pair"
        ]
        return ErrorCountsRecord.model_validate(
            {
                "error_counts": ErrorCounts.model_validate(
                    {
                        "counts": counts,
                    }
                ),
            }
        )

    @classmethod
    def _parse_suppression_count(cls, element: ET.Element) -> SuppressionCount:
        count_text = element.findtext("count")
        name_text = element.findtext("name")

        if count_text is None or name_text is None:
            raise ValueError("suppcounts pair missing count or name")

        return SuppressionCount.model_validate(
            {
                "count": int(count_text.strip()),
                "suppression_name": name_text.strip(),
            }
        )

    @classmethod
    def _parse_suppression_counts(cls, element: ET.Element) -> SuppressionCounts:
        counts = [
            cls._parse_suppression_count(pair_element)
            for pair_element in list(element)
            if pair_element.tag == "pair"
        ]

        return SuppressionCounts.model_validate({"counts": counts})

    @classmethod
    def _parse_plain_message(cls, element: ET.Element) -> PlainTextMessage:
        return PlainTextMessage(text=cls._require_text(element))

    @classmethod
    def _parse_extended_message(cls, element: ET.Element) -> ExtendedTextMessage:
        text_value: str | None = None
        structured_fields: dict[str, Any] = {}

        for child in list(element):
            child_text = cls._normalized_text(child)
            if child.tag == "text":
                text_value = child_text or ""
                continue

            if len(list(child)) == 0:
                structured_fields[child.tag] = child_text
            else:
                structured_fields[child.tag] = cls._element_to_python_value(child)

        if text_value is None:
            text_value = cls._normalized_text(element) or ""

        return ExtendedTextMessage(
            text=text_value,
            structured_fields=structured_fields,
        )

    @classmethod
    def _element_to_python_value(cls, element: ET.Element) -> Any:
        children = list(element)
        if not children:
            return cls._normalized_text(element)

        grouped: dict[str, list[Any]] = {}
        for child in children:
            grouped.setdefault(child.tag, []).append(
                cls._element_to_python_value(child)
            )

        output: dict[str, Any] = {}
        for key, values in grouped.items():
            if len(values) == 1:
                output[key] = values[0]
            else:
                output[key] = values
        return output

    @staticmethod
    def _find_first_child(element: ET.Element, *tag_names: str) -> ET.Element | None:
        for tag_name in tag_names:
            found = element.find(tag_name)
            if found is not None:
                return found
        return None

    @classmethod
    def _require_child_int(cls, element: ET.Element, *tag_names: str) -> int:
        child = cls._find_first_child(element, *tag_names)
        if child is None:
            raise ValueError(f"expected one of {tag_names!r} in <{element.tag}>")
        return cls._require_int_text(child)

    @classmethod
    def _optional_child_int(cls, element: ET.Element, *tag_names: str) -> int | None:
        child = cls._find_first_child(element, *tag_names)
        if child is None:
            return None
        return cls._require_int_text(child)

    @classmethod
    def _optional_child_text(cls, element: ET.Element, *tag_names: str) -> str | None:
        child = cls._find_first_child(element, *tag_names)
        if child is None:
            return None
        return cls._normalized_text(child)

    @classmethod
    def _parse_suppression(cls, element: ET.Element) -> Suppression:
        name: str | None = None
        kind: str | None = None
        auxiliary_kind: str | None = None
        frames: list[SuppressionFrame] = []
        raw_text_parts: list[str] = []

        for child in list(element):
            if child.tag == "name":
                name = cls._require_text(child)
            elif child.tag == "kind":
                kind = cls._require_text(child)
            elif child.tag == "auxkind":
                auxiliary_kind = cls._require_text(child)
            elif child.tag in {"sframe", "frame"}:
                frame_kind_text = child.findtext("fun") or child.findtext("obj")
                fun_elem = child.find("fun")
                obj_elem = child.find("obj")
                if fun_elem is not None:
                    frames.append(
                        SuppressionFrame.model_validate(
                            {
                                "frame_kind": SuppressionFrameKind.FUNCTION,
                                "pattern": cls._require_text(fun_elem),
                            }
                        )
                    )
                elif obj_elem is not None:
                    frames.append(
                        SuppressionFrame.model_validate(
                            {
                                "frame_kind": SuppressionFrameKind.OBJECT,
                                "pattern": cls._require_text(obj_elem),
                            }
                        )
                    )
                elif frame_kind_text is not None:
                    frames.append(
                        SuppressionFrame.model_validate(
                            {
                                "frame_kind": SuppressionFrameKind.FUNCTION,
                                "pattern": frame_kind_text.strip(),
                            }
                        )
                    )

            child_text = child.text or ""
            if child_text:
                raw_text_parts.append(child_text)

        if name is None:
            name = ""
        if kind is None:
            kind = ""

        return Suppression.model_validate(
            {
                "name": name,
                "kind": kind,
                "auxiliary_kind": auxiliary_kind,
                "frames": frames,
                "raw_text": "".join(raw_text_parts).strip(),
            }
        )

    @classmethod
    def _parse_error_event(
        cls,
        element: ET.Element,
        protocol_tool_name: ToolName | None,
        protocol_version: ProtocolVersion,
    ) -> ErrorEvent:
        unique_elem = element.find("unique")
        tid_elem = element.find("tid")
        kind_elem = element.find("kind")
        if unique_elem is None:
            raise ValueError(
                f"Error event must contain `<unique>` element; found nothing in `<{element.tag}>`: {ET.tostring(element).decode('utf-8', errors='ignore')}"
            )
        if tid_elem is None:
            raise ValueError(
                f"Error event must contain `<tid>` element; found nothing in `<{element.tag}>`: {ET.tostring(element).decode('utf-8', errors='ignore')}"
            )
        if kind_elem is None:
            raise ValueError(
                f"Error event must contain `<kind>` element; found nothing in `<{element.tag}>`: {ET.tostring(element).decode('utf-8', errors='ignore')}"
            )
        unique_error_identifier = cls._require_text(unique_elem)
        thread_identifier = cls._require_int_text(tid_elem)

        thread_name_element = element.find("threadname")
        thread_name = (
            cls._normalized_text(thread_name_element)
            if thread_name_element is not None
            else None
        )

        kind_text = cls._require_text(kind_elem)

        primary_messages: list[Message] = []
        primary_stack: Stack | None = None
        auxiliary_items: list[AuxiliaryItem] = []
        suppression: Suppression | None = None

        for child in list(element):
            if child.tag == "what":
                primary_messages.append(cls._parse_plain_message(child))
            elif child.tag == "xwhat":
                primary_messages.append(cls._parse_extended_message(child))
            elif child.tag == "stack":
                if primary_stack is None:
                    primary_stack = cls._parse_stack(child)
                else:
                    auxiliary_items.append(
                        AuxiliaryStackItem(stack=cls._parse_stack(child))
                    )
            elif child.tag == "auxwhat":
                auxiliary_items.append(
                    AuxiliaryTextItem(message=cls._parse_plain_message(child))
                )
            elif child.tag == "xauxwhat":
                auxiliary_items.append(
                    AuxiliaryTextItem(message=cls._parse_extended_message(child))
                )
            elif child.tag == "suppression":
                suppression = cls._parse_suppression(child)

        if primary_stack is None:
            primary_stack = Stack()

        common_data: dict[str, Any] = {
            "unique_error_identifier": unique_error_identifier,
            "thread_identifier": thread_identifier,
            "thread_name": thread_name,
            "primary_messages": primary_messages,
            "primary_stack": primary_stack,
            "auxiliary_items": auxiliary_items,
            "suppression": suppression,
        }

        # noinspection PyTypeChecker
        if kind_text in {member.value for member in CoreFileDescriptorErrorKind}:
            fd_text = element.findtext("fd")
            path_text = element.findtext("path")
            if fd_text is None:
                raise ValueError(
                    f"core file descriptor error {kind_text!r} missing <fd>"
                )

            return CoreFileDescriptorError.model_validate(
                {
                    **common_data,
                    "kind": CoreFileDescriptorErrorKind(kind_text),
                    "file_descriptor": int(fd_text.strip()),
                    "path": path_text.strip() if path_text is not None else None,
                }
            )

        if protocol_tool_name == ToolName.HELGRIND:
            return HelgrindError(**common_data, kind=kind_text)
        if protocol_tool_name == ToolName.DRD:
            return DrdError(**common_data, kind=kind_text)

        return MemcheckError(**common_data, kind=kind_text)

    @classmethod
    def _parse_error_record(
        cls,
        element: ET.Element,
        protocol_tool_name: ToolName | None,
        protocol_version: ProtocolVersion,
    ) -> ErrorRecord:
        return ErrorRecord(
            error=cls._parse_error_event(element, protocol_tool_name, protocol_version),
        )

    @classmethod
    def _parse_client_message(cls, element: ET.Element) -> ClientMessage:
        tid_elem = element.find("tid")

        if tid_elem is None:
            raise ValueError(
                f"Client message event must contain `<tid>` element; found nothing in `<{element.tag}>`: {ET.tostring(element).decode('utf-8', errors='ignore')}"
            )

        thread_identifier = cls._require_int_text(tid_elem)

        thread_name_element = element.find("threadname")
        thread_name = (
            cls._normalized_text(thread_name_element)
            if thread_name_element is not None
            else None
        )

        text_element = element.find("text")
        if text_element is None:
            text = cls._normalized_text(element) or ""
        else:
            text = cls._normalized_text(text_element) or ""

        stack_element = element.find("stack")
        stack = cls._parse_stack(stack_element) if stack_element is not None else None

        return ClientMessage.model_validate(
            {
                "thread_identifier": thread_identifier,
                "thread_name": thread_name,
                "text": text,
                "stack": stack,
            }
        )

    @classmethod
    def _parse_announced_thread(cls, element: ET.Element) -> AnnouncedThread:
        hthreadid_elem = element.find("hthreadid")
        if hthreadid_elem is None:
            raise ValueError(
                f"Announced thread event must contain `<hthreadid>` element; found nothing in `<{element.tag}>`: {ET.tostring(element).decode('utf-8', errors='ignore')}"
            )
        helgrind_thread_identifier = cls._require_int_text(hthreadid_elem)
        stack_element = element.find("stack")
        if stack_element is None:
            raise ValueError("announced thread missing <stack>")

        return AnnouncedThread.model_validate(
            {
                "helgrind_thread_identifier": helgrind_thread_identifier,
                "creation_stack": cls._parse_stack(stack_element),
            }
        )

    @classmethod
    def _parse_fatal_signal(cls, element: ET.Element) -> FatalSignal:
        stack_element = cls._find_first_child(element, "stack")
        if stack_element is None:
            raise ValueError("fatal signal missing <stack>")

        signal_number = cls._require_child_int(element, "signum", "signo", "signal")

        thread_identifier = cls._optional_child_int(element, "tid", "threadid")
        if thread_identifier is None:
            thread_identifier = 0

        signal_code = cls._optional_child_int(element, "sicode", "code")

        return FatalSignal.model_validate(
            {
                "thread_identifier": thread_identifier,
                "thread_name": cls._optional_child_text(element, "threadname"),
                "signal_number": signal_number,
                "signal_name": cls._optional_child_text(
                    element, "signame", "signalname"
                ),
                "signal_code": signal_code,
                "signal_code_name": cls._optional_child_text(
                    element, "sicodename", "codename"
                ),
                "fault_address": cls._optional_child_text(element, "faultaddr", "addr"),
                "stack": cls._parse_stack(stack_element),
            }
        )

    @classmethod
    def _parse_summary_like_record(cls, element: ET.Element) -> ErrorSummary:
        return ErrorSummary(
            summary_type=element.tag,
            data=(
                cls._element_to_python_value(element)
                if list(element)
                else {"text": cls._normalized_text(element)}
            ),
        )


def parse_valgrind_xml(path: str | Path) -> ValgrindOutput:
    return ValgrindOutput.from_xml_file(path)
