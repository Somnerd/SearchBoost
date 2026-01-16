import json , logging , os , aiofiles
from typing import Type, Dict, Any, TypeVar , Optional
from pydantic import BaseModel , Field
from pydantic_settings import BaseSettings , SettingsConfigDict

T = TypeVar("T", bound=BaseModel)

class AISettings(BaseModel):
    model: str = Field(default="llama3.2", description="LLM model to use for optimization and summarization")
    host: str = Field(default="sb_ollama", description="Host for the LLM service")
    port: int = Field(default=11434, description="Port for the LLM service")
    stream: bool = Field(default=False, description="Enable streaming responses from the LLM")
    role: str = Field(default="user", description="Role for the chat messages")
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

class CloudAISettings(AISettings):
    #model: str = Field(default="llama3.2", description="LLM model to use for optimization and summarization")
    provider: str = Field(default="poe.com/api/", description="Host for the LLM service")
    api: str = Field(default="", description="API key for the Cloud LLM service")

class SearchSettings(BaseModel):
    engine: str = Field(default="searxng", alias = "search_engine", description="Search engine domain to use")
    num_results: int = Field(default=5, description="Number of search results to retrieve")
    host : str = Field(default="sb_searxng", description="Host for the web search service")
    port : int = Field(default=8080, description="Port for the web search service")
    language: str = Field(default="en-US", description="Language for the search results")
    safe_search: str = Field(default="1", description="Safe search level")
    region: str = Field(default="us", description="Region for the search results")
    format: str = Field(default="json", description="Format of the search results")
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

class RedisSettings(BaseModel):
    host: str = Field(default="sb_redis", description="Redis server host")
    port: int = Field(default=6379, description="Redis server port")
    password: str = Field(default="searchboost_pass", description="Redis password")
    # db: int = Field(default=0, description="Redis database index")
    # decode_responses: bool = Field(default=True)

    @property
    def arq_settings(self) -> Any:
        from arq.connections import RedisSettings as ArqRedisSettings
        return ArqRedisSettings(host=self.host, port=self.port , password=self.password)

class Configurator(BaseSettings):
    _REGISTRY: Dict[str, Type[BaseModel]] = {
        "local_ai": AISettings,
        "cloud_ai": CloudAISettings,
        "web_search": SearchSettings,
        "redis": RedisSettings
    }

    # These are the nested models Pydantic will populate from SEARCHBOOST_AI_HOST etc.
    ai: AISettings = Field(default_factory=AISettings)
    search: SearchSettings = Field(default_factory=SearchSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)

    model_config = SettingsConfigDict(
        env_prefix="SEARCHBOOST_",
        env_nested_delimiter="_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        env_priority=2,
    )

    def __init__(self, logger=None, **values):
        super().__init__(**values)
        self._logger = logger or logging.getLogger("logger")

    async def initialize(self, args) -> Dict:
        cli_data = vars(args) if args else {}
        ai_type = cli_data.get("type", "local")
        ai_strategy = f"{ai_type}_ai"

        self._logger.info(f"Configurator: Resolving {ai_strategy}, web_search and redis...")

        # Load each component via get_settings to handle merge logic
        ai_settings = await self.get_settings(ai_strategy, cli_overrides=cli_data)
        search_settings = await self.get_settings("web_search", cli_overrides=cli_data)
        redis_settings = await self.get_settings("redis", cli_overrides=cli_data)

        return {
            "ai": ai_settings,
            "search": search_settings,
            "redis": redis_settings
        }

    async def get_settings(self, config_name: str, cli_overrides: dict = None) -> Any:
        model_cls = self._REGISTRY.get(config_name)
        if not model_cls:
            raise ValueError(f"Unknown config: {config_name}")

        # 1. Map config_name to the prefix used in ENV vars
        prefix_map = {
            "local_ai": "AI",
            "cloud_ai": "AI",
            "web_search": "SEARCH",
            "redis": "REDIS"
        }
        prefix = prefix_map.get(config_name)

        # 2. MANUAL ENV OVERRIDE (The "I'm not asking" approach)
        # We manually check the OS environment for the specific keys
        # because Pydantic nesting is clearly failing here.
        manual_env_data = {}
        for field_name in model_cls.model_fields.keys():
            env_key = f"SEARCHBOOST_{prefix}_{field_name.upper()}"
            env_val = os.getenv(env_key)
            if env_val:
                manual_env_data[field_name] = env_val

        # 3. Get existing data from Pydantic's internal state
        attr_map = {"local_ai": "ai", "cloud_ai": "ai", "web_search": "search", "redis": "redis"}
        env_instance = getattr(self, attr_map.get(config_name))
        base_data = env_instance.model_dump()

        # 4. Filter CLI overrides
        allowed_keys = model_cls.model_fields.keys()
        filtered_cli = {k: v for k, v in (cli_overrides or {}).items() if k in allowed_keys}

        # 5. Merge Order: Base < Manual Env < CLI
        # Manual Env is specifically added here to fix the 127.0.0.1 bug
        final_data = {**base_data, **manual_env_data, **filtered_cli}

        try:
            settings_obj = model_cls(**final_data)
            self._logger.debug(f"DEBUG: {config_name} resolved host -> {getattr(settings_obj, 'host', 'N/A')}")
            return settings_obj
        except Exception as e:
            self._logger.error(f"Configurator: Resolution failed for {config_name}: {e}")
            return model_cls()

    async def _load_json_file(self, filename: str) -> dict:
        filepath = f"configs/{filename}.json"
        try:
            if os.path.exists(filepath):
                async with aiofiles.open(filepath, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return {}
        except Exception as e:
            self._logger.warning(f"Config Loader: Error reading {filepath}: {e}")
            return {}

_instance = None

def get_configurator(logger=None) -> Configurator :
    global _instance

    if _instance == None :
        _instance = Configurator(logger=logger)
    return _instance