import json

from pydantic import BaseModel


class Message(BaseModel):
    ogmessage_id: int
    replymessage_jump_url: str
    replymessage_id: int
    author_id: int
    channel_id: int
    guild_id: int
    roundness: float | None
    labels_json: dict[str, float] | None

    @classmethod
    def select(cls) -> str:
        return "SELECT ogmessage_id,replymessage_jump_url,replymessage_id,author_id,channel_id,guild_id,roundness,labels_json FROM messages"

    @classmethod
    def from_row(cls, row: list) -> "Message":
        field_names = list(cls.model_fields.keys())
        data = dict(zip(field_names, row))
        data["labels_json"] = json.loads(data["labels_json"])
        return cls(**data)


class User(BaseModel):
    author_id: int
    author_nickname: str | None = None
    author_name: str

    @classmethod
    def select(cls) -> str:
        return "SELECT author_id, author_nickname, author_name FROM discordusers"
