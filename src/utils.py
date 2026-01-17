# utils.py
import logging
import os

# --- NEW CODE START ---
# Get the absolute path of the directory where this file is located (i.e., your src folder)
base_dir = os.path.dirname(os.path.abspath(__file__))
# Create the full path for the log file
log_file_path = os.path.join(base_dir, 'chatbot.log')
# --- NEW CODE END ---


# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        # Use the new absolute path for the FileHandler
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

# Default configuration for the bot
DEFAULT_CONFIG = {
    "memory_file": "chat_memory.json",
    "plugin_dir": "plugins",
    "max_history": 100,
    "history_days": 7,
    "default_user_id": "default"
}