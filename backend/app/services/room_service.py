import random
import string

from app.models.room import Room
from app.repositories.room_repository import RoomRepository
from app.schemas.room import RoomCreate
from app.utils.game_state_machine import GamePhase


class RoomService:
    def __init__(self) -> None:
        self._repo = RoomRepository()

    @staticmethod
    def generate_room_code() -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    async def create_room(self, settings: RoomCreate) -> Room:
        for _ in range(10):
            code = self.generate_room_code()
            existing = await self._repo.get_by_code(code)
            if not existing:
                break
        else:
            raise RuntimeError("Could not generate unique room code after 10 attempts")

        room_name = settings.name or f"{settings.nickname}'s Room"
        room = await self._repo.create(
            code=code,
            name=room_name,
            max_players=settings.max_players,
            num_rounds=settings.num_rounds,
            drawing_time=settings.drawing_time,
            voting_time=settings.voting_time,
            num_imposters=settings.num_imposters,
        )
        return room

    async def join_room(self, code: str, nickname: str) -> Room:
        from app.models.player import Player
        from app.repositories.player_repository import PlayerRepository

        room = await self._repo.get_by_code(code)
        if not room:
            raise ValueError("Room not found")

        if room.status != "waiting":
            raise ValueError("Game already in progress")

        players = await PlayerRepository().get_by_room(room.id)
        if len(players) >= room.max_players:
            raise ValueError("Room is full")

        return room

    @staticmethod
    def validate_room_full(room: Room) -> bool:
        return len(room.players) >= room.max_players

    async def get_room_state(self, room_id: str) -> dict:
        import uuid
        from app.repositories.player_repository import PlayerRepository

        room = await self._repo.get_by_id(uuid.UUID(room_id) if isinstance(room_id, str) else room_id)
        if not room:
            raise ValueError("Room not found")

        player_repo = PlayerRepository()
        players = await player_repo.get_by_room(room.id)

        return {
            "id": str(room.id),
            "code": room.code,
            "name": room.name,
            "status": room.status,
            "max_players": room.max_players,
            "num_rounds": room.num_rounds,
            "drawing_time": room.drawing_time,
            "voting_time": room.voting_time,
            "num_imposters": room.num_imposters,
            "word_category": room.word_category,
            "difficulty": room.difficulty,
            "players": [
                {
                    "id": str(p.id),
                    "nickname": p.nickname,
                    "is_host": p.is_host,
                    "is_ready": p.is_ready,
                    "score": p.score,
                    "is_connected": p.is_connected,
                }
                for p in players
            ],
        }
