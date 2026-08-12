"""Demo Mode: synthesizes plausible foot-traffic for a camera without any real
RTSP feed. Generates a stream of simulated 'people' crossing a virtual entry line
then, a little later, a virtual exit line — producing the exact same ENTRY/EXIT
event shape the real YOLO -> ByteTrack -> line-crossing pipeline would, so the
rest of the system (backend, dashboard, WebSocket) can't tell the difference.
"""
import asyncio
import random

from app.events import CountingEvent, emit_event

# Rough hourly traffic shape (0 = quietest hour, 44 = busiest) reused to make the
# demo feel like a real retail floor rather than uniform random noise.
HOURLY_SHAPE = [2,1,1,1,2,4,9,18,26,31,29,34,38,36,30,27,33,41,44,39,29,18,10,5]


class DemoCameraSource:
    def __init__(self, camera_id: str, camera_name: str):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self._next_track_id = 1

    def _spawn_interval(self) -> float:
        import datetime
        hour = datetime.datetime.now().hour
        weight = HOURLY_SHAPE[hour] + 1
        base = 1500.0 / weight  # busier hours -> shorter gaps between visitors
        return max(0.6, base) * random.uniform(0.6, 1.4)

    async def run(self) -> None:
        while True:
            await asyncio.sleep(self._spawn_interval())
            track_id = self._next_track_id
            self._next_track_id += 1

            await emit_event(CountingEvent(
                camera_id=self.camera_id, track_id=track_id, event_type="ENTRY",
                direction="in", confidence=round(random.uniform(0.82, 0.98), 2),
            ))

            # Most visitors leave again within a short, randomized dwell window.
            if random.random() < 0.9:
                asyncio.create_task(self._delayed_exit(track_id))

    async def _delayed_exit(self, track_id: int) -> None:
        await asyncio.sleep(random.uniform(8, 40))
        await emit_event(CountingEvent(
            camera_id=self.camera_id, track_id=track_id, event_type="EXIT",
            direction="out", confidence=round(random.uniform(0.82, 0.98), 2),
        ))
