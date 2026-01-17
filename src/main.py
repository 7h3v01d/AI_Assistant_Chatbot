# main.py
import time
from datetime import datetime
import pytz
import threading
import logging
import database
import sys

from core import AIChatBot
from PyQt6.QtWidgets import QApplication

# The logger for this file
logger = logging.getLogger(__name__)

def scheduler_loop(bot):
    """A loop that runs in the background to check for scheduled events from the database."""
    logger.info("Scheduler thread started.")
    while True:
        time.sleep(60)
        try:
            due_events = database.get_due_events()
            if due_events:
                for event in due_events:
                    # Use the emitter to send reminder messages
                    message = f"⏰ REMINDER: {event['event_text']}"
                    bot.emitter.emit(message)
                    logger.info(f"Reminder triggered: {event['event_text']}")
                    database.mark_event_as_announced(event['id'])
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")

# Main execution block
if __name__ == "__main__":
    database.init_db()
    bot = AIChatBot()

    # Start the background scheduler thread
    scheduler_thread = threading.Thread(target=scheduler_loop, args=(bot,), daemon=True)
    scheduler_thread.start()

    if "--gui" in sys.argv:
        # --- GUI Mode ---
        logger.info("AI Chatbot started in GUI mode.")
        from gui import ChatWindow
        app = QApplication(sys.argv)
        
        # Get the queue from the webhook plugin instance
        webhook_plugin_instance = bot.plugin_manager.plugins.get("webhook_plugin", {}).get("instance")
        webhook_queue = webhook_plugin_instance.webhook_queue if webhook_plugin_instance else None
        
        # Pass the queue to the ChatWindow
        window = ChatWindow(bot, bot.emitter, webhook_queue)
        window.show()
        sys.exit(app.exec())

    elif "--no-interactive" in sys.argv:
        # --- Service Mode ---
        logger.info("AI Chatbot started in non-interactive (service) mode.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            logger.info("AI Chatbot service shutting down.")
            
    else:
        # --- Console Mode ---
        logger.info("AI Chatbot started in interactive mode. Type '!help' or 'quit' to exit.")
        
        # Connect the emitter to a handler that prints to the console
        def console_handler(message):
            print(f"\n{message}\n> ", end="", flush=True)
        bot.emitter.message_emitted.connect(console_handler)

        while True:
            try:
                user_input = input("> ")
                if user_input.lower() == "quit":
                    break
                response = bot.process_message(user_input)
                print(f"Bot: {response}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error processing input: {e}\n{traceback.format_exc()}")
                print("Bot: An error occurred. Please try again.")