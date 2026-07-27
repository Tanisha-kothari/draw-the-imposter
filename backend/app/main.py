import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.base import Base
from app.database.session import engine
from app.routers.health import router as health_router
from app.routers.room import router as room_router
from app.state import manager, handler
from app.repositories.player_repository import PlayerRepository
from app.repositories.room_repository import RoomRepository
from app.utils.room_serializer import serialize_room

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    yield
    await engine.dispose()


app = FastAPI(
    title="Draw The Imposter API",
    description="Backend for the Draw The Imposter game",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(room_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Draw The Imposter API"}


@app.websocket("/ws/{room_code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_id: str) -> None:
    try:
        player_uuid = uuid.UUID(player_id)
    except ValueError:
        logger.error("[WS] Invalid player_id UUID: %s", player_id)
        await websocket.close(code=1008, reason="Invalid player ID")
        return

    await manager.connect(room_code, player_id, websocket)
    _room_repo = RoomRepository()
    _player_repo = PlayerRepository()

    try:
        room = await _room_repo.get_by_code(room_code)
        if room:
            await _player_repo.set_connected(player_uuid, True)
            players = await _player_repo.get_by_room(room.id)
            room_data = serialize_room(room, players)
            logger.info("[SYNC] Player %s connected to room %s, broadcasting state to %d players",
                         player_id, room_code, len(players))
            await manager.broadcast_to_room(room_code, {
                "type": "room_updated",
                "data": room_data,
            })
    except Exception as e:
        logger.error("[WS] Initialization error for %s in %s: %s", player_id, room_code, e)
        manager.disconnect(room_code, player_id)
        await websocket.close(code=1011, reason="Internal server error")
        return

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            if message.get("type") != "ping":
                await handler.handle_message(room_code, player_id, message)
    except WebSocketDisconnect:
        logger.info("[WS] Disconnected: %s in %s", player_id, room_code)
        await handler.handle_disconnect(room_code, player_id, None, websocket=websocket)
    except Exception as e:
        logger.error("[WS] Error for %s in %s: %s", player_id, room_code, e)
        await handler.handle_disconnect(room_code, player_id, None, websocket=websocket)
