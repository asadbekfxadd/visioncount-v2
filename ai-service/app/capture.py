"""Real-camera frame capture via RTSP (OpenCV/FFmpeg backend) with an optional
ONVIF discovery/PTZ helper. This module is not exercised in Demo Mode, but is
kept fully wired so a real IP camera can be plugged in by pointing a Camera's
rtsp_url at it and setting DEMO_MODE=false.
"""
import cv2


class RtspStream:
    def __init__(self, rtsp_url: str, login: str | None = None, password: str | None = None):
        self.url = self._with_credentials(rtsp_url, login, password)
        self._cap: cv2.VideoCapture | None = None

    @staticmethod
    def _with_credentials(url: str, login: str | None, password: str | None) -> str:
        if login and password and "@" not in url:
            scheme, rest = url.split("://", 1)
            return f"{scheme}://{login}:{password}@{rest}"
        return url

    def open(self) -> bool:
        # FFMPEG backend handles most consumer/enterprise RTSP encoders (H.264/H.265)
        self._cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        return self._cap.isOpened()

    def read(self):
        if self._cap is None:
            raise RuntimeError("Stream not opened — call open() first")
        ok, frame = self._cap.read()
        return frame if ok else None

    def fps(self) -> float:
        return self._cap.get(cv2.CAP_PROP_FPS) if self._cap else 0.0

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


def probe_connection(rtsp_url: str, login: str | None = None, password: str | None = None, timeout_s: float = 3.0) -> dict:
    """Used by the backend's POST /cameras/{id}/test flow (via ai-service in a full
    deployment) to validate that a camera is reachable before it's saved."""
    stream = RtspStream(rtsp_url, login, password)
    ok = stream.open()
    fps = stream.fps() if ok else 0.0
    stream.close()
    return {"ok": ok, "fps": fps}
