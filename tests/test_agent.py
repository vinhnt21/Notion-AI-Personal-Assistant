"""Basic tests for the Notion Agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def mock_notion_client():
    """Mock the Notion SDK client"""
    with patch("integrations.notion_discovery.Client") as mock:
        client = MagicMock()
        client.blocks.children.list.return_value = {"results": [], "has_more": False}
        client.search.return_value = {"results": [], "has_more": False}
        mock.return_value = client
        yield client


@pytest.fixture
def mock_llm():
    """Mock LLMFactory.create_llm"""
    with patch("core.agent.LLMFactory") as mock:
        mock.create_llm.return_value = MagicMock()
        yield mock


def test_config_loads():
    """Config should load without errors"""
    from config import config

    assert config is not None
    assert config.DATA_DIR.exists()


def test_llm_factory_list_providers():
    """LLMFactory should list available providers"""
    from core.llm_factory import LLMFactory

    providers = LLMFactory.list_available_providers()
    assert isinstance(providers, dict)
    assert "openai" in providers
    assert "gemini" in providers
    assert "claude" in providers


def test_json_storage():
    """JSONStorage should read/write correctly"""
    from utils.storage import JSONStorage

    store = JSONStorage("_test_storage.json")
    store.write({"hello": "world"})
    assert store.read() == {"hello": "world"}

    store.update_field("count", 42)
    assert store.read()["count"] == 42

    store.append_item("items", "a")
    store.append_item("items", "b")
    assert store.read()["items"] == ["a", "b"]

    # Cleanup
    store.filepath.unlink(missing_ok=True)


def test_conversation_storage():
    """ConversationStorage should save and retrieve messages"""
    from utils.storage import ConversationStorage

    cs = ConversationStorage()
    cs.storage.filepath = cs.storage.filepath.parent / "_test_conversations.json"
    cs.storage._ensure_file_exists()

    cs.save_conversation("test-session", {"role": "user", "content": "hello"})
    messages = cs.get_conversation("test-session")
    assert len(messages) == 1
    assert messages[0]["content"] == "hello"

    sessions = cs.list_sessions()
    assert "test-session" in sessions

    cs.delete_session("test-session")
    assert cs.get_conversation("test-session") == []

    # Cleanup
    cs.storage.filepath.unlink(missing_ok=True)


def test_notion_schemas():
    """Notion schema helpers should produce correct structures"""
    from integrations.notion_schemas import (
        title_property,
        rich_text_property,
        number_property,
        select_property,
        checkbox_property,
        extract_property_value,
    )

    assert title_property("Test")["title"][0]["text"]["content"] == "Test"
    assert rich_text_property("Hello")["rich_text"][0]["text"]["content"] == "Hello"
    assert number_property(42)["number"] == 42
    assert select_property("Option A")["select"]["name"] == "Option A"
    assert checkbox_property(True)["checkbox"] is True

    # Extractor
    val = extract_property_value({"type": "number", "number": 99})
    assert val == 99
