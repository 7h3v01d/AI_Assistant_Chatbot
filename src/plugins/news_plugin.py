import re
import requests

class Plugin:
    metadata = {
        "name": "News Headlines Plugin",
        "version": "1.0",
        "description": "Fetches top news headlines."
    }

    def __init__(self, bot):
        self.bot = bot
        # IMPORTANT: Replace "YOUR_API_KEY" with your actual NewsAPI key
        self.api_key = self.bot.config.get("api_keys", {}).get("news")

    def process(self, user_input, default_response):
        match = re.match(r"^!news(?: (.*))?$", user_input, re.IGNORECASE)
        if not match:
            return None
            
        if not self.api_key or self.api_key == "YOUR_API_KEY":
            return "News plugin is not configured. An API key is required."

        query = (match.group(1) or "").strip()
        url = f"https://newsapi.org/v2/top-headlines?country=au&pageSize=5&apiKey={self.api_key}"
        if query:
            url += f"&q={query}" # Add search query if provided

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            
            if not articles:
                return f"I couldn't find any top headlines for '{query}'." if query else "I couldn't find any top headlines right now."

            response_lines = [f"Top 5 headlines{' for ' + query if query else ''}:"]
            for article in articles:
                response_lines.append(f"- {article['title']}")
            return "\n".join(response_lines)

        except requests.exceptions.RequestException as e:
            return f"Sorry, I couldn't fetch the news. Error: {e}"