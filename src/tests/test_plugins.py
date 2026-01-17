# tests/test_plugins.py
import pytest

# We can reuse the same 'bot' fixture from test_core.py if it's in a conftest.py,
# but for simplicity, we'll redefine it here. In a larger project, you'd use
# a central tests/conftest.py file for shared fixtures.
from tests.test_core import bot 

def test_todo_plugin_add_and_list(bot):
    """Test adding a task and then listing it."""
    # First, test the list command when the list is empty
    initial_list_response = bot.process_message("!todo list")
    assert "Your to-do list is empty!" in initial_list_response

    # Now, add a new task
    add_response = bot.process_message("!todo add Test my new feature priority:high")
    
    # --- UPDATED ASSERTIONS ---
    # Check for the new, more detailed response format
    assert "✅ Added:" in add_response
    assert '"Test my new feature"' in add_response
    assert "(Priority: high, Category: General)" in add_response

    # Check that the task was actually saved to memory correctly
    user_data = bot.memory["knowledge"]["users"]["test_user"]
    assert len(user_data["todo_list"]) == 1
    assert user_data["todo_list"][0]["task"] == "Test my new feature"
    assert user_data["todo_list"][0]["priority"] == "high"

    # Finally, list the tasks and check if the new task is there
    final_list_response = bot.process_message("!todo list")
    assert "Test my new feature" in final_list_response
    assert "(Priority: high" in final_list_response

def test_calculator_plugin_simple_math(bot):
    """Test the calculator with a basic expression."""
    response = bot.process_message("calculate 5 * (2 + 3)")
    assert "The result of 5 * (2 + 3) is 25" in response

def test_datetime_plugin_set_and_check_timezone(bot):
    """Test setting and then using a custom timezone."""
    # Set a new timezone
    set_tz_response = bot.process_message("!settimezone America/New_York")
    assert "Timezone set to America/New_York" in set_tz_response
    
    # Check that it was saved to memory
    user_data = bot.memory["knowledge"]["users"]["test_user"]
    assert user_data["timezone"] == "America/New_York"
    
    # Ask for the time, which should now use the new timezone
    time_response = bot.process_message("!time")
    assert "America/New_York" in time_response