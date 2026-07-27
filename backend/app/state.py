"""Shared application state - singleton instances for WebSocket manager and handler."""

from app.websocket.manager import ConnectionManager
from app.websocket.handler import MessageHandler

manager = ConnectionManager()
handler = MessageHandler(manager)
