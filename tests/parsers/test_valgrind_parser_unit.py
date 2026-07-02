from __future__ import annotations

from xml.etree import ElementTree as xml_etree

from lograder.process.parsers.valgrind import (
    AnnouncedThread,
    AuxiliaryStackItem,
    AuxiliaryTextItem,
    ClientMessage,
    CoreFileDescriptorError,
    DrdError,
    ErrorRecord,
    ExtendedTextMessage,
    FatalSignal,
    HelgrindError,
    MemcheckError,
    ValgrindOutput,
)


def make_minimal_document(
    *,
    protocol_version: int = 4,
    protocol_tool_text: str | None = "memcheck",
    tool_name: str = "memcheck",
    preamble: str = "valgrind preamble",
    before_finish: str = "",
    after_finish: str = "",
    extra_top_level: str = "",
    logfilequalifier_xml: str = "",
    usercomment_xml: str = "",
    args_xml: str = """
    <args>
      <vargv>
        <exe>/usr/bin/valgrind.bin</exe>
        <arg>--xml=yes</arg>
      </vargv>
      <argv>
        <exe>/tmp/program</exe>
        <arg>--flag</arg>
      </argv>
    </args>
    """,
    suppcounts_xml: str = """
    <suppcounts>
      <pair>
        <count>1</count>
        <name>example_suppression</name>
      </pair>
    </suppcounts>
    """,
) -> str:
    protocol_tool_xml = ""
    if protocol_tool_text is not None:
        protocol_tool_xml = f"<protocoltool>{protocol_tool_text}</protocoltool>"

    return f"""<?xml version="1.0"?>
<valgrindoutput>
  <protocolversion>{protocol_version}</protocolversion>
  {protocol_tool_xml}
  <preamble>{preamble}</preamble>
  <pid>123</pid>
  <ppid>45</ppid>
  <tool>{tool_name}</tool>
  {logfilequalifier_xml}
  {usercomment_xml}
  {args_xml}
  <status>
    <state>RUNNING</state>
    <time>0:00:00</time>
  </status>
  {before_finish}
  <status>
    <state>FINISHED</state>
    <time>0:00:01</time>
  </status>
  {after_finish}
  {suppcounts_xml}
  {extra_top_level}
</valgrindoutput>
"""


def make_stack_xml(ip: str = "0x401000", fn: str = "main") -> str:
    return f"""
    <stack>
      <frame>
        <ip>{ip}</ip>
        <obj>/tmp/program</obj>
        <fn>{fn}</fn>
        <dir>/tmp</dir>
        <file>program.c</file>
        <line>12</line>
      </frame>
    </stack>
    """


def make_plain_error_xml(kind: str = "InvalidRead") -> str:
    return f"""
    <error>
      <unique>0xabc</unique>
      <tid>1</tid>
      <kind>{kind}</kind>
      <what>{kind} happened</what>
      {make_stack_xml()}
      <auxwhat>extra context</auxwhat>
      {make_stack_xml(ip="0x401010", fn="helper")}
    </error>
    """


def test_from_xml_string_parses_basic_document() -> None:
    xml_text = make_minimal_document(before_finish=make_plain_error_xml())
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    assert parsed_output.protocol_version.value == 4
    assert parsed_output.protocol_tool_name == "memcheck"
    assert parsed_output.tool_name == "memcheck"
    assert parsed_output.process_identifier == 123
    assert parsed_output.parent_process_identifier == 45
    assert parsed_output.arguments.valgrind_arguments
    assert parsed_output.arguments.client_arguments
    assert parsed_output.start_status.state.value == "RUNNING"
    assert parsed_output.finish_status.state.value == "FINISHED"
    assert len(parsed_output.runtime_events) == 1
    assert (
        parsed_output.suppression_counts.counts[0].suppression_name
        == "example_suppression"
    )


def test_from_xml_element_parses_basic_document() -> None:
    xml_text = make_minimal_document(before_finish=make_plain_error_xml())
    root = xml_etree.fromstring(xml_text)

    parsed_output = ValgrindOutput.from_xml_element(root)

    assert parsed_output.tool_name == "memcheck"
    assert parsed_output.runtime_events
    assert isinstance(parsed_output.runtime_events[0], ErrorRecord)


