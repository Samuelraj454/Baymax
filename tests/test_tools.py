import pytest
import os
from tools.reminder_tool import ReminderTool
from tools.file_tool import FileTool
from tools.web_tool import WebTool
from tools.system_tool import SystemTool

def test_reminder_valid():
    tool = ReminderTool()
    res = tool.run(message="Drink water", time="2030-05-05T12:00:00Z")
    assert res.success == True
    assert "Drink water" in res.output

def test_reminder_invalid():
    tool = ReminderTool()
    res = tool.run(message="Drink water", time="not a time")
    assert res.success == False
    assert "Invalid ISO 8601" in res.error

def test_file_write_read(tmp_path):
    tool = FileTool()
    test_file = str(tmp_path / "test.txt")
    
    # Write
    res_w = tool.run(operation="write", path=test_file, content="Hello World")
    assert res_w.success == True
    
    # Read
    res_r = tool.run(operation="read", path=test_file)
    assert res_r.success == True
    assert res_r.output == "Hello World"

def test_file_list(tmp_path):
    tool = FileTool()
    # Write a file first to have something to list
    test_file = str(tmp_path / "test.txt")
    tool.run(operation="write", path=test_file, content="Hello")
    
    # List
    res_l = tool.run(operation="list", path=str(tmp_path))
    assert res_l.success == True
    assert "test.txt" in res_l.output

def test_web_bad_url():
    tool = WebTool()
    res = tool.run(url="http://thisurldoesnotexist.xyz")
    assert res.success == False

def test_system_get_time():
    tool = SystemTool()
    res = tool.run(action="get_time")
    assert res.success == True
    assert len(res.output) > 5

def test_system_get_date():
    tool = SystemTool()
    res = tool.run(action="get_date")
    assert res.success == True
    assert len(res.output) > 5