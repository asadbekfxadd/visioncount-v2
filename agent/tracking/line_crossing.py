"""Determines when a tracked person's trajectory crosses the configured entry/exit
lines, and turns that into a single ENTRY or EXIT event per track (never both from
the same crossing, and never double-counted while the track persists)."""
from dataclasses import dataclass

from app.tracker import Track


@dataclass
class Line:
    x1: float
    y1: float
    x2: float
    y2: float


def _side(line: Line, point: tuple[float, float]) -> float:
    return (line.x2 - line.x1) * (point[1] - line.y1) - (line.y2 - line.y1) * (point[0] - line.x1)


class LineCrossingCounter:
    def __init__(self, entry_line: Line, exit_line: Line):
        self.entry_line = entry_line
        self.exit_line = exit_line
        self._entered: set[int] = set()
        self._exited: set[int] = set()
        self._last_side: dict[int, tuple[float, float]] = {}

    def process(self, tracks: list[Track]) -> list[tuple[int, str]]:
        events: list[tuple[int, str]] = []
        for track in tracks:
            if len(track.history) < 2:
                continue
            prev_point, curr_point = track.history[-2], track.history[-1]

            if track.track_id not in self._entered:
                if _crossed(self.entry_line, prev_point, curr_point):
                    self._entered.add(track.track_id)
                    events.append((track.track_id, "ENTRY"))

            if track.track_id in self._entered and track.track_id not in self._exited:
                if _crossed(self.exit_line, prev_point, curr_point):
                    self._exited.add(track.track_id)
                    events.append((track.track_id, "EXIT"))

        return events


def _crossed(line: Line, prev_point: tuple[float, float], curr_point: tuple[float, float]) -> bool:
    return (_side(line, prev_point) > 0) != (_side(line, curr_point) > 0)
