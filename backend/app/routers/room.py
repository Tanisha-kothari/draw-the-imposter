import uuid
import logging
from fastapi import APIRouter, HTTPException, Query

from app.repositories.player_repository import PlayerRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.player import PlayerKick, PlayerResponse
from app.schemas.room import JoinRoom, RoomCreate, RoomResponse, RoomSettings
from app.services.room_service import RoomService
from app.state import manager
from app.utils.room_serializer import serialize_room

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

_room_service = RoomService()
_room_repo = RoomRepository()
_player_repo = PlayerRepository()


async def _broadcast_room(room_code: str) -> None:
    """Fetch the latest room state from DB and broadcast to all connected clients."""
    room = await _room_repo.get_by_code(room_code)
    if not room:
        return
    players = await _player_repo.get_by_room(room.id)
    room_data = serialize_room(room, players)
    logger.info("[BROADCAST] Room %s - %d players - broadcasting room_updated",
                room_code, len(players))
    await manager.broadcast_to_room(room_code, {
        "type": "room_updated",
        "data": room_data,
    })


@router.post("", response_model=dict)
async def create_room(body: RoomCreate) -> dict:
    try:
        room = await _room_service.create_room(body)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    player = await _player_repo.create(
        room_id=room.id,
        nickname=body.nickname,
        is_host=True,
    )
    return {
        "code": room.code,
        "room_name": room.name,
        "room_id": str(room.id),
        "player_id": str(player.id),
        "is_host": True,
        "settings": {
            "max_players": room.max_players,
            "num_rounds": room.num_rounds,
            "drawing_time": room.drawing_time,
            "voting_time": room.voting_time,
            "num_imposters": room.num_imposters,
            "word_category": room.word_category,
            "difficulty": room.difficulty,
        },
    }


@router.post("/join")
async def join_room(body: JoinRoom) -> dict:
    try:
        room = await _room_service.join_room(body.code, body.nickname)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing = await _player_repo.get_by_room_and_nickname(room.id, body.nickname)
    if existing:
        raise HTTPException(status_code=409, detail="Nickname already taken in this room")

    player = await _player_repo.create(
        room_id=room.id,
        nickname=body.nickname,
        is_host=False,
    )

    logger.info("[JOIN] Player %s (%s) joined room %s - broadcasting to existing players",
                body.nickname, player.id, body.code)

    await _broadcast_room(body.code)

    return {
        "code": room.code,
        "room_name": room.name,
        "room_id": str(room.id),
        "player_id": str(player.id),
        "is_host": player.is_host,
        "settings": {
            "max_players": room.max_players,
            "num_rounds": room.num_rounds,
            "drawing_time": room.drawing_time,
            "voting_time": room.voting_time,
            "num_imposters": room.num_imposters,
            "word_category": room.word_category,
            "difficulty": room.difficulty,
        },
    }


@router.get("/{code}")
async def get_room(code: str) -> dict:
    room = await _room_repo.get_by_code(code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    players = await _player_repo.get_by_room(room.id)
    return serialize_room(room, players)


@router.put("/{code}/settings")
async def update_room_settings(code: str, body: RoomSettings, player_id: str = Query(...)) -> dict:
    room = await _room_repo.get_by_code(code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    player = await _player_repo.get_by_id(uuid.UUID(player_id))
    if not player or not player.is_host:
        raise HTTPException(status_code=403, detail="Only the host can update settings")

    await _room_repo.update_settings(
        room.id,
        max_players=body.max_players,
        num_rounds=body.num_rounds,
        drawing_time=body.drawing_time,
        voting_time=body.voting_time,
        num_imposters=body.num_imposters,
        word_category=body.word_category,
        difficulty=body.difficulty,
    )

    await _broadcast_room(code)
    return {"success": True}


@router.post("/{code}/kick")
async def kick_player(code: str, body: PlayerKick, player_id: str = Query(...)) -> dict:
    room = await _room_repo.get_by_code(code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    requester = await _player_repo.get_by_id(uuid.UUID(player_id))
    if not requester or not requester.is_host:
        raise HTTPException(status_code=403, detail="Only the host can kick players")

    success = await _player_repo.kick(body.player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Player not found")

    manager.disconnect(code, str(body.player_id))

    await _broadcast_room(code)
    await manager.send_to_player(code, str(body.player_id), {
        "type": "kick",
        "data": {"message": "You were kicked from the room"},
    })
    return {"success": True}


@router.delete("/{code}")
async def delete_room(code: str, player_id: str = Query(...)) -> dict:
    room = await _room_repo.get_by_code(code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    requester = await _player_repo.get_by_id(uuid.UUID(player_id))
    if not requester or not requester.is_host:
        raise HTTPException(status_code=403, detail="Only the host can delete the room")

    await _room_repo.delete(room.id)
    await manager.disconnect_all(code)
    return {"success": True}
