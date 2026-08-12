from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import httpx
import redis.asyncio as redis

from app.config import BACKEND_URL, REDIS_URL, SERVICE_KEY

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
EVENTS_CHANNEL = "visioncount:events"


@dataclass
class CountingEvent:
    camera_id: str
    track_id: int
    event_type: str  # ENTRY | EXIT
    direction: str | None = None
    confidence: float = 0.9
    timestamp: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


async def emit_event(event: CountingEvent) -> None:
    """Fan out an event: publish on Redis (for any local subscribers / horizontal
    scaling) and POST it to the backend so it lands in Postgres and reaches the
    dashboard over WebSocket."""
    payload = asdict(event)
    await redis_client.publish(EVENTS_CHANNEL, str(payload))

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(
                f"{BACKEND_URL}/internal/events",
                json=payload,
                headers={"X-Service-Key": SERVICE_KEY},
            )
        except httpx.HTTPError as exc:
            print(f"[ai-service] failed to deliver event to backend: {exc}")
