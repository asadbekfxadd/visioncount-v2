"""Person detection via YOLO (Ultralytics). COCO class 0 = person."""
from dataclasses import dataclass

from app.config import YOLO_CONF_THRESHOLD, YOLO_MODEL_PATH

PERSON_CLASS_ID = 0


@dataclass
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float

    @property
    def centroid(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2


class PersonDetector:
    def __init__(self, model_path: str = YOLO_MODEL_PATH, conf_threshold: float = YOLO_CONF_THRESHOLD):
        from ultralytics import YOLO  # imported lazily so demo mode doesn't require the weights

        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame) -> list[Detection]:
        results = self.model.predict(frame, classes=[PERSON_CLASS_ID], conf=self.conf_threshold, verbose=False)
        detections: list[Detection] = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(Detection(x1, y1, x2, y2, float(box.conf[0])))
        return detections
