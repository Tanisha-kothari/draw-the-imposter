import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by room and player."""

    def __init__(self) -> None:
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, room_code: str, player_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = {}
        # Close any stale socket for the same player BEFORE overwriting
        existing = self.active_connections[room_code].get(player_id)
        if existing and existing is not websocket:
            try:
                await existing.close(code=1000)
            except Exception:
                pass
        self.active_connections[room_code][player_id] = websocket
        logger.info("Player %s connected to room %s", player_id, room_code)

    def disconnect(self, room_code: str, player_id: str, websocket: WebSocket | None = None) -> bool:
        """Remove a player's WebSocket from the room.
        
        If *websocket* is provided, only removes if it is still the stored
        reference.  Returns True if the entry was actually removed, False if
        it was already replaced by a newer connection.
        """
        if room_code in self.active_connections:
            stored = self.active_connections[room_code].get(player_id)
            # If a specific socket was passed and it's NOT the stored one,
            # a newer connection already replaced it — do nothing.
            if websocket is not None and stored is not websocket:
                return False
            self.active_connections[room_code].pop(player_id, None)
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]
        logger.info("Player %s disconnected from room %s", player_id, room_code)
        return True

    async def send_to_player(self, room_code: str, player_id: str, message: dict[str, Any]) -> None:
        if room_code not in self.active_connections:
            return
        ws = self.active_connections[room_code].get(player_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room_code, player_id, websocket=ws)

    async def broadcast_to_room(
        self, room_code: str, message: dict[str, Any], exclude: list[str] | None = None
    ) -> None:
        if room_code not in self.active_connections:
            return
        exclude = exclude or []
        for pid, ws in list(self.active_connections[room_code].items()):
            if pid in exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room_code, pid, websocket=ws)

    def get_room_connections(self, room_code: str) -> list[str]:
        if room_code not in self.active_connections:
            return []
        return list(self.active_connections[room_code].keys())

    async def disconnect_all(self, room_code: str) -> None:
        if room_code not in self.active_connections:
            return
        for pid, ws in list(self.active_connections[room_code].items()):
            try:
                await ws.close()
            except Exception:
                pass
        del self.active_connections[room_code]
        logger.info("All connections cleaned up for room %s", room_code)
