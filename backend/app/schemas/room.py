import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50)
    name: str | None = None
    max_players: int = Field(default=8, ge=2, le=16)
    num_rounds: int = Field(default=3, ge=1, le=10)
    drawing_time: int = Field(default=60, ge=15, le=300)
    voting_time: int = Field(default=30, ge=10, le=120)
    num_imposters: int = Field(default=1, ge=1, le=3)


class JoinRoom(BaseModel):
    code: str = Field(..., min_length=4, max_length=10)
    nickname: str = Field(..., min_length=1, max_length=50)


class RoomSettings(BaseModel):
    max_players: int = Field(default=8, ge=2, le=16)
    num_rounds: int = Field(default=3, ge=1, le=10)
    drawing_time: int = Field(default=60, ge=15, le=300)
    voting_time: int = Field(default=30, ge=10, le=120)
    num_imposters: int = Field(default=1, ge=1, le=3)
    word_category: str | None = None
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class RoomResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    max_players: int
    num_rounds: int
    drawing_time: int
    voting_time: int
    num_imposters: int
    word_category: str | None
    difficulty: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
