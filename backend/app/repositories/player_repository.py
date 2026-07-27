import uuid

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.player import Player


class PlayerRepository:
    async def create(self, **kwargs) -> Player:
        async with async_session_factory() as session:
            player = Player(**kwargs)
            session.add(player)
            await session.commit()
            await session.refresh(player)
            return player

    async def get_by_id(self, player_id: uuid.UUID) -> Player | None:
        async with async_session_factory() as session:
            return await session.get(Player, player_id)

    async def get_by_room(self, room_id: uuid.UUID) -> list[Player]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Player).where(Player.room_id == room_id).order_by(Player.created_at)
            )
            return list(result.scalars().all())

    async def get_connected_by_room(self, room_id: uuid.UUID) -> list[Player]:
        """Return only connected players in a room."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Player)
                .where(Player.room_id == room_id, Player.is_connected == True)
                .order_by(Player.created_at)
            )
            return list(result.scalars().all())

    async def update_ready(self, player_id: uuid.UUID, is_ready: bool) -> Player | None:
        async with async_session_factory() as session:
            player = await session.get(Player, player_id)
            if not player:
                return None
            player.is_ready = is_ready
            await session.commit()
            await session.refresh(player)
            return player

    async def update_role(self, player_id: uuid.UUID, role: str, is_imposter: bool) -> Player | None:
        async with async_session_factory() as session:
            player = await session.get(Player, player_id)
            if not player:
                return None
            player.role = role
            player.is_imposter = is_imposter
            await session.commit()
            await session.refresh(player)
            return player

    async def update_score(self, player_id: uuid.UUID, score: int) -> Player | None:
        async with async_session_factory() as session:
            player = await session.get(Player, player_id)
            if not player:
                return None
            player.score = score
            await session.commit()
            await session.refresh(player)
            return player

    async def transfer_host(self, room_id: uuid.UUID, new_host_id: uuid.UUID) -> Player | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Player).where(Player.room_id == room_id, Player.is_host == True)
            )
            old_host = result.scalar_one_or_none()
            if old_host:
                old_host.is_host = False

            new_host = await session.get(Player, new_host_id)
            if not new_host:
                return None
            new_host.is_host = True
            await session.commit()
            await session.refresh(new_host)
            return new_host

    async def set_connected(self, player_id: uuid.UUID, is_connected: bool) -> Player | None:
        async with async_session_factory() as session:
            player = await session.get(Player, player_id)
            if not player:
                return None
            player.is_connected = is_connected
            await session.commit()
            await session.refresh(player)
            return player

    async def get_by_room_and_nickname(self, room_id: uuid.UUID, nickname: str) -> Player | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Player).where(
                    Player.room_id == room_id,
                    Player.nickname == nickname,
                )
            )
            return result.scalar_one_or_none()

    async def kick(self, player_id: uuid.UUID) -> bool:
        async with async_session_factory() as session:
            player = await session.get(Player, player_id)
            if not player:
                return False
            await session.delete(player)
            await session.commit()
            return True
