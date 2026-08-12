import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class CameraStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class EventType(str, enum.Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class AlertType(str, enum.Enum):
    CAMERA_OFFLINE = "CAMERA_OFFLINE"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    ANOMALY_DROP = "ANOMALY_DROP"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    users: Mapped[list["User"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    branches: Mapped[list["Branch"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped["Company"] = relationship(back_populates="users")


class Branch(TimestampMixin, Base):
    __tablename__ = "branches"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    visitor_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="branches")
    cameras: Mapped[list["Camera"]] = relationship(back_populates="branch", cascade="all, delete-orphan")


class Camera(TimestampMixin, Base):
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rtsp_url: Mapped[str] = mapped_column(String(500))
    rtsp_login: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rtsp_password_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)
    camera_type: Mapped[str] = mapped_column(String(50), default="RTSP")
    fps: Mapped[int] = mapped_column(Integer, default=25)
    status: Mapped[CameraStatus] = mapped_column(Enum(CameraStatus), default=CameraStatus.OFFLINE)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    branch: Mapped["Branch"] = relationship(back_populates="cameras")
    config: Mapped["CameraConfig"] = relationship(back_populates="camera", uselist=False, cascade="all, delete-orphan")
    events: Mapped[list["AnalyticsEvent"]] = relationship(back_populates="camera", cascade="all, delete-orphan")


class CameraConfig(TimestampMixin, Base):
    """Line-crossing configuration: entry/exit line coordinates on the frame."""
    __tablename__ = "camera_configs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), unique=True)
    # Normalized (0..1) coordinates: [{x, y}, {x, y}] per line
    entry_line: Mapped[dict] = mapped_column(JSONB, default=dict)
    exit_line: Mapped[dict] = mapped_column(JSONB, default=dict)
    detection_zone: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    camera: Mapped["Camera"] = relationship(back_populates="config")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
    track_id: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))
    direction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    camera: Mapped["Camera"] = relationship(back_populates="events")


class DailyStatistic(Base):
    __tablename__ = "daily_statistics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    total_entries: Mapped[int] = mapped_column(Integer, default=0)
    total_exits: Mapped[int] = mapped_column(Integer, default=0)
    peak_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    avg_dwell_minutes: Mapped[float] = mapped_column(Float, default=0.0)


class HourlyStatistic(Base):
    __tablename__ = "hourly_statistics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    hour_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    entries: Mapped[int] = mapped_column(Integer, default=0)
    exits: Mapped[int] = mapped_column(Integer, default=0)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    camera_id: Mapped[str | None] = mapped_column(ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[AlertType] = mapped_column(Enum(AlertType))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(100))
    format: Mapped[str] = mapped_column(String(20))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
