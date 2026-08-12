from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_id: str

    class Config:
        from_attributes = True


class CompanyOut(BaseModel):
    id: str
    name: str
    slug: str
    timezone: str

    class Config:
        from_attributes = True


class BranchOut(BaseModel):
    id: str
    name: str
    address: str | None = None
    visitor_limit: int | None = None
    camera_count: int = 0
    cameras_online: int = 0
    visitors_today: int = 0
    entries_today: int = 0
    exits_today: int = 0
    current_occupancy: int = 0
    avg_dwell_minutes: float = 0.0

    class Config:
        from_attributes = True


class BranchCreate(BaseModel):
    name: str
    address: str | None = None
    visitor_limit: int | None = None


class CameraOut(BaseModel):
    id: str
    branch_id: str
    name: str
    camera_type: str
    fps: int
    status: str
    entries_today: int = 0
    exits_today: int = 0
    last_seen_at: datetime | None = None

    class Config:
        from_attributes = True


class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    rtsp_login: str | None = None
    rtsp_password: str | None = None
    branch_id: str
    camera_type: str = "RTSP"
    fps: int = 25


class CameraUpdate(BaseModel):
    name: str | None = None
    rtsp_url: str | None = None
    rtsp_login: str | None = None
    rtsp_password: str | None = None
    camera_type: str | None = None
    fps: int | None = None


class CameraTestResult(BaseModel):
    ok: bool
    message: str
    resolved_fps: int | None = None


class LineCrossingConfig(BaseModel):
    entry_line: list[dict]
    exit_line: list[dict]
    detection_zone: list[dict] | None = None


class DashboardKpis(BaseModel):
    visitors_today: int
    entries: int
    exits: int
    current_inside: int
    avg_dwell_minutes: float
    conversion_rate: float
    deltas: dict[str, float]


class HourlyPoint(BaseModel):
    hour: str
    entries: int
    exits: int


class DailyPoint(BaseModel):
    date: str
    entries: int
    exits: int


class HeatmapCell(BaseModel):
    zone: str
    slot: str
    value: int


class AlertOut(BaseModel):
    id: str
    type: str
    title: str
    message: str
    branch_id: str | None = None
    camera_id: str | None = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReportRequest(BaseModel):
    type: str
    format: str
    period_start: datetime
    period_end: datetime
    branch_id: str | None = None


class ReportOut(BaseModel):
    id: str
    type: str
    format: str
    file_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventIngest(BaseModel):
    """Payload the AI service posts for each detected line-crossing event."""
    camera_id: str
    track_id: int
    event_type: str  # ENTRY | EXIT
    direction: str | None = None
    confidence: float = 0.9
    timestamp: datetime | None = None
