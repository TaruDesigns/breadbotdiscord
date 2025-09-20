
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Example fields based on typical .env.example contents
    debug: bool = False
    filter_bread_label_confidence: float = 0.5
    filter_bread_seg_confidence: float = 0.4
    bread_detection_confidence: float = 0.5
    override_detection_confidence: float = 0.1

    model_config = SettingsConfigDict(env_prefix="__", env_file=".env")


SETTINGS = Settings()
