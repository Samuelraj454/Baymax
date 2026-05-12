import pytest
import json
from core.accuracy_engine import AccuracyEngine
from core.intent_classifier import IntentClassifier
from core.speech_engine import SpeechEngine

@pytest.fixture
def accuracy_engine():
    return AccuracyEngine()

@pytest.fixture
def intent_classifier():
    return IntentClassifier()

@pytest.fixture
def speech_engine():
    return SpeechEngine()

# 1. AccuracyEngine.validate_json() Tests
def test_validate_json_broken_but_recoverable(accuracy_engine):
    # Strategy 2: Regex extract
    broken_json = "Here is the plan: {\"tool\": \"email\", \"args\": {\"to\": \"sam\"}} Hope this helps!"
    result = accuracy_engine.validate_json(broken_json)
    assert result is not None
    assert result["tool"] == "email"
    
    # Strategy 3: Manual slice
    extra_text = "Wait... {\"action\": \"test\"} ..."
    result = accuracy_engine.validate_json(extra_text)
    assert result["action"] == "test"

def test_validate_json_invalid(accuracy_engine):
    invalid = "This is not json at all."
    assert accuracy_engine.validate_json(invalid) is None

# 2. IntentClassifier.classify() Tests
@pytest.mark.parametrize("command,expected_intent", [
    ("send an email to sam", "email"),
    ("whatsapp message to mom", "whatsapp"),
    ("remind me to buy milk", "reminder"),
    ("add a meeting for tomorrow at 10am", "calendar"),
    ("what is the weather in London", "weather"),
    ("play some jazz music", "music"),
    ("what are the headlines today", "news"),
    ("translate hello to spanish", "translate"),
    ("calculate 5 plus 5", "calculator"),
    ("search for space x launch", "web_search")
])
def test_intent_classification(intent_classifier, command, expected_intent):
    intent = intent_classifier.classify(command)
    assert intent == expected_intent

# 3. SpeechEngine.announce_result() Tests
def test_announce_result_all_tools(speech_engine):
    tools = [
        ("email", {"to": "sam", "subject": "hi"}),
        ("whatsapp", {"name": "mom"}),
        ("reminder", {"time": "8pm"}),
        ("calendar", {"title": "Meeting", "time": "10am"}),
        ("notes", {"title": "Idea"}),
        ("weather", {"city": "Paris"}),
        ("music", {"query": "Jazz"}),
        ("translate", {"language": "Spanish", "original": "Hello"}),
        ("calculator", {"expression": "5+5"}),
        ("contacts", {"name": "Alice"})
    ]
    
    for tool, args in tools:
        result = "success_output"
        speech = speech_engine.announce_result(tool, args, result)
        assert isinstance(speech, str)
        assert len(speech) > 0
        # Check if key args are in the speech if template uses them
        if "to" in args and tool == "email":
            assert "sam" in speech
        if "name" in args and tool == "whatsapp":
            assert "mom" in speech

def test_announce_failure(speech_engine):
    speech = speech_engine.announce_failure("email", "SMTP error")
    assert "Couldn't send" in speech
    assert "SMTP error" in speech
