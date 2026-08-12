"""Multi-object tracker matching detections across frames into stable track IDs.

Exposes the same update(detections) -> list[Track] interface the pipeline expects.
Swap the body of `update()` for the official `bytetrack` package in production for
stronger re-identification under occlusion; this centroid/IOU matcher is a
dependency-light stand-in that is good enough to demonstrate line crossing.
"""
from dataclasses import dataclass, field

from app.detector import Detection


@dataclass
class Track:
    track_id: int
    last_centroid: tuple[float, float]
    history: list[tuple[float, float]] = field(default_factory=list)
    misses: int = 0


class ByteTrackStyleTracker:
    def __init__(self, max_misses: int = 8, match_distance_px: float = 80.0):
        self.max_misses = max_misses
        self.match_distance_px = match_distance_px
        self._tracks: dict[int, Track] = {}
        self._next_id = 1

    def update(self, detections: list[Detection]) -> list[Track]:
        unmatched_detections = list(detections)
        matched_ids: set[int] = set()

        for track in self._tracks.values():
            best, best_dist = None, self.match_distance_px
            for det in unmatched_detections:
                dist = _euclidean(track.last_centroid, det.centroid)
                if dist < best_dist:
                    best, best_dist = det, dist
            if best is not None:
                track.last_centroid = best.centroid
                track.history.append(best.centroid)
                track.misses = 0
                matched_ids.add(track.track_id)
                unmatched_detections.remove(best)

        for track in self._tracks.values():
            if track.track_id not in matched_ids:
                track.misses += 1

        for det in unmatched_detections:
            track = Track(track_id=self._next_id, last_centroid=det.centroid, history=[det.centroid])
            self._tracks[self._next_id] = track
            self._next_id += 1

        self._tracks = {tid: t for tid, t in self._tracks.items() if t.misses <= self.max_misses}
        return list(self._tracks.values())


def _euclidean(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
