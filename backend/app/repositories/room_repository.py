import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import async_session_factory
from app.models.room import Room


class RoomRepository:
    async def create(self, **kwargs) -> Room:
        async with async_session_factory() as session:
            room = Room(**kwargs)
            session.add(room)
            await session.commit()
            await session.refresh(room)
            return room

    async def get_by_code(self, code: str) -> Room | None:
        async with async_session_factory() as session:
            result = await session.execute(select(Room).where(Room.code == code))
            return result.scalar_one_or_none()

    async def get_by_code_with_players(self, code: str) -> Room | None:
        """Fetch room + eagerly loaded players within a single session."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Room)
                .where(Room.code == code)
                .options(selectinload(Room.players))
            )
            return result.scalar_one_or_none()

    async def get_by_id(self, room_id: uuid.UUID) -> Room | None:
        async with async_session_factory() as session:
            return await session.get(Room, room_id)

    async def get_by_id_with_players(self, room_id: uuid.UUID) -> Room | None:
        """Fetch room + eagerly loaded players within a single session."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Room)
                .where(Room.id == room_id)
                .options(selectinload(Room.players))
            )
            return result.scalar_one_or_none()

    async def update_settings(self, room_id: uuid.UUID, **kwargs) -> Room | None:
        async with async_session_factory() as session:
            room = await session.get(Room, room_id)
            if not room:
                return None
            for key, value in kwargs.items():
                if hasattr(room, key):
                    setattr(room, key, value)
            await session.commit()
            await session.refresh(room)
            return room

    async def update_status(self, room_id: uuid.UUID, status: str) -> Room | None:
        async with async_session_factory() as session:
            room = await session.get(Room, room_id)
            if not room:
                return None
            room.status = status
            await session.commit()
            await session.refresh(room)
            return room

    async def delete(self, room_id: uuid.UUID) -> bool:
        async with async_session_factory() as session:
            room = await session.get(Room, room_id)
            if not room:
                return False
            await session.delete(room)
            await session.commit()
            return True
