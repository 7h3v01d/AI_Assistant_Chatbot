import re
import requests
from datetime import datetime, date

class Plugin:
    metadata = {
        "name": "Proactive Assistant Plugin",
        "version": "1.0",
        "description": "Provides a daily briefing by summarizing information from other plugins."
    }

    def __init__(self, bot):
        self.bot = bot
        # You can reuse your API keys from the other plugins here
        self.weather_api_key = "YOUR_WEATHER_API_KEY" # Paste your OpenWeatherMap API key

    def _get_weather_briefing(self):
        """Fetches and formats the weather part of the briefing."""
        if not self.weather_api_key or self.weather_api_key == "YOUR_WEATHER_API_KEY":
            return "🌤️ Weather: (API key not configured)"

        location = "Marsden, AU"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.weather_api_key}&units=metric"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description'].title()
            return f"🌤️ Weather: The forecast for {location.split(',')[0]} is {temp}°C with {desc}."
        except requests.exceptions.RequestException:
            return "🌤️ Weather: (Could not fetch data)"

    def _get_todo_briefing(self, user_data):
        """Fetches and formats the to-do list part of the briefing."""
        todo_list = user_data.get("todo_list", [])
        if not todo_list:
            return "✅ To-Do List: Your to-do list is empty. Great job!"

        today = date.today()
        overdue_count = 0
        due_today_count = 0

        for task in todo_list:
            if task.get("completed"):
                continue
            
            if "due_date" in task:
                due_date = datetime.fromisoformat(task["due_date"]).date()
                if due_date < today:
                    overdue_count += 1
                elif due_date == today:
                    due_today_count += 1
        
        if overdue_count == 0 and due_today_count == 0:
            pending_count = len([t for t in todo_list if not t.get("completed")])
            return f"✅ To-Do List: You have no tasks due today. {pending_count} pending tasks overall."
        
        parts = []
        if due_today_count > 0:
            parts.append(f"you have **{due_today_count} task(s) due today**")
        if overdue_count > 0:
            parts.append(f"**{overdue_count} task(s) are overdue**")
            
        return f"❗ To-Do List: Heads up, {' and '.join(parts)}."

    def _get_notes_briefing(self, user_data):
        """Fetches and formats the most recent note for the briefing."""
        notes = user_data.get("notes", [])
        if not notes:
            return None # Don't show the notes section if there are no notes

        # Find the most recent note
        most_recent_note = sorted(notes, key=lambda n: n["created"], reverse=True)[0]
        title = most_recent_note.get('title', 'Untitled')
        text = most_recent_note.get('text', '')
        
        return f"📝 Recent Note: Your latest note is titled \"{title}\": *{text[:75]}...*"

    def _get_joke_briefing(self):
        """Fetches a random joke for the briefing."""
        try:
            headers = {"Accept": "application/json"}
            response = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=5)
            response.raise_for_status()
            return f"😂 Joke of the Day: {response.json()['joke']}"
        except requests.exceptions.RequestException:
            return "😂 Joke of the Day: (Could not fetch a joke)"

    def process(self, user_input, default_response):
        if user_input.lower() not in ["!briefing", "!summary"]:
            return None

        user_id = self.bot.config["default_user_id"]
        user_data = self.bot.memory["knowledge"]["users"].get(user_id, {})
        
        # --- Assemble the Briefing ---
        today_formatted = datetime.now().strftime('%A, %B %d, %Y')
        briefing_parts = [
            f"**Good morning! Here's your daily briefing for {today_formatted}:**"
        ]
        
        # Add each section to the briefing
        briefing_parts.append(self._get_weather_briefing())
        briefing_parts.append(self._get_todo_briefing(user_data))
        
        notes_part = self._get_notes_briefing(user_data)
        if notes_part: # Only add notes if there are any
            briefing_parts.append(notes_part)
            
        briefing_parts.append(self._get_joke_briefing())

        return "\n\n".join(briefing_parts)