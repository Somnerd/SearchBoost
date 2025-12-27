class ChatDetails:
    def __init__(self):
        self.model = "local"
        self.prompt = None
        self.role = "user"
        self.engine = {"import json"}
        # Thinking budget and web search are Poe-specific extra_body params
        self.extra_body = {
            "thinking_budget": 4096,
            "web_search": True
        }
