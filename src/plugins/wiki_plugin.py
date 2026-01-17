import re
import wikipediaapi
from datetime import datetime, timedelta
import json

class Plugin:
    metadata = {
        "name": "Wikipedia Summarizer",
        "version": "2.0",
        "description": "Fetches Wikipedia summaries, supports multiple languages, section queries, and disambiguation."
    }

    def __init__(self, bot):
        self.bot = bot
        self.default_language = "en"
        self.cache_duration = timedelta(hours=24)
        self.wiki_apis = {}  # Cache Wikipedia API instances by language

    def get_wiki_api(self, language):
        """Get or create Wikipedia API instance for a language"""
        if language not in self.wiki_apis:
            self.wiki_apis[language] = wikipediaapi.Wikipedia(
                f"AIChatBot/2.0 ({language})", language
            )
        return self.wiki_apis[language]

    def get_user_language(self, user_id):
        """Retrieve user's preferred language from memory"""
        user_data = self.bot.memory["knowledge"]["users"].get(user_id, {})
        return user_data.get("wiki_language", self.default_language)

    def set_user_language(self, user_id, language):
        """Set user's preferred Wikipedia language in memory"""
        user_data = self.bot.memory["knowledge"]["users"].setdefault(user_id, {})
        try:
            # Validate language by attempting to create API instance
            wikipediaapi.Wikipedia(f"AIChatBot/2.0 ({language})", language)
            user_data["wiki_language"] = language
            self.bot.save_memory()
            return True
        except Exception:
            return False

    def get_cached_result(self, user_id, query, language):
        """Check for cached result in memory"""
        user_data = self.bot.memory["knowledge"]["users"].get(user_id, {})
        cache = user_data.get("wiki_cache", {})
        cache_key = f"{language}:{query.lower()}"
        if cache_key in cache:
            entry = cache[cache_key]
            cache_time = datetime.fromisoformat(entry["timestamp"])
            if datetime.now() - cache_time < self.cache_duration:
                return entry["result"]
        return None

    def cache_result(self, user_id, query, language, result):
        """Cache result in memory"""
        user_data = self.bot.memory["knowledge"]["users"].setdefault(user_id, {})
        user_data.setdefault("wiki_cache", {})
        cache_key = f"{language}:{query.lower()}"
        user_data["wiki_cache"][cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        # Limit cache size
        if len(user_data["wiki_cache"]) > 50:
            oldest_key = min(user_data["wiki_cache"], key=lambda k: user_data["wiki_cache"][k]["timestamp"])
            del user_data["wiki_cache"][oldest_key]
        self.bot.save_memory()

    def process(self, user_input, default_response):
        """Process user input for Wikipedia-related commands"""
        user_id = self.bot.config["default_user_id"]
        user_language = self.get_user_language(user_id)
        user_input_lower = user_input.lower().strip()

        # Command: !wiki <query> [lang:<language>] [section:<section>]
        wiki_match = re.match(
            r"^!wiki\s+(.+?)(?:\s+lang:([\w-]+))?(?:\s+section:([\w\s]+))?$",
            user_input_lower
        )
        if wiki_match:
            query = wiki_match.group(1).strip()
            language = wiki_match.group(2) if wiki_match.group(2) else user_language
            section = wiki_match.group(3).strip() if wiki_match.group(3) else None

            # Check cache first
            cached_result = self.get_cached_result(user_id, query, language)
            if cached_result:
                return f"[Cached] {cached_result}"

            wiki_api = self.get_wiki_api(language)
            page = wiki_api.page(query)

            if not page.exists():
                # Try to handle disambiguation
                disambig_page = wiki_api.page(query + " (disambiguation)")
                if disambig_page.exists():
                    suggestions = [title for title in disambig_page.links.keys()][:5]
                    return (
                        f"No exact match for '{query}' in {language} Wikipedia. "
                        f"Did you mean one of these? {', '.join(suggestions)} "
                        "Try specifying one with !wiki <suggestion>."
                    )
                return f"Sorry, I couldn't find a Wikipedia page for '{query}' in {language} Wikipedia."

            # Get specific section or summary
            if section:
                section_data = page.section_by_title(section)
                if section_data:
                    content = section_data.text
                    # Limit to first 500 characters for brevity
                    content = content[:500] + ("..." if len(content) > 500 else "")
                    result = f"Section '{section}' of '{query}' ({language}):\n{content}"
                else:
                    return f"No section named '{section}' found in '{query}'."
            else:
                # Get first paragraph of summary
                summary_paragraph = page.summary.split('\n')[0]
                result = f"Summary for '{query}' ({language}):\n{summary_paragraph}"

            # Cache the result
            self.cache_result(user_id, query, language, result)
            return result

        # Command: !setwikilang <language>
        lang_match = re.match(r"^!setwikilang\s+([\w-]+)$", user_input_lower)
        if lang_match:
            language = lang_match.group(1)
            if self.set_user_language(user_id, language):
                return f"Wikipedia language set to {language}."
            return f"Invalid Wikipedia language: {language}. Try 'en', 'fr', 'de', etc."

        # Command: !wiki search <query>
        search_match = re.match(r"^!wiki search\s+(.+)$", user_input_lower)
        if search_match:
            query = search_match.group(1).strip()
            wiki_api = self.get_wiki_api(user_language)
            search_results = wiki_api.search(query, results=5)
            if not search_results:
                return f"No search results found for '{query}' in {user_language} Wikipedia."
            response_lines = [f"Search results for '{query}' ({user_language}):"]
            response_lines.extend([f"- {result}" for result in search_results])
            return "\n".join(response_lines)

        return None

    def on_load(self):
        """Called when plugin is loaded"""
        self.bot.command_registry.register(
            "wiki_help",
            lambda bot, args: (
                "Wikipedia Summarizer Plugin Commands:\n"
                "!wiki <query> [lang:<language>] [section:<section>] : Get a summary or specific section\n"
                "!setwikilang <language> : Set preferred Wikipedia language\n"
                "!wiki search <query> : Search Wikipedia for related pages\n"
                "Examples:\n"
                "  !wiki Python lang:fr section:History\n"
                "  !setwikilang de\n"
                "  !wiki search Machine learning"
            ),
            "Show Wikipedia plugin help"
        )

    def on_unload(self):
        """Called when plugin is unloaded"""
        pass