def test_error_after_finished_status_goes_to_postrun_events() -> None:
    xml_text = make_minimal_document(
        before_finish=make_plain_error_xml("InvalidRead"),
        after_finish=make_plain_error_xml("Leak_DefinitelyLost"),
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    assert len(parsed_output.runtime_events) == 1
    assert len(parsed_output.postrun_events) == 1

    runtime_error = parsed_output.runtime_events[0]
    postrun_error = parsed_output.postrun_events[0]

    assert isinstance(runtime_error, ErrorRecord)
    assert isinstance(postrun_error, ErrorRecord)
    assert str(runtime_error.error.kind) == "InvalidRead"
    assert str(postrun_error.error.kind) == "Leak_DefinitelyLost"


def test_protocol_tool_absent_defaults_to_memcheck_error_model() -> None:
    xml_text = make_minimal_document(
        protocol_tool_text=None,
        tool_name="memcheck",
        before_finish=make_plain_error_xml("InvalidWrite"),
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    assert parsed_output.protocol_tool_name is None
    error_record = parsed_output.runtime_events[0]
    assert isinstance(error_record, ErrorRecord)
    assert isinstance(error_record.error, MemcheckError)


def test_drd_protocol_tool_uses_drd_error_model() -> None:
    xml_text = make_minimal_document(
        protocol_tool_text="drd",
        tool_name="drd",
        before_finish=make_plain_error_xml("SomeDrdKind"),
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    error_record = parsed_output.runtime_events[0]
    assert isinstance(error_record, ErrorRecord)
    assert isinstance(error_record.error, DrdError)
    assert str(error_record.error.kind) == "SomeDrdKind"


def test_helgrind_protocol_tool_uses_helgrind_error_model() -> None:
    xml_text = make_minimal_document(
        protocol_tool_text="helgrind",
        tool_name="helgrind",
        before_finish=make_plain_error_xml("Race"),
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    error_record = parsed_output.runtime_events[0]
    assert isinstance(error_record, ErrorRecord)
    assert isinstance(error_record.error, HelgrindError)
    assert str(error_record.error.kind) == "Race"


def test_protocol_five_core_file_descriptor_error_is_parsed() -> None:
    xml_text = make_minimal_document(
        protocol_version=5,
        protocol_tool_text="memcheck",
        tool_name="memcheck",
        before_finish=f"""
        <error>
          <unique>0xdead</unique>
          <tid>1</tid>
          <kind>FdBadClose</kind>
          <what>bad close</what>
          <fd>7</fd>
          <path>/tmp/file.txt</path>
          {make_stack_xml()}
        </error>
        <error>
          <unique>0xbeef</unique>
          <tid>1</tid>
          <kind>FdNotClosed</kind>
          <what>not closed</what>
          <fd>8</fd>
          {make_stack_xml(ip="0x401020", fn="cleanup")}
        </error>
        """,
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    first = parsed_output.runtime_events[0]
    second = parsed_output.runtime_events[1]

    assert isinstance(first, ErrorRecord)
    assert isinstance(first.error, CoreFileDescriptorError)
    assert first.error.file_descriptor == 7
    assert first.error.path == "/tmp/file.txt"

    assert isinstance(second, ErrorRecord)
    assert isinstance(second.error, CoreFileDescriptorError)
    assert second.error.file_descriptor == 8
    assert second.error.path is None


def test_logfilequalifier_variants_are_parsed() -> None:
    xml_text = make_minimal_document(
        logfilequalifier_xml="""
        <logfilequalifier>
          <var>ENV_ONE</var>
          <value>abc</value>
        </logfilequalifier>
        <logfilequalifier var="ENV_TWO" value="xyz" />
        """,
        before_finish=make_plain_error_xml(),
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    assert len(parsed_output.log_file_qualifiers) == 2
    assert parsed_output.log_file_qualifiers[0].variable_name == "ENV_ONE"
    assert parsed_output.log_file_qualifiers[0].value == "abc"
    assert parsed_output.log_file_qualifiers[1].variable_name == "ENV_TWO"
    assert parsed_output.log_file_qualifiers[1].value == "xyz"


def test_user_comment_raw_inner_text_is_preserved() -> None:
    xml_text = make_minimal_document(
        usercomment_xml="""
        <usercomment>before<nested>tag</nested>after</usercomment>
        """,
        before_finish=make_plain_error_xml(),
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    assert parsed_output.user_comment is not None
    assert "before" in parsed_output.user_comment
    assert "<nested>tag</nested>" in parsed_output.user_comment
    assert "after" in parsed_output.user_comment


def test_xwhat_and_xauxwhat_are_parsed_with_structured_fields() -> None:
    xml_text = make_minimal_document(
        before_finish=f"""
        <error>
          <unique>0x100</unique>
          <tid>1</tid>
          <kind>Leak_DefinitelyLost</kind>
          <xwhat>
            <text>definitely lost</text>
            <leakedbytes>16</leakedbytes>
            <leakedblocks>2</leakedblocks>
            <detail>
              <name>payload</name>
            </detail>
          </xwhat>
          {make_stack_xml()}
          <xauxwhat>
            <text>allocated here</text>
            <bytes>16</bytes>
          </xauxwhat>
          {make_stack_xml(ip="0x401030", fn="allocator")}
        </error>
        """,
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)
    error_record = parsed_output.runtime_events[0]

    assert isinstance(error_record, ErrorRecord)
    assert isinstance(error_record.error.primary_messages[0], ExtendedTextMessage)
    assert (
        error_record.error.primary_messages[0].structured_fields["leakedbytes"] == "16"
    )
    assert (
        error_record.error.primary_messages[0].structured_fields["leakedblocks"] == "2"
    )
    assert (
        error_record.error.primary_messages[0].structured_fields["detail"]["name"]
        == "payload"
    )

    assert isinstance(error_record.error.auxiliary_items[0], AuxiliaryTextItem)
    assert isinstance(
        error_record.error.auxiliary_items[0].message, ExtendedTextMessage
    )
    assert (
        error_record.error.auxiliary_items[0].message.structured_fields["bytes"] == "16"
    )
    assert isinstance(error_record.error.auxiliary_items[1], AuxiliaryStackItem)


def test_suppression_with_function_and_object_frames_is_parsed() -> None:
    xml_text = make_minimal_document(
        before_finish=f"""
        <error>
          <unique>0x200</unique>
          <tid>1</tid>
          <kind>InvalidRead</kind>
          <what>invalid read</what>
          {make_stack_xml()}
          <suppression>
            <name>supp_one</name>
            <kind>Memcheck:Addr4</kind>
            <auxkind>match-leak-kinds:all</auxkind>
            <sframe>
              <fun>malloc</fun>
            </sframe>
            <sframe>
              <obj>/usr/lib/libc.so</obj>
            </sframe>
          </suppression>
        </error>
        """,
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)
    error_record = parsed_output.runtime_events[0]

    assert isinstance(error_record, ErrorRecord)
    assert error_record.error.suppression is not None
    assert error_record.error.suppression.name == "supp_one"
    assert error_record.error.suppression.kind == "Memcheck:Addr4"
    assert error_record.error.suppression.auxiliary_kind == "match-leak-kinds:all"
    assert len(error_record.error.suppression.frames) == 2
    assert error_record.error.suppression.frames[0].frame_kind.value == "fun"
    assert error_record.error.suppression.frames[0].pattern == "malloc"
    assert error_record.error.suppression.frames[1].frame_kind.value == "obj"
    assert error_record.error.suppression.frames[1].pattern == "/usr/lib/libc.so"


def test_alternate_top_level_tag_spellings_are_parsed() -> None:
    xml_text = make_minimal_document(
        protocol_tool_text="helgrind",
        tool_name="helgrind",
        before_finish=f"""
        <clientmsg>
          <tid>1</tid>
          <text>hello from client</text>
          {make_stack_xml()}
        </clientmsg>
        <announcethread>
          <hthreadid>9</hthreadid>
          {make_stack_xml(ip="0x401040", fn="thread_start")}
        </announcethread>
        <fatalsignal>
          <tid>1</tid>
          <signum>11</signum>
          <signame>SIGSEGV</signame>
          <faultaddr>0x0</faultaddr>
          {make_stack_xml(ip="0x401050", fn="crash")}
        </fatalsignal>
        """,
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    assert isinstance(parsed_output.runtime_events[0], ClientMessage)
    assert isinstance(parsed_output.runtime_events[1], AnnouncedThread)
    assert isinstance(parsed_output.runtime_events[2], FatalSignal)


def test_summary_like_unknown_top_level_records_are_preserved() -> None:
    xml_text = make_minimal_document(
        before_finish=make_plain_error_xml(),
        extra_top_level="""
        <mysterysummary>
          <alpha>1</alpha>
          <beta>
            <child>x</child>
          </beta>
        </mysterysummary>
        """,
    )
    parsed_output = ValgrindOutput.from_xml_string(xml_text)

    assert parsed_output.summaries
    assert parsed_output.summaries[0].summary_type == "mysterysummary"
    assert parsed_output.summaries[0].data["alpha"] == "1"
    assert parsed_output.summaries[0].data["beta"]["child"] == "x"
