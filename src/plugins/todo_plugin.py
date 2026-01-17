# plugins/todo_plugin.py
import re
from datetime import datetime, timedelta
import json
import database
import pytz

class Plugin:
    metadata = {
        "name": "To-Do List Plugin",
        "version": "2.1",
        "description": "Manages a user's to-do list with priorities, due dates, categories, and automatic reminders."
    }

    def __init__(self, bot):
        self.bot = bot

    def format_due_date(self, iso_date):
        """Format ISO date to readable MM/DD/YYYY"""
        try:
            # Assumes iso_date is a UTC string from the database/parser
            user_timezone_str = self.bot.config.get("default_timezone", "UTC")
            if 'datetime' in self.bot.services:
                 user_timezone_str = self.bot.services['datetime'].get_user_timezone(self.bot.config["default_user_id"])
            
            user_timezone = pytz.timezone(user_timezone_str)
            dt_utc = datetime.fromisoformat(iso_date)
            dt_local = dt_utc.astimezone(user_timezone)
            return dt_local.strftime("%m/%d/%Y")
        except (ValueError, TypeError):
            return "Invalid date"

    def process(self, user_input, default_response):
        """Process user input for to-do list commands"""
        user_id = self.bot.config["default_user_id"]
        user_data = self.bot.memory["knowledge"]["users"].setdefault(user_id, {})
        
        user_data.setdefault("todo_list", [])

        # Command: !todo add <task> [priority:high|medium|low] [due:<date>] [category:<category>]
        add_match = re.match(
            r"^!todo add (.*?)(?:\s+priority:(high|medium|low))?(?:\s+due:(.+?))?(?:\s+category:([\w\s]+))?$",
            user_input,
            re.IGNORECASE
        )
        if add_match:
            task = add_match.group(1).strip()
            priority = add_match.group(2).lower() if add_match.group(2) else "medium"
            due_str = add_match.group(3).strip() if add_match.group(3) else None
            category = add_match.group(4).strip() if add_match.group(4) else "General"
            
            if not task:
                return "Please provide a task description."
            
            task_data = {
                "task": task,
                "priority": priority,
                "category": category,
                "created": datetime.now().isoformat()
            }

            # --- NEW INTEROPERABILITY LOGIC ---
            if due_str and 'datetime' in self.bot.services:
                # Use the service from datetime_plugin to parse the date
                target_date_utc = self.bot.services['datetime']['parse_date_offset'](due_str)
                
                if target_date_utc:
                    due_date_iso = target_date_utc.isoformat()
                    task_data["due_date"] = due_date_iso
                    # Automatically schedule a reminder in the database
                    reminder_text = f"To-Do Reminder: {task}"
                    database.add_event(user_id, reminder_text, due_date_iso)
                else:
                    return f"Sorry, I couldn't understand the due date '{due_str}'."
            # --- END NEW LOGIC ---
                
            user_data["todo_list"].append(task_data)
            self.bot.save_memory()
            
            response = f"✅ Added: \"{task}\" (Priority: {priority}, Category: {category}"
            if "due_date" in task_data:
                response += f", Due: {self.format_due_date(task_data['due_date'])}"
                response += ", Reminder set!"
            response += ")"
            return response

        # Command: !todo list [all|pending|category:<category>|overdue]
        list_match = re.match(r"^!todo list\s*(all|pending|category:([\w\s]+)|overdue)?$", user_input, re.IGNORECASE)
        if list_match:
            filter_type = list_match.group(1).lower() if list_match.group(1) else "pending"
            category = list_match.group(2).strip() if list_match.group(2) else None
            todo_list = user_data["todo_list"]
            
            if not todo_list:
                return "Your to-do list is empty!"
                
            filtered_tasks = todo_list
            now_iso = datetime.now().isoformat()
            
            if filter_type == "pending":
                filtered_tasks = [t for t in todo_list if "completed" not in t or not t["completed"]]
            elif filter_type == "category":
                filtered_tasks = [t for t in todo_list if t["category"].lower() == category.lower()]
            elif filter_type == "overdue":
                filtered_tasks = [t for t in todo_list if "due_date" in t and t["due_date"] < now_iso and ("completed" not in t or not t["completed"])]

            if not filtered_tasks:
                return f"No tasks found for {filter_type}{' ' + category if category else ''}."
                
            response_lines = [f"Your To-Do List ({filter_type}{' ' + category if category else ''}):"]
            for i, task in enumerate(filtered_tasks):
                line = f"{i + 1}. {task['task']} (Priority: {task['priority']}, Category: {task['category']}"
                if "due_date" in task:
                    line += f", Due: {self.format_due_date(task['due_date'])}"
                if "completed" in task and task["completed"]:
                    line += ", Completed"
                line += ")"
                response_lines.append(line)
            return "\n".join(response_lines)

        # Command: !todo done <number>
        done_match = re.match(r"^!todo done (\d+)", user_input, re.IGNORECASE)
        if done_match:
            try:
                task_number = int(done_match.group(1))
                pending_tasks = [t for t in user_data["todo_list"] if not t.get("completed")]
                if 1 <= task_number <= len(pending_tasks):
                    task_to_complete = pending_tasks[task_number - 1]
                    task_to_complete["completed"] = True
                    task_to_complete["completed_date"] = datetime.now().isoformat()
                    self.bot.save_memory()
                    return f"👍 Great job! Completed: \"{task_to_complete['task']}\""
                else:
                    return "Invalid task number. Please use the number from the '!todo list pending' command."
            except ValueError:
                return "Please provide a valid number."

        # Command: !todo remove <number>
        remove_match = re.match(r"^!todo remove (\d+)", user_input, re.IGNORECASE)
        if remove_match:
            try:
                task_number = int(remove_match.group(1))
                if 1 <= task_number <= len(user_data["todo_list"]):
                    removed_task = user_data["todo_list"].pop(task_number - 1)
                    self.bot.save_memory()
                    return f"🗑️ Removed from your list: \"{removed_task['task']}\""
                else:
                    return "Invalid task number."
            except ValueError:
                return "Please provide a valid number."

        # Command: !todo clear [all|completed|category:<category>]
        clear_match = re.match(r"^!todo clear\s*(all|completed|category:([\w\s]+))?$", user_input, re.IGNORECASE)
        if clear_match:
            clear_type = clear_match.group(1).lower() if clear_match.group(1) else "completed"
            category = clear_match.group(2).strip() if clear_match.group(2) else None
            
            if clear_type == "all":
                user_data["todo_list"] = []
                self.bot.save_memory()
                return "🗑️ Cleared all tasks from your to-do list!"
            elif clear_type == "completed":
                user_data["todo_list"] = [t for t in user_data["todo_list"] if not t.get("completed")]
                self.bot.save_memory()
                return "🗑️ Cleared all completed tasks from your to-do list!"
            elif clear_type == "category":
                initial_count = len(user_data["todo_list"])
                user_data["todo_list"] = [t for t in user_data["todo_list"] if t["category"].lower() != category.lower()]
                removed_count = initial_count - len(user_data["todo_list"])
                self.bot.save_memory()
                return f"🗑️ Cleared {removed_count} task(s) in category: {category}!"

        return None

    def on_load(self):
        """Called when plugin is loaded"""
        self.bot.command_registry.register(
            "todo_help",
            lambda bot, args: (
                "To-Do List Plugin Commands:\n"
                "!todo add <task> [priority:h|m|l] [due:<date>] [category:<name>] : Add a new task\n"
                "!todo list [all|pending|category:<name>|overdue] : List tasks\n"
                "!todo done <number> : Mark a PENDING task as completed\n"
                "!todo remove <number> : Remove a task by its overall list number\n"
                "!todo clear [all|completed|category:<name>] : Clear tasks\n"
                "Examples:\n"
                "  !todo add Finish report due:in 2 days category:Work\n"
                "  !todo list category:Work\n"
                "  !todo done 1"
            ),
            "Show to-do list plugin help"
        )

    def on_unload(self):
        """Called when plugin is unloaded"""
        pass