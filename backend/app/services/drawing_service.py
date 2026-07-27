import uuid

from app.database.session import async_session_factory
from app.models.drawing import Drawing
from app.models.game import Game
from app.models.player import Player
from app.repositories.game_repository import GameRepository


class DrawingService:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_STROKE_SIZE = 1024 * 1024  # 1 MB

    def __init__(self) -> None:
        self._game_repo = GameRepository()

    async def save_drawing(
        self,
        game: Game,
        player: Player,
        round_num: int,
        image_data: str,
        stroke_data: dict | None = None,
    ) -> Drawing:
        async with async_session_factory() as session:
            drawing = Drawing(
                game_id=game.id,
                player_id=player.id,
                round_number=round_num,
                image_data=image_data,
                stroke_data=stroke_data,
            )
            session.add(drawing)
            await session.commit()
            await session.refresh(drawing)
            return drawing

    async def get_round_drawings(self, game_id: uuid.UUID, round_num: int) -> list[dict]:
        async with async_session_factory() as session:
            from sqlalchemy import select
            from app.models.player import Player

            result = await session.execute(
                select(Drawing).where(
                    Drawing.game_id == game_id,
                    Drawing.round_number == round_num,
                )
            )
            drawings = result.scalars().all()

            # Build a player-id → nickname map for lookups
            player_ids = [d.player_id for d in drawings]
            nicknames = {}
            if player_ids:
                player_result = await session.execute(
                    select(Player).where(Player.id.in_(player_ids))
                )
                for p in player_result.scalars().all():
                    nicknames[str(p.id)] = p.nickname

            return [
                {
                    "id": str(d.id),
                    "player_id": str(d.player_id),
                    "nickname": nicknames.get(str(d.player_id), "Unknown"),
                    "image_data": d.image_data,
                    "stroke_data": d.stroke_data,
                    "submitted_at": d.submitted_at.isoformat() if d.submitted_at else None,
                }
                for d in drawings
            ]

    @staticmethod
    def validate_drawing(data: dict) -> tuple[bool, str]:
        image_data = data.get("image_data", "")
        if len(image_data) > DrawingService.MAX_IMAGE_SIZE:
            return False, f"Image data exceeds {DrawingService.MAX_IMAGE_SIZE // (1024 * 1024)}MB limit"

        stroke_data = data.get("stroke_data")
        if stroke_data is not None:
            import json
            stroke_str = json.dumps(stroke_data)
            if len(stroke_str) > DrawingService.MAX_STROKE_SIZE:
                return False, f"Stroke data exceeds {DrawingService.MAX_STROKE_SIZE // (1024 * 1024)}MB limit"

        return True, ""
