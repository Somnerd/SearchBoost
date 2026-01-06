import searchboost_src.logger

class ChatDetails:
    def __init__(self):
        self.model = "llama3.2"
        self.prompt = None
        self.system_prompt = None
        self.stream = True
        self.role = "user"
        self.port = 11434
        self.host = "localhost"
        self.host = f"http://{self.host}:{self.port}"
        # Thinking budget and web search are Poe-specific extra_body params
        self.extra_body = {
            "thinking_budget": 4096,
            "web_search": True
        }

    async def config_setup(self, config):
        self.model = config["model"]
        self.host = config["host"]
        self.port = config["port"]
        self.host = f"http://{self.host}:{self.port}"
        self.stream = config["stream"]
        self.role = config["role"]

    async def args_to_class(self, args):
        self.model = args.model
        self.prompt = args.query
        self.engine = args.engine
        self.stream = args.stream
