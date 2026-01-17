import requests

class Plugin:
    metadata = {
        "name": "Joke Teller",
        "version": "1.0",
        "description": "Tells a random dad joke."
    }

    def __init__(self, bot):
        self.bot = bot

    def process(self, user_input, default_response):
        if user_input.lower() != "!joke":
            return None

        try:
            # The API requires a specific 'Accept' header to return JSON
            headers = {"Accept": "application/json"}
            response = requests.get("https://icanhazdadjoke.com/", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data["joke"]
            
        except requests.exceptions.RequestException as e:
            return f"Sorry, I couldn't fetch a joke right now. Error: {e}"