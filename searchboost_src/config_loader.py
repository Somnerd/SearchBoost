import json
import os 

class ConfigLoader:
    def __init__(self, config_name , logger=None):
        self.config_name = config_name
        self.config_path = f"configs/{self.config_name}.json"
        self.config = {}
        self.logger = logger
        self.defaults = {
            "local_ai": {"model": "llama3.2", "host": "localhost", "port": 11434},
            "web_search": {"search_engine": "searxng", "num_results": 5}
        }
        pass

    def load_config(self):
        try :
            self.logger.debug(f"Config Loader : Loading config for {self.config_name} from {self.config_path}")
            settings = self.defaults.get(self.config_name,{}).copy()

            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                    settings.update(self.config)

            else:
                self.logger.warning(f"Config file not found: {self.config_path}.Using Defaults.")

            self.logger.debug(f"Config Loader : Loaded settings for {self.config_name} : {settings}")
            return settings
        except Exception as e:
            self.logger.warning(f"Error in Config Loader :\t{e}")
            self.logger.warning(f"Using default settings for {self.config_name}.")
            return self.defaults.get(self.config_name,{})

