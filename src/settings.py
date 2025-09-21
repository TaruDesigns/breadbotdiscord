from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Example fields based on typical .env.example contents
    debug: bool = False
    filter_bread_label_confidence: float = 0.5
    filter_bread_seg_confidence: float = 0.4
    bread_detection_confidence: float = 0.5
    override_detection_confidence: float = 0.1

    discord_token: str
    discord_bread_channels: list[int]
    discord_bread_role: list[int]

    db_data_path: Path = Path("dbdata/messages.db")
    downloads_path: Path = Path("downloads/")

    inference_service_url: str = "http://localhost:8001"

    model_config = SettingsConfigDict(env_prefix="__", env_file=".env")

    @field_validator("discord_bread_channels", "discord_bread_role", mode="before")
    def parse_list(cls, v):
        if isinstance(v, str):
            v = v.strip("[]")
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @field_validator("db_data_path", "downloads_path", mode="before")
    def parse_path(cls, v):
        return Path(v) if isinstance(v, str) else v


SETTINGS = Settings()
