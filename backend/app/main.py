import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager

from alembic.config import Config as AlembicConfig
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


async def run_migrations() -> None:
    """Run pending Alembic migrations on startup (off the event loop)."""
    cfg = AlembicConfig("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    loop = asyncio.get_running_loop()

    def _upgrade():
        from alembic import command
        command.upgrade(cfg, "head")

    await loop.run_in_executor(None, _upgrade)
    logger.info("Database migrations complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations()
    yield
    await engine.dispose()


print("===== CORS DEBUG =====")
print("settings.CORS_ORIGINS =", settings.CORS_ORIGINS)
print("type =", type(settings.CORS_ORIGINS))
if isinstance(settings.CORS_ORIGINS, list):
    for i, o in enumerate(settings.CORS_ORIGINS):
        print(f"  [{i}] {o!r} (type={type(o).__name__})")
print("======================")

app = FastAPI(
    title="Draw The Imposter API",
    description="Backend for the Draw The Imposter game",
    version="1.0.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def debug_origin(request, call_next):
    origin = request.headers.get("origin")
    method = request.method
    path = request.url.path
    acrm = request.headers.get("access-control-request-method")
    acrh = request.headers.get("access-control-request-headers")

    print(f"[CORS] {method} {path}")
    print(f"  Origin: {origin}")
    print(f"  Access-Control-Request-Method: {acrm}")
    print(f"  Access-Control-Request-Headers: {acrh}")
    print(f"  Allowed origins: {settings.CORS_ORIGINS}")
    if origin and isinstance(settings.CORS_ORIGINS, list):
        print(f"  Origin matches allowed? {origin in settings.CORS_ORIGINS}")

    response = await call_next(request)
    print(f"  Response status: {response.status_code}")
    print(f"  Response ACAO: {response.headers.get('access-control-allow-origin')}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
