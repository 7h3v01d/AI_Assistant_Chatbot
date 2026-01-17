import re
from datetime import datetime
import json

class Plugin:
    metadata = {
        "name": "Note Keeper Plugin",
        "version": "2.0",
        "description": "Manages user notes with titles, categories, timestamps, and search functionality."
    }

    def __init__(self, bot):
        self.bot = bot

    def process(self, user_input, default_response):
        """Process user input for note-related commands"""
        user_id = self.bot.config["default_user_id"]
        user_data = self.bot.memory["knowledge"]["users"].setdefault(user_id, {})
        
        user_data.setdefault("notes", [])

        # Command: !note add <text> [title:<title>] [category:<category>]
        add_match = re.match(
            r"^!note add (.*?)(?:\s+title:([\w\s]+))?(?:\s+category:([\w\s]+))?$",
            user_input,
            re.IGNORECASE
        )
        if add_match:
            note_text = add_match.group(1).strip()
            title = add_match.group(2).strip() if add_match.group(2) else "Untitled"
            category = add_match.group(3).strip() if add_match.group(3) else "General"
            
            if not note_text:
                return "Please provide note content."
            
            note_data = {
                "text": note_text,
                "title": title,
                "category": category,
                "created": datetime.now().isoformat()
            }
            user_data["notes"].append(note_data)
            self.bot.save_memory()
            
            response = f"🗒️ Note saved: \"{title}\" (Category: {category})"
            return response

        # Command: !note list [all|category:<category>]
        list_match = re.match(r"^!note list\s*(all|category:([\w\s]+))?$", user_input, re.IGNORECASE)
        if list_match:
            filter_type = list_match.group(1).lower() if list_match.group(1) else "all"
            category = list_match.group(2).strip() if list_match.group(2) else None
            notes = user_data["notes"]
            
            if not notes:
                return "You don't have any notes saved."
                
            filtered_notes = notes
            if filter_type == "category":
                filtered_notes = [n for n in notes if n["category"].lower() == category.lower()]
            
            if not filtered_notes:
                return f"No notes found for category: {category}."
                
            response_lines = [f"Your Notes ({filter_type}{' ' + category if category else ''}):"]
            for i, note in enumerate(filtered_notes):
                created_date = datetime.fromisoformat(note["created"]).strftime("%m/%d/%Y %I:%M %p")
                line = f"{i + 1}. {note['title']} (Category: {note['category']}, Created: {created_date})"
                line += f"\n   {note['text']}"
                response_lines.append(line)
            return "\n".join(response_lines)

        # Command: !note search <keyword>
        search_match = re.match(r"^!note search (.*)", user_input, re.IGNORECASE)
        if search_match:
            keyword = search_match.group(1).strip().lower()
            if not keyword:
                return "Please provide a search keyword."
                
            notes = user_data["notes"]
            matching_notes = [
                n for n in notes
                if keyword in n["text"].lower() or keyword in n["title"].lower()
            ]
            
            if not matching_notes:
                return f"No notes found containing '{keyword}'."
                
            response_lines = [f"Notes containing '{keyword}':"]
            for i, note in enumerate(matching_notes):
                created_date = datetime.fromisoformat(note["created"]).strftime("%m/%d/%Y %I:%M %p")
                line = f"{i + 1}. {note['title']} (Category: {note['category']}, Created: {created_date})"
                line += f"\n   {note['text']}"
                response_lines.append(line)
            return "\n".join(response_lines)

        # Command: !note delete <number>
        delete_match = re.match(r"^!note delete (\d+)", user_input, re.IGNORECASE)
        if delete_match:
            try:
                note_number = int(delete_match.group(1))
                if 1 <= note_number <= len(user_data["notes"]):
                    deleted_note = user_data["notes"].pop(note_number - 1)
                    self.bot.save_memory()
                    return f"🗑️ Deleted note: \"{deleted_note['title']}\""
                else:
                    return "Invalid note number."
            except ValueError:
                return "Please provide a valid number."

        # Command: !note clear [all|category:<category>]
        clear_match = re.match(r"^!note clear\s*(all|category:([\w\s]+))?$", user_input, re.IGNORECASE)
        if clear_match:
            clear_type = clear_match.group(1).lower() if clear_match.group(1) else "all"
            category = clear_match.group(2).strip() if clear_match.group(2) else None
            
            if clear_type == "all":
                user_data["notes"] = []
                self.bot.save_memory()
                return "🗑️ Cleared all notes!"
            elif clear_type == "category":
                user_data["notes"] = [n for n in user_data["notes"] if n["category"].lower() != category.lower()]
                self.bot.save_memory()
                return f"🗑️ Cleared all notes in category: {category}!"

        return None

    def on_load(self):
        """Called when plugin is loaded"""
        self.bot.command_registry.register(
            "note_help",
            lambda bot, args: (
                "Note Keeper Plugin Commands:\n"
                "!note add <text> [title:<title>] [category:<category>] : Add a new note\n"
                "!note list [all|category:<category>] : List notes\n"
                "!note search <keyword> : Search notes by keyword\n"
                "!note delete <number> : Delete a specific note\n"
                "!note clear [all|category:<category>] : Clear notes\n"
                "Examples:\n"
                "  !note add Remember to call Alice title:Reminder category:Personal\n"
                "  !note list category:Personal\n"
                "  !note search Alice\n"
                "  !note delete 1"
            ),
            "Show note keeper plugin help"
        )

    def on_unload(self):
        """Called when plugin is unloaded"""
        pass