import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SERVICE_KEY = os.getenv("SERVICE_KEY") or os.getenv("SECRET_KEY", "change_me_to_a_long_random_string")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF_THRESHOLD", "0.45"))
TRACKER = os.getenv("TRACKER", "bytetrack")
POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "0.2"))
