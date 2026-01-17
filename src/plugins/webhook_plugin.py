# plugins/webhook_plugin.py
import threading
from flask import Flask, request, jsonify
import logging
import queue

logger = logging.getLogger(__name__)

class Plugin:
    metadata = {
        "name": "Webhook Listener Plugin",
        "version": "1.2",
        "description": "Listens for incoming webhooks and uses a queue for GUI communication."
    }

    def __init__(self, bot):
        self.bot = bot
        self.host = "0.0.0.0"
        self.port = 5001
        # Create a thread-safe queue for messages
        self.webhook_queue = queue.Queue()

    def _start_flask_app(self):
        app = Flask(__name__)
        app.logger.disabled = True
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.disabled = True

        @app.route('/webhook', methods=['POST'])
        def handle_webhook():
            logger.debug("Received webhook request")  # Changed to DEBUG for more granularity
            try:
                data = request.get_json()
                logger.debug(f"Webhook data received: {data}")
                if "series" in data and "episodes" in data:
                    message = f"Sonarr: Downloaded '{data['series']['title']} - {data['episodes'][0]['title']}'"
                elif "movie" in data:
                    message = f"Radarr: Downloaded '{data['movie']['title']}'"
                else:
                    message = f"Webhook Received: {str(data)[:200]}"
                logger.debug(f"Putting message in queue: {message}")
                self.webhook_queue.put(f"🔌 {message}")
                logger.debug(f"Queue size after put: {self.webhook_queue.qsize()}")
                return jsonify({"status": "success"}), 200
            except Exception as e:
                logger.error(f"Error processing webhook: {e}", exc_info=True)
                return jsonify({"status": "error", "message": str(e)}), 400

        try:
            app.run(host=self.host, port=self.port, debug=False)
        except Exception as e:
            logger.error(f"Flask server failed to start: {e}")

    def on_load(self):
        logger.info("Starting Webhook Listener server...")
        flask_thread = threading.Thread(target=self._start_flask_app, daemon=True)
        flask_thread.start()
        logger.info(f"Webhook server is listening on http://{self.host}:{self.port}/webhook")

    def process(self, user_input, default_response):
        if user_input.lower() == "!webhook url":
            return (f"Webhook URL for local testing: http://localhost:{self.port}/webhook\n"
                    f"Use your machine's local IP for other devices on your network.")
        return None