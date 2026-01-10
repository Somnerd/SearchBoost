import json
import os 
import aiofiles
import logging
from typing import Type, TypeVar, Dict, Any, TypeVar
from pydantic import BaseModel , Field
from pydantic_settings import BaseSettings , SettingsConfigDict

T = TypeVar("T", bound=BaseModel)

class AISettings(BaseModel):
    model: str = Field(default="llama3.2", description="LLM model to use for optimization and summarization")
    host: str = Field(default="localhost", description="Host for the LLM service")
    port: int = Field(default=11434, description="Port for the LLM service")
    stream: bool = Field(default=False, description="Enable streaming responses from the LLM")
    role: str = Field(default="user", description="Role for the chat messages")
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

class CloudAISettings(AISettings):
    model: str = Field(default="llama3.2", description="LLM model to use for optimization and summarization")
    provider: str = Field(default="poe.com/api/", description="Host for the LLM service")
    api: str = Field(default="", description="API key for the Cloud LLM service")

class SearchSettings(BaseModel):
    engine: str = Field(default="searxng", alias = "search_engine", description="Search engine domain to use")
    num_results: int = Field(default=5, description="Number of search results to retrieve")
    host : str = Field(default="localhost", description="Host for the web search service")
    port : int = Field(default=8080, description="Port for the web search service")
    language: str = Field(default="en-US", description="Language for the search results")
    safe_search: str = Field(default="1", description="Safe search level")
    region: str = Field(default="us", description="Region for the search results")
    format: str = Field(default="json", description="Format of the search results")
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

class RedisSettings(BaseModel):
    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, description="Redis server port")
    password: str = Field(default="searchboost_pass", description="Redis password")
    db: int = Field(default=0, description="Redis database index")
    decode_responses: bool = Field(default=True)

class Configurator(BaseSettings):

    default_ai_type: str = "local_ai"
    _REGISTRY: Dict[str, Type[BaseModel]] = {
        "local_ai": AISettings,
        "cloud_ai": CloudAISettings,
        "web_search": SearchSettings,
        "redis": RedisSettings
    }

    model_config = SettingsConfigDict(
        env_prefix="SEARCHBOOST_",
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore",
        populate_by_name=True,
    )

    def __init__(self,logger=None,**values):
        super().__init__(**values)
        self._logger = logger or logging.getLogger("logger")

    async def initialize(self,args) -> Dict:
        cli_data = vars(args) if args else {}
        ai_type = cli_data.get("type","local")
        ai_strategy = f"{ai_type}_ai"

        self._logger.info(f"Configurator: Resolving {ai_strategy} ,web_search and redis...")
        ai_settings = await self.get_settings(ai_strategy,cli_overrides=cli_data)
        search_settings = await self.get_settings("web_search",cli_overrides=cli_data)
        redis_settings = await self.get_settings("redis",cli_overrides=cli_data)
        return {
            "ai" : ai_settings,
            "search" : search_settings,
            "redis" : redis_settings
        }

    async def get_settings(self, config_name: str,cli_overrides: dict = None) -> Any:

        model_cls = self._REGISTRY.get(config_name)
        if not model_cls:
            self._logger.error(f"Configurator: Unknown config name '{config_name}'")
            raise ValueError(f"Unknown config: {config_name}")

        file_data = await self._load_json_file(config_name)
        final_data = {**file_data, **(cli_overrides or {})}

        try:
            settings_obj = model_cls(**final_data)
            self._logger.debug(f"Configurator: Loaded {config_name} settings.")
            return settings_obj
        except Exception as e:
            self._logger.warning(f"Configurator: Validation failed for {config_name}: {e}. Using defaults.")
            return model_cls()

    async def _load_json_file(self, filename: str) -> dict:
        filepath = f"configs/{filename}.json"
        try:
            if os.path.exists(filepath):
                async with aiofiles.open(filepath, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            else:
                self._logger.warning(f"Config Loader : Config file not found: {filepath}. Using Defaults.")
                return {}
        except Exception as e:
            self._logger.warning(f"Config Loader : Error loading config file {filepath} : {e}")
            return {}
