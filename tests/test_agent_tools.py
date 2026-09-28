"""Tool-call parsing: the [TOOL_CALL: ...] contract the agent relies on."""
import pytest
from assistant.agent import parse_tool_call_args, TOOL_CALL_RE

def test_parse_positional_and_kwargs():
    args, kwargs = parse_tool_call_args('("task-1", priority="P1")')
    assert args == ["task-1"]
    assert kwargs == {"priority": "P1"}

def test_parse_empty():
    assert parse_tool_call_args(None) == ([], {})
    assert parse_tool_call_args("") == ([], {})

def test_parse_rejects_non_literals():
    with pytest.raises(Exception):
        parse_tool_call_args('(os.system("id"))')

def test_regex_extracts_calls():
    text = 'Sure! [TOOL_CALL: list_tasks(status="pending")] and [TOOL_CALL: get_calendar_events()]'
    calls = TOOL_CALL_RE.findall(text)
    assert [c[0] for c in calls] == ["list_tasks", "get_calendar_events"]

def test_regex_ignores_plain_text():
    assert TOOL_CALL_RE.findall("no tools here, just braces (like this)") == []
