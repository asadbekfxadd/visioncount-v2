"""Configuration for VisionCount Agent (Phase 3 skeleton).
Loaded from .env — never hardcode camera credentials in source.
"""
import os

from dotenv import load_dotenv

load_dotenv()

CAMERA_NAME = os.getenv("CAMERA_NAME", "Atlas Chimgan")
RTSP_URL = os.getenv("RTSP_URL", "rtsp://81.95.228.80:8098/Streaming/Channels/102")
RTSP_LOGIN = os.getenv("RTSP_LOGIN", "admin")
RTSP_PASSWORD = os.getenv("RTSP_PASSWORD", "")

# How often (seconds) to print an FPS/status line while the smoke test runs.
REPORT_INTERVAL_SECONDS = float(os.getenv("REPORT_INTERVAL_SECONDS", "2.0"))

# Reconnect behaviour (used from Phase 3 onward, ties into raздел 30 — auto recovery)
RECONNECT_DELAY_SECONDS = float(os.getenv("RECONNECT_DELAY_SECONDS", "3.0"))
