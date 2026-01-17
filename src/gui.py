# gui.py
import sys
import queue
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QLineEdit, 
                             QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QMessageBox)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QTimer
from events import MessageEmitter

class ChatWindow(QMainWindow):
    def __init__(self, bot_instance, emitter, webhook_queue):
        super().__init__()
        self.bot = bot_instance
        self.emitter = emitter
        self.webhook_queue = webhook_queue # Store the queue

        self.setWindowTitle("AI Assistant Chatbot")
        self.setGeometry(100, 100, 600, 800)

        # ... (central_widget, layout, chat_display, input_line setup is the same)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.chat_display)
        self.input_line = QLineEdit()
        self.input_line.setStyleSheet("font-size: 14px;")
        self.input_line.setPlaceholderText("Type your message here and press Enter...")
        layout.addWidget(self.input_line)

        # --- Connect signals and slots ---
        self.input_line.returnPressed.connect(self.send_message)
        self.emitter.message_emitted.connect(self.display_system_message)
        self.emitter.message_emitted.connect(self.show_desktop_notification)

        # --- Setup a timer to check the webhook queue ---
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_webhook_queue)
        self.queue_timer.start(250) # Check every 250 milliseconds

        self.create_tray_icon()

    def check_webhook_queue(self):
        """Checks the queue for new messages and emits them."""
        while not self.webhook_queue.empty():
            try:
                message = self.webhook_queue.get_nowait()
                # Use the existing emitter to display the message
                self.emitter.emit(message)
            except queue.Empty:
                break
    
    # ... (all other methods like show_desktop_notification, generate_icon, etc. are the same)
    def show_desktop_notification(self, message):
        title = "Bot Notification"
        if "REMINDER" in message:
            title = "Scheduled Reminder"
        elif "Webhook" in message or "Radarr" in message or "Sonarr" in message:
            title = "Webhook Received"
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)
        
    def generate_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor("#4285F4"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 64, 64)
        painter.end()
        return QIcon(pixmap)

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self.generate_icon(), self)
        self.tray_icon.setToolTip("AI Assistant Chatbot")
        tray_menu = QMenu()
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        reload_action = QAction("Reload Plugins", self)
        reload_action.triggered.connect(self.reload_plugins)
        tray_menu.addAction(reload_action)
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def toggle_visibility(self):
        if self.isVisible(): self.hide()
        else: self.show(); self.activateWindow()

    def reload_plugins(self):
        self.bot.plugin_manager.reload_plugins()
        self.tray_icon.showMessage("Plugins Reloaded", "All plugins have been successfully reloaded.", QSystemTrayIcon.MessageIcon.Information, 2000)
        
    def show_settings(self):
        QMessageBox.information(self, "Settings", "Settings are not yet implemented.")

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: self.toggle_visibility()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Still Running", "The chatbot is running in the system tray.", QSystemTrayIcon.MessageIcon.Information, 2000)

    def send_message(self):
        user_input = self.input_line.text()
        if not user_input: return
        self.chat_display.append(f"<font color='blue'><b>You:</b> {user_input}</font>")
        self.input_line.clear()
        bot_response = self.bot.process_message(user_input)
        self.chat_display.append(f"<font color='green'><b>Bot:</b> {bot_response}</font>")

    def display_system_message(self, message):
        self.chat_display.append(f"<font color='purple'><i><b>System:</b> {message}</i></font>")