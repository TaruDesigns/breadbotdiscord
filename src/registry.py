from db.service import DBService
from discordclient.service import DiscordBot
from inference.predict import InferenceClient
from settings import SETTINGS


class Registry:
    def __init__(self) -> None:
        self.settings = SETTINGS
        self.db = DBService(str(self.settings.db_data_path))
        self.inference = InferenceClient(self.settings.inference_service_url)
        self.bot = DiscordBot(self.db, self.inference)


REGISTRY = Registry()
