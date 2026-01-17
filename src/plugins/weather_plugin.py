import re
import requests

class Plugin:
    metadata = {
        "name": "Live Weather Plugin",
        "version": "1.0",
        "description": "Fetches the current weather for a location."
    }

    def __init__(self, bot):
        self.bot = bot
        # IMPORTANT: Replace "YOUR_API_KEY" with your actual OpenWeatherMap API key
        self.api_key = self.bot.config.get("api_keys", {}).get("weather")

    def process(self, user_input, default_response):
        match = re.match(r"^!weather(?: (.*))?$", user_input, re.IGNORECASE)
        if not match:
            return None
        
        if not self.api_key or self.api_key == "YOUR_API_KEY":
            return "Weather plugin is not configured. An API key is required."

        location = (match.group(1) or "Marsden, AU").strip()
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.api_key}&units=metric"

        try:
            response = requests.get(url)
            response.raise_for_status() # Raise an exception for bad status codes
            data = response.json()
            
            city = data['name']
            country = data['sys']['country']
            temp = data['main']['temp']
            weather_desc = data['weather'][0]['description'].title()
            
            return f"The weather in {city}, {country} is currently {temp}°C with {weather_desc}."

        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                return f"Sorry, I couldn't find the weather for '{location}'. Please check the location."
            return f"Sorry, I couldn't fetch the weather data. Error: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"