"""VisionCount Agent — Phase 3 smoke test.

Goal (per docs/PHASE1-PLAN.md, section 14): prove the Agent can open a real
RTSP stream on the branch's local network and read frames reliably, before
wiring in YOLO detection / tracking / line crossing / sync.

Run this ON the monoblock, in the same local network as the camera — e.g. use
the camera's LOCAL IP (192.168.0.165:554) if the Agent runs at the branch, or
the port-forwarded external address if testing remotely.

Usage:
    python -m agent.core.main
"""
import sys
import time
from pathlib import Path

# Allow running as `python -m agent.core.main` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent.camera.capture import RtspStream
from agent.core import config


def run() -> None:
    print(f"[agent] VisionCount Agent — Phase 3 smoke test")
    print(f"[agent] camera: {config.CAMERA_NAME}")
    print(f"[agent] connecting to RTSP stream...")

    while True:
        stream = RtspStream(config.RTSP_URL, config.RTSP_LOGIN, config.RTSP_PASSWORD)
        if not stream.open():
            print(f"[agent] could not open stream, retrying in {config.RECONNECT_DELAY_SECONDS}s...")
            time.sleep(config.RECONNECT_DELAY_SECONDS)
            continue

        print(f"[agent] stream opened. reported fps: {stream.fps():.1f}")
        frame_count = 0
        last_report = time.time()

        try:
            while True:
                frame = stream.read()
                if frame is None:
                    print("[agent] lost frame / stream ended, reconnecting...")
                    break

                frame_count += 1
                now = time.time()
                elapsed = now - last_report
                if elapsed >= config.REPORT_INTERVAL_SECONDS:
                    measured_fps = frame_count / elapsed
                    h, w = frame.shape[:2]
                    print(f"[agent] OK — {measured_fps:.1f} fps measured, frame size {w}x{h}")
                    frame_count = 0
                    last_report = now
        finally:
            stream.close()

        time.sleep(config.RECONNECT_DELAY_SECONDS)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[agent] stopped by user")
