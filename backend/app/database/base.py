from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models AFTER Base is defined to register them on the metadata
# (required by Alembic for auto-detection).
import app.models  # noqa: F401, E402
