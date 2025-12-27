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

    async def args_to_class(self, args):
        self.model = args.model
        self.prompt = args.query
        self.engine = args.engine