import uuid
from app.models.room import Room
from app.models.player import Player


def serialize_room(room: Room, players: list[Player]) -> dict:
    return {
        "id": str(room.id),
        "code": room.code,
        "name": room.name,
        "host_id": _find_host_id(players),
        "status": room.status,
        "settings": {
            "max_players": room.max_players,
            "num_rounds": room.num_rounds,
            "drawing_time": room.drawing_time,
            "voting_time": room.voting_time,
            "num_imposters": room.num_imposters,
            "word_category": room.word_category,
            "difficulty": room.difficulty,
        },
        "players": [
            {
                "id": str(p.id),
                "nickname": p.nickname,
                "is_host": p.is_host,
                "is_ready": p.is_ready,
                "score": p.score,
                "is_connected": p.is_connected,
                "is_imposter": p.is_imposter,
            }
            for p in players
        ],
    }


def _find_host_id(players: list[Player]) -> str | None:
    for p in players:
        if p.is_host:
            return str(p.id)
    return None
