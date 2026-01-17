# tests/test_core.py
import pytest
import os
import json
from core import AIChatBot

@pytest.fixture
def bot(tmp_path):
    """
    This is a pytest fixture.
    It creates a fresh, isolated instance of our bot for each test function.
    'tmp_path' is a special pytest fixture that provides a temporary directory.
    """
    # Create temporary files for config and memory so we don't mess with our real ones
    config_path = tmp_path / "config.json"
    memory_path = tmp_path / "chat_memory.json"
    plugin_dir = "plugins" # Assume plugins are in the standard directory relative to tests

    config_data = {
        "memory_file": str(memory_path),
        "plugin_dir": plugin_dir,
        "default_user_id": "test_user"
    }
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    
    # Yield the bot instance for the test to use
    yield AIChatBot(config_file=str(config_path))
    
    # Teardown (cleanup) happens automatically after the test runs

def test_bot_initialization(bot):
    """Test if the bot and its components are created successfully."""
    assert bot is not None
    assert bot.command_registry is not None
    assert bot.plugin_manager is not None
    assert bot.config["default_user_id"] == "test_user"

def test_default_command_help(bot):
    """Test that a built-in command like !help works."""
    response = bot.process_message("!help")
    assert "!help: Show available commands" in response
    assert "!reload: Reload all plugins" in response

def test_knowledge_extraction(bot):
    """Test that the bot can learn a new fact."""
    # Check that memory is initially empty for this fact
    assert "name" not in bot.memory["knowledge"]["users"].get("test_user", {})
    
    bot.process_message("my name is Alice")
    
    # Check that memory was updated correctly
    assert bot.memory["knowledge"]["users"]["test_user"]["name"] == "Alice"

def test_plugin_loading(bot):
    """Test that the plugin manager successfully loads plugins."""
    # Check if a known, essential plugin was loaded
    assert "todo_plugin" in bot.plugin_manager.plugins
    assert "calculator_plugin" in bot.plugin_manager.plugins
    assert "assistant_plugin" in bot.plugin_manager.plugins