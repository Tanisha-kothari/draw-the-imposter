import uuid

from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50)


class PlayerResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    score: int = 0
    is_ready: bool = False
    is_host: bool = False

    model_config = {"from_attributes": True}


class PlayerKick(BaseModel):
    player_id: uuid.UUID
