import uuid

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.vote import Vote


class VoteRepository:
    async def get_by_game(self, game_id: uuid.UUID) -> list[Vote]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Vote).where(Vote.game_id == game_id)
            )
            return list(result.scalars().all())

    async def get_by_round(self, game_id: uuid.UUID, round_number: int) -> list[Vote]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Vote).where(
                    Vote.game_id == game_id,
                    Vote.round_number == round_number,
                )
            )
            return list(result.scalars().all())

    async def get_by_voter(self, game_id: uuid.UUID, voter_id: uuid.UUID, round_number: int) -> Vote | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Vote).where(
                    Vote.game_id == game_id,
                    Vote.voter_id == voter_id,
                    Vote.round_number == round_number,
                )
            )
            return result.scalar_one_or_none()
