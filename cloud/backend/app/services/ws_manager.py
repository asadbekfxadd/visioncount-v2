import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:
    """Keeps track of open WebSocket connections per channel (dashboard, camera:<id>)."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.setdefault(channel, set()).add(ws)

    async def disconnect(self, channel: str, ws: WebSocket) -> None:
        async with self._lock:
            if channel in self._connections:
                self._connections[channel].discard(ws)
                if not self._connections[channel]:
                    del self._connections[channel]

    async def broadcast(self, channel: str, message: dict) -> None:
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in self._connections.get(channel, set()):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(channel, ws)


manager = ConnectionManager()
