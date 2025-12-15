class ChatDetails:
    def __init__(self, model, prompt,role="user"):
        self.model = model
        self.prompt = prompt
        self.role = role
        self.extra_body = {
            "thinking_budget": 4096,
            "web_search": True
        }


