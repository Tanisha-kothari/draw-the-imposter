import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.game import Game
from app.models.round import Round


class GameRepository:
    async def create(self, **kwargs) -> Game:
        async with async_session_factory() as session:
            game = Game(**kwargs)
            session.add(game)
            await session.commit()
            await session.refresh(game)
            return game

    async def get_by_id(self, game_id: uuid.UUID) -> Game | None:
        async with async_session_factory() as session:
            return await session.get(Game, game_id)

    async def get_by_room(self, room_id: uuid.UUID) -> Game | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Game).where(Game.room_id == room_id).order_by(Game.started_at.desc()).limit(1)
            )
            return result.scalar_one_or_none()

    async def update_phase(self, game_id: uuid.UUID, phase: str) -> Game | None:
        async with async_session_factory() as session:
            game = await session.get(Game, game_id)
            if not game:
                return None
            game.current_phase = phase
            await session.commit()
            await session.refresh(game)
            return game

    async def update_round(self, game_id: uuid.UUID, round_num: int, word: str | None = None) -> Game | None:
        async with async_session_factory() as session:
            game = await session.get(Game, game_id)
            if not game:
                return None
            game.current_round = round_num
            if word is not None:
                game.word = word
            await session.commit()
            await session.refresh(game)
            return game

    async def set_word(self, game_id: uuid.UUID, word: str) -> Game | None:
        async with async_session_factory() as session:
            game = await session.get(Game, game_id)
            if not game:
                return None
            game.word = word
            await session.commit()
            await session.refresh(game)
            return game

    async def end_game(self, game_id: uuid.UUID) -> Game | None:
        async with async_session_factory() as session:
            game = await session.get(Game, game_id)
            if not game:
                return None
            game.current_phase = "game_over"
            game.ended_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(game)
            return game

    async def create_round(self, game_id: uuid.UUID, round_number: int, word: str, phase: str) -> Round:
        async with async_session_factory() as session:
            round_entry = Round(
                game_id=game_id, round_number=round_number, word=word, phase=phase,
                started_at=datetime.now(timezone.utc),
            )
            session.add(round_entry)
            await session.commit()
            await session.refresh(round_entry)
            return round_entry
