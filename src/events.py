# events.py
from PyQt6.QtCore import QObject, pyqtSignal

class MessageEmitter(QObject):
    """
    A simple object that emits a PyQt signal when a message is ready.
    Background threads can call the emit() method, and the UI (or console handler)
    can connect to the message_emitted signal.
    """
    message_emitted = pyqtSignal(str)

    def emit(self, message):
        self.message_emitted.emit(message)