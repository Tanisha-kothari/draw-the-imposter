import uuid
from collections import Counter

from app.database.session import async_session_factory
from app.models.game import Game
from app.models.player import Player
from app.models.vote import Vote
from app.repositories.game_repository import GameRepository
from app.repositories.player_repository import PlayerRepository


class VoteService:
    def __init__(self) -> None:
        self._game_repo = GameRepository()
        self._player_repo = PlayerRepository()

    async def submit_vote(self, game: Game, voter: Player, target_id: uuid.UUID) -> Vote:
        async with async_session_factory() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Vote).where(
                    Vote.game_id == game.id,
                    Vote.voter_id == voter.id,
                    Vote.round_number == game.current_round,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError("Player has already voted this round")

            target = await session.get(Player, target_id)
            if not target:
                raise ValueError("Target player not found")

            vote = Vote(
                game_id=game.id,
                voter_id=voter.id,
                target_id=target_id,
                round_number=game.current_round,
            )
            session.add(vote)
            await session.commit()
            await session.refresh(vote)
            return vote

    async def get_vote_results(self, game_id: uuid.UUID) -> dict:
        async with async_session_factory() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Vote).where(Vote.game_id == game_id)
            )
            votes = result.scalars().all()

        target_counts: dict[str, int] = {}
        for vote in votes:
            pid = str(vote.target_id)
            target_counts[pid] = target_counts.get(pid, 0) + 1

        max_votes = max(target_counts.values()) if target_counts else 0
        most_voted = [pid for pid, count in target_counts.items() if count == max_votes]

        return {
            "vote_counts": target_counts,
            "total_votes": len(votes),
            "most_voted": most_voted,
            "max_votes": max_votes,
        }

    async def has_everyone_voted(self, game_id: uuid.UUID) -> bool:
        from sqlalchemy import select

        game = await self._game_repo.get_by_id(game_id)
        if not game:
            return False

        players = await self._player_repo.get_by_room(game.room_id)

        async with async_session_factory() as session:
            result = await session.execute(
                select(Vote).where(
                    Vote.game_id == game.id,
                    Vote.round_number == game.current_round,
                )
            )
            votes = result.scalars().all()

        voted_ids = {str(v.voter_id) for v in votes}
        active_players = [p for p in players if p.is_connected]

        return len(voted_ids) >= len(active_players)

    async def get_current_round_vote_count(self, game_id: uuid.UUID) -> int:
        """Return number of unique voters who have voted in the current round."""
        from sqlalchemy import select, func

        game = await self._game_repo.get_by_id(game_id)
        if not game:
            return 0

        async with async_session_factory() as session:
            result = await session.execute(
                select(func.count(Vote.voter_id.distinct())).where(
                    Vote.game_id == game.id,
                    Vote.round_number == game.current_round,
                )
            )
            return result.scalar() or 0

    async def get_active_player_count(self, game_id: uuid.UUID) -> int:
        """Return number of connected players in the game's room."""
        game = await self._game_repo.get_by_id(game_id)
        if not game:
            return 0
        players = await self._player_repo.get_by_room(game.room_id)
        return len([p for p in players if p.is_connected])
