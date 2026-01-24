import searchboost_src.logger

class ChatDetails:
    def __init__(self,config,prompt):
        self.config = config
        self.prompt = prompt
        self.system_prompt = None
        self.host = self.config.base_url
        self.extra_body = {
            "thinking_budget": 4096,
            "web_search": True
        }
