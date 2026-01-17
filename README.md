# Modular AI Assistant Chatbot

A powerful, extensible, and persistent AI assistant chatbot built in Python. This project evolved from a single script into a multi-threaded, modular application capable of managing tasks, providing real-time information, and integrating with other services, complete with a full graphical user interface.

---
## Features

* **✨ Graphical User Interface (GUI)**: A clean and user-friendly interface built with PyQt6.
* **tray System Tray Integration**: The bot runs conveniently in the system tray with a context menu for quick actions like reloading plugins or quitting the application.
* **🤖 Modular Plugin Architecture**: Easily add new skills by dropping Python files into the `plugins/` directory.
* **💾 Persistent Database**: Uses SQLite to store scheduled events, ensuring no data is lost on restart.
* **⏰ Proactive Reminders**: A background thread actively monitors the schedule and provides real-time reminders.
* **🔗 Webhook Integration**: Runs a lightweight Flask server to listen for notifications from other applications like Sonarr or Radarr.
* **🧠 Knowledge & Memory**: Remembers user-specific facts like name, preferences, and notes.
* **🛠️ Core Utilities**: A suite of powerful plugins including an advanced calculator, timezone-aware date/time functions, and a multi-language Wikipedia search.
* **📝 Productivity Tools**: Includes a full-featured to-do list manager and a note-keeping system.
* **🎮 Interactive Fun**: Features a trivia game plugin that fetches questions from a live API.
* **✅ Automated Testing**: Comes with a `pytest` suite to ensure stability and prevent regressions.
* **⚙️ Windows Service Deployment**: Includes instructions for running the bot as a persistent background service.

---
## Screenshot



---
## Project Structure

```
/Taskbot_Assistant/
|
├── plugins/
│   ├── todo_plugin.py
│   └── ... (and all other plugins)
|
├── tests/
│   ├── test_core.py
│   └── test_plugins.py
|
├── core.py             # Core classes (AIChatBot, PluginManager)
├── main.py             # Main application entry point (handles GUI/console/service modes)
├── gui.py              # The PyQt6 GUI and system tray implementation
├── events.py           # The PyQt signal emitter for thread-safe communication
├── utils.py            # Logging and default configuration
├── database.py         # SQLite database management functions
|
├── chatbot_data.db     # Persistent database file (created on first run)
├── chat_memory.json    # JSON file for user knowledge and conversation history
├── chatbot.log         # Log file for diagnostics
└── requirements.txt    # List of Python dependencies
```

---
## Setup and Installation

Follow these steps to get the chatbot running on your system.

### 1. Create a Virtual Environment
It's highly recommended to run the project in a Python virtual environment.

```powershell
# Navigate to the project directory
cd Taskbot_Assistant

# Create the virtual environment
python -m venv venv

# Activate the environment
.\venv\Scripts\activate
```

### 2. Install Dependencies
All required Python libraries are listed in `requirements.txt`. Create this file and then install them with one command.

**Create the file `requirements.txt`:**
```
beautifulsoup4
Flask
pytest
PyQt6
pytz
requests
wikipedia-api
```

**Install from the file:**
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Some plugins (Weather, News) require free API keys to function.

1.  Find the `self.api_key = "YOUR_API_KEY"` line in `plugins/weather_plugin.py` and `plugins/news_plugin.py`.
2.  Replace `"YOUR_API_KEY"` with the keys you obtain from [OpenWeatherMap](https://openweathermap.org/api) and [NewsAPI.org](https://newsapi.org/).
3.  Do the same in `plugins/assistant_plugin.py` for the weather summary.

---
## Usage

The bot can be run in three different modes from your activated virtual environment.

### 1. GUI Mode
This is the recommended way for daily use. It provides a full user interface and system tray integration.

```bash
python main.py --gui
```
The bot will start and an icon will appear in your system tray.
* **Left-click** the tray icon to show or hide the main chat window.
* **Right-click** the tray icon to access a menu with options to reload plugins or quit the application.
* Closing the main window with the 'X' button will minimize it to the tray; the bot will continue running.

### 2. Interactive Console Mode
For direct interaction in your terminal, development, and debugging.

```bash
python main.py
```
The bot will start, and you can type commands directly into the console.

### 3. Service Mode (Windows)
To run the bot 24/7 as a background service without any user interface. See the **Deployment** section below.

---
## Testing

The project includes a test suite to verify core functionality. To run the tests, execute `pytest` from the root project directory.

```bash
pytest -v
```

---
## Deployment as a Windows Service

To make the bot a permanent, "always-on" fixture on your Windows machine, use **NSSM (the Non-Sucking Service Manager)**. This will run the bot in its non-interactive mode.

1.  **Download NSSM**: Get the latest version from [nssm.cc](https://nssm.cc/download).
2.  **Install the Service**: Open PowerShell as an **Administrator** and run the install command:
    ```powershell
    # Assuming nssm.exe is in C:\NSSM
    C:\NSSM\nssm.exe install MyChatBot
    ```
3.  **Configure in the GUI**:
    * **Path**: Path to your virtual environment's Python executable (e.g., `E:\Projects\Taskbot_Assistant\venv\Scripts\python.exe`).
    * **Startup directory**: Path to your project's `src` folder (or wherever `main.py` is).
    * **Arguments**: `main.py --no-interactive`
4.  **Start the Service**:
    ```powershell
    C:\NSSM\nssm.exe start MyChatBot
    ```
The bot will now run silently in the background. All its activity will be recorded in `chatbot.log`.
