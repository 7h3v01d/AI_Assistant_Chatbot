
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
