class Chat_Details:
    def __init__(self, model, prompt):
        self.model = model
        self.prompt = prompt
        self.role = "user"
        self.extra_body = {
            "thinking_budget": 4096,
            "web_search": True
        }


