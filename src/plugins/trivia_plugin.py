# plugins/trivia_plugin.py
import re
import requests
import random
from bs4 import BeautifulSoup

class Plugin:
    metadata = {
        "name": "Trivia Game Plugin",
        "version": "1.0",
        "description": "An interactive trivia game."
    }

    def __init__(self, bot):
        self.bot = bot
        self.current_question = None
        self.current_answers = []
        self.correct_answer = None

    def ask_new_question(self):
        """Fetches a new trivia question from the Open Trivia Database."""
        try:
            response = requests.get("https://opentdb.com/api.php?amount=1&type=multiple")
            response.raise_for_status()
            data = response.json()["results"][0]
            
            self.current_question = BeautifulSoup(data["question"], "html.parser").text
            
            answers = data["incorrect_answers"]
            answers.append(data["correct_answer"])
            random.shuffle(answers)
            self.current_answers = [BeautifulSoup(a, "html.parser").text for a in answers]
            self.correct_answer = BeautifulSoup(data["correct_answer"], "html.parser").text

            response_text = f"Here is your trivia question:\n\n{self.current_question}\n\n"
            for i, answer in enumerate(self.current_answers):
                response_text += f"{i + 1}. {answer}\n"
            response_text += "\nType `!answer <number>` to respond."
            return response_text
        except requests.exceptions.RequestException as e:
            return f"Sorry, I couldn't fetch a trivia question. Error: {e}"

    def process(self, user_input, default_response):
        user_input_lower = user_input.lower()

        # Command: !trivia
        if user_input_lower == "!trivia":
            return self.ask_new_question()

        # Command: !answer <number>
        answer_match = re.match(r"^!answer (\d+)$", user_input_lower)
        if answer_match:
            if not self.current_question:
                return "There is no active trivia question. Type `!trivia` to start a new game."
            
            try:
                choice_index = int(answer_match.group(1)) - 1
                if 0 <= choice_index < len(self.current_answers):
                    chosen_answer = self.current_answers[choice_index]
                    
                    if chosen_answer == self.correct_answer:
                        response = f"Correct! The answer was \"{self.correct_answer}\". Great job!"
                    else:
                        response = f"Sorry, that's not correct. The right answer was \"{self.correct_answer}\"."
                    
                    # Reset the game state
                    self.current_question = None
                    self.current_answers = []
                    self.correct_answer = None
                    
                    return response + " Type `!trivia` to play again!"
                else:
                    return "Invalid answer number. Please choose from the options provided."
            except ValueError:
                return "Please provide a valid number for your answer."
        
        return None