# core.py
import json
import os
import importlib
import glob
from datetime import datetime, timedelta
import logging
import traceback
import re
import time
import random
from collections import Counter
from events import MessageEmitter

# Import config from our new utils file
from utils import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class CommandRegistry:
    """Manages bot commands"""
    def __init__(self):
        self.commands = {}
    
    def register(self, name, handler, description="No description provided"):
        """Register a command with its handler and description"""
        self.commands[name] = {"handler": handler, "description": description}
    
    def get_help(self):
        """Generate help text for all commands"""
        return "\n".join([f"!{name}: {info['description']}" for name, info in self.commands.items()])
    
    def execute(self, command, args, bot):
        """Execute a command with arguments"""
        if command in self.commands:
            return self.commands[command]["handler"](bot, args)
        return "Unknown command"

class PluginManager:
    """Manages plugin loading and lifecycle"""
    def __init__(self, bot, plugin_dir):
        self.bot = bot
        self.plugin_dir = plugin_dir
        self.plugins = {}
    
    def load_plugins(self):
        """Load all plugins from plugin directory"""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
        
        plugin_files = glob.glob(f"{self.plugin_dir}/*.py")
        for plugin_file in plugin_files:
            plugin_name = os.path.basename(plugin_file).replace('.py', '')
            if plugin_name != "__init__":
                self.load_plugin(plugin_name)
    
    def load_plugin(self, plugin_name):
        """Load a single plugin"""
        try:
            # Invalidate caches to ensure reloading works correctly
            importlib.invalidate_caches()
            module_name = f"{self.plugin_dir}.{plugin_name}"
            # If the module is already loaded, reload it
            if module_name in locals():
                 module = importlib.reload(locals()[module_name])
            else:
                 module = importlib.import_module(module_name)
            
            plugin_class = getattr(module, 'Plugin', None)
            if plugin_class:
                plugin_instance = plugin_class(self.bot)
                self.plugins[plugin_name] = {
                    "instance": plugin_instance,
                    "metadata": getattr(plugin_instance, 'metadata', {"name": plugin_name, "version": "1.0", "description": "No description"})
                }
                if hasattr(plugin_instance, 'on_load'):
                    plugin_instance.on_load()
                logger.info(f"Loaded plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}\n{traceback.format_exc()}")
    
    def reload_plugins(self):
        """Reload all plugins"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)
        self.load_plugins()
    
    def unload_plugin(self, plugin_name):
        """Unload a single plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]["instance"]
            if hasattr(plugin, 'on_unload'):
                plugin.on_unload()
            del self.plugins[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
    
    def get_plugin_info(self):
        """Get information about loaded plugins"""
        return "\n".join([
            f"{meta['name']} (v{meta['version']}): {meta['description']}"
            for meta in [p["metadata"] for p in self.plugins.values()]
        ])

class AIChatBot:
    def __init__(self, config_file="config.json"):
        self.config = self.load_config(config_file)
        self.memory_file = self.config["memory_file"]
        self.plugin_dir = self.config["plugin_dir"]
        self.max_history = self.config["max_history"]
        self.history_days = self.config["history_days"]

        self.history_days = self.config["history_days"]
        self.emitter = MessageEmitter()

        # Add this line to create the services registry
        self.services = {}        

        self.memory = self.load_memory()
        self.command_registry = CommandRegistry()
        self.plugin_manager = PluginManager(self, self.plugin_dir)
        self.plugin_manager.load_plugins()
        self.register_default_commands()
        
        self.response_templates = {
            "like": ["Noted, you like to {0}!", "Cool, you enjoy {0}!", "Great, {0} sounds fun!"],
            "hobby": ["Cool, your hobby is {0}!", "Awesome, you love {0}!", "Nice, {0} is a great hobby!"],
            "love": ["Awesome, you love {0}!", "Sweet, {0} is on your love list!", "Great choice, you love {0}!"],
            "general": ["Got it, your {0} is {1}!", "Noted, {0} is set to {1}!", "Thanks, I saved your {0} as {1}!"],
            "negation_like": ["Okay, I removed {0} from your likes!", "Got it, {0} is no longer on your likes list!"],
            "negation_love": ["Okay, I removed {0} from your loves!", "Got it, {0} is off your loves list!"]
        }
    
    def load_config(self, config_file):
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return {**DEFAULT_CONFIG, **config}
            return DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Error loading config: {e}\n{traceback.format_exc()}")
            return DEFAULT_CONFIG
    
    def load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                    if not isinstance(memory, dict):
                        memory = {"conversations": [], "knowledge": {"users": {}}}
                    if "conversations" not in memory:
                        memory["conversations"] = []
                    if "knowledge" not in memory:
                        memory["knowledge"] = {"users": {}}
                    if "users" not in memory["knowledge"]:
                        memory["knowledge"]["users"] = {}
                    self.prune_memory(memory)
                    logger.info("Memory loaded successfully")
                    return memory
            logger.info("No memory file found, initializing new memory")
            return {"conversations": [], "knowledge": {"users": {}}}
        except Exception as e:
            logger.error(f"Error loading memory: {e}\n{traceback.format_exc()}")
            return {"conversations": [], "knowledge": {"users": {}}}
    
    def save_memory(self):
        try:
            self.prune_memory(self.memory)
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}\n{traceback.format_exc()}")
    
    def prune_memory(self, memory):
        cutoff_date = datetime.now() - timedelta(days=self.history_days)
        memory["conversations"] = [
            conv for conv in memory["conversations"]
            if datetime.fromisoformat(conv["timestamp"]) >= cutoff_date
        ][-self.max_history:]
    
    def register_default_commands(self):
        self.command_registry.register("help", lambda bot, args: bot.command_registry.get_help(), "Show available commands")
        self.command_registry.register("clear", lambda bot, args: bot.clear_memory(), "Clear conversation history")
        self.command_registry.register("plugins", lambda bot, args: bot.plugin_manager.get_plugin_info(), "List loaded plugins")
        self.command_registry.register("reload", lambda bot, args: bot.reload_plugins(), "Reload all plugins")
        self.command_registry.register("setname", self.set_user_name, "Set your nickname (e.g., !setname Alice)")
        self.command_registry.register("facts", self.list_facts, "List all known facts about you")
        self.command_registry.register("forget", self.forget_fact, "Forget a specific fact (e.g., !forget hobby)")
    
    def clear_memory(self):
        self.memory["conversations"] = []
        self.memory["knowledge"] = {"users": {}}
        self.save_memory()
        return "Conversation history cleared"
    
    def reload_plugins(self):
        self.plugin_manager.reload_plugins()
        return "Plugins reloaded"
    
    def set_user_name(self, args):
        if not args:
            return "Please provide a nickname (e.g., !setname Alice)"
        user_id = args[0]
        self.memory["knowledge"]["users"][user_id] = self.memory["knowledge"]["users"].get(user_id, {})
        self.memory["knowledge"]["users"][user_id]["name"] = user_id
        self.save_memory()
        return f"Name set to {user_id}"
    
    def list_facts(self, args, user_id=None):
        user_id = user_id or self.config["default_user_id"]
        user_info = self.memory["knowledge"].get("users", {}).get(user_id, {})
        if not user_info:
            return "I don't know anything about you yet! Tell me something, like your name or hobby."
        facts = []
        for key, value in user_info.items():
            if key == "likes" and value:
                facts.append(f"You like to {' and '.join(value)}.")
            elif key == "loves" and value:
                facts.append(f"You love {' and '.join(value)}.")
            elif key not in ["likes", "loves"] and value:
                facts.append(f"Your {key} is {value}.")
        return "\n".join(facts) if facts else "I don't know anything about you yet!"
    
    def forget_fact(self, args, user_id=None):
        user_id = user_id or self.config["default_user_id"]
        if not args:
            return "Please specify a fact to forget (e.g., !forget hobby)."
        fact_key = args[0].lower()
        user_info = self.memory["knowledge"].get("users", {}).get(user_id, {})
        if fact_key in user_info:
            del user_info[fact_key]
            self.save_memory()
            return f"Okay, I forgot your {fact_key}!"
        return f"I don't have a {fact_key} for you."

    def extract_knowledge(self, user_input, user_id):
        user_input_lower = user_input.lower().strip()
        self.memory["knowledge"]["users"][user_id] = self.memory["knowledge"]["users"].get(user_id, {})
        user_data = self.memory["knowledge"]["users"][user_id]
        knowledge_extractors = [
            {
                "name": "negation_like",
                "patterns": [r"i don\'t like to ([\w\s]+)", r"i don\'t like ([\w\s]+ing)", r"i no longer like to ([\w\s]+)", r"i no longer enjoy ([\w\s]+ing)", r"i stopped liking ([\w\s]+ing)"],
                "handler": lambda data, match: (data.get("likes", []).remove(match.group(1)) or random.choice(self.response_templates["negation_like"]).format(match.group(1))) if match.group(1) in data.get("likes", []) else f"I don't have {match.group(1)} in your likes."
            },
            {
                "name": "negation_love",
                "patterns": [r"i don\'t love ([\w\s]+)", r"i don\'t prefer ([\w\s]+)", r"i no longer love ([\w\s]+)", r"i stopped loving ([\w\s]+)"],
                "handler": lambda data, match: (data.get("loves", []).remove(match.group(1)) or random.choice(self.response_templates["negation_love"]).format(match.group(1))) if match.group(1) in data.get("loves", []) else f"I don't have {match.group(1)} in your loves."
            },
            {"name": "name", "patterns": [r"my name is ([\w\s]+)", r"i am ([\w\s]+)", r"call me ([\w\s]+)"], "handler": lambda data, match: (data.update({"name": match.group(1).title()}) or f"Got it, your name is {match.group(1).title()}! What's something you enjoy doing?")},
            {"name": "like", "patterns": [r"i like to ([\w\s]+)", r"i like ([\w\s]+ing)", r"i enjoy ([\w\s]+ing)"], "handler": lambda data, match: ((data.setdefault("likes", [])).append(match.group(1)) if match.group(1) not in data.get("likes", []) else None) or (random.choice(self.response_templates["like"]).format(match.group(1)) + " " + ("What else do you like to do?" if random.random() > 0.5 else f"Why do you enjoy {match.group(1)}?"))},
            {"name": "hobby", "patterns": [r"my hobby is ([\w\s]+)", r"my hobby is now ([\w\s]+)"], "handler": lambda data, match: (data.update({"hobby": match.group(1)}) or random.choice(self.response_templates["hobby"]).format(match.group(1)) + f" How did you get into {match.group(1)}?")},
            {"name": "love", "patterns": [r"i love ([\w\s]+)", r"i prefer ([\w\s]+)"], "handler": lambda data, match: ((data.setdefault("loves", [])).append(match.group(1).title()) if match.group(1).title() not in data.get("loves", []) else None) or (random.choice(self.response_templates["love"]).format(match.group(1).title()) + f" Tell me more about why you love {match.group(1).title()}!")},
            {"name": "general_fact", "patterns": [r"my (\w+) is ([\w\s]+)"], "handler": lambda data, match: (data.update({match.group(1): match.group(2).title()}) or random.choice(self.response_templates["general"]).format(match.group(1), match.group(2).title()) + f" Tell me more about your {match.group(1)}!") if match.group(1) not in ["name", "hobby", "likes", "loves"] else None}
        ]
        for extractor in knowledge_extractors:
            for pattern in extractor["patterns"]:
                match = re.match(pattern, user_input_lower)
                if match:
                    response = extractor["handler"](user_data, match)
                    if response:
                        self.save_memory()
                        return response
        return None
    
    def process_message(self, user_input, user_id=None):
        user_id = user_id or self.config["default_user_id"]
        timestamp = datetime.now().isoformat()
        self.memory["conversations"].append({"user_id": user_id, "input": user_input, "timestamp": timestamp})
        
        response = None
        try:
            # --- REFACTORED LOGIC START ---
            
            # 1. Give plugins the first chance to process ANY input.
            # This allows them to handle their own commands (e.g., !todo) or any other text.
            for plugin_name, plugin_data in self.plugin_manager.plugins.items():
                try:
                    plugin_response = plugin_data["instance"].process(user_input, None)
                    if plugin_response is not None:
                        response = plugin_response
                        break  # Stop after the first plugin handles the message
                except Exception as e:
                    logger.error(f"Plugin {plugin_name} error: {e}\n{traceback.format_exc()}")
            
            # 2. If no plugin handled it, check for core commands (if it's a command).
            if response is None and user_input.startswith("!"):
                cmd_parts = user_input[1:].split(maxsplit=1)
                command = cmd_parts[0].lower()
                args = cmd_parts[1].split() if len(cmd_parts) > 1 else []
                response = self.command_registry.execute(command, args, self)

            # 3. If still no response, fall back to knowledge and general conversation.
            if response is None:
                knowledge_response = self.extract_knowledge(user_input, user_id)
                if knowledge_response:
                    response = knowledge_response
                else:
                    response = self.generate_response(user_input, user_id)
            
            # --- REFACTORED LOGIC END ---

        except Exception as e:
            logger.error(f"Error generating response: {e}\n{traceback.format_exc()}")
            response = "Sorry, I encountered an error. Please try again."
        
        self.memory["conversations"].append({"user_id": "bot", "input": response, "timestamp": timestamp})
        self.save_memory()
        return response
    
    def generate_response(self, user_input, user_id):
        user_input_lower = user_input.lower().strip()
        user_info = self.memory["knowledge"].get("users", {}).get(user_id, {})
        name = user_info.get("name", "there")
        sentiment_responses = {
            "sad": f"I'm sorry to hear you're feeling down, {name}. Is there anything I can do to help?",
            "happy": f"That's wonderful to hear, {name}! What's making you so happy?",
            "tired": f"It sounds like you need a rest, {name}. Make sure to take a break and recharge."
        }
        intent_handlers = [
            {"name": "greeting", "pattern": r"^\b(hi|hello|hey)\b", "handler": lambda ui, m: f"Hello {name}! How can I help you today?" + (f" Thinking of doing some {ui.get('likes')[0]}?" if ui.get("likes") else "")},
            {"name": "status_check", "pattern": r"\bhow are you\b", "handler": lambda ui, m: f"I'm just a program, but I'm running perfectly! Thanks for asking, {name}." + (f" Are you planning any {ui.get('hobby')} projects soon?" if ui.get("hobby") else "")},
            {"name": "sentiment", "pattern": r"\b(sad|upset|down|happy|great|awesome|tired|exhausted)\b", "handler": lambda ui, m: sentiment_responses.get({"sad": "sad", "upset": "sad", "down": "sad", "happy": "happy", "great": "happy", "awesome": "happy", "tired": "tired", "exhausted": "tired"}.get(m.group(1)), f"I see you're feeling {m.group(1)}, {name}.")},
            {"name": "query_bot_name", "pattern": r"\bwhat is your name\b|\bwhat's your name\b", "handler": lambda ui, m: "You can call me Gemini. And you are " + (name if name != "there" else "...") + "?"},
            {"name": "query_user_name", "pattern": r"\bwhat is my name\b|\bwhat's my name\b", "handler": lambda ui, m: f"Your name is {name}." if name != "there" else "I don't know your name yet. What should I call you?"},
            {"name": "farewell", "pattern": r"^\b(bye|goodbye|see ya)\b", "handler": lambda ui, m: f"Goodbye, {name}! Talk to you later."}
        ]
        for intent in intent_handlers:
            match = re.search(intent["pattern"], user_input_lower)
            if match:
                return intent["handler"](user_info, match)
        if len(user_input_lower.split()) > 1 and not user_input_lower.endswith("?"):
            context = self.get_relevant_context(user_input, user_id)
            if context:
                return f"That reminds me of when you said: '{context}'. Can you tell me more?"
        default_responses = [
            f"That's an interesting point, {name}. Could you elaborate?",
            "I'm not sure I understand. Could you rephrase that?",
            f"Tell me more about that, {name}.",
            "How does that relate to your interests, like {}?".format(user_info.get('hobby') or 'your hobbies'),
        ]
        return random.choice(default_responses)
    
    def get_relevant_context(self, user_input, user_id):
        user_input_tokens = re.findall(r'\w+', user_input.lower())
        if len(user_input_tokens) < 2:
            return None
        input_tf = Counter(user_input_tokens)
        total_input_terms = sum(input_tf.values())
        best_match = None
        best_score = 0
        for conv in reversed(self.memory["conversations"][-10:]):
            if conv["user_id"] == user_id and conv["user_id"] != "bot":
                conv_tokens = re.findall(r'\w+', conv["input"].lower())
                conv_tf = Counter(conv_tokens)
                total_conv_terms = sum(conv_tf.values())
                score = 0
                for token in set(user_input_tokens) & set(conv_tokens):
                    score += min(input_tf[token] / total_input_terms, conv_tf[token] / total_conv_terms)
                if score > best_score and score > 0.7:
                    best_match = conv["input"]
                    best_score = score
        return best_match
    
    def create_plugin_template(self):
        plugin_code = """
class Plugin:
    metadata = {
        "name": "template",
        "version": "1.0",
        "description": "Template plugin"
    }
    
    def __init__(self, bot):
        self.bot = bot
    
    def on_load(self):
        pass
    
    def on_unload(self):
        pass
    
    def process(self, user_input, default_response):
        # Return None to keep default response
        # Return string to override response
        return None
"""
        os.makedirs(self.plugin_dir, exist_ok=True)
        with open(os.path.join(self.plugin_dir, "template.py"), "w") as f:
            f.write(plugin_code)