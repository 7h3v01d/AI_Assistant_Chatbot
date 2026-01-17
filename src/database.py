# database.py
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
DB_FILE = "chatbot_data.db"

def init_db():
    """Initializes the database and creates the schedule table if it doesn't exist."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event_text TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    is_announced INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database error during initialization: {e}")

def add_event(user_id, event_text, event_time_iso):
    """Adds a new event to the schedule table."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO schedule (user_id, event_text, event_time) VALUES (?, ?, ?)",
                (user_id, event_text, event_time_iso)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to add event to database: {e}")
        return False

def get_events(user_id):
    """Retrieves all non-announced events for a user."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row # Allows accessing columns by name
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM schedule WHERE user_id = ? AND is_announced = 0 ORDER BY event_time ASC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get events from database: {e}")
        return []

def get_due_events():
    """Gets all events that are past their scheduled time and haven't been announced."""
    now_iso = datetime.utcnow().isoformat()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM schedule WHERE event_time <= ? AND is_announced = 0",
                (now_iso,)
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get due events from database: {e}")
        return []

def mark_event_as_announced(event_id):
    """Marks a specific event as announced so it doesn't trigger again."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE schedule SET is_announced = 1 WHERE id = ?",
                (event_id,)
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to mark event as announced: {e}")