"""Real-camera frame capture via RTSP (OpenCV/FFmpeg backend).
Runs locally on the branch monoblock, in the same network as the camera —
no port forwarding, no public IP needed (master-prompt раздел 3, 6, 7).
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
