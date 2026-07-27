import uuid
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class BaseWSMessage(BaseModel):
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class JoinRoomMessage(BaseWSMessage):
    type: Literal["join_room"] = "join_room"
    data: Dict[str, Any]


class LeaveRoomMessage(BaseWSMessage):
    type: Literal["leave_room"] = "leave_room"


class ReadyMessage(BaseWSMessage):
    type: Literal["ready"] = "ready"
    data: Dict[str, Any]


class StartGameMessage(BaseWSMessage):
    type: Literal["start_game"] = "start_game"


class DrawingUpdate(BaseWSMessage):
    type: Literal["drawing_update"] = "drawing_update"
    data: Dict[str, Any]


class DrawingSubmit(BaseWSMessage):
    type: Literal["drawing_submit"] = "drawing_submit"
    data: Dict[str, Any]


class VoteSubmit(BaseWSMessage):
    type: Literal["vote_submit"] = "vote_submit"
    data: Dict[str, Any]


class ChatMessage(BaseWSMessage):
    type: Literal["chat_message"] = "chat_message"
    data: Dict[str, Any]


class GameStateUpdate(BaseWSMessage):
    type: Literal["game_state_update"] = "game_state_update"
    data: Dict[str, Any]


class TimerSync(BaseWSMessage):
    type: Literal["timer_sync"] = "timer_sync"
    data: Dict[str, Any]


class PlayerJoined(BaseWSMessage):
    type: Literal["player_joined"] = "player_joined"
    data: Dict[str, Any]


class PlayerLeft(BaseWSMessage):
    type: Literal["player_left"] = "player_left"
    data: Dict[str, Any]


class RoundResult(BaseWSMessage):
    type: Literal["round_result"] = "round_result"
    data: Dict[str, Any]


class GameOver(BaseWSMessage):
    type: Literal["game_over"] = "game_over"
    data: Dict[str, Any]


class RevealDrawings(BaseWSMessage):
    type: Literal["reveal_drawings"] = "reveal_drawings"
    data: Dict[str, Any]
