import uuid

from pydantic import BaseModel, Field


class PlayerState(BaseModel):
    id: uuid.UUID
    nickname: str
    score: int = 0
    is_ready: bool = False
    is_host: bool = False
    is_imposter: bool = False


class GameState(BaseModel):
    phase: str
    round: int = 0
    word_hint: str | None = None
    time_remaining: int = 0
    players: list[PlayerState] = []


class VoteSubmission(BaseModel):
    target_player_id: uuid.UUID


class DrawingSubmission(BaseModel):
    image_data: str = Field(..., description="Base64-encoded PNG image")
    stroke_data: dict | None = None
