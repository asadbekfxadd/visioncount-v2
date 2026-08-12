"""Entrypoint for the AI Video Analytics Service.
Pipeline (per camera, real mode):
  RTSP -> frame extraction -> YOLO person detection -> ByteTrack-style tracking
  -> line crossing -> ENTRY/EXIT event -> emit_event() -> Redis + backend -> dashboard
In Demo Mode (default), DemoCameraSource replaces the capture/detect/track/line-
crossing stages with a synthetic-but-realistic event generator so the whole
product can be shown end-to-end without any physical camera connected.
"""
import asyncio
import httpx
from app.config import BACKEND_URL, DEMO_MODE, POLL_INTERVAL_SECONDS, SERVICE_KEY
from app.demo_source import DemoCameraSource
async def fetch_cameras() -> list[dict]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{BACKEND_URL}/internal/cameras", headers={"X-Service-Key": SERVICE_KEY})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            print(f"[ai-service] could not reach backend yet ({exc}), retrying...")
            return []
async def run_real_pipeline(camera: dict) -> None:
    """Real-camera path: RTSP capture -> YOLO -> tracker -> line crossing.
    Left as an explicit, runnable stub — wire in app.capture.RtspStream,
    app.detector.PersonDetector and app.tracker.ByteTrackStyleTracker here to go live."""
    from app.capture import RtspStream
    from app.detector import PersonDetector
    from app.line_crossing import Line, LineCrossingCounter
    from app.tracker import ByteTrackStyleTracker
    from app.events import CountingEvent, emit_event
    stream = RtspStream(camera["rtsp_url"], camera.get("rtsp_login"), camera.get("rtsp_password"))
    if not stream.open():
        print(f"[ai-service] camera {camera['name']}: RTSP stream unreachable, skipping")
        return
    detector = PersonDetector()
    tracker = ByteTrackStyleTracker()
    # Line coordinates are normally loaded from CameraConfig; using sane defaults here.
    counter = LineCrossingCounter(
        entry_line=Line(0.3, 0, 0.3, 1),
        exit_line=Line(0.7, 0, 0.7, 1),
    )
    while True:
        frame = stream.read()
        if frame is None:
            await asyncio.sleep(1.0)
            continue
        detections = detector.detect(frame)
        tracks = tracker.update(detections)
        for track_id, event_type in counter.process(tracks):
            await emit_event(CountingEvent(camera_id=camera["id"], track_id=track_id, event_type=event_type))
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
async def run_demo_pipeline(camera: dict) -> None:
    source = DemoCameraSource(camera_id=camera["id"], camera_name=camera["name"])
    await source.run()
async def main() -> None:
    print(f"[ai-service] starting — DEMO_MODE={DEMO_MODE}")
    cameras: list[dict] = []
    while not cameras:
        cameras = await fetch_cameras()
        if not cameras:
            await asyncio.sleep(2.0)
    print(f"[ai-service] discovered {len(cameras)} camera(s)")
    tasks = []
    for camera in cameras:
        runner = run_demo_pipeline if DEMO_MODE else run_real_pipeline
        tasks.append(asyncio.create_task(runner(camera)))
    await asyncio.gather(*tasks)
if __name__ == "__main__":
    asyncio.run(main())
