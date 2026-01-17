from datetime import datetime, timedelta
import re
import pytz
import database

class Plugin:
    metadata = {
        "name": "Date & Time Plugin",
        "version": "2.0",
        "description": "Provides advanced date and time functions including time zones, date arithmetic, and scheduling."
    }

    def __init__(self, bot):
        self.bot = bot
        self.default_timezone = "UTC"
        self.timezone_pattern = r"(?:in\s+)?([A-Za-z\s\/]+?)(?:\s+time)?$"

    def get_user_timezone(self, user_id):
        """Retrieve user's preferred timezone from memory"""
        user_data = self.bot.memory["knowledge"]["users"].get(user_id, {})
        return user_data.get("timezone", self.default_timezone)

    def set_user_timezone(self, user_id, timezone):
        """Set user's preferred timezone in memory"""
        user_data = self.bot.memory["knowledge"]["users"].setdefault(user_id, {})
        try:
            pytz.timezone(timezone)  # Validate timezone
            user_data["timezone"] = timezone
            self.bot.save_memory()
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False

    def format_datetime(self, dt, timezone, format_str="%I:%M %p, %A, %B %d, %Y"):
        """Format datetime for given timezone"""
        tz = pytz.timezone(timezone)
        dt = dt.astimezone(tz)
        return dt.strftime(format_str).lstrip("0").replace(" 0", " ")

    def parse_date_offset(self, offset_str):
        """Parse date offset (e.g., 'in 2 days', 'next week')"""
        offset_str = offset_str.lower().strip()
        now = datetime.now(pytz.UTC)
        
        patterns = [
            (r"in\s+(\d+)\s+days?", lambda n: now + timedelta(days=int(n))),
            (r"in\s+(\d+)\s+weeks?", lambda n: now + timedelta(weeks=int(n))),
            (r"in\s+(\d+)\s+hours?", lambda n: now + timedelta(hours=int(n))),
            (r"next\s+week", lambda _: now + timedelta(weeks=1)),
            (r"tomorrow", lambda _: now + timedelta(days=1)),
            (r"(\d{1,2}/\d{1,2}/\d{4})", lambda d: datetime.strptime(d, "%m/%d/%Y").replace(tzinfo=pytz.UTC))
        ]
        
        for pattern, handler in patterns:
            match = re.match(pattern, offset_str, re.IGNORECASE)
            if match:
                try:
                    return handler(match.group(1) if match.group(1) else None)
                except ValueError:
                    return None
        return None

    def process(self, user_input, default_response):
        """Process user input for date and time commands"""
        user_id = self.bot.config["default_user_id"]
        user_timezone = self.get_user_timezone(user_id)

        # Command: !time [timezone]
        time_match = re.match(r"^!time(?:\s+in\s+([\w\s\/]+))?$", user_input, re.IGNORECASE)
        if time_match:
            timezone = time_match.group(1).strip() if time_match.group(1) else user_timezone
            try:
                tz = pytz.timezone(timezone)
                current_time = datetime.now(tz)
                return f"The current time in {timezone} is {self.format_datetime(current_time, timezone, '%I:%M %p')}."
            except pytz.exceptions.UnknownTimeZoneError:
                return f"Invalid timezone: {timezone}. Try 'America/New_York' or 'Europe/London'."

        # Command: !date [timezone]
        date_match = re.match(r"^!date(?:\s+in\s+([\w\s\/]+))?$", user_input, re.IGNORECASE)
        if date_match:
            timezone = date_match.group(1).strip() if date_match.group(1) else user_timezone
            try:
                tz = pytz.timezone(timezone)
                current_date = datetime.now(tz)
                return f"Today's date in {timezone} is {self.format_datetime(current_date, timezone, '%A, %B %d, %Y')}."
            except pytz.exceptions.UnknownTimeZoneError:
                return f"Invalid timezone: {timezone}. Try 'America/New_York' or 'Europe/London'."

        # Command: !settimezone <timezone>
        tz_match = re.match(r"^!settimezone\s+([\w\s\/]+)$", user_input, re.IGNORECASE)
        if tz_match:
            timezone = tz_match.group(1).strip()
            if self.set_user_timezone(user_id, timezone):
                return f"Timezone set to {timezone}."
            return f"Invalid timezone: {timezone}. Try 'America/New_York' or 'Europe/London'."

        # Command: !timeuntil <date or offset>
        until_match = re.match(r"^!timeuntil\s+(.+)$", user_input, re.IGNORECASE)
        if until_match:
            offset_str = until_match.group(1).strip()
            target_date = self.parse_date_offset(offset_str)
            if not target_date:
                return f"Invalid date format: {offset_str}. Try 'in 2 days', 'next week', or 'MM/DD/YYYY'."
            
            now = datetime.now(pytz.UTC)
            delta = target_date - now
            if delta.total_seconds() < 0:
                return f"The date {offset_str} is in the past."
                
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            response = f"Time until {offset_str}: "
            parts = []
            if days > 0:
                parts.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            return response + (", ".join(parts) or "less than a minute")

        # Command: !schedule <event> at <time> [on <date>] [in <timezone>]
        schedule_match = re.match(
            r"^!schedule\s+(.+?)\s+at\s+(\d{1,2}:\d{2}\s*(?:am|pm)?)(?:\s+on\s+(\d{1,2}/\d{1,2}/\d{4}))?(?:\s+in\s+([\w\s\/]+))?$",
            user_input, re.IGNORECASE
        )
        if schedule_match:
            event = schedule_match.group(1).strip()
            time_str = schedule_match.group(2).strip()
            date_str = schedule_match.group(3).strip() if schedule_match.group(3) else datetime.now().strftime("%m/%d/%Y")
            timezone = schedule_match.group(4).strip() if schedule_match.group(4) else user_timezone
            
            try:
                tz = pytz.timezone(timezone)
                naive_dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %I:%M %p")
                event_time_local = tz.localize(naive_dt)
                event_time_utc = event_time_local.astimezone(pytz.UTC)

                if database.add_event(user_id, event, event_time_utc.isoformat()):
                    return f"📅 Scheduled: {event} at {self.format_datetime(event_time_local, timezone, '%I:%M %p on %A, %B %d, %Y')}."
                else:
                    return "Sorry, there was an error saving your event."
            except (ValueError, pytz.exceptions.UnknownTimeZoneError) as e:
                return f"Error scheduling event: Invalid {('timezone' if isinstance(e, pytz.exceptions.UnknownTimeZoneError) else 'time or date')} format."

        # Command: !schedule list
        if user_input.lower() == "!schedule list":
            schedule = database.get_events(user_id)
            if not schedule:
                return "You have no upcoming scheduled events."
                
            response_lines = ["Your Upcoming Events:"]
            for i, event in enumerate(schedule):
                event_time = datetime.fromisoformat(event["event_time"]).astimezone(pytz.timezone(user_timezone))
                response_lines.append(f"{i + 1}. {event['event_text']} at {self.format_datetime(event_time, user_timezone, '%I:%M %p on %A, %B %d, %Y')}")
            return "\n".join(response_lines)

        # Legacy support for original queries
        if re.search(r"\bwhat time is it\b", user_input, re.IGNORECASE):
            current_time = datetime.now(pytz.timezone(user_timezone))
            return f"The current time in your timezone ({user_timezone}) is {self.format_datetime(current_time, user_timezone, '%I:%M %p')}."
        
        if re.search(r"\bwhat is the date\b", user_input, re.IGNORECASE):
            current_date = datetime.now(pytz.timezone(user_timezone))
            return f"Today's date in your timezone ({user_timezone}) is {self.format_datetime(current_date, user_timezone, '%A, %B %d, %Y')}."

        return None

    def on_load(self):
        """Called when plugin is loaded. Registers help and shared services."""
        # Register a shared service for other plugins to use
        self.bot.services['datetime'] = {
            'parse_date_offset': self.parse_date_offset
        }
        self.bot.command_registry.register(
            "datetime_help",
            lambda bot, args: (
                "Date & Time Plugin Commands:\n"
                "!time [in <timezone>] : Get current time\n"
                "!date [in <timezone>] : Get current date\n"
                "!settimezone <timezone> : Set your preferred timezone\n"
                "!timeuntil <date or offset> : Calculate time until a date\n"
                "!schedule <event> at <time> [on <MM/DD/YYYY>] [in <timezone>] : Schedule an event\n"
                "!schedule list : List scheduled events\n"
                "Examples:\n"
                "  !time in America/New_York\n"
                "  !timeuntil in 2 days\n"
                "  !schedule Meeting at 2:30 pm on 12/31/2025 in Europe/London\n"
                "  !settimezone Asia/Tokyo"
            ),
            "Show date and time plugin help"
        )

    def on_unload(self):
        """Called when plugin is unloaded"""
        pass